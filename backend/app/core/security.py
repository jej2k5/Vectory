"""Security utilities: JWT tokens, password hashing, API key management."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ── Password hashing ─────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return ``True`` if *plain_password* matches *hashed_password*."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT tokens ────────────────────────────────────────────────────────────────


def create_access_token(
    subject: str | UUID,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    subject:
        The ``sub`` claim – typically the user's UUID as a string.
    extra_claims:
        Additional claims merged into the payload.
    expires_delta:
        Custom expiry.  Falls back to ``ACCESS_TOKEN_EXPIRE_MINUTES`` from
        settings.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT refresh token.

    Refresh tokens use a separate secret (``JWT_REFRESH_SECRET``) so that
    compromise of one secret does not automatically compromise both token
    types.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token.

    Raises
    ------
    JWTError
        If the token is expired, malformed, or signed with the wrong key.
    ValueError
        If the token's ``type`` claim is not ``"access"``.
    """
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise ValueError("Token type is not 'access'")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a refresh token.

    Raises
    ------
    JWTError
        If the token is expired, malformed, or signed with the wrong key.
    ValueError
        If the token's ``type`` claim is not ``"refresh"``.
    """
    payload = jwt.decode(
        token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("type") != "refresh":
        raise ValueError("Token type is not 'refresh'")
    return payload


# ── API key utilities ─────────────────────────────────────────────────────────

API_KEY_PREFIX = "vy_"
API_KEY_BYTE_LENGTH = 32  # 256 bits of entropy


def generate_api_key() -> str:
    """Generate a cryptographically random API key.

    The key is prefixed with ``vy_`` to make it easy to identify in logs
    or secret scanners.  Example: ``vy_a3f1c9...``
    """
    return f"{API_KEY_PREFIX}{secrets.token_hex(API_KEY_BYTE_LENGTH)}"


def hash_api_key(api_key: str) -> str:
    """Return the SHA-256 hex digest of *api_key*.

    Only the hash is stored; the raw key is shown to the user exactly once
    at creation time.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
    "generate_api_key",
    "hash_api_key",
    "pwd_context",
    "JWTError",
]
