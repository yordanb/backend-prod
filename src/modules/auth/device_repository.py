# Device pairing repository: CRUD for device pairing
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from .model import DevicePairing
from typing import Optional, List

class DeviceRepository:
    @staticmethod
    async def get_by_android_id(db: AsyncSession, android_id: str) -> Optional[DevicePairing]:
        """Get device pairing record by Android ID."""
        result = await db.execute(
            select(DevicePairing).where(DevicePairing.android_id == android_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_id: int, android_id: str) -> DevicePairing:
        """Create or update device pairing record."""
        device = DevicePairing(
            android_id=android_id,
            user_id=user_id,
            last_used_at=None
        )
        db.add(device)
        await db.flush()
        return device

    @staticmethod
    async def update_last_used(db: AsyncSession, device: DevicePairing) -> None:
        """Update last_used_at timestamp."""
        device.last_used_at = datetime.utcnow()
        await db.flush()

    @staticmethod
    async def delete_by_android_id(db: AsyncSession, android_id: str) -> bool:
        """Remove device pairing."""
        result = await db.execute(
            select(DevicePairing).where(DevicePairing.android_id == android_id)
        )
        device = result.scalar_one_or_none()
        if device:
            await db.delete(device)
            await db.flush()
            return True
        return False
