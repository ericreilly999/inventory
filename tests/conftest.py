"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from shared.database.config import get_db
from shared.models.assignment_history import AssignmentHistory

# Import Base first
from shared.models.base import Base
from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory

# Force import all models at module level to ensure they are registered
# Import in dependency order to avoid foreign key issues
from shared.models.user import Role, User

# Create in-memory SQLite database for testing with a shared connection
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create a single engine and connection for all tests
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,  # Set to True for SQL debugging
)


# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create all tables once at module load
Base.metadata.create_all(bind=engine)

# Create a session factory
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session with savepoint rollback for each test."""
    # Create a new session for this test
    session = TestingSessionLocal()

    # Start a savepoint
    session.begin_nested()

    # Setup an event listener to recreate savepoint after each commit
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        # Clean up all data after test
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the get_db dependency for testing."""

    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    return _override_get_db
