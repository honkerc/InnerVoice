import json
from collections import Counter
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"

path = DATA_DIR / "deepseek-share-content.json"
with open(path, encoding="utf-8") as f:
    data = json.load(f)

msgs = data["data"]["biz_data"]["messages"]
summary = {
    "title": data["data"]["biz_data"].get("title"),
    "count": len(msgs),
    "roles": dict(Counter(m["role"] for m in msgs)),
    "with_thinking": sum(1 for m in msgs if m.get("thinking_content")),
    "first_user": next((m.get("content", "")[:80] for m in msgs if m["role"] == "USER"), ""),
    "time_range": {
        "start": min(m.get("inserted_at") or 0 for m in msgs),
        "end": max(m.get("inserted_at") or 0 for m in msgs),
    },
}

out = DATA_DIR / "deepseek-share-summary.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("wrote", out)
