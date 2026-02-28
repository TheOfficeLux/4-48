"""CRUD children + neuro profile + disabilities."""

from uuid import UUID

from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_required, get_child
from app.models import Caregiver, ChildProfile, ChildDisability, NeuroProfile
from app.schemas.child import (
    ChildCreate,
    ChildResponse,
    ChildFullResponse,
    NeuroprofileUpsertRequest,
    NeuroprofileResponse,
    DisabilityAddRequest,
    DisabilityResponse,
    DisabilityType,
)
from app.models.child import ChildProfile as ChildProfileModel

router = APIRouter()


@router.post("", response_model=ChildResponse)
async def register_child(
    body: ChildCreate,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    db: AsyncSession = request.state.db
    child = ChildProfile(
        caregiver_id=current_user.caregiver_id,
        full_name=body.full_name,
        date_of_birth=body.date_of_birth,
        primary_language=body.primary_language,
        grade_level=body.grade_level,
    )
    db.add(child)
    await db.flush()
    return ChildResponse(
        child_id=child.child_id,
        caregiver_id=child.caregiver_id,
        full_name=child.full_name,
        date_of_birth=child.date_of_birth,
        primary_language=child.primary_language,
        grade_level=child.grade_level,
        created_at=child.created_at.isoformat() if child.created_at else "",
    )


@router.get("", response_model=list[ChildResponse])
async def list_children(
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    db: AsyncSession = request.state.db
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.caregiver_id == current_user.caregiver_id)
    )
    children = result.scalars().all()
    return [
        ChildResponse(
            child_id=c.child_id,
            caregiver_id=c.caregiver_id,
            full_name=c.full_name,
            date_of_birth=c.date_of_birth,
            primary_language=c.primary_language,
            grade_level=c.grade_level,
            created_at=c.created_at.isoformat() if c.created_at else "",
        )
        for c in children
    ]


@router.get("/{child_id}", response_model=ChildFullResponse)
async def get_child_profile(
    child_id: UUID,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    child = await get_child(child_id, request, current_user)
    db: AsyncSession = request.state.db
    neuro = None
    result = await db.execute(select(NeuroProfile).where(NeuroProfile.child_id == child_id))
    np = result.scalar_one_or_none()
    if np:
        neuro = NeuroprofileResponse(
            profile_id=np.profile_id,
            child_id=np.child_id,
            diagnoses=np.diagnoses or [],
            attention_span_mins=np.attention_span_mins,
            preferred_modalities=np.preferred_modalities or [],
            communication_style=np.communication_style,
            sensory_thresholds=np.sensory_thresholds or {},
            ui_preferences=np.ui_preferences or {},
            hyperfocus_topics=np.hyperfocus_topics or [],
            frustration_threshold=np.frustration_threshold,
            updated_at=np.updated_at.isoformat() if np.updated_at else "",
        )
    result = await db.execute(select(ChildDisability).where(ChildDisability.child_id == child_id))
    disabilities = [
        DisabilityResponse(
            disability_id=d.disability_id,
            child_id=d.child_id,
            disability_type=d.disability_type,
            severity=d.severity,
            accommodations=d.accommodations or {},
            notes=d.notes,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in result.scalars().all()
    ]
    return ChildFullResponse(
        child=ChildResponse(
            child_id=child.child_id,
            caregiver_id=child.caregiver_id,
            full_name=child.full_name,
            date_of_birth=child.date_of_birth,
            primary_language=child.primary_language,
            grade_level=child.grade_level,
            created_at=child.created_at.isoformat() if child.created_at else "",
        ),
        neuro_profile=neuro,
        disabilities=disabilities,
    )


@router.put("/{child_id}/neuro", response_model=NeuroprofileResponse)
async def upsert_neuro(
    child_id: UUID,
    body: NeuroprofileUpsertRequest,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    child = await get_child(child_id, request, current_user)
    db: AsyncSession = request.state.db
    result = await db.execute(select(NeuroProfile).where(NeuroProfile.child_id == child_id))
    np = result.scalar_one_or_none()
    if np:
        np.diagnoses = [d.value for d in body.diagnoses]
        np.attention_span_mins = body.attention_span_mins
        np.preferred_modalities = body.preferred_modalities
        np.communication_style = body.communication_style
        np.sensory_thresholds = body.sensory_thresholds
        np.ui_preferences = body.ui_preferences
        np.hyperfocus_topics = body.hyperfocus_topics
        np.frustration_threshold = body.frustration_threshold
        await db.flush()
    else:
        np = NeuroProfile(
            child_id=child_id,
            diagnoses=[d.value for d in body.diagnoses],
            attention_span_mins=body.attention_span_mins,
            preferred_modalities=body.preferred_modalities,
            communication_style=body.communication_style,
            sensory_thresholds=body.sensory_thresholds,
            ui_preferences=body.ui_preferences,
            hyperfocus_topics=body.hyperfocus_topics,
            frustration_threshold=body.frustration_threshold,
        )
        db.add(np)
        await db.flush()
    # Invalidate adaptation cache
    try:
        from app.redis_client import get_redis
        r = get_redis()
        if r:
            await r.delete(f"adaptation:{child_id}")
    except Exception:
        pass
    return NeuroprofileResponse(
        profile_id=np.profile_id,
        child_id=np.child_id,
        diagnoses=np.diagnoses or [],
        attention_span_mins=np.attention_span_mins,
        preferred_modalities=np.preferred_modalities or [],
        communication_style=np.communication_style,
        sensory_thresholds=np.sensory_thresholds or {},
        ui_preferences=np.ui_preferences or {},
        hyperfocus_topics=np.hyperfocus_topics or [],
        frustration_threshold=np.frustration_threshold,
        updated_at=np.updated_at.isoformat() if np.updated_at else "",
    )


@router.post("/{child_id}/disabilities", response_model=DisabilityResponse)
async def add_disability(
    child_id: UUID,
    body: DisabilityAddRequest,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(child_id, request, current_user)
    db: AsyncSession = request.state.db
    result = await db.execute(
        select(ChildDisability).where(
            ChildDisability.child_id == child_id,
            ChildDisability.disability_type == body.disability_type.value,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disability type already added for this child",
        )
    d = ChildDisability(
        child_id=child_id,
        disability_type=body.disability_type.value,
        severity=body.severity,
        accommodations=body.accommodations,
        notes=body.notes,
    )
    db.add(d)
    await db.flush()
    try:
        from app.redis_client import get_redis
        r = get_redis()
        if r:
            await r.delete(f"adaptation:{child_id}")
    except Exception:
        pass
    return DisabilityResponse(
        disability_id=d.disability_id,
        child_id=d.child_id,
        disability_type=d.disability_type,
        severity=d.severity,
        accommodations=d.accommodations or {},
        notes=d.notes,
        created_at=d.created_at.isoformat() if d.created_at else "",
    )


@router.delete("/{child_id}/disabilities/{disability_type}")
async def delete_disability(
    child_id: UUID,
    disability_type: DisabilityType,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    await get_child(child_id, request, current_user)
    db: AsyncSession = request.state.db
    result = await db.execute(
        select(ChildDisability).where(
            ChildDisability.child_id == child_id,
            ChildDisability.disability_type == disability_type.value,
        )
    )
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disability not found")
    await db.delete(d)
    await db.flush()
    try:
        from app.redis_client import get_redis
        r = get_redis()
        if r:
            await r.delete(f"adaptation:{child_id}")
    except Exception:
        pass
    return {"ok": True}
