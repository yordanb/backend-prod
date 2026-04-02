# Auth router: login, refresh, logout
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.limiter import limiter, _rate_limit_exceeded_handler
from src.core.database import get_db
from .service import AuthService
from .device_repository import DeviceRepository
from src.deps import require_roles
from src.modules.user.repository import UserRepository
from src.modules.user.schemas import LoginRequest, LoginResponse, RefreshRequest, UserResponse
from src.core.security import create_access_token, create_refresh_token, hash_password
from src.modules.auth.repository import RefreshTokenRepository
from src.modules.audit.repository import AuditLogRepository
from datetime import datetime, timedelta
import json
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

class LogoutRequest(BaseModel):
    refresh_token: str

class LogoutAllRequest(BaseModel):
    user_id: int

class AndroidIDCheckRequest(BaseModel):
    androidID: str

@router.post("/id-cek")
async def check_android_id(
    data: AndroidIDCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate device using Android ID (device-based auth).
    If Android ID is registered, returns user's access + refresh tokens.
    """
    device = await DeviceRepository.get_by_android_id(db, data.androidID)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered"
        )

    # Get user
    user = await UserRepository.get_by_id(db, device.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive"
        )

    # Generate new tokens
    access_token = create_access_token(user.id, user.role.name)
    refresh_token, jti = create_refresh_token(user.id)

    # Store refresh token
    token_hash = hash_password(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS)
    await RefreshTokenRepository.create_token(
        db=db,
        user_id=user.id,
        jti=jti,
        token_hash=token_hash,
        expires_at=expires_at
    )

    # Update device last_used
    await DeviceRepository.update_last_used(db, device)

    # Audit log
    await AuditLogRepository.create(
        db=db,
        user_id=user.id,
        action="device.auth",
        ip_address=None,
        details=json.dumps({"android_id": data.androidID})
    )

    # Serialize user for response (excluding sensitive fields like password)
    user_response = UserResponse.from_orm(user)

    return {
        "status": "already_registered",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_response
    }

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with identifier (email or nrp) and password.
    Optionally accepts androidId for device pairing.
    Rate limited: 5 attempts per minute per IP.
    """
    result = await AuthService.login(
        db=db,
        identifier=data.identifier,
        password=data.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        android_id=data.androidId
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token, refresh_token, user = result
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user  # automatically serialized via UserResponse
    }

@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Exchange valid refresh token for new access token and new refresh token.
    Rotation: old refresh token is revoked and cannot be used again.
    Returns both tokens to maintain persistent login session.
    """
    result = await AuthService.refresh(db, data.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    access_token, refresh_token = result
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin", "user"]))
):
    """
    Revoke a single refresh token (logout from specific device).
    """
    success = await AuthService.revoke_refresh_token(
        db=db,
        refresh_token=data.refresh_token,
        user_id=user["user_id"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )
    return {"message": "Logged out successfully"}

@router.post("/logout-all")
async def logout_all(
    data: LogoutAllRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    Revoke all refresh tokens for a user (admin only).
    Useful for forcing logout across all devices.
    """
    # Admin can revoke all tokens for any user, or only self?
    # For now, allow admin to revoke any user
    count = await AuthService.revoke_all_user_tokens(db, data.user_id)
    return {
        "message": f"Revoked {count} refresh tokens",
        "user_id": data.user_id
    }
