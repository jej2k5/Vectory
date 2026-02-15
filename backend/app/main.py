"""Vectory FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.database import Base, engine
from app.utils.logger import logger

# ---------------------------------------------------------------------------
# Router imports – each module exposes a ``router`` attribute.
# Routes that have not been created yet are imported conditionally so the
# application can still start during early development.
# ---------------------------------------------------------------------------

_routers: list = []


def _try_import_router(module_path: str) -> None:
    """Attempt to import a router; log a warning on failure."""
    try:
        import importlib

        mod = importlib.import_module(module_path)
        _routers.append(mod.router)
    except (ImportError, AttributeError) as exc:
        logger.warning("Could not import router from {}: {}", module_path, exc)


_try_import_router("app.api.routes.auth")
_try_import_router("app.api.routes.collections")
_try_import_router("app.api.routes.vectors")
_try_import_router("app.api.routes.ingestion")
_try_import_router("app.api.routes.keys")
_try_import_router("app.api.routes.system")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle hook.

    * On startup: create all database tables (safe in dev; use Alembic for prod).
    * On shutdown: dispose of the async engine connection pool.
    """
    logger.info("Starting Vectory v{}", __version__)

    # Create tables if they don't already exist.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified / created")

    yield  # ← application is running

    await engine.dispose()
    logger.info("Vectory shutdown complete")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Vectory",
    description=(
        "A vector database management platform providing REST APIs for "
        "collection management, vector storage, document ingestion, and "
        "semantic search powered by configurable embedding models."
    ),
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS middleware ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers under /api ──────────────────────────────────────────────────

for router in _routers:
    app.include_router(router, prefix="/api")


# ── Root health-check (outside /api prefix) ───────────────────────────────────


@app.get("/health", tags=["health"])
async def health_check():
    """Minimal liveness probe."""
    return {"status": "healthy", "version": __version__}
