from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    distance_metric: Mapped[str] = mapped_column(
        String(20),
        default="cosine",
        server_default=text("'cosine'"),
        nullable=False,
    )
    index_type: Mapped[str] = mapped_column(
        String(20),
        default="hnsw",
        server_default=text("'hnsw'"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    config: Mapped[dict | None] = mapped_column(JSONB, default=None)
    vector_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    index_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default=text("0"),
        nullable=False,
    )

    # Relationships
    creator: Mapped[User | None] = relationship(
        "User",
        back_populates="collections",
    )
    vectors: Mapped[list[VectorRecord]] = relationship(
        "VectorRecord",
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin",
        passive_deletes=True,
    )
    ingestion_jobs: Mapped[list[IngestionJob]] = relationship(
        "IngestionJob",
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin",
        passive_deletes=True,
    )
    queries: Mapped[list[Query]] = relationship(
        "Query",
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name={self.name!r}, dimension={self.dimension})>"
