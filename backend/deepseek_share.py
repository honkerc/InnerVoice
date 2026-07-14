import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from ai_client import format_ai_storage_content

SHARE_ID_PATTERN = re.compile(r"/share/([a-z0-9]+)", re.IGNORECASE)
SHARE_API = "https://chat.deepseek.com/api/v0/share/content"


class DeepSeekShareError(Exception):
    pass


def extract_share_id(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise DeepSeekShareError("请提供 DeepSeek 分享链接或 share_id")

    match = SHARE_ID_PATTERN.search(raw)
    if match:
        return match.group(1)

    if re.fullmatch(r"[a-z0-9]+", raw, flags=re.IGNORECASE):
        return raw

    raise DeepSeekShareError("无法识别分享链接，请使用 chat.deepseek.com/share/... 格式")


def fetch_share_payload(share_id: str) -> dict:
    query = urllib.parse.urlencode({"share_id": share_id})
    url = f"{SHARE_API}?{query}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
    except Exception as exc:
        raise DeepSeekShareError(f"获取分享内容失败：{exc}") from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise DeepSeekShareError("分享内容解析失败") from exc

    if payload.get("code") != 0:
        raise DeepSeekShareError(payload.get("msg") or "分享接口返回错误")

    data = payload.get("data") or {}
    if data.get("biz_code") != 0:
        raise DeepSeekShareError(data.get("biz_msg") or "分享内容不可用")

    biz_data = data.get("biz_data")
    if not isinstance(biz_data, dict):
        raise DeepSeekShareError("分享内容格式异常")

    return biz_data


def _to_created_at(inserted_at: float | int | None) -> datetime:
    if not inserted_at:
        return datetime.now()
    return datetime.fromtimestamp(float(inserted_at), tz=timezone.utc).replace(tzinfo=None)


def _map_role(role: str) -> str | None:
    normalized = (role or "").upper()
    if normalized == "USER":
        return "me"
    if normalized == "ASSISTANT":
        return "ai"
    return None


def _message_content(item: dict, role: str) -> str:
    content = (item.get("content") or "").strip()
    if role != "ai":
        return content

    thinking = (item.get("thinking_content") or "").strip()
    if thinking:
        return format_ai_storage_content(thinking, content)
    return content


def parse_share_messages(biz_data: dict) -> list[dict]:
    raw_messages = biz_data.get("messages") or []
    if not isinstance(raw_messages, list):
        raise DeepSeekShareError("分享消息列表格式异常")

    parsed: list[dict] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        if item.get("status") not in (None, "FINISHED"):
            continue

        role = _map_role(item.get("role", ""))
        if not role:
            continue

        content = _message_content(item, role)
        if not content:
            continue

        parsed.append(
            {
                "role": role,
                "content": content,
                "createdAt": _to_created_at(item.get("inserted_at")),
                "sourceMessageId": item.get("message_id"),
            }
        )

    if not parsed:
        raise DeepSeekShareError("分享对话中没有可导入的消息")

    return parsed


def preview_share(value: str) -> dict:
    share_id = extract_share_id(value)
    biz_data = fetch_share_payload(share_id)
    messages = parse_share_messages(biz_data)

    me_count = sum(1 for item in messages if item["role"] == "me")
    ai_count = sum(1 for item in messages if item["role"] == "ai")
    start = messages[0]["createdAt"]
    end = messages[-1]["createdAt"]

    return {
        "shareId": share_id,
        "title": biz_data.get("title") or "Shared Conversation",
        "total": len(messages),
        "meCount": me_count,
        "aiCount": ai_count,
        "rangeFrom": start.isoformat(),
        "rangeTo": end.isoformat(),
        "preview": [
            {
                "role": item["role"],
                "createdAt": item["createdAt"].isoformat(),
                "content": item["content"][:160],
            }
            for item in messages[:6]
        ],
    }
