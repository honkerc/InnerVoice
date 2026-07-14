import json
import re
from collections.abc import AsyncIterator
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, OpenAIError

from models import Message, UserSettings
from settings_store import DEFAULTS, get_effective_api_key

AI_MENTION = re.compile(r"@ai\b", re.IGNORECASE)
AI_THINKING_START = "<!--ai-thinking-->"
AI_THINKING_END = "<!--/ai-thinking-->"

# 仿 DeepSeek 正文风格：思考过程由 API 单独返回，此处约束可见回答的排版与语气
AI_OUTPUT_RULES = """\
【输出规则】（仅约束最终回答，思考过程请自由推理，勿写入回答）

1. 语言：与用户一致；用户用中文则全程中文。
2. 开篇：复杂问题先用 1～2 句话给出核心结论或态度，再展开；简单问题直接回答，不要寒暄套话。
3. 结构：内容稍长时用 Markdown 小标题（## / ###）分段；并列要点用列表；步骤用有序列表；对比可用表格。
4. 强调：关键概念、结论、术语用 **加粗**；避免整段加粗或过度使用 emoji。
5. 代码：技术内容给出可复制代码块，并标注语言；先说明用途，再给代码，必要时补一句关键逻辑。
6. 语气：理性、清晰、克制，像 DeepSeek 那样有条理地对话；有温度但不煽情，不居高临下，不过度自称 AI。
7. 篇幅：匹配问题复杂度——能一句说清就不写三段；需要展开时写充分，但不重复、不灌水。
8. 禁止：空泛收尾（如「希望对你有帮助」「如有其他问题欢迎继续问」）；无意义的「好的，我来…」开场；把思考过程复述进正文。
9. 场景：这是用户写给自己的私人记录空间；你是辅助工具，帮助用户整理思路、回应自己写下的内容，可结合历史记录理解语境。"""


def contains_ai_mention(text: str) -> bool:
    return bool(AI_MENTION.search(text))


def strip_ai_mention(text: str) -> str:
    return AI_MENTION.sub("", text).strip()


def format_ai_storage_content(thinking: str, answer: str) -> str:
    thinking_text = thinking.strip()
    answer_text = answer.strip()
    if not answer_text and thinking_text:
        return thinking_text
    if thinking_text:
        return (
            f"{AI_THINKING_START}\n{thinking_text}\n{AI_THINKING_END}\n\n{answer_text}"
        )
    return answer_text


def normalize_openai_base_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")].rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")].rstrip("/")
    return base


def strip_ai_storage_markers(text: str) -> str:
    start = text.find(AI_THINKING_START)
    end = text.find(AI_THINKING_END)
    if start == -1 or end == -1 or end < start:
        return text.strip()
    thinking = text[start + len(AI_THINKING_START) : end].strip()
    answer = text[end + len(AI_THINKING_END) :].strip()
    if answer:
        return answer
    return thinking


def message_to_chat(msg: Message) -> dict[str, str] | None:
    content = msg.content.strip()
    if msg.role == "ai":
        content = strip_ai_storage_markers(content)
    if msg.type == "image":
        content = content or "[图片]"
    elif msg.type == "media_group":
        content = content or "[多图消息]"
    elif msg.type in ("video", "file"):
        content = content or f"[{msg.type}]"
    elif not content:
        return None

    if msg.role == "ai":
        role = "assistant"
    else:
        role = "user"
    return {"role": role, "content": content}


async def build_chat_messages(
    settings: UserSettings,
    history: list[Message],
    trigger: Message,
) -> list[dict[str, str]]:
    system_prompt = (
        settings.ai_system_prompt.strip()
        or DEFAULTS["ai_system_prompt"]
    )
    full_system = f"{system_prompt.strip()}\n\n{AI_OUTPUT_RULES}"
    messages: list[dict[str, str]] = [{"role": "system", "content": full_system}]

    for msg in history:
        item = message_to_chat(msg)
        if item:
            messages.append(item)

    trigger_text = strip_ai_mention(trigger.content)
    if trigger.type != "text":
        if not trigger_text:
            trigger_text = trigger.content.strip() or "[附件消息]"
        else:
            trigger_text = strip_ai_mention(trigger_text)
    if not trigger_text:
        trigger_text = "（用户 @ 了你，请回应）"

    # 如果 trigger 有引用，把被引用消息的内容也带入
    if trigger.quote_id:
        quoted = await Message.get_or_none(id=trigger.quote_id)
        if quoted:
            quoted_text = quoted.content.strip()
            if quoted.role == "ai":
                quoted_text = strip_ai_storage_markers(quoted_text)
            trigger_text = f"针对（引用了过去的消息）：{quoted_text}\n\n回复：{trigger_text}"

    messages.append({"role": "user", "content": trigger_text})
    return messages


