#!/usr/bin/env python3
"""
Seed initial data: create default roles (admin, user)
Run: python scripts/seed_roles.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.core.database import engine, Base
from src.modules.user.model import User  # Ensure User model is loaded
from src.modules.role.repository import RoleRepository
from src.modules.role.schemas import RoleCreate
from sqlalchemy.ext.asyncio import AsyncSession

async def seed():
    # Tables are created via Alembic migrations using admin DB user.
    # This seed only inserts initial data.
    async with engine.connect() as conn:
        async with AsyncSession(bind=conn) as session:
            # Check if roles exist
            admin = await RoleRepository.get_by_name(session, "admin")
            user = await RoleRepository.get_by_name(session, "user")

            if not admin:
                admin = await RoleRepository.create(
                    session,
                    RoleCreate(name="admin", description="Administrator with full access")
                )
                print("✅ Created role: admin")
            else:
                print("ℹ️  Role 'admin' already exists")

            if not user:
                user = await RoleRepository.create(
                    session,
                    RoleCreate(name="user", description="Regular user")
                )
                print("✅ Created role: user")
            else:
                print("ℹ️  Role 'user' already exists")

            await session.commit()
            print("✅ Seed completed!")

if __name__ == "__main__":
    asyncio.run(seed())
