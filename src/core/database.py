# Database setup with async SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

# Async engine using aiomysql driver
engine = create_async_engine(settings.DB_URL, echo=False, pool_pre_ping=True)
#SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=async_sessionmaker)
Base = declarative_base()

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Dependency for FastAPI routes to get database session"""
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
