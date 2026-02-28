"""POST /learn/ask, /learn/signal, /learn/feedback."""

from uuid import UUID

from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy import select

from app.dependencies import get_current_user_required, get_child
from app.models import Caregiver, MasteryRecord, Interaction
from app.schemas.learn import (
    AskRequest,
    AskResponse,
    SignalRequest,
    SignalResponse,
    StateSnapshot,
    FeedbackRequest,
    FeedbackResponse,
    UsageResponse,
)
from app.usage import get_usage
from app.services.rag import RAGPipeline
from app.services.signals import SignalProcessor, StateService
from app.services.fsrs import FSRSService
from app.constants import LEARN_ASK_RATE_LIMIT_PER_MINUTE
from app.redis_client import get_redis

router = APIRouter()
rag = RAGPipeline()
fsrs = FSRSService()


@router.get("/usage", response_model=UsageResponse)
async def learn_usage(
    current_user: Caregiver = Depends(get_current_user_required),
):
    """Return today's LLM and embedding usage vs configured daily limits (for UI)."""
    data = await get_usage()
    return UsageResponse(**data)


@router.post("/ask", response_model=AskResponse)
async def learn_ask(
    body: AskRequest,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(body.child_id, request, current_user)
    redis = get_redis()
    if redis:
        try:
            key = f"rate:ask:{body.child_id}"
            n = await redis.incr(key)
            if n == 1:
                await redis.expire(key, 60)
            if n > LEARN_ASK_RATE_LIMIT_PER_MINUTE:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        except HTTPException:
            raise
        except Exception:
            pass
    db = request.state.db
    try:
        interaction_id, response_text, ui_directives, session_constraints, chunks_used, response_time_ms = await rag.ask(
            db, body.child_id, body.session_id, body.input_text, body.input_type
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return AskResponse(
        interaction_id=interaction_id,
        response_text=response_text,
        ui_directives=ui_directives,
        session_constraints=session_constraints,
        chunks_used=chunks_used,
        response_time_ms=response_time_ms,
    )


@router.post("/signal", response_model=SignalResponse)
async def learn_signal(
    body: SignalRequest,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(body.child_id, request, current_user)
    db = request.state.db
    state_svc = StateService()
    await state_svc.ingest_signal(
        db, body.child_id, body.session_id, body.signal_type, body.value, body.raw_payload
    )
    from app.models import BehavioralSignal, AdaptiveState
    result = await db.execute(
        select(BehavioralSignal)
        .where(BehavioralSignal.session_id == body.session_id)
        .where(BehavioralSignal.child_id == body.child_id)
    )
    signals = [
        {"signal_type": s.signal_type, "value": s.value}
        for s in result.scalars().all()
    ]
    state = await state_svc.update(db, body.child_id, body.session_id, signals)
    return SignalResponse(
        state=StateSnapshot(
            cognitive_load=state.cognitive_load,
            mood_score=state.mood_score,
            readiness_score=state.readiness_score,
        )
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def learn_feedback(
    body: FeedbackRequest,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(body.child_id, request, current_user)
    db = request.state.db
    result = await db.execute(
        select(MasteryRecord).where(
            MasteryRecord.child_id == body.child_id,
            MasteryRecord.topic == body.topic,
        )
    )
    record = result.scalar_one_or_none()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if record and record.last_reviewed:
        res = fsrs.review(
            record.stability,
            record.difficulty,
            record.last_reviewed,
            body.rating,
        )
        record.stability = res.stability
        record.difficulty = res.difficulty
        record.last_reviewed = now
        record.next_review_due = res.next_review
        record.review_count = (record.review_count or 0) + 1
        mastery_level = min(1.0, record.mastery_level + 0.1 * body.rating)
        record.mastery_level = mastery_level
        next_days = (res.next_review - now).total_seconds() / 86400
    else:
        res = fsrs.initial_review(body.rating)
        if record:
            record.stability = res.stability
            record.difficulty = res.difficulty
            record.last_reviewed = now
            record.next_review_due = res.next_review
            record.review_count = (record.review_count or 0) + 1
            record.mastery_level = min(1.0, 0.2 * body.rating)
        else:
            record = MasteryRecord(
                child_id=body.child_id,
                topic=body.topic,
                stability=res.stability,
                difficulty=res.difficulty,
                last_reviewed=now,
                next_review_due=res.next_review,
                review_count=1,
                mastery_level=min(1.0, 0.2 * body.rating),
            )
            db.add(record)
        next_days = (res.next_review - now).total_seconds() / 86400

    # Persist engagement feedback onto the interaction for analytics / timeline
    interaction = await db.get(Interaction, body.interaction_id)
    if interaction is not None:
        interaction.engagement_score = body.engagement_score
        interaction.child_reaction = body.child_reaction

    await db.flush()
    from app.redis_client import get_redis
    r = get_redis()
    if r:
        try:
            await r.delete(f"mastery:weak:{body.child_id}")
        except Exception:
            pass
    return FeedbackResponse(
        topic=body.topic,
        mastery_level=record.mastery_level,
        next_review_days=round(next_days, 1),
    )
