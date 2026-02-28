"""POST /auth/register, /auth/login, /auth/refresh."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_caregiver_by_email,
    hash_password,
    verify_password,
)
from app.models import Caregiver
from fastapi import Request

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    request: Request,
):
    db: AsyncSession = request.state.db
    existing = await get_caregiver_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    caregiver = Caregiver(
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(caregiver)
    await db.flush()
    access = create_access_token(str(caregiver.caregiver_id))
    refresh = create_refresh_token(str(caregiver.caregiver_id))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
):
    db: AsyncSession = request.state.db
    caregiver = await get_caregiver_by_email(db, body.email)
    if not caregiver or not verify_password(body.password, caregiver.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access = create_access_token(str(caregiver.caregiver_id))
    refresh = create_refresh_token(str(caregiver.caregiver_id))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request):
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    token = auth_header.split(" ", 1)[1]
    payload = decode_refresh_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    db: AsyncSession = request.state.db
    from uuid import UUID
    from app.services.auth_service import get_caregiver_by_id
    caregiver = await get_caregiver_by_id(db, UUID(sub))
    if not caregiver:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access = create_access_token(sub)
    new_refresh = create_refresh_token(sub)
    return TokenResponse(access_token=access, refresh_token=new_refresh)
