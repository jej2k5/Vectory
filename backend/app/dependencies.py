"""Reusable FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token, hash_api_key
from app.database import get_db

# ── OAuth2 scheme (JWT Bearer) ────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# ── API key header scheme ─────────────────────────────────────────────────────

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Extract and validate the current user from a JWT access token.

    Returns the User ORM instance or raises 401.

    The import of the User model is deferred to avoid circular imports
    (models -> database -> dependencies -> models).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    # Deferred import to break circular dependency.
    from app.models.user import User  # noqa: WPS433

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user if a valid token is present, otherwise ``None``.

    Useful for endpoints that behave differently for authenticated vs.
    anonymous requests.
    """
    if token is None:
        return None

    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        return None

    from app.models.user import User  # noqa: WPS433

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
):
    """Validate an API key passed via the ``X-API-Key`` header.

    Returns the ApiKey ORM instance (with the owning user eagerly loaded)
    or raises 401.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    key_hash = hash_api_key(api_key)

    # Deferred import to avoid circular dependency.
    from app.models.api_key import ApiKey  # noqa: WPS433

    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key_record = result.scalar_one_or_none()

    if api_key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    if not api_key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has been revoked",
        )

    return api_key_record


__all__ = [
    "get_current_user",
    "get_optional_user",
    "verify_api_key",
]
