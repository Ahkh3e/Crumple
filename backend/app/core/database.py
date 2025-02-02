from typing import AsyncGenerator
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from ..models.base import Base

# Get PostgreSQL URL from environment variable, fallback to localhost for development
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/crumple"
)

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    future=True,
    echo=True,  # Set to False in production
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,  # seconds
    pool_recycle=1800,  # 30 minutes
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def init_db() -> None:
    """Initialize database with all models"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Database utilities
async def get_or_create(session: AsyncSession, model, **kwargs):
    """Get an instance of a model or create it if it doesn't exist"""
    instance = await session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    
    instance = model(**kwargs)
    try:
        session.add(instance)
        await session.commit()
        return instance, True
    except Exception as e:
        await session.rollback()
        raise e

async def bulk_create_or_update(session: AsyncSession, model, objects: list, key_fields: list):
    """Bulk create or update objects based on key fields"""
    existing_objects = {}
    for obj in objects:
        key_values = tuple(obj.get(field) for field in key_fields)
        existing_objects[key_values] = obj
    
    # Update existing records
    for db_obj in await session.query(model).all():
        key_values = tuple(getattr(db_obj, field) for field in key_fields)
        if key_values in existing_objects:
            obj_data = existing_objects.pop(key_values)
            for key, value in obj_data.items():
                setattr(db_obj, key, value)
    
    # Create new records
    for obj_data in existing_objects.values():
        session.add(model(**obj_data))
    
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
