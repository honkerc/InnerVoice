import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from models import User

JWT_SECRET = os.getenv("JWT_SECRET", "yushenduihua-dev-secret-change-me")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


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
    user = await User.get_or_none(username="admin")
    if user:
        return user

    default_password = os.getenv("APP_DEFAULT_PASSWORD", "123456")
    return await User.create(
        id=f"user-{secrets.token_hex(6)}",
        username="admin",
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
