"""Pydantic schemas for Collection endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CollectionCreate(BaseModel):
    """Schema for creating a new collection."""

    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: str | None = Field(None, description="Optional description")
    embedding_model: str = Field(
        "text-embedding-3-small", max_length=100, description="Embedding model name"
    )
    dimension: int = Field(1536, gt=0, le=65536, description="Vector dimension")
    distance_metric: str = Field(
        "cosine",
        pattern="^(cosine|euclidean|dot_product)$",
        description="Distance metric",
    )
    index_type: str = Field(
        "hnsw",
        pattern="^(hnsw|ivfflat|flat)$",
        description="Index type",
    )
    config: dict | None = Field(None, description="Additional configuration")


class CollectionUpdate(BaseModel):
    """Schema for updating an existing collection."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    config: dict | None = None


class CollectionResponse(BaseModel):
    """Schema for collection responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    embedding_model: str
    dimension: int
    distance_metric: str
    index_type: str
    vector_count: int = 0
    index_size_bytes: int = 0
    config: dict | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class CollectionList(BaseModel):
    """Paginated list of collections."""

    items: list[CollectionResponse] = Field(default_factory=list)
    total: int = 0
    skip: int = 0
    limit: int = 50


class CollectionStats(BaseModel):
    """Collection statistics."""

    collection_id: UUID
    vector_count: int = 0
    index_size_bytes: int = 0
    dimension: int
    distance_metric: str
    index_type: str
    total_queries: int = 0
    avg_query_latency_ms: float | None = None
