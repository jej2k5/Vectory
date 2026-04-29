# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack

- **Backend**: FastAPI (async) + SQLAlchemy 2.0 + Pydantic v2, served by uvicorn
- **Frontend**: Next.js 14 App Router + TailwindCSS + React Query + Zustand
- **Datastore**: PostgreSQL 15 with `pgvector` (IVFFlat / HNSW); JSONB metadata with GIN indexes
- **Async work**: Celery workers backed by Redis (broker on db `0`, results on db `1`)
- **Object storage**: MinIO (S3-compatible) for uploaded source documents
- **Auth**: JWT (access + refresh) plus hashed API keys with permission scopes

## Common commands

Full stack via Docker (`postgres`, `redis`, `minio`, `backend`, `celery-worker`, `frontend`):

```bash
cp .env.example .env          # required — backend reads DATABASE_URL, JWT secrets, etc. from here
docker-compose up -d
```

Backend dev (from `backend/`, requires Postgres/Redis/MinIO running — typically `docker-compose up -d postgres redis minio`):

```bash
uvicorn app.main:app --reload                          # API on :8000, docs at /api/docs
celery -A app.workers.celery_app worker --loglevel=info  # ingestion worker
pytest                                                  # all tests
pytest tests/test_mcp.py::test_name                     # single test
black . && ruff check .                                 # format + lint (line-length 100, py311)
```

Frontend dev (from `frontend/`):

```bash
npm run dev      # Next.js on :3000
npm run build
npm run lint     # eslint (next/core-web-vitals)
npm run format   # prettier on src/**/*.{ts,tsx}
```

The frontend in dev mode proxies `/api/*` to `BACKEND_URL` (default `http://localhost:8000`) via `frontend/src/middleware.ts`, so client code calls relative `/api/...` paths.

## Architecture notes that aren't obvious from a single file

### Two SQLAlchemy engines, on purpose
`backend/app/database.py` exports both an **async** engine (`engine`, `async_session_maker`, `get_db`) used by FastAPI request handlers and a **sync** engine (`sync_engine`, `sync_session_maker`) used inside Celery tasks. `Settings.async_database_url` / `sync_database_url` rewrite the same `DATABASE_URL` between `asyncpg` and `psycopg2` drivers, so config carries one URL but code picks the right driver per context. Don't import the async session into a Celery task or vice versa.

### Schema is created at startup, not via migrations
`main.py`'s `lifespan` runs `Base.metadata.create_all` on boot. Alembic is in `requirements.txt` but no migration tree is wired up — schema changes happen by editing `app/models/*.py`. `database/init.sql` runs once on first Postgres container init (creates the `vector` extension, pre-creates indexes). For schema changes against an existing volume, you must drop tables or reset the volume manually.

### Routers are imported defensively
`main.py` uses `_try_import_router` so the app still starts when a route module fails to import. When adding a new route module, also add a `_try_import_router("app.api.routes.<name>")` line — otherwise it silently won't be mounted. All routers are mounted under the `/api` prefix.

### MCP is a layer over REST, not a parallel implementation
`backend/app/api/routes/mcp.py` defines `TOOLS` and `RESOURCES` dicts that map MCP primitives to existing REST routes. Invocations dispatch *back into the same FastAPI app* via `httpx.ASGITransport`, so auth, validation, and business logic are reused. The router is mounted twice — under `/api/mcp` (alongside the REST API) and at the root `/mcp` (standard MCP discovery path). When you add a new REST endpoint that should be MCP-callable, add a corresponding entry to `TOOLS` or `RESOURCES`; do not duplicate logic in the MCP module.

### Auth flow (frontend)
`frontend/src/middleware.ts` enforces auth at the edge: it allows `/auth/*` and static assets, rewrites `/api/*` to the backend, and otherwise requires a `vectory_access_token` cookie (redirecting to `/auth/login?redirect=...` if missing). The cookie is set client-side after login. Server components/routes do not see the JWT — token usage happens in browser-side fetches.

### Ingestion pipeline
Upload (`POST /api/ingestion/upload`) → create job (`POST /api/ingestion/jobs`) → Celery task in `app/workers/tasks.py` parses (PDF/DOCX/TXT/CSV/JSON/MD via `app/utils/parsers.py`), chunks (`app/utils/chunking.py`), embeds (`app/core/embeddings.py`, OpenAI or mock), batch-inserts vectors, and writes progress to the `ingestion_jobs` row. Clients poll `GET /api/ingestion/jobs/:id/progress` (SSE).

### Upload size cap
`MAX_UPLOAD_SIZE_MB` (default 100) exists because parsers materialize content in memory — see the comment on `Settings.MAX_UPLOAD_SIZE_MB` for the multipliers per format. Treat changing this as a memory/cost decision, not just a config tweak.

## Conventions

- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `perf:`).
- **Python**: Black + Ruff (line-length 100, target `py311`), type hints required, `asyncio_mode = "auto"` for pytest.
- **TypeScript**: strict mode; Prettier + ESLint (`next/core-web-vitals`).
