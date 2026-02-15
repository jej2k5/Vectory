"""Collection management routes: CRUD, statistics, optimization, and export."""

from __future__ import annotations

import uuid as _uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.collection import Collection
from app.models.user import User
from app.models.vector import VectorRecord
from app.models.query import Query
from app.schemas.collection import (
    CollectionCreate,
    CollectionList,
    CollectionResponse,
    CollectionStats,
    CollectionUpdate,
)

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _get_collection_or_404(
    collection_id: _uuid.UUID,
    db: AsyncSession,
) -> Collection:
    """Return the collection or raise 404."""
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection {collection_id} not found.",
        )
    return collection


# ── GET / ─────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=CollectionList,
    summary="List all collections",
)
async def list_collections(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated list of collections."""
    # Total count
    count_result = await db.execute(select(func.count(Collection.id)))
    total = count_result.scalar_one()

    # Paginated items
    result = await db.execute(
        select(Collection)
        .order_by(Collection.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    collections = list(result.scalars().all())

    return CollectionList(items=collections, total=total, skip=skip, limit=limit)


# ── POST / ────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new collection",
)
async def create_collection(
    payload: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new vector collection.

    Validates that the collection name is unique.
    """
    # Check uniqueness
    result = await db.execute(
        select(Collection).where(Collection.name == payload.name)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A collection named '{payload.name}' already exists.",
        )

    collection = Collection(
        name=payload.name,
        description=payload.description,
        embedding_model=payload.embedding_model,
        dimension=payload.dimension,
        distance_metric=payload.distance_metric,
        index_type=payload.index_type,
        config=payload.config,
        created_by=current_user.id,
    )
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return collection


# ── GET /{collection_id} ─────────────────────────────────────────────────────


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Get collection details",
)
async def get_collection(
    collection_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return the details of a single collection."""
    return await _get_collection_or_404(collection_id, db)


# ── PATCH /{collection_id} ───────────────────────────────────────────────────


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Update a collection",
)
async def update_collection(
    collection_id: _uuid.UUID,
    payload: CollectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update mutable fields of a collection.

    Only fields present in the request body are updated.
    """
    collection = await _get_collection_or_404(collection_id, db)

    update_data = payload.model_dump(exclude_unset=True)

    # If the name is being changed, check uniqueness
    if "name" in update_data:
        result = await db.execute(
            select(Collection).where(
                Collection.name == update_data["name"],
                Collection.id != collection_id,
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A collection named '{update_data['name']}' already exists.",
            )

    for field, value in update_data.items():
        setattr(collection, field, value)

    await db.commit()
    await db.refresh(collection)
    return collection


# ── DELETE /{collection_id} ──────────────────────────────────────────────────


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a collection",
)
async def delete_collection(
    collection_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a collection and all of its vectors."""
    collection = await _get_collection_or_404(collection_id, db)
    await db.delete(collection)
    await db.commit()
    return None


# ── GET /{collection_id}/stats ───────────────────────────────────────────────


@router.get(
    "/{collection_id}/stats",
    response_model=CollectionStats,
    summary="Get collection statistics",
)
async def get_collection_stats(
    collection_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return statistics for a collection including vector count and index size."""
    collection = await _get_collection_or_404(collection_id, db)

    # Get actual vector count from the vectors table
    count_result = await db.execute(
        select(func.count(VectorRecord.id)).where(
            VectorRecord.collection_id == collection_id
        )
    )
    vector_count = count_result.scalar_one()

    # Get query count
    query_count_result = await db.execute(
        select(func.count(Query.id)).where(
            Query.collection_id == collection_id
        )
    )
    query_count = query_count_result.scalar_one()

    # Average query latency
    avg_latency_result = await db.execute(
        select(func.avg(Query.latency_ms)).where(
            Query.collection_id == collection_id
        )
    )
    avg_latency = avg_latency_result.scalar_one()

    return CollectionStats(
        collection_id=collection.id,
        vector_count=vector_count,
        index_size_bytes=collection.index_size_bytes,
        dimension=collection.dimension,
        distance_metric=collection.distance_metric,
        index_type=collection.index_type,
        total_queries=query_count,
        avg_query_latency_ms=round(avg_latency, 2) if avg_latency is not None else None,
    )


# ── POST /{collection_id}/optimize ──────────────────────────────────────────


@router.post(
    "/{collection_id}/optimize",
    summary="Rebuild the collection index",
)
async def optimize_collection(
    collection_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Trigger an index rebuild / optimization for the collection.

    This is an idempotent operation.  In a production setup this would
    dispatch a background task; here we acknowledge the request.
    """
    collection = await _get_collection_or_404(collection_id, db)

    # In production, dispatch an async task to rebuild the index.
    # For now we acknowledge the request.
    return {
        "status": "optimization_started",
        "collection_id": str(collection.id),
        "index_type": collection.index_type,
        "message": f"Index rebuild queued for collection '{collection.name}'.",
    }


# ── POST /{collection_id}/export ─────────────────────────────────────────────


@router.post(
    "/{collection_id}/export",
    summary="Export collection data",
)
async def export_collection(
    collection_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Export all vectors and metadata for a collection as JSON."""
    collection = await _get_collection_or_404(collection_id, db)

    # Fetch all vectors belonging to this collection
    result = await db.execute(
        select(VectorRecord).where(VectorRecord.collection_id == collection_id)
    )
    vectors = result.scalars().all()

    exported_vectors = []
    for v in vectors:
        exported_vectors.append(
            {
                "id": str(v.id),
                "vector": list(v.vector) if v.vector is not None else None,
                "metadata": v.metadata_,
                "text_content": v.text_content,
                "source_file": v.source_file,
                "chunk_index": v.chunk_index,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
        )

    return {
        "collection": {
            "id": str(collection.id),
            "name": collection.name,
            "dimension": collection.dimension,
            "distance_metric": collection.distance_metric,
            "embedding_model": collection.embedding_model,
        },
        "vectors": exported_vectors,
        "total": len(exported_vectors),
    }
