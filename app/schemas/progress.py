"""Progress, mastery, timeline, report schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class MasteryRecordResponse(BaseModel):
    mastery_id: UUID
    child_id: UUID
    topic: str
    mastery_level: float
    stability: float
    difficulty: float
    last_reviewed: str | None
    next_review_due: str | None
    review_count: int
    updated_at: str

    model_config = {"from_attributes": True}


class ProgressDashboardResponse(BaseModel):
    child_id: UUID
    mastery_records: list[MasteryRecordResponse] = Field(default_factory=list)
    total_sessions: int = 0
    total_interactions: int = 0


class TimelineDayPoint(BaseModel):
    date: str
    interactions: int
    avg_engagement: float | None


class TimelineResponse(BaseModel):
    child_id: UUID
    days: int
    timeline: list[TimelineDayPoint] = Field(default_factory=list)


class ReportResponse(BaseModel):
    child_id: UUID
    period_days: int
    total_sessions: int
    total_interactions: int
    mastery_summary: list[dict]
    trend_data: dict
    generated_at: str


class ReviewQueueItem(BaseModel):
    topic: str
    next_review_due: str
    mastery_level: float
    stability: float


class ReviewQueueResponse(BaseModel):
    child_id: UUID
    due_topics: list[ReviewQueueItem] = Field(default_factory=list)
