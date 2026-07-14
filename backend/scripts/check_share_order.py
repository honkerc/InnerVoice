import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from deepseek_share import fetch_share_payload, parse_share_messages, extract_share_id  # noqa: E402

share_id = extract_share_id("https://chat.deepseek.com/share/ffwlmix3jqi66ux6r0")
biz = fetch_share_payload(share_id)
raw = [m for m in biz["messages"] if m.get("status") in (None, "FINISHED")]

inversions_time = 0
inversions_array = 0
for i in range(1, len(raw)):
    prev, cur = raw[i - 1], raw[i]
    if prev.get("role") == "ASSISTANT" and cur.get("role") == "USER":
        inversions_array += 1
    if prev.get("inserted_at", 0) > cur.get("inserted_at", 0):
        inversions_time += 1

parsed = parse_share_messages(biz)
wrong_pairs = 0
for i in range(1, len(parsed)):
    if parsed[i - 1]["role"] == "ai" and parsed[i]["role"] == "me":
        wrong_pairs += 1

print("raw count", len(raw))
print("array ASSISTANT->USER inversions", inversions_array)
print("time desc pairs in raw", inversions_time)
print("parsed ai->me inversions", wrong_pairs)

# show first mismatch in parsed
for i in range(1, len(parsed)):
    if parsed[i]["role"] == "ai" and parsed[i - 1]["role"] != "me":
        print("wrong at", i, parsed[i - 1]["role"], "->", parsed[i]["role"])
        break

# compare first 6 roles: raw vs parsed
print("raw roles first 12:", [m.get("role") for m in raw[:12]])
print("parsed roles first 12:", [m["role"] for m in parsed[:12]])
