"""Admin (ingest) request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    content: str = Field(min_length=1)
    topic: str = Field(min_length=1, max_length=100)
    subject_area: str | None = None
    difficulty_level: int = Field(ge=1, le=10)
    format_type: str  # EXPLANATION, STORY, QUIZ, etc.
    flesch_score: float = 60.0
    sensory_load: float = Field(default=0.3, ge=0, le=1)
    neuro_tags: dict = Field(
        default_factory=dict,
        description="e.g. {adhd_suitable, asd_suitable, idiom_density, word_count}",
    )


class IngestResponse(BaseModel):
    chunk_id: UUID
