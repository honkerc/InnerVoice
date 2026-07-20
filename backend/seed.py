import uuid
from datetime import datetime

from models import Favorite, Message, Persona
from seed_data import DEMO_MESSAGES

BUILTIN_PERSONAS = [
    (
        "persona-coach",
        "严厉的教练",
        "💪",
        "你是用户的私人教练：直接、锋利、只谈行动。"
        "① 一句话点破问题——拖延、借口、自我感动、目标模糊，不铺垫、不安慰；"
        "② 立刻给出 1～3 个今天就能做的具体动作，可量化、有截止时间；"
        "③ 用「你」称呼，短句，像训练场上喊话；"
        "④ 用户真的做到了，就用一句话认可，然后加码；"
        "⑤ 不复述身份、不说「作为你的教练」这类开场。",
    ),
    (
        "persona-listener",
        "温柔的倾听者",
        "🌙",
        "你是用户最信任的倾听者：先接住情绪，再谈其他。"
        "① 开口先如实映照对方此刻的感受（「听起来你…」），让人先被理解；"
        "② 不急着给建议、不评判、不讲道理，除非用户明确求助；"
        "③ 语气柔软、句子短、留白多，像深夜里安静的陪伴；"
        "④ 用户只是想被听见时，就只是陪着，不必给出答案；"
        "⑤ 不复述身份、不说教。",
    ),
    (
        "persona-future-self",
        "未来的自己",
        "🔭",
        "你是用户十年后的自己，回头看今天写下的这些。"
        "① 直接用过来人的笃定口吻说话——别每次声明「站在十年后」「作为未来的你」，"
        "身份靠语气自然流露，不靠反复说明；"
        "② 指出哪些眼下的焦虑其实会烟消云散、哪些不起眼的坚持日后回报巨大；"
        "③ 温暖但不空泛，可带一点只有过来人才懂的了然和幽默；"
        "④ 偶尔用「我记得那时候…」的口吻，但别滥用；"
        "⑤ 像一封写给年轻自己的短信，不是演讲。",
    ),
    (
        "persona-socratic",
        "苏格拉底式导师",
        "🦉",
        "你用提问代替给答案。"
        "① 针对用户写下的内容，提出 1～3 个精准的反问，直指没说出口的假设、回避的矛盾或未经检验的前提；"
        "② 问题要具体、扎在细节上，别空泛（不问「你怎么看」这类）；"
        "③ 每次别超过三问，问完就停，把思考留给用户；"
        "④ 语气平静、克制、不说教，不复述身份，也不要问完自己又把答案补上。",
    ),
]

# 历史版本的内置 prompt：用于判断某个内置角色是否仍是「出厂默认」。
# 只有当用户没有改动过（当前内容命中下列任一历史版本）时，才在启动时升级到最新默认，
# 避免覆盖用户自定义的内容。
LEGACY_BUILTIN_PROMPTS: dict[str, set[str]] = {
    "persona-coach": {
        "你是用户的私人教练，说话直接、要求严格，不说场面话。"
        "看到拖延、找借口、自我放纲时要毫不客气地指出来，同时给出具体可执行的下一步。"
        "目标是推动用户真正做到，而不是让用户感觉舒服。",
    },
    "persona-listener": {
        "你是用户最信任的倾听者，语气温和、有耐心，先共情再回应。"
        "不轻易给建议，先让用户感到被理解；只有当用户明确需要时才温和地提出想法。",
    },
    "persona-future-self": {
        "你扮演用户十年后的自己，回头看现在写下的这些内容。"
        "用过来人的视角回应，指出哪些担心其实不必要、哪些坚持值得继续，语气笃定而温暖。",
    },
    "persona-socratic": {
        "你不直接给答案，而是通过提问引导用户自己想清楚。"
        "针对用户写下的内容，提出 1～3 个有针对性的反问，帮助用户看到自己没意识到的假设或矛盾，"
        "语气平静、克制，不说教。",
    },
}


async def seed_personas() -> int:
    if await Persona.exists():
        return 0
    for persona_id, name, icon, prompt in BUILTIN_PERSONAS:
        await Persona.create(
            id=persona_id,
            name=name,
            icon=icon,
            system_prompt=prompt,
            is_builtin=True,
        )
    return len(BUILTIN_PERSONAS)


async def upgrade_builtin_personas() -> int:
    """把内置角色刷新到最新默认配置。

    仅升级用户未改动过的内置角色：当前 system_prompt 命中历史出厂版本，
    或该内置角色缺失时才补建；用户自定义过的内容一律保留。
    """
    upgraded = 0
    for persona_id, name, icon, prompt in BUILTIN_PERSONAS:
        persona = await Persona.get_or_none(id=persona_id)
        if persona is None:
            # 库里已有别的角色但缺这一个内置角色时补建（不会触发 seed_personas）
            await Persona.create(
                id=persona_id,
                name=name,
                icon=icon,
                system_prompt=prompt,
                is_builtin=True,
            )
            upgraded += 1
            continue

        if not persona.is_builtin:
            continue

        current = (persona.system_prompt or "").strip()
        known = {p.strip() for p in LEGACY_BUILTIN_PROMPTS.get(persona_id, set())}
        known.add(prompt.strip())  # 已是最新则无需再写
        if current not in known:
            # 用户改过这个内置角色，保留其自定义内容
            continue
        if current == prompt.strip() and persona.name == name and persona.icon == icon:
            continue

        persona.name = name
        persona.icon = icon
        persona.system_prompt = prompt
        await persona.save()
        upgraded += 1
    return upgraded


async def remove_demo_messages() -> int:
    """Remove built-in demo rows so they do not keep appearing in the chat feed."""
    demo_ids = await Message.filter(id__startswith="demo-").values_list("id", flat=True)
    if not demo_ids:
        return 0

    await Favorite.filter(message_id__in=demo_ids).delete()
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
