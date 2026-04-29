"""System routes: health, metrics, models, and system info."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query as QueryParam
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.config import settings
from app.database import get_db
from app.models.collection import Collection
from app.models.vector import VectorRecord
from app.models.query import Query

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health", summary="Health check")
async def health_check(db: AsyncSession = Depends(get_db)):
    # Check DB connectivity
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    # Check Redis connectivity
    redis_status = "healthy"
    try:
        import redis as redis_lib
        import os
        r = redis_lib.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        r.close()
    except Exception:
        redis_status = "unavailable"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "version": __version__,
    }


@router.get("/metrics", summary="System metrics")
async def system_metrics(db: AsyncSession = Depends(get_db)):
    collections_count = (await db.execute(select(func.count(Collection.id)))).scalar_one()
    vectors_count = (await db.execute(select(func.count(VectorRecord.id)))).scalar_one()
    queries_count = (await db.execute(select(func.count(Query.id)))).scalar_one()
    avg_latency = (await db.execute(select(func.avg(Query.latency_ms)))).scalar_one()

    return {
        "total_collections": collections_count,
        "total_vectors": vectors_count,
        "total_queries": queries_count,
        "avg_latency_ms": round(avg_latency, 2) if avg_latency else 0.0,
    }


@router.get("/metrics/activity", summary="Per-day query activity time series")
async def query_activity(
    days: int = QueryParam(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Return query count and average latency bucketed by UTC day, oldest first.

    Always returns exactly ``days`` buckets — missing days are zero-filled so the
    client can render a stable axis.
    """
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)

    result = await db.execute(
        text(
            """
            SELECT
                (date_trunc('day', created_at AT TIME ZONE 'UTC'))::date AS day,
                COUNT(*)::int AS queries,
                AVG(latency_ms) AS avg_latency
            FROM queries
            WHERE created_at >= :start_dt
            GROUP BY day
            """
        ),
        {"start_dt": start_dt},
    )
    rows_by_day = {row["day"]: row for row in result.mappings()}

    series: list[dict] = []
    for offset in range(days):
        d = start_date + timedelta(days=offset)
        row = rows_by_day.get(d)
        latency = row["avg_latency"] if row else None
        series.append(
            {
                "date": d.isoformat(),
                "queries": int(row["queries"]) if row else 0,
                "latency": round(float(latency), 2) if latency is not None else 0.0,
            }
        )
    return series


@router.get("/models", summary="List available embedding models")
async def list_models():
    return [
        {"name": "text-embedding-3-small", "provider": "openai", "dimensions": 1536},
        {"name": "text-embedding-3-large", "provider": "openai", "dimensions": 3072},
        {"name": "text-embedding-ada-002", "provider": "openai", "dimensions": 1536},
        {"name": "embed-english-v3.0", "provider": "cohere", "dimensions": 1024},
        {"name": "embed-multilingual-v3.0", "provider": "cohere", "dimensions": 1024},
        {"name": "all-MiniLM-L6-v2", "provider": "local", "dimensions": 384},
        {"name": "all-mpnet-base-v2", "provider": "local", "dimensions": 768},
    ]


@router.get("/system/info", summary="System information")
async def system_info():
    return {
        "name": "Vectory",
        "version": __version__,
        "api_version": "v1",
        "capabilities": [
            "vector_storage",
            "similarity_search",
            "hybrid_search",
            "ingestion_pipeline",
            "api_keys",
            "batch_operations",
        ],
        "supported_distance_metrics": ["cosine", "euclidean", "dot_product"],
        "supported_index_types": ["hnsw", "ivfflat", "flat"],
        "max_dimension": 4096,
        "max_batch_size": 1000,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
    }
