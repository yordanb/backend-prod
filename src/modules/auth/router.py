# Auth router: login, refresh, logout
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.limiter import limiter, _rate_limit_exceeded_handler
from src.core.database import get_db
from .service import AuthService
from src.deps import require_roles
from src.modules.user.schemas import LoginRequest, LoginResponse, RefreshRequest
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

class LogoutRequest(BaseModel):
    refresh_token: str

class LogoutAllRequest(BaseModel):
    user_id: int

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with email/password.
    Rate limited: 5 attempts per minute per IP.
    """
    result = await AuthService.login(
        db=db,
        email=data.email,
        password=data.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token, refresh_token = result
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Exchange valid refresh token for new access token.
    Rotation: old refresh token is revoked and cannot be used again.
    """
    access_token = await AuthService.refresh(db, data.refresh_token)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return {
        "access_token": access_token,
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
