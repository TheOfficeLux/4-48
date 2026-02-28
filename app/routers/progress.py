"""GET /progress/{child_id}, /mastery, /timeline, /report, /review-queue."""

from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy import select, func

from app.dependencies import get_current_user_required, get_child
from app.models import Caregiver, MasteryRecord, LearningSession, Interaction
from app.schemas.progress import (
    ProgressDashboardResponse,
    MasteryRecordResponse,
    TimelineResponse,
    TimelineDayPoint,
    ReportResponse,
    ReviewQueueResponse,
    ReviewQueueItem,
)

router = APIRouter()


@router.get("/{child_id}", response_model=ProgressDashboardResponse)
async def progress_dashboard(
    child_id: UUID,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(child_id, request, current_user)
    db = request.state.db
    result = await db.execute(select(MasteryRecord).where(MasteryRecord.child_id == child_id))
    records = result.scalars().all()
    session_count = await db.execute(
        select(func.count()).select_from(LearningSession).where(LearningSession.child_id == child_id)
    )
    total_sessions = session_count.scalar() or 0
    interaction_count = await db.execute(
        select(func.count()).select_from(Interaction).where(Interaction.child_id == child_id)
    )
    total_interactions = interaction_count.scalar() or 0
    return ProgressDashboardResponse(
        child_id=child_id,
        mastery_records=[
            MasteryRecordResponse(
                mastery_id=r.mastery_id,
                child_id=r.child_id,
                topic=r.topic,
                mastery_level=r.mastery_level,
                stability=r.stability,
                difficulty=r.difficulty,
                last_reviewed=r.last_reviewed.isoformat() if r.last_reviewed else None,
                next_review_due=r.next_review_due.isoformat() if r.next_review_due else None,
                review_count=r.review_count or 0,
                updated_at=r.updated_at.isoformat() if r.updated_at else "",
            )
            for r in records
        ],
        total_sessions=total_sessions,
        total_interactions=total_interactions,
    )


@router.get("/{child_id}/mastery")
async def get_mastery(
    child_id: UUID,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(child_id, request, current_user)
    db = request.state.db
    result = await db.execute(select(MasteryRecord).where(MasteryRecord.child_id == child_id))
    records = result.scalars().all()
    return [
        MasteryRecordResponse(
            mastery_id=r.mastery_id,
            child_id=r.child_id,
            topic=r.topic,
            mastery_level=r.mastery_level,
            stability=r.stability,
            difficulty=r.difficulty,
            last_reviewed=r.last_reviewed.isoformat() if r.last_reviewed else None,
            next_review_due=r.next_review_due.isoformat() if r.next_review_due else None,
            review_count=r.review_count or 0,
            updated_at=r.updated_at.isoformat() if r.updated_at else "",
        )
        for r in records
    ]


@router.get("/{child_id}/timeline", response_model=TimelineResponse)
async def get_timeline(
    child_id: UUID,
    request: Request,
    days: int = Query(30, ge=1, le=365),
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(child_id, request, current_user)
    db = request.state.db
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = select(
        func.date_trunc("day", Interaction.ts).label("day"),
        func.count(Interaction.interaction_id).label("count"),
        func.avg(Interaction.engagement_score).label("avg_eng"),
    ).where(
        Interaction.child_id == child_id,
        Interaction.ts >= since,
    ).group_by(func.date_trunc("day", Interaction.ts))
    result = await db.execute(q)
    rows = result.fetchall()
    timeline = [
        TimelineDayPoint(
            date=row[0].isoformat()[:10] if row[0] else "",
            interactions=row[1] or 0,
            avg_engagement=float(row[2]) if row[2] is not None else None,
        )
        for row in rows
    ]
    return TimelineResponse(child_id=child_id, days=days, timeline=timeline)


@router.get("/{child_id}/report", response_model=ReportResponse)
async def get_report(
    child_id: UUID,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(child_id, request, current_user)
    db = request.state.db
    period = 30
    since = datetime.now(timezone.utc) - timedelta(days=period)
    session_count = await db.execute(
        select(func.count()).select_from(LearningSession).where(
            LearningSession.child_id == child_id,
            LearningSession.started_at >= since,
        )
    )
    total_sessions = session_count.scalar() or 0
    interaction_count = await db.execute(
        select(func.count()).select_from(Interaction).where(
            Interaction.child_id == child_id,
            Interaction.ts >= since,
        )
    )
    total_interactions = interaction_count.scalar() or 0
    result = await db.execute(select(MasteryRecord).where(MasteryRecord.child_id == child_id))
    records = result.scalars().all()
    mastery_summary = [
        {"topic": r.topic, "mastery_level": r.mastery_level, "review_count": r.review_count or 0}
        for r in records
    ]
    return ReportResponse(
        child_id=child_id,
        period_days=period,
        total_sessions=total_sessions,
        total_interactions=total_interactions,
        mastery_summary=mastery_summary,
        trend_data={"period_days": period},
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{child_id}/review-queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    child_id: UUID,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(child_id, request, current_user)
    db = request.state.db
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(MasteryRecord).where(
            MasteryRecord.child_id == child_id,
            MasteryRecord.next_review_due <= now,
        ).order_by(MasteryRecord.next_review_due.asc())
    )
    records = result.scalars().all()
    return ReviewQueueResponse(
        child_id=child_id,
        due_topics=[
            ReviewQueueItem(
                topic=r.topic,
                next_review_due=r.next_review_due.isoformat() if r.next_review_due else "",
                mastery_level=r.mastery_level,
                stability=r.stability,
            )
            for r in records
        ],
    )
