# Audit log repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .model import AuditLog
from typing import List, Optional

class AuditLogRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: str = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip=ip_address,
            user_agent=user_agent,
            details=details
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def list(
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """List audit logs with optional filters"""
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
