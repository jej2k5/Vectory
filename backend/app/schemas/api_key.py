"""Pydantic schemas for API key endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key."""

    name: str = Field(..., min_length=1, max_length=255, description="Key name")
    permissions: dict | None = Field(None, description="Permission scopes")
    expires_at: datetime | None = Field(None, description="Expiration datetime")


class ApiKeyUpdate(BaseModel):
    """Schema for updating an API key."""

    name: str | None = Field(None, min_length=1, max_length=255)
    permissions: dict | None = None
    is_active: bool | None = None


class ApiKeyResponse(BaseModel):
    """Schema for API key responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = None
    user_id: UUID
    permissions: dict | None = None
    rate_limit: int = 100
    last_used_at: datetime | None = None
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool = True


class ApiKeyCreateResponse(ApiKeyResponse):
    """Schema returned when creating an API key (includes raw key)."""

    raw_key: str = Field(..., description="The raw API key (only shown once)")
