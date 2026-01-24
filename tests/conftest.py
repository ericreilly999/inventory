"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import Base first
from shared.models.base import Base

# Force import all models at module level to ensure they are registered
# Import in dependency order to avoid foreign key issues
from shared.models.user import Role, User  # noqa: F401
from shared.models.location import Location, LocationType  # noqa: F401
from shared.models.item import (  # noqa: F401
    ChildItem,
    ItemType,
    ParentItem,
)
from shared.models.move_history import MoveHistory  # noqa: F401
from shared.models.assignment_history import AssignmentHistory  # noqa: F401


@pytest.fixture(scope="function")
def test_db_session():
    """Provide a transactional database session for tests."""
    # Create in-memory database for this test
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
    # Import directly from modules to avoid circular imports
    from shared.models.user import Role, User  # noqa: F401
    from shared.models.location import Location, LocationType  # noqa: F401
    from shared.models.item import (  # noqa: F401
        ChildItem,
        ItemType,
        ParentItem,
    )
    from shared.models.move_history import MoveHistory  # noqa: F401
    from shared.models.assignment_history import (  # noqa: F401
        AssignmentHistory,
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables to ensure clean state
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
