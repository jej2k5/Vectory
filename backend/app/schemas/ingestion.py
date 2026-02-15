"""Pydantic schemas for ingestion job endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IngestionJobCreate(BaseModel):
    """Schema for creating an ingestion job."""

    file_path: str = Field(..., max_length=1000, description="Path to uploaded file")
    file_name: str = Field(..., max_length=500, description="Original file name")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    file_type: str = Field(..., max_length=50, description="MIME type or extension")
    config: dict | None = Field(None, description="Chunking / processing configuration")


class IngestionJobUpdate(BaseModel):
    """Schema for updating an ingestion job."""

    status: str | None = Field(
        None,
        pattern="^(pending|processing|completed|failed|cancelled)$",
        description="Job status",
    )
    error_message: str | None = None
    total_chunks: int | None = Field(None, ge=0)
    processed_chunks: int | None = Field(None, ge=0)
    failed_chunks: int | None = Field(None, ge=0)


class IngestionJobResponse(BaseModel):
    """Schema for ingestion job responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collection_id: UUID
    status: str
    file_path: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    total_chunks: int = 0
    processed_chunks: int = 0
    failed_chunks: int = 0
    error_message: str | None = None
    config: dict | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
