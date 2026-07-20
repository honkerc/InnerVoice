import re
import uuid
from pathlib import Path
from typing import Literal

import aiofiles
from fastapi import HTTPException, UploadFile

from config import UPLOAD_DIR

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".heic",
    ".heif",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".webm",
    ".mkv",
    ".avi",
    ".m4v",
}

# 不接受上传的可执行文件类型，避免把上传目录当可执行文件/网页托管
EXECUTABLE_EXTENSIONS = {
    ".exe",
    ".sh",
    ".bat",
    ".cmd",
    ".com",
    ".msi",
    ".ps1",
    ".scr",
    ".apk",
    ".jar",
    ".html",
    ".htm",
    ".xhtml",
    ".shtml",
    ".svg",
    ".svgz",
}

MediaKind = Literal["image", "video", "file"]


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    if not name or name in (".", ".."):
        return "file"
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name[:200] or "file"


def is_image_file(file: UploadFile) -> bool:
    ext = Path(file.filename or "").suffix.lower()
    if ext in EXECUTABLE_EXTENSIONS:
        return False
    content_type = (file.content_type or "").lower()
    if content_type.startswith("image/"):
        return True
    return ext in IMAGE_EXTENSIONS


def is_video_file(file: UploadFile) -> bool:
    content_type = (file.content_type or "").lower()
    if content_type.startswith("video/"):
        return True
    ext = Path(file.filename or "").suffix.lower()
    return ext in VIDEO_EXTENSIONS


def detect_kind(file: UploadFile) -> MediaKind:
    if is_image_file(file):
        return "image"
    if is_video_file(file):
        return "video"
    ext = Path(file.filename or "").suffix.lower()
    if ext in EXECUTABLE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持上传可执行文件（{ext}）")
    return "file"


def make_stored_name(original_filename: str) -> str:
    safe = sanitize_filename(original_filename)
    return f"{uuid.uuid4().hex[:12]}_{safe}"


def media_url_for(stored_name: str) -> str:
    return f"/uploads/{stored_name}"


def resolve_upload_path(media_url: str | None) -> Path | None:
    if not media_url or not media_url.startswith("/uploads/"):
        return None
    rel = media_url.removeprefix("/uploads/").lstrip("/")
    if not rel or ".." in Path(rel).parts:
        return None
    return UPLOAD_DIR / rel


async def save_media_file(file: UploadFile) -> tuple[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")

    original_name = sanitize_filename(file.filename)
    stored_name = make_stored_name(original_name)
    stored_path = UPLOAD_DIR / stored_name

    async with aiofiles.open(stored_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            await out.write(chunk)

    return media_url_for(stored_name), original_name


def delete_media_url(media_url: str | None) -> None:
    file_path = resolve_upload_path(media_url)
    if file_path and file_path.exists():
        file_path.unlink()
