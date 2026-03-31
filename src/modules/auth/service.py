# Auth service: login, refresh, token management
from sqlalchemy.ext.asyncio import AsyncSession
#from .repository import UserRepository, RefreshTokenRepository, AuditLogRepository
from src.modules.user.repository import UserRepository
from src.modules.auth.repository import RefreshTokenRepository
from src.modules.audit.repository import AuditLogRepository
from .schemas import LoginRequest
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
from src.core.redis import redis_client
from datetime import datetime, timedelta
from typing import Optional, Tuple
import json

class AuthService:
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        """
        Authenticate user and return access + refresh tokens.
        Returns None if credentials invalid.
        """
        user = await UserRepository.get_by_email(db, email)
        if not user or not user.is_active:
            return None

        if not verify_password(password, user.password):
            # Log failed attempt
            await AuditLogRepository.create(
                db=db,
                user_id=user.id,
                action="login.failed",
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps({"email": email})
            )
            return None

        # Generate tokens
        access_token = create_access_token(user.id, user.role.name)
        refresh_token, jti = create_refresh_token(user.id)

        # Hash and store refresh token in DB
        token_hash = hash_password(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS)
        await RefreshTokenRepository.create_token(
            db=db,
            user_id=user.id,
            jti=jti,
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Log successful login
        await AuditLogRepository.create(
            db=db,
            user_id=user.id,
            action="login.success",
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps({"email": email})
        )

        return access_token, refresh_token

    @staticmethod
    async def refresh(
        db: AsyncSession,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> Optional[str]:
        """
        Validate refresh token and issue new access token.
        Implements rotation: old refresh token is immediately blacklisted.
        """
        try:
            from src.core.security import decode_token
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            user_id = payload.get("sub")
        except ValueError:
            return None

        # Check if token exists and not revoked in DB
        stored_token = await RefreshTokenRepository.get_by_jti(db, jti)
        if not stored_token or stored_token.revoked:
            return None

        # Verify token hash (defense against DB tampering)
        if not verify_password(refresh_token, stored_token.token_hash):
            return None

        # Revoke old token
        await RefreshTokenRepository.revoke_token(db, jti)

        # Blacklist JTI in Redis (additional fast check)
        await redis_client.setex(f"blacklist:{jti}", 3600, "1")

        # Create new access token
        user = await UserRepository.get_by_id(db, int(user_id))
        if not user or not user.is_active:
            return None

        access_token = create_access_token(user.id, user.role.name)

        # Log token refresh
        await AuditLogRepository.create(
            db=db,
            user_id=user.id,
            action="token.refresh",
            ip_address=ip_address,
            details=json.dumps({"jti": jti})
        )

        return access_token

    @staticmethod
    async def revoke_refresh_token(
        db: AsyncSession,
        refresh_token: str,
        user_id: int
    ) -> bool:
        """
        Revoke a specific refresh token (logout from device).
        """
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
        except ValueError:
            return False

        success = await RefreshTokenRepository.revoke_token(db, jti)
        if success:
            await redis_client.setex(f"blacklist:{jti}", 3600, "1")
            await AuditLogRepository.create(
                db=db,
                user_id=user_id,
                action="token.revoke",
                details=json.dumps({"jti": jti})
            )
        return success

    @staticmethod
    async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> int:
        """
        Revoke all refresh tokens for a user (force logout everywhere).
        Returns count of revoked tokens.
        """
        count = await RefreshTokenRepository.revoke_all_user_tokens(db, user_id)
        await AuditLogRepository.create(
            db=db,
            user_id=user_id,
            action="tokens.revoke_all",
            details=json.dumps({"count": count})
        )
        return count
