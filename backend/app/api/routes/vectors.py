"""Vector operations routes: CRUD and search."""

from __future__ import annotations

import hashlib
import time
import uuid as _uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.collection import Collection
from app.models.vector import VectorRecord
from app.models.query import Query
from app.models.user import User
from app.schemas.vector import VectorCreate, VectorResponse, VectorUpdate
from app.schemas.search import QueryRequest, QueryResponse, SearchResult, HybridSearchRequest
from app.core.embeddings import EmbeddingProvider

router = APIRouter(prefix="/collections", tags=["vectors"])


async def _get_collection_or_404(collection_id: _uuid.UUID, db: AsyncSession) -> Collection:
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection {collection_id} not found.")
    return collection


def _fingerprint(vector: list[float]) -> str:
    data = ",".join(f"{v:.8f}" for v in vector)
    return hashlib.sha256(data.encode()).hexdigest()


@router.post(
    "/{collection_id}/vectors",
    status_code=status.HTTP_201_CREATED,
    summary="Insert vectors",
)
async def insert_vectors(
    collection_id: _uuid.UUID,
    payload: VectorCreate | list[VectorCreate],
    db: AsyncSession = Depends(get_db),
):
    collection = await _get_collection_or_404(collection_id, db)

    items = payload if isinstance(payload, list) else [payload]
    results = []

    for item in items:
        if len(item.vector) != collection.dimension:
            raise HTTPException(
                status_code=400,
                detail=f"Vector dimension {len(item.vector)} doesn't match collection dimension {collection.dimension}",
            )
        record = VectorRecord(
            collection_id=collection_id,
            vector=item.vector,
            metadata_=item.metadata,
            text_content=item.text_content,
            source_file=item.source_file,
            chunk_index=item.chunk_index,
            fingerprint=_fingerprint(item.vector),
        )
        db.add(record)
        results.append(record)

    await db.flush()
    for r in results:
        await db.refresh(r)

    if isinstance(payload, list):
        return [{"id": str(r.id), "status": "created"} for r in results]
    return {"id": str(results[0].id), "status": "created"}


@router.get(
    "/{collection_id}/vectors/{vector_id}",
    response_model=VectorResponse,
    summary="Get vector by ID",
)
async def get_vector(
    collection_id: _uuid.UUID,
    vector_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VectorRecord).where(
            VectorRecord.id == vector_id,
            VectorRecord.collection_id == collection_id,
        )
    )
    vector = result.scalar_one_or_none()
    if vector is None:
        raise HTTPException(status_code=404, detail="Vector not found.")
    return vector


@router.patch(
    "/{collection_id}/vectors/{vector_id}",
    response_model=VectorResponse,
    summary="Update a vector",
)
async def update_vector(
    collection_id: _uuid.UUID,
    vector_id: _uuid.UUID,
    payload: VectorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(VectorRecord).where(
            VectorRecord.id == vector_id,
            VectorRecord.collection_id == collection_id,
        )
    )
    vector = result.scalar_one_or_none()
    if vector is None:
        raise HTTPException(status_code=404, detail="Vector not found.")

    update_data = payload.model_dump(exclude_unset=True)
    if "vector" in update_data and update_data["vector"] is not None:
        vector.vector = update_data["vector"]
        vector.fingerprint = _fingerprint(update_data["vector"])
    if "metadata" in update_data:
        vector.metadata_ = update_data["metadata"]
    if "text_content" in update_data:
        vector.text_content = update_data["text_content"]

    await db.commit()
    await db.refresh(vector)
    return vector


@router.delete(
    "/{collection_id}/vectors/{vector_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a vector",
)
async def delete_vector(
    collection_id: _uuid.UUID,
    vector_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(VectorRecord).where(
            VectorRecord.id == vector_id,
            VectorRecord.collection_id == collection_id,
        )
    )
    vector = result.scalar_one_or_none()
    if vector is None:
        raise HTTPException(status_code=404, detail="Vector not found.")
    await db.delete(vector)
    await db.commit()


