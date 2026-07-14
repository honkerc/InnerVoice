import re
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

SHARE_ID = "ffwlmix3jqi66ux6r0"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Download main bundle and search share API paths
main_url = "https://fe-static.deepseek.com/chat/static/main.9245f67c01.js"
req = urllib.request.Request(main_url, headers=HEADERS)
data = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
out = BACKEND_ROOT / "data" / "deepseek-main.js"
with open(out, "w", encoding="utf-8") as f:
    f.write(data)

paths = set(re.findall(r'["\'](/api[^"\']*share[^"\']*)["\']', data))
print("share api paths:")
for p in sorted(paths):
    print(p)

# Try discovered paths + common variants
candidates = list(paths) + [
    f"/api/v0/share/get?share_id={SHARE_ID}",
    f"/api/v0/share/{SHARE_ID}",
    f"/api/v0/share/detail?share_id={SHARE_ID}",
    f"/api/v0/share/detail/{SHARE_ID}",
    f"/api/v0/share/info?share_id={SHARE_ID}",
    f"/api/v0/share/info/{SHARE_ID}",
    f"/api/v0/share/load?share_id={SHARE_ID}",
    f"/api/v0/share/load/{SHARE_ID}",
]

seen = set()
for path in candidates:
    if path in seen:
        continue
    seen.add(path)
    url = f"https://chat.deepseek.com{path}" if path.startswith("/") else path
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=15)
        body = r.read(2000)
        ctype = r.headers.get("Content-Type", "")
        print("\n", url, r.status, ctype, body[:300])
    except Exception as e:
        print("\n", url, "ERR", e)
