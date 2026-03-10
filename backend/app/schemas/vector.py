"""Pydantic schemas for Vector endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VectorCreate(BaseModel):
    """Schema for creating/inserting a single vector."""

    vector: list[float] = Field(..., description="The embedding vector")
    metadata: dict | None = Field(None, description="Arbitrary JSON metadata")
    text_content: str | None = Field(None, description="Original text content")
    source_file: str | None = Field(None, max_length=500, description="Source file path")
    chunk_index: int | None = Field(None, ge=0, description="Chunk index within source")


class VectorUpdate(BaseModel):
    """Schema for updating a vector record."""

    vector: list[float] | None = Field(None, description="Replacement embedding vector")
    metadata: dict | None = None
    text_content: str | None = None


class VectorResponse(BaseModel):
    """Schema for vector responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collection_id: UUID
    job_id: UUID | None = None
    metadata: dict | None = Field(None, alias="metadata_")
    text_content: str | None = None
    source_file: str | None = None
    chunk_index: int | None = None
    fingerprint: str | None = None
    created_at: datetime
    updated_at: datetime
