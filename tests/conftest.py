"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
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


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine for the entire test session."""
    test_engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables once for the session
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # Drop all tables at the end of the session
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(engine):
    """Create a test database session with transaction rollback for each test."""
    # Create a connection
    connection = engine.connect()
    
    # Begin a transaction
    transaction = connection.begin()
    
    # Create session bound to the connection
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Rollback transaction to clean up test data
        transaction.rollback()
        # Close connection
        connection.close()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the get_db dependency for testing."""
    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    return _override_get_db