import asyncio
import json
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

import aiofiles
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise
from tortoise.expressions import Q

from config import LEGACY_JSON, MAX_AVATAR_MB, TORTOISE_ORM, UPLOAD_DIR
from models import Favorite, Message, Persona, User, UserSettings
from auth import (
    auth_middleware,
    clear_login_failures,
    create_access_token,
    create_refresh_token,
    ensure_default_user,
    get_current_user,
    hash_password,
    is_login_locked,
    register_login_failure,
    rotate_refresh_session,
    verify_password,
    verify_refresh_token,
)
from ai_client import (
    build_chat_messages,
    contains_ai_mention,
    format_ai_storage_content,
    iter_ai_reply_stream,
    request_ai_reply,
    sse_line,
    strip_ai_storage_markers,
)
from deepseek_share import DeepSeekShareError, extract_share_id, fetch_share_payload, parse_share_messages, preview_share
from schemas import (
    AiReplyRequest,
    AiReviewRequest,
    AuthTokensOut,
    AuthUserOut,
    ChangePasswordRequest,
    ChangeUsernameRequest,
    DeepSeekShareImportOut,
    DeepSeekShareImportRequest,
    DeepSeekSharePreviewOut,
    LoginRequest,
    MessageAttachmentOut,
    MessageCreate,
    MessageListOut,
    MessageOut,
    MessageUpdate,
    PersonaCreate,
    PersonaOut,
    PersonaUpdate,
    QuotePreview,
    RefreshRequest,
    SetActivePersonaRequest,
    SettingsOut,
    SettingsUpdate,
    UploadOut,
)
from seed import (
    remove_demo_messages,
    seed_demo_messages,
    seed_personas,
    upgrade_builtin_personas,
)
from settings_store import get_settings, update_settings, has_api_key
from storage import (
    IMAGE_EXTENSIONS,
    delete_media_url,
    detect_kind,
    is_image_file,
    resolve_upload_path,
    sanitize_filename,
    save_media_file,
)


def normalize_message_role(role: str) -> str:
    """Only me (self-written) and ai (tool-generated) exist; legacy god counts as me."""
    return "ai" if role == "ai" else "me"


def parse_attachments(raw: str | None) -> list[MessageAttachmentOut] | None:
    if not raw:
        return None
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(items, list):
        return None
    return [MessageAttachmentOut.model_validate(item) for item in items]


