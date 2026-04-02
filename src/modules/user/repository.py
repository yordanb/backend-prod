# User repository: database operations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from .model import User, Role
from .schemas import UserCreate, UserUpdate
from src.core.security import hash_password, verify_password
from typing import Optional, List
from datetime import datetime, timedelta

class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_nrp(db: AsyncSession, nrp: str) -> Optional[User]:
        result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.nrp == nrp)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        hashed_pw = hash_password(user_data.password)
        db_user = User(
            nama=user_data.nama,
            email=user_data.email,
            password=hashed_pw,
            role_id=user_data.role_id
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def update(db: AsyncSession, user_id: int, update_data: UserUpdate) -> Optional[User]:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data.dict(exclude_unset=True))
        )
        await db.execute(stmt)
        await db.commit()
        return await UserRepository.get_by_id(db, user_id)

    @staticmethod
    async def list(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(
            select(User).options(selectinload(User.role)).offset(skip).limit(limit)
        )
        return result.scalars().all()
