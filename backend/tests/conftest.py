"""Pytest configuration and fixtures."""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-jwt-secret-key-for-testing-only-32chars"
os.environ["JWT_REFRESH_SECRET"] = "test-refresh-secret-key-for-testing-32chars"

# Patch engine factories so SQLite works without pool_size/max_overflow args
import sqlalchemy
import sqlalchemy.ext.asyncio as _async_mod

_orig_async_create = _async_mod.create_async_engine
_orig_sync_create = sqlalchemy.create_engine


def _safe_async_create(url, **kw):
    if "sqlite" in str(url):
        for k in ("pool_size", "max_overflow", "pool_pre_ping", "pool_recycle"):
            kw.pop(k, None)
    return _orig_async_create(url, **kw)


def _safe_sync_create(url, **kw):
    if "sqlite" in str(url):
        for k in ("pool_size", "max_overflow", "pool_pre_ping", "pool_recycle"):
            kw.pop(k, None)
    return _orig_sync_create(url, **kw)


_async_mod.create_async_engine = _safe_async_create
sqlalchemy.create_engine = _safe_sync_create


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