@router.post(
    "/{collection_id}/vectors/batch-delete",
    summary="Bulk delete vectors",
)
async def batch_delete_vectors(
    collection_id: _uuid.UUID,
    vector_ids: list[_uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        delete(VectorRecord).where(
            VectorRecord.id.in_(vector_ids),
            VectorRecord.collection_id == collection_id,
        )
    )
    await db.commit()
    return {"deleted": result.rowcount}


@router.post(
    "/{collection_id}/query",
    response_model=QueryResponse,
    summary="Similarity search",
)
async def similarity_search(
    collection_id: _uuid.UUID,
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    collection = await _get_collection_or_404(collection_id, db)

    if payload.vector is None and payload.text is None:
        raise HTTPException(status_code=400, detail="Either 'vector' or 'text' must be provided.")

    query_vector = payload.vector
    if query_vector is None:
        # In production, generate embedding from text. For now, return error.
        query_vector = EmbeddingProvider.get_embedding(
           payload.text,
           model=collection.embedding_model,
           dimension=collection.dimension,
       )

    if len(query_vector) != collection.dimension:
        raise HTTPException(
            status_code=400,
            detail=f"Query vector dimension {len(query_vector)} doesn't match collection dimension {collection.dimension}",
        )

    metric = payload.distance_metric or collection.distance_metric

    # Distance operator for pgvector
    if metric == "cosine":
        op = "<=>"
    elif metric == "euclidean":
        op = "<->"
    elif metric == "dot_product":
        op = "<#>"
    else:
        op = "<=>"

    start = time.perf_counter()

    vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

    filter_clause = ""
    if payload.filters:
        filter_clause = "AND metadata @> :filters::jsonb"

    sql = text(f"""
        SELECT id, collection_id, metadata, text_content, source_file, chunk_index,
               vector {op} :query_vector::vector AS distance
        FROM vectors
        WHERE collection_id = :collection_id
        {filter_clause}
        ORDER BY vector {op} :query_vector::vector
        LIMIT :top_k
    """)

    params: dict[str, Any] = {
        "query_vector": vector_str,
        "collection_id": str(collection_id),
        "top_k": payload.top_k,
    }
    if payload.filters:
        import json
        params["filters"] = json.dumps(payload.filters)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    elapsed_ms = (time.perf_counter() - start) * 1000

    results = []
    for row in rows:
        distance = float(row.distance) if row.distance is not None else 0.0
        if metric == "cosine":
            score = 1.0 - distance
        elif metric == "dot_product":
            score = -distance
        else:
            score = 1.0 / (1.0 + distance)

        results.append(SearchResult(
            id=row.id,
            score=round(score, 6),
            distance=round(distance, 6),
            metadata=row.metadata,
            text_content=row.text_content,
        ))

    # Record query analytics
    query_record = Query(
        collection_id=collection_id,
        query_vector=query_vector,
        query_text=payload.text,
        results_count=len(results),
        latency_ms=round(elapsed_ms, 2),
        filters=payload.filters,
    )
    db.add(query_record)

    return QueryResponse(
        results=results,
        total=len(results),
        query_id=query_record.id,
        latency_ms=round(elapsed_ms, 2),
        collection_id=collection_id,
        distance_metric=metric,
    )


@router.post(
    "/{collection_id}/hybrid-search",
    response_model=QueryResponse,
    summary="Hybrid search (vector + text)",
)
async def hybrid_search(
    collection_id: _uuid.UUID,
    payload: HybridSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    collection = await _get_collection_or_404(collection_id, db)

    if payload.vector is None and payload.text is None:
        raise HTTPException(status_code=400, detail="Either 'vector' or 'text' must be provided.")

    start = time.perf_counter()

    metric = payload.distance_metric or collection.distance_metric
    if metric == "cosine":
        op = "<=>"
    elif metric == "euclidean":
        op = "<->"
    else:
        op = "<#>"

    # Build hybrid query combining vector similarity and text search
    has_vector = payload.vector is not None
    has_text = payload.text is not None and payload.text.strip() != ""

    if has_vector and has_text:
        vector_str = "[" + ",".join(str(v) for v in payload.vector) + "]"
        sql = text(f"""
            SELECT id, collection_id, metadata, text_content, source_file, chunk_index,
                   (1.0 - (vector {op} :query_vector::vector)) * :vector_weight +
                   ts_rank(to_tsvector('english', COALESCE(text_content, '')), plainto_tsquery('english', :query_text)) * :text_weight
                   AS combined_score
            FROM vectors
            WHERE collection_id = :collection_id
            ORDER BY combined_score DESC
            LIMIT :top_k
        """)
        params = {
            "query_vector": vector_str,
            "query_text": payload.text,
            "vector_weight": payload.vector_weight,
            "text_weight": payload.text_weight,
            "collection_id": str(collection_id),
            "top_k": payload.top_k,
        }
    elif has_text:
        sql = text("""
            SELECT id, collection_id, metadata, text_content, source_file, chunk_index,
                   ts_rank(to_tsvector('english', COALESCE(text_content, '')), plainto_tsquery('english', :query_text))
                   AS combined_score
            FROM vectors
            WHERE collection_id = :collection_id
              AND to_tsvector('english', COALESCE(text_content, '')) @@ plainto_tsquery('english', :query_text)
            ORDER BY combined_score DESC
            LIMIT :top_k
        """)
        params = {
            "query_text": payload.text,
            "collection_id": str(collection_id),
            "top_k": payload.top_k,
        }
    else:
        # Vector only - delegate to similarity_search logic
        return await similarity_search(
            collection_id,
            QueryRequest(
                vector=payload.vector,
                top_k=payload.top_k,
                filters=payload.filters,
                distance_metric=payload.distance_metric,
            ),
            db,
        )

    result = await db.execute(sql, params)
    rows = result.fetchall()

    elapsed_ms = (time.perf_counter() - start) * 1000

    results = []
    for row in rows:
        score = float(row.combined_score) if row.combined_score is not None else 0.0
        results.append(SearchResult(
            id=row.id,
            score=round(score, 6),
            metadata=row.metadata,
            text_content=row.text_content,
        ))

    query_record = Query(
        collection_id=collection_id,
        query_vector=payload.vector,
        query_text=payload.text,
        results_count=len(results),
        latency_ms=round(elapsed_ms, 2),
        filters=payload.filters,
    )
    db.add(query_record)

    return QueryResponse(
        results=results,
        total=len(results),
        query_id=query_record.id,
        latency_ms=round(elapsed_ms, 2),
        collection_id=collection_id,
        distance_metric=metric,
    )
