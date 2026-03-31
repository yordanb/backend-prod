# Role repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .model import Role
from .schemas import RoleCreate, RoleUpdate
from typing import List, Optional

class RoleRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
        result = await db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Role]:
        result = await db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, role_data: RoleCreate) -> Role:
        db_role = Role(
            name=role_data.name,
            description=role_data.description
        )
        db.add(db_role)
        await db.commit()
        await db.refresh(db_role)
        return db_role

    @staticmethod
    async def update(db: AsyncSession, role_id: int, update_data: RoleUpdate) -> Optional[Role]:
        from sqlalchemy import update
        stmt = (
            update(Role)
            .where(Role.id == role_id)
            .values(**update_data.dict(exclude_unset=True))
        )
        await db.execute(stmt)
        await db.commit()
        return await RoleRepository.get_by_id(db, role_id)

    @staticmethod
    async def list(db: AsyncSession) -> List[Role]:
        result = await db.execute(select(Role))
        return result.scalars().all()
