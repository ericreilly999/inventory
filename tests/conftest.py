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

        # Create all tables once
        Base.metadata.create_all(bind=test_engine)

        # Create a connection for this test
        connection = test_engine.connect()

        # Begin a transaction
        transaction = connection.begin()

        # Create session bound to the transaction
        SessionLocal = sessionmaker(bind=connection)
        session = SessionLocal()

        # Override commit to use flush instead - prevents actual commits
        # This ensures transaction rollback will undo all changes
        session.commit = session.flush
        session.rollback = lambda: None  # Prevent rollback errors in tests

        try:
            yield session
        finally:
            session.close()
            # Rollback the transaction to undo all changes
            transaction.rollback()
            connection.close()
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

        # Create all tables
        Base.metadata.create_all(bind=test_engine)

        # Create session with autoflush=False for better control
        SessionLocal = sessionmaker(bind=test_engine, autoflush=False)

        # Start a transaction
        connection = test_engine.connect()
        transaction = connection.begin()

        # Bind session to the transaction
        session = SessionLocal(bind=connection)

        # Override commit for SQLite too
        session.commit = session.flush
        session.rollback = lambda: None

        try:
            yield session
        finally:
            session.close()
            # Rollback the transaction to undo all changes
            transaction.rollback()
            connection.close()
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


@pytest.fixture
def test_user_for_auth(test_db_session):
    """Create a test user with actual commit for auth tests.

    This fixture is specifically for tests that need to query the user
    from the database (like get_current_user tests). It temporarily
    restores the real commit function to ensure data is visible.
    """
    from uuid import uuid4

    from shared.auth.utils import hash_password
    from shared.models.user import Role as RoleModel
    from shared.models.user import User as UserModel

    # Save the original commit function
    original_commit = test_db_session.commit

    # Temporarily restore real commit behavior
    def real_commit():
        test_db_session.flush()
        test_db_session.expire_all()

    test_db_session.commit = real_commit

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

    # Restore the flush-based commit
    test_db_session.commit = original_commit

    # Refresh to ensure relationships are loaded
    test_db_session.refresh(user)
    test_db_session.refresh(role)

    return user
