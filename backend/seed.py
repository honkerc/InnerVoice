import uuid
from datetime import datetime

from models import Message
from seed_data import DEMO_MESSAGES
from settings_store import get_settings


async def remove_demo_messages() -> int:
    """Remove built-in demo rows so they do not keep appearing in the chat feed."""
    demo_ids = await Message.filter(id__startswith="demo-").values_list("id", flat=True)
    if not demo_ids:
        return 0

    settings = await get_settings()
    if settings.pinned_message_id in demo_ids:
        settings.pinned_message_id = None
        await settings.save()

    await Message.filter(id__startswith="demo-").delete()
    return len(demo_ids)


async def seed_demo_messages(*, replace: bool = False) -> int:
    if replace:
        await Message.all().delete()
    else:
        exists = await Message.filter(id__startswith="demo-").exists()
        if exists:
            return 0

    for item in DEMO_MESSAGES:
        msg_id, role, msg_type, content, media_url, created_at, quote_id = item
        await Message.create(
            id=msg_id,
            role=role,
            type=msg_type,
            content=content,
            media_url=media_url,
            quote_id=quote_id,
            created_at=created_at,
        )

    return len(DEMO_MESSAGES)