def _thinking_enabled(settings: UserSettings) -> bool:
    return bool(getattr(settings, "ai_thinking", DEFAULTS["ai_thinking"]))


def _build_client(settings: UserSettings) -> AsyncOpenAI:
    provider = settings.ai_provider
    api_key = get_effective_api_key(settings)
    if provider != "ollama" and not api_key:
        raise ValueError("请在后端配置 AI_API_KEY 环境变量")

    base_url = normalize_openai_base_url(
        settings.ai_base_url or DEFAULTS["ai_base_url"]
    )
    return AsyncOpenAI(
        api_key=api_key or "ollama",
        base_url=base_url,
        timeout=120.0,
    )


def _build_request_kwargs(
    settings: UserSettings,
    messages: list[dict[str, str]],
    *,
    stream: bool,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": settings.ai_model,
        "messages": messages,
        "stream": stream,
    }
    if settings.ai_provider == "deepseek" and _thinking_enabled(settings):
        kwargs["reasoning_effort"] = "high"
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
    return kwargs


def _delta_reasoning(delta: Any) -> str | None:
    if delta is None:
        return None
    for key in ("reasoning_content", "reasoning"):
        value = getattr(delta, key, None)
        if isinstance(value, str) and value:
            return value
    extra = getattr(delta, "model_extra", None)
    if isinstance(extra, dict):
        for key in ("reasoning_content", "reasoning"):
            value = extra.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def _delta_content(delta: Any) -> str | None:
    if delta is None:
        return None
    value = getattr(delta, "content", None)
    if isinstance(value, str) and value:
        return value
    return None


async def iter_ai_reply_stream(
    settings: UserSettings,
    messages: list[dict[str, str]],
) -> AsyncIterator[dict[str, Any]]:
    client = _build_client(settings)
    kwargs = _build_request_kwargs(settings, messages, stream=True)

    try:
        stream = await client.chat.completions.create(**kwargs)
    except APIConnectionError as exc:
        raise RuntimeError(
            f"无法连接 AI 服务，请检查 API 地址与网络"
        ) from exc
    except APITimeoutError as exc:
        raise RuntimeError("AI 请求超时，请稍后重试") from exc
    except OpenAIError as exc:
        raise RuntimeError(str(exc) or "AI 请求失败") from exc

    thinking_parts: list[str] = []
    answer_parts: list[str] = []

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        reasoning = _delta_reasoning(delta)
        if reasoning:
            thinking_parts.append(reasoning)
            yield {"type": "thinking", "delta": reasoning}

        content = _delta_content(delta)
        if content:
            answer_parts.append(content)
            yield {"type": "content", "delta": content}

    thinking = "".join(thinking_parts).strip()
    answer = "".join(answer_parts).strip()
    if not answer and not thinking:
        raise RuntimeError("AI 返回内容为空")

    yield {
        "type": "complete",
        "thinking": thinking,
        "answer": answer,
    }


async def request_ai_reply(settings: UserSettings, messages: list[dict[str, str]]) -> str:
    thinking = ""
    answer = ""
    async for event in iter_ai_reply_stream(settings, messages):
        if event["type"] == "thinking":
            thinking += event["delta"]
        elif event["type"] == "content":
            answer += event["delta"]
        elif event["type"] == "complete":
            thinking = event.get("thinking", thinking)
            answer = event.get("answer", answer)
    return format_ai_storage_content(thinking, answer)


def sse_line(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
