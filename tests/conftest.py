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
    """Provide an isolated database session for each test.
    
    Each test gets a fresh in-memory SQLite database to ensure complete isolation.
    This prevents test interference and state leakage between tests.
    """
    # Always use in-memory SQLite for test isolation
    # This ensures each test has a completely fresh database
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

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables and dispose engine for complete cleanup
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


@pytest.fixture
def test_user_with_auth(test_db_session):
    """Create a test user for auth tests.

    This fixture creates a user in the isolated test database.
    Since each test has its own database, we can safely commit.
    """
    from uuid import uuid4

    from shared.auth.utils import hash_password
    from shared.models.user import Role as RoleModel
    from shared.models.user import User as UserModel

    # Create role and user
    role = RoleModel(
        id=uuid4(),
        name=f"test_role_{uuid4().hex[:8]}",
        description="Test Role",
        permissions={"inventory": ["read", "write"], "location": ["read"]},
    )
    test_db_session.add(role)
    test_db_session.commit()

    user = UserModel(
        id=uuid4(),
        username=f"testuser_{uuid4().hex[:8]}",
        email=f"test_{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("testpass"),
        role_id=role.id,
        active=True,
    )
    test_db_session.add(user)
    test_db_session.commit()

    # Refresh to ensure relationships are loaded
    test_db_session.refresh(user)
    test_db_session.refresh(role)

    return user
