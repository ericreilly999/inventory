"""Database configuration and connection management."""

import os

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Import all models to ensure they're registered with SQLAlchemy
from shared.models import (  # noqa: F401
    ChildItem,
    ItemType,
    Location,
    LocationType,
    MoveHistory,
    ParentItem,
    Role,
    User,
)
from shared.models.base import Base

# Get database URL directly from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    (
        "postgresql://inventory_user:inventory_password@"
        "localhost:5432/inventory_management"
    ),
)

print(f"Using DATABASE_URL: {DATABASE_URL}")  # Debug print

# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    poolclass=QueuePool,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models

# Metadata for migrations
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

Base.metadata = metadata


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)
