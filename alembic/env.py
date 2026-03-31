# Alembic environment configuration (async)
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import asyncio
import os
import sys
from src.core.config import Settings

# Add src directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import Base metadata from core.database (contains all models)
from src.core.database import Base

# IMPORT ALL MODELS to ensure they are registered with Base.metadata
# (Alembic autogenerate only detects models that have been imported)
from src.modules.user.model import User
from src.modules.role.model import Role
from src.modules.auth.model import RefreshToken
from src.modules.audit.model import AuditLog

# All models should be imported here for autogenerate support
target_metadata = Base.metadata

config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url():
    """Get database URL from environment or config"""
    # Use DB_ADMIN_URL for migrations (has schema privileges)
    settings = Settings()
    return settings.DB_ADMIN_URL

def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """
    Run migrations in 'online' mode.
    """
    url = get_url()
    connectable = create_async_engine(url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
