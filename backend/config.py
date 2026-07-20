from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# 数据目录（数据库、上传文件等），可通过环境变量自定义
DATA_DIR = Path(os.getenv("INNERVOICE_DATA_DIR", BASE_DIR / "data"))
# 上传文件目录，默认在数据目录下，可单独用环境变量覆盖到其他位置
UPLOAD_DIR = Path(os.getenv("INNERVOICE_UPLOAD_DIR", str(DATA_DIR / "uploads")))
DB_PATH = DATA_DIR / "chat.db"
LEGACY_JSON = DATA_DIR / "messages.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

AI_API_KEY = os.getenv("AI_API_KEY", "").strip()

# 附件上传大小上限（图片不限制，与现状保持一致）
MAX_VIDEO_MB = 300
MAX_FILE_MB = 50
MAX_AVATAR_MB = 8

# 后端监听端口
INNERVOICE_PORT = int(os.getenv("INNERVOICE_PORT", "8000"))

TORTOISE_ORM = {
    "connections": {"default": f"sqlite://{DB_PATH}"},
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        },
    },
}
