"""Password hashing and JWT access/refresh token helpers."""
import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# bcrypt has a hard 72-byte input limit; passwords are validated to <=128 chars
# (schemas/auth.py) which is comfortably under that for virtually all inputs,
# but we truncate defensively rather than letting bcrypt raise.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (used directly — no passlib — to
    avoid the passlib/bcrypt>=4.1 `__about__` incompatibility)."""
    truncated = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    truncated = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(truncated, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict[str, Any]) -> str:
    """Create a short-lived (30min default) JWT access token."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {**data, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> tuple[str, datetime]:
    """Create a long-lived (7d default) JWT refresh token. Returns (token, expires_at)."""
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_hex(16)
    payload = {**data, "exp": expire, "type": "refresh", "jti": jti}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT. Returns None if invalid/expired."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        logger.info("Failed to decode token: %s", exc)
        return None


def hash_token(token: str) -> str:
    """Hash a refresh token for storage/lookup (raw tokens are never persisted)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
