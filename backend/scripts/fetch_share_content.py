import json
import urllib.parse
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"

SHARE_ID = "ffwlmix3jqi66ux6r0"
BASE = "https://chat.deepseek.com"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

queries = [
    {"share_id": SHARE_ID},
    {"shareId": SHARE_ID},
    {"id": SHARE_ID},
    {"share_id": SHARE_ID, "share_type": "chat"},
    {"share_id": SHARE_ID, "type": "chat"},
]

for q in queries:
    url = f"{BASE}/api/v0/share/content?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            print("QUERY", q)
            print("STATUS", r.status)
            text = raw.decode("utf-8", "replace")
            print(text[:500])
            print("LEN", len(raw))
            print("---")
            if text.startswith("{"):
                with open(
                    DATA_DIR / "deepseek-share-content.json",
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(text)
    except Exception as e:
        err_body = ""
        if hasattr(e, "read"):
            err_body = e.read().decode("utf-8", "replace")[:500]
        print("QUERY", q, "ERR", e, err_body)
        print("---")
