import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise

from config import LEGACY_JSON, TORTOISE_ORM, UPLOAD_DIR
from models import Message, User, UserSettings
from auth import (
    auth_middleware,
    create_access_token,
    create_refresh_token,
    ensure_default_user,
    get_current_user,
    hash_password,
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
)
from deepseek_share import DeepSeekShareError, extract_share_id, fetch_share_payload, parse_share_messages, preview_share
from schemas import (
    AiReplyRequest,
    AuthTokensOut,
    AuthUserOut,
    ChangePasswordRequest,
    DeepSeekShareImportOut,
    DeepSeekShareImportRequest,
    DeepSeekSharePreviewOut,
    LoginRequest,
    MessageAttachmentOut,
    MessageCreate,
    MessageOut,
    QuotePreview,
    PinMessageRequest,
    RefreshRequest,
    SettingsOut,
    SettingsUpdate,
)
from seed import remove_demo_messages, seed_demo_messages
from settings_store import get_settings, update_settings, has_api_key
from storage import delete_media_url, is_image_file, resolve_upload_path, save_image_file


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


async def to_out(msg: Message) -> MessageOut:
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

    return MessageOut(
        id=msg.id,
        role=normalize_message_role(msg.role),
        type=msg.type,
        content=msg.content,
        mediaUrl=media_url,
        mediaName=msg.media_name,
        attachments=attachments,
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
        pinnedMessageId=getattr(settings, "pinned_message_id", None),
    )


async def ensure_settings_columns() -> None:
    conn = Tortoise.get_connection("default")
    _, rows = await conn.execute_query("PRAGMA table_info(user_settings)")
    columns = {row[1] for row in rows}
    if "ai_thinking" not in columns:
        await conn.execute_script(
            "ALTER TABLE user_settings ADD COLUMN ai_thinking INTEGER NOT NULL DEFAULT 1"
        )
    if "pinned_message_id" not in columns:
        await conn.execute_script(
            "ALTER TABLE user_settings ADD COLUMN pinned_message_id VARCHAR(64) NULL"
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


async def create_image_message_record(
    saved: list[tuple[str, str]],
    caption: str,
    quote_id: str | None,
    role: str = "me",
) -> Message:
    safe_role = normalize_message_role(role)
    author_fields = await get_author_snapshot(safe_role)

    if len(saved) == 1:
        media_url, media_name = saved[0]
        return await Message.create(
            id=f"msg-{uuid.uuid4().hex[:12]}",
            role=safe_role,
            type="image",
            content=caption,
            media_url=media_url,
            media_name=media_name,
            quote_id=quote_id,
            **author_fields,
        )

    attachments = [{"type": "image", "url": url, "name": name} for url, name in saved]
    return await Message.create(
        id=f"msg-{uuid.uuid4().hex[:12]}",
        role=safe_role,
        type="media_group",
        content=caption,
        media_url=attachments[0]["url"],
        attachments=json.dumps(attachments, ensure_ascii=False),
        quote_id=quote_id,
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
    await get_settings()
    await ensure_default_user()
    await import_legacy_messages()
    await remove_demo_messages()
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

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.post("/api/auth/login", response_model=AuthTokensOut)
async def login(body: LoginRequest) -> AuthTokensOut:
    username = body.username.strip()
    if not username or not body.password:
        raise HTTPException(status_code=400, detail="请输入用户名和密码")

    user = await User.get_or_none(username=username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

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


@app.get("/api/messages", response_model=list[MessageOut])
async def list_messages() -> list[MessageOut]:
    messages = await Message.all().order_by("created_at")
    result = []
    for msg in messages:
        result.append(await to_out(msg))
    return result


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

    try:
        chat_messages = await build_chat_messages(settings, history, trigger)
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

    async def event_generator():
        if existing:
            yield sse_line({"type": "done", "message": (await to_out(existing)).model_dump(mode="json")})
            return

        try:
            chat_messages = await build_chat_messages(settings, history, trigger)
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


@app.post("/api/messages", response_model=MessageOut, status_code=201)
async def create_message(body: MessageCreate) -> MessageOut:
    if body.type == "text" and not body.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")

    await validate_quote(body.quoteId)

    author_fields = await get_author_snapshot(body.role)
    safe_role = normalize_message_role(body.role)
    msg = await Message.create(
        id=f"msg-{uuid.uuid4().hex[:12]}",
        role=safe_role,
        type=body.type,
        content=body.content.strip(),
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


@app.post("/api/messages/images", response_model=MessageOut, status_code=201)
async def upload_images(
    files: list[UploadFile] = File(...),
    content: str = Form(""),
    role: str = Form("me"),
    quote_id: str | None = Form(default=None),
) -> MessageOut:
    if not files:
        raise HTTPException(status_code=400, detail="未选择图片")

    if quote_id == "":
        quote_id = None

    await validate_quote(quote_id)
    caption = content.strip()
    saved: list[tuple[str, str]] = []

    try:
        for file in files:
            saved.append(await save_image_file(file))

        msg = await create_image_message_record(saved, caption, quote_id, role)
        return await to_out(msg)
    except HTTPException:
        for media_url, _ in saved:
            delete_media_url(media_url)
        raise
    except Exception as exc:
        for media_url, _ in saved:
            delete_media_url(media_url)
        raise HTTPException(status_code=500, detail=f"上传失败: {exc}") from exc


@app.delete("/api/messages/{message_id}", status_code=204)
async def delete_message(message_id: str) -> None:
    msg = await Message.get_or_none(id=message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    delete_message_media(msg)
    settings = await get_settings()
    if settings.pinned_message_id == message_id:
        settings.pinned_message_id = None
        await settings.save()
    await msg.delete()


@app.put("/api/settings/pin", response_model=SettingsOut)
async def set_pinned_message(body: PinMessageRequest) -> SettingsOut:
    settings = await get_settings()
    if body.messageId:
        exists = await Message.filter(id=body.messageId).exists()
        if not exists:
            raise HTTPException(status_code=404, detail="消息不存在")
        settings.pinned_message_id = body.messageId
    else:
        settings.pinned_message_id = None
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

    ext = Path(file.filename).suffix or ".png"
    stored_name = f"avatar-{uuid.uuid4().hex}{ext}"
    stored_path = UPLOAD_DIR / stored_name

    async with aiofiles.open(stored_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            await out.write(chunk)

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
        await Message.all().delete()
        settings = await get_settings()
        if settings.pinned_message_id:
            settings.pinned_message_id = None
            await settings.save()

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
