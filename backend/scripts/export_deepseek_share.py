"""Export DeepSeek share JSON to readable Markdown transcript."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from deepseek_share import extract_share_id, fetch_share_payload, parse_share_messages  # noqa: E402


def format_time(value) -> str:
    if hasattr(value, "isoformat"):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    source = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://chat.deepseek.com/share/ffwlmix3jqi66ux6r0"
    )
    share_id = extract_share_id(source)
    biz_data = fetch_share_payload(share_id)
    messages = parse_share_messages(biz_data)

    lines = [
        f"# {biz_data.get('title') or 'DeepSeek 分享对话'}",
        "",
        f"- share_id: `{share_id}`",
        f"- 消息数: {len(messages)}",
        f"- 时间范围: {format_time(messages[0]['createdAt'])} ~ {format_time(messages[-1]['createdAt'])}",
        "",
        "---",
        "",
    ]

    for item in messages:
        role_label = "我" if item["role"] == "me" else "AI"
        lines.append(f"## {role_label} · {format_time(item['createdAt'])}")
        lines.append("")
        lines.append(item["content"])
        lines.append("")
        lines.append("---")
        lines.append("")

    out = BACKEND_ROOT / "data" / f"deepseek-share-{share_id}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"exported {len(messages)} messages -> {out}")


if __name__ == "__main__":
    main()
