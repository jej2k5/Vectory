"""SQLAlchemy async (and sync) engine, session factories, and base model."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# ── Naming convention for constraints (keeps Alembic auto-gen predictable) ────

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


# ── Declarative Base ──────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    metadata = metadata


# ── Async engine & session (FastAPI) ──────────────────────────────────────────

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.LOG_LEVEL.upper() == "DEBUG",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    The session is committed on success and rolled back on exception.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Sync engine & session (Celery workers) ────────────────────────────────────

sync_engine = create_engine(
    settings.sync_database_url,
    echo=settings.LOG_LEVEL.upper() == "DEBUG",
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
)

sync_session_maker = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False,
)


__all__ = [
    "Base",
    "async_session_maker",
    "engine",
    "get_db",
    "metadata",
    "sync_engine",
    "sync_session_maker",
]
