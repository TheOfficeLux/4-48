"""FastAPI Depends: get_current_user, get_child."""

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Caregiver, ChildProfile
from app.models.child import ChildProfile as ChildProfileModel

security = HTTPBearer(auto_error=False)


async def get_current_user_required(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Caregiver:
    """Require valid JWT; return caregiver or 401."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from app.services.auth_service import decode_access_token, get_caregiver_by_id

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db: AsyncSession = request.state.db
    caregiver = await get_caregiver_by_id(db, UUID(sub))
    if caregiver is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return caregiver


async def get_child(
    child_id: UUID,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
) -> ChildProfileModel:
    """Load child and verify caregiver owns this child."""
    db: AsyncSession = request.state.db
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.child_id == child_id,
            ChildProfile.caregiver_id == current_user.caregiver_id,
        )
    )
    child = result.scalar_one_or_none()
    if child is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied",
        )
    return child
