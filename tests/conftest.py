"""Test configuration and fixtures."""

import os

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models at module level to ensure they are registered
# Import in dependency order to avoid foreign key issues
from shared.models.assignment_history import AssignmentHistory  # noqa: F401

# Import Base first
from shared.models.base import Base
from shared.models.item import ChildItem, ItemType, ParentItem  # noqa: F401
from shared.models.location import Location, LocationType  # noqa: F401
from shared.models.move_history import MoveHistory  # noqa: F401
from shared.models.user import Role, User  # noqa: F401


@pytest.fixture(scope="function")
def test_db_session():
    """Provide a transactional database session for tests."""
    # Use PostgreSQL if DATABASE_URL is set (CI environment)
    # Otherwise use in-memory SQLite (local development)
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Use PostgreSQL from environment
        test_engine = create_engine(database_url, echo=False)
    else:
        # Use in-memory SQLite for local testing
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Enable foreign keys for SQLite
        @event.listens_for(test_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Ensure all models are imported and registered
    # Models are already imported at module level

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session with autoflush=False for better control
    SessionLocal = sessionmaker(bind=test_engine, autoflush=False)
    session = SessionLocal()

    # Start a transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Bind session to the transaction
    session = SessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        # Rollback the transaction to undo all changes
        transaction.rollback()
        connection.close()
        # For PostgreSQL, we don't drop tables between tests
        # They're cleaned by the rollback
        if not database_url:
            # For SQLite, drop tables
            Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the get_db dependency for testing."""

    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    return _override_get_db
