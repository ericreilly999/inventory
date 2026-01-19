"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import Base first
from shared.models.base import Base

# Force import all models at module level to ensure they are registered
# Import in dependency order to avoid foreign key issues
from shared.models.user import User, Role
from shared.models.location import Location, LocationType
from shared.models.item import ParentItem, ChildItem, ItemType, ItemCategory
from shared.models.move_history import MoveHistory
from shared.models.assignment_history import AssignmentHistory

from shared.database.config import get_db


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the get_db dependency for testing."""
    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    return _override_get_db