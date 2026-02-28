"""POST /sessions/start, POST /sessions/{id}/end, GET /sessions/{id}."""

from uuid import UUID

from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy import select

from app.dependencies import get_current_user_required, get_child
from app.models import Caregiver, LearningSession
from app.schemas.session import (
    SessionStartRequest,
    SessionStartResponse,
    SessionEndResponse,
    SessionStatusResponse,
)
from app.services.accessibility import AccessibilityEngine
from app.redis_client import get_redis
from app.constants import CACHE_SESSION_ACTIVE_TTL

router = APIRouter()


@router.post("/start", response_model=SessionStartResponse)
async def start_session(
    body: SessionStartRequest,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    child = await get_child(body.child_id, request, current_user)
    db = request.state.db
    session = LearningSession(child_id=body.child_id)
    db.add(session)
    await db.flush()
    engine = AccessibilityEngine()
    from app.models import NeuroProfile, ChildDisability
    np_result = await db.execute(select(NeuroProfile).where(NeuroProfile.child_id == body.child_id))
    neuro = np_result.scalar_one_or_none()
    d_result = await db.execute(select(ChildDisability).where(ChildDisability.child_id == body.child_id))
    disabilities = list(d_result.scalars().all())
    rules = await engine.derive(child, neuro, disabilities)
    redis = get_redis()
    if redis:
        try:
            await redis.set(f"session:{session.session_id}:active", "1", ex=CACHE_SESSION_ACTIVE_TTL)
        except Exception:
            pass
    return SessionStartResponse(
        session_id=session.session_id,
        ui_directives=rules.ui_directives,
        session_constraints=rules.session_constraints,
    )


@router.post("/{session_id}/end", response_model=SessionEndResponse)
async def end_session(
    session_id: UUID,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    db = request.state.db
    result = await db.execute(
        select(LearningSession).where(LearningSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await get_child(session.child_id, request, current_user)
    from datetime import datetime, timezone
    session.ended_at = datetime.now(timezone.utc)
    await db.flush()
    redis = get_redis()
    if redis:
        try:
            await redis.delete(f"session:{session_id}:active")
        except Exception:
            pass
    return SessionEndResponse(
        session_id=session.session_id,
        total_interactions=session.total_interactions or 0,
        avg_response_time_ms=session.avg_response_time_ms,
        frustration_events=session.frustration_events or 0,
        hyperfocus_flag=session.hyperfocus_flag or False,
        session_quality=session.session_quality,
        topics_covered=session.topics_covered,
    )


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session(
    session_id: UUID,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    db = request.state.db
    result = await db.execute(
        select(LearningSession).where(LearningSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await get_child(session.child_id, request, current_user)
    return SessionStatusResponse(
        session_id=session.session_id,
        child_id=session.child_id,
        started_at=session.started_at.isoformat() if session.started_at else "",
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        total_interactions=session.total_interactions or 0,
        avg_response_time_ms=session.avg_response_time_ms,
        frustration_events=session.frustration_events or 0,
        hyperfocus_flag=session.hyperfocus_flag or False,
        session_quality=session.session_quality,
        topics_covered=session.topics_covered,
    )
