from sqlalchemy.ext.asyncio import AsyncSession
from .model import AuditLog

class AuditLogRepository:

    @staticmethod
    async def log(db: AsyncSession, data: dict):
        log = AuditLog(**data)
        db.add(log)
        await db.commit()
