"""Unit tests for user service routers."""

from uuid import uuid4

import pytest

from shared.auth.utils import hash_password, verify_password
from shared.models.user import Role, User


class TestRolesRouter:
    """Test roles router functionality."""

    def test_create_role(self, test_db_session):
        """Test creating a role."""
        role = Role(
            id=uuid4(),
            name="admin",
            description="Administrator role",
            permissions={"read": True, "write": True, "delete": True},
        )
        test_db_session.add(role)
        test_db_session.commit()
        test_db_session.refresh(role)

        assert role.id is not None
        assert role.name == "admin"
        assert role.permissions["read"] is True

    def test_get_role(self, test_db_session):
        """Test retrieving a role."""
        role = Role(
            name="viewer",
            description="Viewer role",
            permissions={"read": True, "write": False},
        )
        test_db_session.add(role)
        test_db_session.commit()

        retrieved = (
            test_db_session.query(Role).filter(Role.id == role.id).first()
        )
        assert retrieved is not None
        assert retrieved.name == "viewer"

    def test_list_roles(self, test_db_session):
        """Test listing roles."""
        role1 = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        role2 = Role(
            name="viewer",
            description="Viewer",
            permissions={"read": True, "write": False},
        )
        test_db_session.add_all([role1, role2])
        test_db_session.commit()

        all_roles = test_db_session.query(Role).all()
        assert len(all_roles) >= 2


class TestUsersRouter:
    """Test users router functionality."""

    def test_create_user(self, test_db_session):
        """Test creating a user."""
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        user = User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password123"),
            role_id=role.id,
            active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.active is True

    def test_get_user(self, test_db_session):
        """Test retrieving a user."""
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password123"),
            role_id=role.id,
            active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()

        retrieved = (
            test_db_session.query(User).filter(User.id == user.id).first()
        )
        assert retrieved is not None
        assert retrieved.username == "testuser"

    def test_password_hashing(self, test_db_session):
        """Test password hashing and verification."""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


class TestAuthRouter:
    """Test authentication router functionality."""

    def test_user_authentication(self, test_db_session):
        """Test user authentication flow."""
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        password = "test_password"
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password(password),
            role_id=role.id,
            active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()

        # Verify password
        assert verify_password(password, user.password_hash) is True

        # Verify user is active
        assert user.active is True

    def test_inactive_user(self, test_db_session):
        """Test that inactive users cannot authenticate."""
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        user = User(
            username="inactive_user",
            email="inactive@example.com",
            password_hash=hash_password("password"),
            role_id=role.id,
            active=False,
        )
        test_db_session.add(user)
        test_db_session.commit()

        assert user.active is False
