from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .model import RefreshToken

class RefreshTokenRepository:

    @staticmethod
    async def save(db: AsyncSession, token: RefreshToken):
        db.add(token)
        await db.commit()

    @staticmethod
    async def get_by_jti(db: AsyncSession, jti: str):
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke(db: AsyncSession, token: RefreshToken):
        token.revoked = True
        await db.commit()
