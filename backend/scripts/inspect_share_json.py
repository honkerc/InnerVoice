import json
from collections import Counter
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
path = BACKEND_ROOT / "data" / "deepseek-share-content.json"
data = json.load(open(path, encoding="utf-8"))
msgs = data["data"]["biz_data"]["messages"]
print("count", len(msgs))
print("roles", Counter(m["role"] for m in msgs))
print("title", data["data"]["biz_data"].get("title"))

for m in msgs[:3]:
    print("---")
    print("id", m.get("message_id"), "role", m.get("role"), "time", m.get("inserted_at"))
    print("content", (m.get("content") or "")[:150])

ai = next(m for m in msgs if m["role"] != "USER")
print("ai sample keys", sorted(ai.keys()))
for key in ["content", "reasoning_content", "thinking_content", "search_results"]:
    if ai.get(key):
        print(key, str(ai[key])[:200])
