"""Session request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class SessionStartRequest(BaseModel):
    child_id: UUID


class SessionStartResponse(BaseModel):
    session_id: UUID
    ui_directives: dict = Field(default_factory=dict)
    session_constraints: dict = Field(default_factory=dict)


class SessionEndResponse(BaseModel):
    session_id: UUID
    total_interactions: int
    avg_response_time_ms: int | None
    frustration_events: int
    hyperfocus_flag: bool
    session_quality: float | None
    topics_covered: list[str] | None


class SessionStatusResponse(BaseModel):
    session_id: UUID
    child_id: UUID
    started_at: str
    ended_at: str | None
    total_interactions: int
    avg_response_time_ms: int | None
    frustration_events: int
    hyperfocus_flag: bool
    session_quality: float | None
    topics_covered: list[str] | None
