# Refresh token repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from .model import RefreshToken
from datetime import datetime, timedelta
from typing import Optional

class RefreshTokenRepository:

    @staticmethod
    async def create_token(
        db: AsyncSession,
        user_id: int,
        jti: str,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """Create a new refresh token record"""
        db_token = RefreshToken(
            user_id=user_id,
            jti=jti,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(db_token)
        await db.commit()
        await db.refresh(db_token)
        return db_token

    @staticmethod
    async def get_by_jti(db: AsyncSession, jti: str) -> Optional[RefreshToken]:
        """Get refresh token by JTI"""
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_token(db: AsyncSession, jti: str) -> bool:
        """Revoke a specific refresh token by JTI"""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(revoked=True)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> int:
        """Revoke all refresh tokens for a user"""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """Delete expired tokens (housekeeping)"""
        stmt = delete(RefreshToken).where(RefreshToken.expires_at < datetime.utcnow())
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