def parse_tags(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(items, list):
        return None
    return [str(item) for item in items]


TAG_PATTERN = re.compile(r"#([^\s#]{1,20})")
KEYWORD_PATTERN = re.compile(r"[\w一-鿿]{2,}")


def extract_tags(content: str) -> list[str]:
    seen: list[str] = []
    for match in TAG_PATTERN.finditer(content):
        tag = match.group(1)
        if tag not in seen:
            seen.append(tag)
    return seen


def tags_json(content: str) -> str | None:
    tags = extract_tags(content)
    return json.dumps(tags, ensure_ascii=False) if tags else None


def extract_keywords(text: str, limit: int = 5) -> list[str]:
    candidates = TAG_PATTERN.findall(text) + KEYWORD_PATTERN.findall(text)
    seen: list[str] = []
    for word in candidates:
        if word not in seen:
            seen.append(word)
    seen.sort(key=len, reverse=True)
    return seen[:limit]


async def find_relevant_history(
    trigger_text: str, exclude_ids: set[str], limit: int = 8
) -> list[Message]:
    """轻量关键词检索增强：从触发消息里提取候选词，用现有的 icontains 搜索补充上下文。"""
    keywords = extract_keywords(trigger_text)
    if not keywords:
        return []

    collected: dict[str, Message] = {}
    for keyword in keywords:
        rows = (
            await Message.filter(content__icontains=keyword)
            .exclude(id__in=exclude_ids)
            .order_by("-created_at")
            .limit(limit)
        )
        for row in rows:
            collected[row.id] = row
        if len(collected) >= limit:
            break

    result = list(collected.values())[:limit]
    result.sort(key=lambda m: m.created_at)
    return result


def to_quote_preview(msg: Message) -> QuotePreview:
    attachments = parse_attachments(msg.attachments)
    media_url = msg.media_url
    if msg.type == "media_group" and attachments:
        first_image = next((item for item in attachments if item.type == "image"), None)
        if first_image:
            media_url = first_image.url

    return QuotePreview(
        id=msg.id,
        role=normalize_message_role(msg.role),
        type=msg.type,
        content=msg.content,
        mediaUrl=media_url,
        mediaName=msg.media_name,
    )


async def to_out(msg: Message, favorited_ids: set[str] | None = None) -> MessageOut:
    quote = None
    if msg.quote_id:
        quoted = await Message.get_or_none(id=msg.quote_id)
        if quoted:
            quote = to_quote_preview(quoted)

    attachments = parse_attachments(msg.attachments)
    media_url = msg.media_url
    if msg.type == "media_group" and attachments:
        first_image = next((item for item in attachments if item.type == "image"), None)
        if first_image:
            media_url = first_image.url

    if favorited_ids is not None:
        is_favorited = msg.id in favorited_ids
    else:
        is_favorited = await Favorite.filter(message_id=msg.id).exists()

    return MessageOut(
        id=msg.id,
        role=normalize_message_role(msg.role),
        type=msg.type,
        content=msg.content,
        mediaUrl=media_url,
        mediaName=msg.media_name,
        attachments=attachments,
        tags=parse_tags(getattr(msg, "tags", None)),
        isFavorited=is_favorited,
        quoteId=msg.quote_id,
        quote=quote,
        authorAvatarUrl=getattr(msg, "author_avatar_url", None),
        authorDisplayName=getattr(msg, "author_display_name", None),
        createdAt=msg.created_at,
    )


async def to_settings_out(settings: UserSettings) -> SettingsOut:
    provider = settings.ai_provider
    if provider not in ("deepseek", "openai", "ollama", "custom"):
        provider = "custom"
    return SettingsOut(
        displayName=settings.display_name,
        avatarUrl=settings.avatar_url,
        aiProvider=provider,
        aiModel=settings.ai_model,
        aiBaseUrl=settings.ai_base_url,
        hasApiKey=has_api_key(settings),
        aiSystemPrompt=settings.ai_system_prompt,
        aiThinking=bool(getattr(settings, "ai_thinking", True)),
        avatarTransparent=bool(getattr(settings, "avatar_transparent", False)),
        activePersonaId=getattr(settings, "active_persona_id", None),
    )


def to_persona_out(persona: Persona) -> PersonaOut:
    return PersonaOut(
        id=persona.id,
        name=persona.name,
        icon=persona.icon,
        systemPrompt=persona.system_prompt,
        isBuiltin=persona.is_builtin,
    )


async def ensure_settings_columns() -> None:
    conn = Tortoise.get_connection("default")
    _, rows = await conn.execute_query("PRAGMA table_info(user_settings)")
    columns = {row[1] for row in rows}
    if "ai_thinking" not in columns:
        await conn.execute_script(
            "ALTER TABLE user_settings ADD COLUMN ai_thinking INTEGER NOT NULL DEFAULT 1"
        )
    if "avatar_transparent" not in columns:
        await conn.execute_script(
            "ALTER TABLE user_settings ADD COLUMN avatar_transparent INTEGER NOT NULL DEFAULT 0"
        )
    if "pinned_message_id" not in columns:
        # 历史遗留列：仅用于 migrate_legacy_pin() 一次性读取旧的单条置顶值，
        # 不在模型里声明，也不再被业务代码写入。
        await conn.execute_script(
            "ALTER TABLE user_settings ADD COLUMN pinned_message_id VARCHAR(64) NULL"
        )
    if "active_persona_id" not in columns:
        await conn.execute_script(
            "ALTER TABLE user_settings ADD COLUMN active_persona_id VARCHAR(64) NULL"
        )


async def migrate_legacy_god_role() -> None:
    conn = Tortoise.get_connection("default")
    await conn.execute_script("UPDATE messages SET role='me' WHERE role='god'")


async def ensure_message_columns() -> None:
    conn = Tortoise.get_connection("default")
    _, rows = await conn.execute_query("PRAGMA table_info(messages)")
    columns = {row[1] for row in rows}
    if "quote_id" not in columns:
        await conn.execute_script(
            "ALTER TABLE messages ADD COLUMN quote_id VARCHAR(64) NULL"
        )
        await conn.execute_script(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_quote_id "
            "ON messages(quote_id) WHERE quote_id IS NOT NULL"
        )
    if "media_name" not in columns:
        await conn.execute_script(
            "ALTER TABLE messages ADD COLUMN media_name VARCHAR(255) NULL"
        )
    if "attachments" not in columns:
        await conn.execute_script(
            "ALTER TABLE messages ADD COLUMN attachments TEXT NULL"
        )
    if "reply_to_id" not in columns:
        await conn.execute_script(
            "ALTER TABLE messages ADD COLUMN reply_to_id VARCHAR(64) NULL"
        )
        await conn.execute_script(
            "CREATE INDEX IF NOT EXISTS idx_messages_reply_to_id "
            "ON messages(reply_to_id) WHERE reply_to_id IS NOT NULL"
        )
    if "author_avatar_url" not in columns:
        await conn.execute_script(
            "ALTER TABLE messages ADD COLUMN author_avatar_url VARCHAR(512) NULL"
        )
    if "author_display_name" not in columns:
        await conn.execute_script(
            "ALTER TABLE messages ADD COLUMN author_display_name VARCHAR(64) NULL"
        )
    if "tags" not in columns:
        await conn.execute_script(
            "ALTER TABLE messages ADD COLUMN tags TEXT NULL"
        )


async def migrate_legacy_pin() -> None:
    """把旧的单值 pinned_message_id 迁移成收藏夹里的一条记录（幂等，可重复执行）。"""
    conn = Tortoise.get_connection("default")
    _, rows = await conn.execute_query("PRAGMA table_info(user_settings)")
    columns = {row[1] for row in rows}
    if "pinned_message_id" not in columns:
        return

    _, settings_rows = await conn.execute_query(
        "SELECT pinned_message_id FROM user_settings WHERE id='default'"
    )
    if not settings_rows or not settings_rows[0][0]:
        return

    pinned_id = settings_rows[0][0]
    exists = await Message.filter(id=pinned_id).exists()
    if not exists:
        return

    await Favorite.get_or_create(
        message_id=pinned_id,
        defaults={"id": f"fav-{uuid.uuid4().hex[:12]}"},
    )


async def validate_quote(quote_id: str | None) -> None:
    if not quote_id:
        return

    target = await Message.get_or_none(id=quote_id)
    if not target:
        raise HTTPException(status_code=404, detail="引用的消息不存在")

    already_used = await Message.filter(quote_id=quote_id).exists()
    if already_used:
        raise HTTPException(status_code=409, detail="该消息已被引用，不能再次引用")


async def get_author_snapshot(role: str) -> dict[str, str | None]:
    if normalize_message_role(role) != "me":
        return {}
    settings = await get_settings()
    return {
        "author_avatar_url": settings.avatar_url,
        "author_display_name": settings.display_name,
    }


async def create_media_message_record(
    saved: list[tuple[str, str, str]],
    caption: str,
    quote_id: str | None,
    role: str = "me",
) -> Message:
    safe_role = normalize_message_role(role)
    author_fields = await get_author_snapshot(safe_role)
    tags = tags_json(caption)

    if len(saved) == 1:
        media_url, media_name, kind = saved[0]
        return await Message.create(
            id=f"msg-{uuid.uuid4().hex[:12]}",
            role=safe_role,
            type=kind,
            content=caption,
            media_url=media_url,
            media_name=media_name,
            quote_id=quote_id,
            tags=tags,
            **author_fields,
        )

    attachments = [{"type": kind, "url": url, "name": name} for url, name, kind in saved]
    return await Message.create(
        id=f"msg-{uuid.uuid4().hex[:12]}",
        role=safe_role,
        type="media_group",
        content=caption,
        media_url=attachments[0]["url"],
        attachments=json.dumps(attachments, ensure_ascii=False),
        quote_id=quote_id,
        tags=tags,
        **author_fields,
    )


async def import_legacy_messages() -> None:
    if not LEGACY_JSON.exists():
        return
    if await Message.exists():
        return

    raw = json.loads(LEGACY_JSON.read_text(encoding="utf-8"))
    for item in raw:
        created_raw = item.get("createdAt")
        if created_raw:
            created_at = datetime.fromisoformat(
                created_raw.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        else:
            created_at = datetime.now()

        await Message.create(
            id=item.get("id") or f"msg-{uuid.uuid4().hex[:12]}",
            role=normalize_message_role(item.get("role", "me")),
            type=item.get("type", "text"),
            content=item.get("content", ""),
            media_url=item.get("mediaUrl"),
            created_at=created_at,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await ensure_message_columns()
    await migrate_legacy_god_role()
    await ensure_settings_columns()
    await migrate_legacy_pin()
    await get_settings()
    await ensure_default_user()
    await import_legacy_messages()
    await remove_demo_messages()
    await seed_personas()
    await upgrade_builtin_personas()
    yield
    await Tortoise.close_connections()


app = FastAPI(title="与神对话 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(auth_middleware)


async def add_upload_security_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/uploads/"):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "sandbox"
    return response


app.middleware("http")(add_upload_security_headers)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.post("/api/auth/login", response_model=AuthTokensOut)
async def login(body: LoginRequest) -> AuthTokensOut:
    username = body.username.strip()
    if not username or not body.password:
        raise HTTPException(status_code=400, detail="请输入用户名和密码")

    if is_login_locked(username):
        raise HTTPException(status_code=429, detail="登录失败次数过多，请 5 分钟后再试")

    user = await User.get_or_none(username=username)
    if not user or not verify_password(body.password, user.password_hash):
        register_login_failure(username)
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    clear_login_failures(username)
    user = await rotate_refresh_session(user)
    return AuthTokensOut(
        accessToken=create_access_token(user),
        refreshToken=create_refresh_token(user),
        username=user.username,
    )


@app.post("/api/auth/refresh", response_model=AuthTokensOut)
async def refresh_tokens(body: RefreshRequest) -> AuthTokensOut:
    user = await verify_refresh_token(body.refreshToken)
    return AuthTokensOut(
        accessToken=create_access_token(user),
        refreshToken=create_refresh_token(user),
        username=user.username,
    )


@app.get("/api/auth/me", response_model=AuthUserOut)
async def read_auth_user(user: User = Depends(get_current_user)) -> AuthUserOut:
    return AuthUserOut(username=user.username)


@app.post("/api/auth/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    if len(body.newPassword.strip()) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")

    if not verify_password(body.currentPassword, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")

    user.password_hash = hash_password(body.newPassword)
    user = await rotate_refresh_session(user)
    await user.save(update_fields=["password_hash", "refresh_token_version"])
    return {"message": "密码已更新，请重新登录"}


@app.post("/api/auth/change-username", response_model=AuthUserOut)
async def change_username(
    body: ChangeUsernameRequest,
    user: User = Depends(get_current_user),
) -> AuthUserOut:
    new_username = body.newUsername.strip()
    if len(new_username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少 2 位")

    existing = await User.get_or_none(username=new_username)
    if existing and existing.id != user.id:
        raise HTTPException(status_code=409, detail="用户名已被占用")

    user.username = new_username
    await user.save(update_fields=["username"])
    return AuthUserOut(username=user.username)


MESSAGE_PAGE_DEFAULT = 60
MESSAGE_PAGE_MAX = 200


async def _favorited_ids_set() -> set[str]:
    return set(await Favorite.all().values_list("message_id", flat=True))


async def _messages_to_out(
    rows: list[Message], favorited_ids: set[str] | None = None
) -> list[MessageOut]:
    return [await to_out(msg, favorited_ids) for msg in rows]


def _older_than(anchor: Message) -> Q:
    """keyset：早于锚点（(created_at, id) 复合游标，稳定去重）。"""
    return Q(created_at__lt=anchor.created_at) | Q(
        created_at=anchor.created_at, id__lt=anchor.id
    )


def _newer_than(anchor: Message) -> Q:
    return Q(created_at__gt=anchor.created_at) | Q(
        created_at=anchor.created_at, id__gt=anchor.id
    )


async def _require_message(message_id: str) -> Message:
    anchor = await Message.get_or_none(id=message_id)
    if not anchor:
        raise HTTPException(status_code=404, detail="消息不存在")
    return anchor


async def _window_around(anchor: Message, limit: int) -> tuple[list[Message], bool, bool]:
    half = limit // 2
    older = await Message.filter(_older_than(anchor)).order_by(
        "-created_at", "-id"
    ).limit(half + 1)
    has_more_before = len(older) > half
    older = older[:half]
    older.reverse()
    newer = await Message.filter(_newer_than(anchor)).order_by(
        "created_at", "id"
    ).limit(half + 1)
    has_more_after = len(newer) > half
    newer = newer[:half]
    window = older + [anchor] + newer
    return window, has_more_before, has_more_after


@app.get("/api/messages", response_model=MessageListOut)
async def list_messages(
    q: str | None = None,
    tag: str | None = None,
    before: str | None = None,
    after: str | None = None,
    around: str | None = None,
    limit: int = MESSAGE_PAGE_DEFAULT,
) -> MessageListOut:
    """
    统一的消息读取入口：
    - q：全文搜索，返回最新的匹配项（倒序）+ 总匹配数 total。
    - tag：按标签过滤，返回最新的匹配项（倒序）+ 总匹配数 total。
    - before / after：以某条消息为游标向更早 / 更晚翻页。
    - around：围绕某条消息取一个窗口（用于搜索结果 / 引用跳转定位）。
    - 默认：返回最新一页，items 按时间升序。
    """
    limit = max(1, min(limit, MESSAGE_PAGE_MAX))
    favorited_ids = await _favorited_ids_set()

    keyword = (q or "").strip()
    if keyword:
        base = Message.filter(content__icontains=keyword)
        total = await base.count()
        rows = await base.order_by("-created_at", "-id").limit(limit)
        # 搜索结果按最新在前返回，供搜索面板直接展示。
        return MessageListOut(items=await _messages_to_out(rows, favorited_ids), total=total)

    tag_query = (tag or "").strip()
    if tag_query:
        base = Message.filter(tags__icontains=f'"{tag_query}"')
        total = await base.count()
        rows = await base.order_by("-created_at", "-id").limit(limit)
        return MessageListOut(items=await _messages_to_out(rows, favorited_ids), total=total)

    if before:
        anchor = await _require_message(before)
        rows = await Message.filter(_older_than(anchor)).order_by(
            "-created_at", "-id"
        ).limit(limit + 1)
        has_more_before = len(rows) > limit
        rows = rows[:limit]
        rows.reverse()
        return MessageListOut(
            items=await _messages_to_out(rows, favorited_ids),
            hasMoreBefore=has_more_before,
            hasMoreAfter=True,
        )

    if after:
        anchor = await _require_message(after)
        rows = await Message.filter(_newer_than(anchor)).order_by(
            "created_at", "id"
        ).limit(limit + 1)
        has_more_after = len(rows) > limit
        rows = rows[:limit]
        return MessageListOut(
            items=await _messages_to_out(rows, favorited_ids),
            hasMoreBefore=True,
            hasMoreAfter=has_more_after,
        )

    if around:
        anchor = await _require_message(around)
        window, has_more_before, has_more_after = await _window_around(anchor, limit)
        return MessageListOut(
            items=await _messages_to_out(window, favorited_ids),
            hasMoreBefore=has_more_before,
            hasMoreAfter=has_more_after,
        )

    total = await Message.all().count()
    rows = await Message.all().order_by("-created_at", "-id").limit(limit)
    has_more_before = total > len(rows)
    rows.reverse()
    return MessageListOut(
        items=await _messages_to_out(rows, favorited_ids),
        hasMoreBefore=has_more_before,
        hasMoreAfter=False,
    )


@app.get("/api/messages/near-date", response_model=MessageListOut)
async def messages_near_date(date: str, limit: int = MESSAGE_PAGE_DEFAULT) -> MessageListOut:
    """时间线导航：定位到某个日期附近的消息窗口。"""
    limit = max(1, min(limit, MESSAGE_PAGE_MAX))
    try:
        day_start = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD") from exc

    anchor = await Message.filter(created_at__gte=day_start).order_by("created_at", "id").first()
    if not anchor:
        anchor = await Message.filter(created_at__lt=day_start).order_by("-created_at", "-id").first()
    if not anchor:
        raise HTTPException(status_code=404, detail="没有可定位的消息")

    favorited_ids = await _favorited_ids_set()
    window, has_more_before, has_more_after = await _window_around(anchor, limit)
    return MessageListOut(
        items=await _messages_to_out(window, favorited_ids),
        hasMoreBefore=has_more_before,
        hasMoreAfter=has_more_after,
        anchorId=anchor.id,
    )


@app.get("/api/messages/{message_id}", response_model=MessageOut)
async def get_message(message_id: str) -> MessageOut:
    return await to_out(await _require_message(message_id))


@app.put("/api/messages/{message_id}", response_model=MessageOut)
async def update_message(message_id: str, body: MessageUpdate) -> MessageOut:
    msg = await _require_message(message_id)
    content = body.content.strip()
    if msg.type == "text" and not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    msg.content = content
    msg.tags = tags_json(content)
    await msg.save(update_fields=["content", "tags"])
    return await to_out(msg)


@app.post("/api/messages/ai-reply", response_model=MessageOut, status_code=201)
async def create_ai_reply(body: AiReplyRequest) -> MessageOut:
    trigger = await Message.get_or_none(id=body.triggerMessageId)
    if not trigger:
        raise HTTPException(status_code=404, detail="触发消息不存在")

    if not body.force and not contains_ai_mention(trigger.content):
        raise HTTPException(status_code=400, detail="消息中未包含 @ai")

    existing = await Message.filter(
        reply_to_id=body.triggerMessageId,
        role="ai",
    ).first()
    if existing:
        return await to_out(existing)

    settings = await get_settings()
    history = (
        await Message.filter(created_at__lt=trigger.created_at)
        .order_by("-created_at")
        .limit(30)
    )
    history.reverse()

    persona = None
    if settings.active_persona_id:
        persona = await Persona.get_or_none(id=settings.active_persona_id)

    exclude_ids = {m.id for m in history} | {trigger.id}
    relevant = await find_relevant_history(trigger.content, exclude_ids)

    try:
        chat_messages = await build_chat_messages(
            settings,
            history,
            trigger,
            relevant=relevant,
            system_prompt_override=persona.system_prompt if persona else None,
        )
        reply_text = await request_ai_reply(settings, chat_messages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI 调用失败: {exc}") from exc

    ai_msg = await Message.create(
        id=f"msg-{uuid.uuid4().hex[:12]}",
        role="ai",
        type="text",
        content=reply_text,
        reply_to_id=body.triggerMessageId,
    )
    return await to_out(ai_msg)


@app.post("/api/messages/ai-reply/stream")
async def stream_ai_reply(body: AiReplyRequest) -> StreamingResponse:
    trigger = await Message.get_or_none(id=body.triggerMessageId)
    if not trigger:
        raise HTTPException(status_code=404, detail="触发消息不存在")

    if not body.force and not contains_ai_mention(trigger.content):
        raise HTTPException(status_code=400, detail="消息中未包含 @ai")

    existing = await Message.filter(
        reply_to_id=body.triggerMessageId,
        role="ai",
    ).first()

    settings = await get_settings()
    history = (
        await Message.filter(created_at__lt=trigger.created_at)
        .order_by("-created_at")
        .limit(30)
    )
    history.reverse()

    persona = None
    if settings.active_persona_id:
        persona = await Persona.get_or_none(id=settings.active_persona_id)

    exclude_ids = {m.id for m in history} | {trigger.id}
    relevant = await find_relevant_history(trigger.content, exclude_ids)

    async def event_generator():
        if existing:
            yield sse_line({"type": "done", "message": (await to_out(existing)).model_dump(mode="json")})
            return

        try:
            chat_messages = await build_chat_messages(
                settings,
                history,
                trigger,
                relevant=relevant,
                system_prompt_override=persona.system_prompt if persona else None,
            )
            thinking = ""
            answer = ""

            async for event in iter_ai_reply_stream(settings, chat_messages):
                if event["type"] == "thinking":
                    thinking += event["delta"]
                    yield sse_line(event)
                    await asyncio.sleep(0)
                elif event["type"] == "content":
                    answer += event["delta"]
                    yield sse_line(event)
                    await asyncio.sleep(0)
                elif event["type"] == "complete":
                    thinking = event.get("thinking", thinking)
                    answer = event.get("answer", answer)

            content = format_ai_storage_content(thinking, answer)
            ai_msg = await Message.create(
                id=f"msg-{uuid.uuid4().hex[:12]}",
                role="ai",
                type="text",
                content=content,
                reply_to_id=body.triggerMessageId,
            )
            yield sse_line(
                {
                    "type": "done",
                    "message": (await to_out(ai_msg)).model_dump(mode="json"),
                }
            )
        except ValueError as exc:
            yield sse_line({"type": "error", "error": str(exc)})
        except RuntimeError as exc:
            yield sse_line({"type": "error", "error": str(exc)})
        except Exception as exc:
            yield sse_line({"type": "error", "error": f"AI 调用失败: {exc}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/messages/ai-review", response_model=MessageOut, status_code=201)
async def create_ai_review(body: AiReviewRequest) -> MessageOut:
    days = 7 if body.period == "week" else 30
    since = datetime.now() - timedelta(days=days)
    rows = await Message.filter(created_at__gte=since).order_by("created_at")

    lines: list[str] = []
    for msg in rows:
        text = msg.content.strip()
        if msg.role == "ai":
            text = strip_ai_storage_markers(text)
        if not text:
            continue
        role_label = "我" if normalize_message_role(msg.role) == "me" else "AI"
        lines.append(f"【{role_label}】{text}")

    if not lines:
        raise HTTPException(status_code=400, detail="该时间段内没有记录")

    label = "过去一周" if body.period == "week" else "过去一个月"
    review_prompt = (
        f"请基于用户{label}写下的以下记录，做一次回顾：总结主要主题、情绪与进展，"
        "并给出你的观察或建议。像日常对话一样自然回应，不要逐条复述原文。\n\n"
        + "\n\n".join(lines)
    )

    settings = await get_settings()
    persona = None
    if settings.active_persona_id:
        persona = await Persona.get_or_none(id=settings.active_persona_id)

    trigger = Message(id="review", role="me", type="text", content=review_prompt)
    try:
        chat_messages = await build_chat_messages(
            settings,
            [],
            trigger,
            system_prompt_override=persona.system_prompt if persona else None,
        )
        reply_text = await request_ai_reply(settings, chat_messages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI 调用失败: {exc}") from exc

    ai_msg = await Message.create(
        id=f"msg-{uuid.uuid4().hex[:12]}",
        role="ai",
        type="text",
        content=reply_text,
    )
    return await to_out(ai_msg)


@app.post("/api/messages", response_model=MessageOut, status_code=201)
async def create_message(body: MessageCreate) -> MessageOut:
    if body.type == "text" and not body.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")

    await validate_quote(body.quoteId)

    author_fields = await get_author_snapshot(body.role)
    safe_role = normalize_message_role(body.role)
    content = body.content.strip()
    msg = await Message.create(
        id=f"msg-{uuid.uuid4().hex[:12]}",
        role=safe_role,
        type=body.type,
        content=content,
        tags=tags_json(content),
        quote_id=body.quoteId,
        **author_fields,
    )
    return await to_out(msg)


def delete_message_media(msg: Message) -> None:
    delete_media_url(msg.media_url)
    attachments = parse_attachments(msg.attachments)
    if attachments:
        for item in attachments:
            delete_media_url(item.url)


@app.post("/api/uploads", response_model=UploadOut, status_code=201)
async def upload_file(file: UploadFile = File(...)) -> UploadOut:
    kind = detect_kind(file)
    try:
        media_url, media_name = await save_media_file(file)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"上传失败: {exc}") from exc
    return UploadOut(url=media_url, name=media_name, kind=kind)


@app.post("/api/messages/media", response_model=MessageOut, status_code=201)
async def upload_media(
    files: list[UploadFile] = File(...),
    content: str = Form(""),
    role: str = Form("me"),
    quote_id: str | None = Form(default=None),
) -> MessageOut:
    if not files:
        raise HTTPException(status_code=400, detail="未选择文件")

    if quote_id == "":
        quote_id = None

    await validate_quote(quote_id)
    caption = content.strip()
    saved: list[tuple[str, str, str]] = []

    try:
        for file in files:
            kind = detect_kind(file)
            media_url, media_name = await save_media_file(file)
            saved.append((media_url, media_name, kind))

        msg = await create_media_message_record(saved, caption, quote_id, role)
        return await to_out(msg)
    except HTTPException:
        for media_url, _, _ in saved:
            delete_media_url(media_url)
        raise
    except Exception as exc:
        for media_url, _, _ in saved:
            delete_media_url(media_url)
        raise HTTPException(status_code=500, detail=f"上传失败: {exc}") from exc


@app.delete("/api/messages/{message_id}", status_code=204)
async def delete_message(message_id: str) -> None:
    msg = await Message.get_or_none(id=message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    delete_message_media(msg)
    await Favorite.filter(message_id=message_id).delete()
    await msg.delete()


@app.post("/api/messages/{message_id}/favorite", response_model=MessageOut)
async def favorite_message(message_id: str) -> MessageOut:
    msg = await _require_message(message_id)
    await Favorite.get_or_create(
        message_id=message_id,
        defaults={"id": f"fav-{uuid.uuid4().hex[:12]}"},
    )
    return await to_out(msg, {message_id})


@app.delete("/api/messages/{message_id}/favorite", response_model=MessageOut)
async def unfavorite_message(message_id: str) -> MessageOut:
    msg = await _require_message(message_id)
    await Favorite.filter(message_id=message_id).delete()
    return await to_out(msg, set())


@app.get("/api/favorites", response_model=list[MessageOut])
async def list_favorites() -> list[MessageOut]:
    favorites = await Favorite.all()
    ids = [f.message_id for f in favorites]
    if not ids:
        return []

    messages = await Message.filter(id__in=ids)
    by_id = {m.id: m for m in messages}
    favorited_ids = set(ids)

    result: list[MessageOut] = []
    for fav in favorites:
        msg = by_id.get(fav.message_id)
        if not msg:
            continue
        result.append(await to_out(msg, favorited_ids))
    return result


@app.get("/api/personas", response_model=list[PersonaOut])
async def list_personas() -> list[PersonaOut]:
    personas = await Persona.all()
    return [to_persona_out(p) for p in personas]


@app.post("/api/personas", response_model=PersonaOut, status_code=201)
async def create_persona(body: PersonaCreate) -> PersonaOut:
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="名称不能为空")
    persona = await Persona.create(
        id=f"persona-{uuid.uuid4().hex[:12]}",
        name=name,
        icon=body.icon,
        system_prompt=body.systemPrompt.strip(),
    )
    return to_persona_out(persona)


@app.put("/api/personas/{persona_id}", response_model=PersonaOut)
async def update_persona(persona_id: str, body: PersonaUpdate) -> PersonaOut:
    persona = await Persona.get_or_none(id=persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="人格不存在")

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="名称不能为空")
        persona.name = name
    if body.icon is not None:
        persona.icon = body.icon
    if body.systemPrompt is not None:
        persona.system_prompt = body.systemPrompt.strip()

    await persona.save()
    return to_persona_out(persona)


@app.delete("/api/personas/{persona_id}", status_code=204)
async def delete_persona(persona_id: str) -> None:
    persona = await Persona.get_or_none(id=persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="人格不存在")

    await persona.delete()
    settings = await get_settings()
    if settings.active_persona_id == persona_id:
        settings.active_persona_id = None
        await settings.save()


@app.put("/api/settings/persona", response_model=SettingsOut)
async def set_active_persona(body: SetActivePersonaRequest) -> SettingsOut:
    settings = await get_settings()
    if body.personaId:
        exists = await Persona.filter(id=body.personaId).exists()
        if not exists:
            raise HTTPException(status_code=404, detail="人格不存在")
    settings.active_persona_id = body.personaId
    await settings.save()
    return await to_settings_out(settings)


@app.get("/api/settings", response_model=SettingsOut)
async def read_settings() -> SettingsOut:
    return await to_settings_out(await get_settings())


@app.put("/api/settings", response_model=SettingsOut)
async def save_settings(body: SettingsUpdate) -> SettingsOut:
    payload = body.model_dump(exclude_unset=True)
    mapping = {
        "displayName": "display_name",
        "avatarUrl": "avatar_url",
        "aiProvider": "ai_provider",
        "aiModel": "ai_model",
        "aiBaseUrl": "ai_base_url",
        "aiApiKey": "ai_api_key",
        "aiSystemPrompt": "ai_system_prompt",
        "aiThinking": "ai_thinking",
        "avatarTransparent": "avatar_transparent",
    }
    data = {mapping[k]: v for k, v in payload.items() if k in mapping}
    settings = await update_settings(data)
    return await to_settings_out(settings)


@app.post("/api/settings/avatar", response_model=SettingsOut)
async def upload_avatar(file: UploadFile = File(...)) -> SettingsOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")
    if not is_image_file(file):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    safe_name = sanitize_filename(file.filename)
    ext = Path(safe_name).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的图片格式")

    stored_name = f"avatar-{uuid.uuid4().hex}{ext}"
    stored_path = UPLOAD_DIR / stored_name

    max_bytes = MAX_AVATAR_MB * 1024 * 1024
    written = 0
    try:
        async with aiofiles.open(stored_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"头像文件过大，上限 {MAX_AVATAR_MB}MB",
                    )
                await out.write(chunk)
    except HTTPException:
        stored_path.unlink(missing_ok=True)
        raise

    settings = await get_settings()
    delete_media_url(settings.avatar_url)

    settings.avatar_url = f"/uploads/{stored_name}"
    await settings.save()
    return await to_settings_out(settings)


@app.delete("/api/settings/avatar", response_model=SettingsOut)
async def remove_avatar() -> SettingsOut:
    settings = await get_settings()
    delete_media_url(settings.avatar_url)
    settings.avatar_url = None
    await settings.save()
    return await to_settings_out(settings)


def _format_export_markdown(rows: list[Message]) -> str:
    lines = ["# 与神对话 · 导出记录\n"]
    for msg in rows:
        role_label = "我" if normalize_message_role(msg.role) == "me" else "AI"
        text = msg.content.strip()
        if msg.role == "ai":
            text = strip_ai_storage_markers(text)
        stamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
        lines.append(f"## {stamp} · {role_label}\n")
        if text:
            lines.append(f"{text}\n")

        attachments = parse_attachments(msg.attachments)
        if attachments:
            for item in attachments:
                if item.type == "image":
                    lines.append(f"![{item.name}]({item.url})\n")
                else:
                    lines.append(f"[{item.name}]({item.url})\n")
        elif msg.media_url:
            if msg.type == "image":
                lines.append(f"![{msg.media_name or msg.media_url}]({msg.media_url})\n")
            else:
                lines.append(f"[{msg.media_name or msg.media_url}]({msg.media_url})\n")
    return "\n".join(lines)


@app.get("/api/export")
async def export_messages(format: str = "md") -> Response:
    if format not in ("md", "json"):
        raise HTTPException(status_code=400, detail="format 仅支持 md 或 json")

    rows = await Message.all().order_by("created_at")
    stamp = datetime.now().strftime("%Y%m%d")

    if format == "json":
        items = [json.loads((await to_out(msg)).model_dump_json()) for msg in rows]
        payload = json.dumps(
            {"exportedAt": datetime.now().isoformat(), "total": len(items), "items": items},
            ensure_ascii=False,
            indent=2,
        )
        return Response(
            content=payload,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="export-{stamp}.json"'},
        )

    markdown = _format_export_markdown(rows)
    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="export-{stamp}.md"'},
    )


@app.post("/api/import/deepseek-share/preview", response_model=DeepSeekSharePreviewOut)
async def preview_deepseek_share(body: DeepSeekShareImportRequest) -> DeepSeekSharePreviewOut:
    try:
        data = await asyncio.to_thread(preview_share, body.url)
    except DeepSeekShareError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DeepSeekSharePreviewOut.model_validate(data)


@app.post("/api/import/deepseek-share", response_model=DeepSeekShareImportOut)
async def import_deepseek_share(body: DeepSeekShareImportRequest) -> DeepSeekShareImportOut:
    try:
        share_id = extract_share_id(body.url)
        biz_data = await asyncio.to_thread(fetch_share_payload, share_id)
        rows = parse_share_messages(biz_data)
    except DeepSeekShareError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if body.mode == "replace":
        existing = await Message.all()
        for msg in existing:
            delete_message_media(msg)
        await Favorite.all().delete()
        await Message.all().delete()

    author_fields = await get_author_snapshot("me")
    for row in rows:
        fields = author_fields if row["role"] == "me" else {}
        await Message.create(
            id=f"msg-{uuid.uuid4().hex[:12]}",
            role=row["role"],
            type="text",
            content=row["content"],
            created_at=row["createdAt"],
            **fields,
        )

    me_count = sum(1 for row in rows if row["role"] == "me")
    ai_count = sum(1 for row in rows if row["role"] == "ai")
    return DeepSeekShareImportOut(
        imported=len(rows),
        meCount=me_count,
        aiCount=ai_count,
        mode=body.mode,
        shareId=share_id,
        title=biz_data.get("title") or "Shared Conversation",
    )


# @app.post("/api/dev/seed")
# async def dev_seed(replace: bool = False) -> dict:
#     count = await seed_demo_messages(replace=replace)
#     return {"seeded": count, "replace": replace}
