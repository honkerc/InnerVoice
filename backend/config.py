from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

# 数据目录（数据库、上传文件等），可通过环境变量自定义
DATA_DIR = Path(os.getenv("INNERVOICE_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "chat.db"
LEGACY_JSON = DATA_DIR / "messages.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

AI_API_KEY = os.getenv("AI_API_KEY", "").strip()

# 后端监听端口
INNERVOICE_PORT = int(os.getenv("INNERVOICE_PORT", "8001"))

TORTOISE_ORM = {
    "connections": {"default": f"sqlite://{DB_PATH}"},
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        },
    },
}
