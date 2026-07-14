from models import UserSettings
from config import AI_API_KEY

DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-pro"
LEGACY_DEEPSEEK_MODELS = frozenset({"deepseek-chat", "deepseek-reasoner"})

DEFAULTS = {
    "display_name": "我",
    "avatar_url": None,
    "ai_provider": "deepseek",
    "ai_model": DEEPSEEK_DEFAULT_MODEL,
    "ai_base_url": "https://api.deepseek.com",
    "ai_api_key": "",
    "ai_system_prompt": (
        "你是用户的写作与思考辅助工具，帮助整理、回应用户写给自己的记录。"
        "理解用户的日记、备忘与自问，给出清晰、有见地的回应；"
        "你不是对话对象，只是帮助用户与自己对话的工具。"
    ),
    "ai_thinking": True,
}


def get_effective_api_key(settings: UserSettings) -> str:
    if AI_API_KEY:
        return AI_API_KEY
    return (settings.ai_api_key or "").strip()


def has_api_key(settings: UserSettings) -> bool:
    return bool(get_effective_api_key(settings))


async def get_settings() -> UserSettings:
    settings, _ = await UserSettings.get_or_create(
        id="default",
        defaults=DEFAULTS,
    )
    changed = False
    if settings.ai_provider == "deepseek":
        if settings.ai_model in LEGACY_DEEPSEEK_MODELS:
            settings.ai_model = DEEPSEEK_DEFAULT_MODEL
            changed = True
    if changed:
        await settings.save()
    return settings


async def update_settings(data: dict) -> UserSettings:
    settings = await get_settings()
    for key, value in data.items():
        if value is not None and hasattr(settings, key):
            setattr(settings, key, value)
    await settings.save()
    return settings
