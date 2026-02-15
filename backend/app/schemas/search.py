"""Pydantic schemas for search / query endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema for a similarity search request."""

    vector: list[float] | None = Field(None, description="Query vector")
    text: str | None = Field(None, description="Query text (will be embedded)")
    top_k: int = Field(10, ge=1, le=1000, description="Number of results to return")
    distance_metric: str | None = Field(
        None,
        pattern="^(cosine|euclidean|dot_product)$",
        description="Override collection distance metric",
    )
    filters: dict | None = Field(None, description="Metadata filters (JSONB containment)")
    include_vectors: bool = Field(False, description="Include vectors in results")
    include_metadata: bool = Field(True, description="Include metadata in results")


class HybridSearchRequest(BaseModel):
    """Schema for a hybrid (vector + full-text) search request."""

    vector: list[float] | None = Field(None, description="Query vector")
    text: str | None = Field(None, description="Query text for full-text + embedding")
    top_k: int = Field(10, ge=1, le=1000, description="Number of results to return")
    distance_metric: str | None = Field(None, pattern="^(cosine|euclidean|dot_product)$")
    filters: dict | None = Field(None, description="Metadata filters")
    include_vectors: bool = Field(False)
    include_metadata: bool = Field(True)
    vector_weight: float = Field(0.7, ge=0.0, le=1.0, description="Weight for vector similarity")
    text_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for text relevance")


class SearchResult(BaseModel):
    """A single search result."""

    id: UUID
    score: float = Field(..., description="Similarity/relevance score")
    distance: float | None = Field(None, description="Raw distance value")
    metadata: dict | None = None
    text_content: str | None = None
    vector: list[float] | None = None


class QueryResponse(BaseModel):
    """Schema for search query responses."""

    results: list[SearchResult] = Field(default_factory=list)
    total: int = Field(0, description="Number of results returned")
    query_id: UUID | None = Field(None, description="ID of the stored query record")
    latency_ms: float = Field(0.0, description="Query latency in milliseconds")
    collection_id: UUID | None = None
    distance_metric: str | None = None
