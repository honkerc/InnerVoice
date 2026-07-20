import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import DATA_DIR
from models import User

_JWT_SECRET_FILE = DATA_DIR / ".jwt_secret"


def _resolve_jwt_secret() -> str:
    env_secret = os.getenv("JWT_SECRET", "").strip()
    if env_secret:
        return env_secret
    stored = ""
    if _JWT_SECRET_FILE.exists():
        stored = _JWT_SECRET_FILE.read_text(encoding="utf-8").strip()
    if stored:
        return stored
    generated = secrets.token_hex(32)
    _JWT_SECRET_FILE.write_text(generated, encoding="utf-8")
    return generated


JWT_SECRET = _resolve_jwt_secret()
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300

_login_failures: dict[str, list[float]] = {}


def _prune_attempts(attempts: list[float], now: float) -> list[float]:
    return [t for t in attempts if now - t < LOGIN_WINDOW_SECONDS]


def is_login_locked(key: str) -> bool:
    now = time.time()
    attempts = _prune_attempts(_login_failures.get(key, []), now)
    _login_failures[key] = attempts
    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def register_login_failure(key: str) -> None:
    now = time.time()
    attempts = _prune_attempts(_login_failures.get(key, []), now)
    attempts.append(now)
    _login_failures[key] = attempts


def clear_login_failures(key: str) -> None:
    _login_failures.pop(key, None)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _encode(payload: dict[str, Any], expires_delta: timedelta) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(data, JWT_SECRET, algorithm="HS256")


def create_access_token(user: User) -> str:
    return _encode(
        {"sub": user.id, "type": "access"},
        timedelta(minutes=ACCESS_TOKEN_MINUTES),
    )


def create_refresh_token(user: User) -> str:
    return _encode(
        {
            "sub": user.id,
            "type": "refresh",
            "ver": user.refresh_token_version,
        },
        timedelta(days=REFRESH_TOKEN_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="未登录或登录已过期")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="登录令牌无效") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="登录令牌无效")

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="登录令牌无效")

    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


async def verify_refresh_token(token: str) -> User:
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="刷新令牌无效") from exc

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="刷新令牌无效")

    user_id = payload.get("sub")
    version = payload.get("ver")
    if not isinstance(user_id, str) or not isinstance(version, int):
        raise HTTPException(status_code=401, detail="刷新令牌无效")

    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    if user.refresh_token_version != version:
        raise HTTPException(status_code=401, detail="登录已在其他设备更新，请重新登录")

    return user


async def rotate_refresh_session(user: User) -> User:
    user.refresh_token_version += 1
    await user.save(update_fields=["refresh_token_version"])
    return user


async def ensure_default_user() -> User:
    default_username = os.getenv("APP_DEFAULT_USERNAME", "").strip() or "admin"
    user = await User.get_or_none(username=default_username)
    if user:
        return user

    default_password = os.getenv("APP_DEFAULT_PASSWORD", "").strip()
    if not default_password:
        default_password = secrets.token_urlsafe(9)
        print(
            f"[与神对话] 未检测到已有账户，且未设置 APP_DEFAULT_PASSWORD，"
            f"已自动生成初始账户：用户名 {default_username} / 密码 {default_password}"
            f"（请尽快登录后在设置页修改密码）"
        )
    return await User.create(
        id=f"user-{secrets.token_hex(6)}",
        username=default_username,
        password_hash=hash_password(default_password),
        refresh_token_version=0,
    )


def is_public_api_path(path: str) -> bool:
    if path in ("/api/auth/login", "/api/auth/refresh"):
        return True
    return False


async def auth_middleware(request: Request, call_next):
    from starlette.responses import JSONResponse

    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if not path.startswith("/api/") or is_public_api_path(path):
        return await call_next(request)

    credentials = request.headers.get("authorization", "")
    if not credentials.lower().startswith("bearer "):
        return JSONResponse(status_code=401, content={"detail": "未登录或登录已过期"})

    token = credentials.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except JWTError:
        return JSONResponse(status_code=401, content={"detail": "登录令牌无效"})

    if payload.get("type") != "access":
        return JSONResponse(status_code=401, content={"detail": "登录令牌无效"})

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        return JSONResponse(status_code=401, content={"detail": "登录令牌无效"})

    user = await User.get_or_none(id=user_id)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "用户不存在"})

    request.state.user = user
    return await call_next(request)
