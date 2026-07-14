from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = DATA_DIR / "chat.db"
LEGACY_JSON = DATA_DIR / "messages.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
PORT = int(os.getenv("PORT", "8001"))

TORTOISE_ORM = {
    "connections": {"default": f"sqlite://{DB_PATH}"},
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        },
    },
}
