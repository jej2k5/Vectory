"""Pydantic schemas for auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    name: str | None = Field(None, description="User display name")


class UserLogin(BaseModel):
    """Schema for logging in."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Schema for token responses."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for refreshing a token."""

    refresh_token: str = Field(..., description="The refresh token")
