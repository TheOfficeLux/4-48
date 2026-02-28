"""Knowledge chunk and mastery ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-10
    format_type: Mapped[str] = mapped_column(String(50), nullable=False)  # content_format
    flesch_score: Mapped[float] = mapped_column(Float, default=60.0)
    neuro_tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    sensory_load: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)
    avg_engagement: Mapped[float] = mapped_column(Float, default=0.5)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class MasteryRecord(Base):
    __tablename__ = "mastery_records"

    mastery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("child_profiles.child_id"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    mastery_level: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stability: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)
    last_reviewed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_review_due: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    fsrs_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
