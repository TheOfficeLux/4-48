"""Learn (ask, signal, feedback) request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    child_id: UUID
    session_id: UUID
    input_text: str = Field(min_length=1, max_length=2000)
    input_type: str = Field(default="TEXT", pattern="^(TEXT|VOICE|SELECTION)$")


class ChunkUsed(BaseModel):
    topic: str
    difficulty_level: int
    format_type: str


class AskResponse(BaseModel):
    interaction_id: UUID
    response_text: str
    ui_directives: dict = Field(default_factory=dict)
    session_constraints: dict = Field(default_factory=dict)
    chunks_used: list[dict] = Field(default_factory=list)  # [{topic, difficulty_level, format_type}]
    response_time_ms: int


class SignalRequest(BaseModel):
    child_id: UUID
    session_id: UUID
    signal_type: str
    value: float
    raw_payload: dict | None = None


class StateSnapshot(BaseModel):
    cognitive_load: float
    mood_score: float
    readiness_score: float


class SignalResponse(BaseModel):
    state: StateSnapshot


class FeedbackRequest(BaseModel):
    interaction_id: UUID
    child_id: UUID
    topic: str
    rating: int = Field(ge=1, le=4)  # FSRS: 1=Again 2=Hard 3=Good 4=Easy
    engagement_score: float = Field(ge=0, le=1, default=0.5)
    child_reaction: str = Field(
        pattern="^(POSITIVE|NEUTRAL|CONFUSED|FRUSTRATED|EXCITED)$"
    )


class FeedbackResponse(BaseModel):
    topic: str
    mastery_level: float
    next_review_days: float | None
