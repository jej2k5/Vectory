"""Pydantic schemas for User responses."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Schema for user responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str | None = None
    is_active: bool = True
    created_at: datetime
