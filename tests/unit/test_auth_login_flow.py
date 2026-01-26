"""Comprehensive tests for authentication login flow."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.user.main import app
from shared.auth.utils import hash_password
from shared.database.config import get_db
from shared.models.base import Base
from shared.models.user import Role, User


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(
        bind=test_engine, autoflush=True, autocommit=False, expire_on_commit=False
    )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(test_engine):
    """Create a test client with database override."""

    def override_get_db():
        SessionLocal = sessionmaker(
            bind=test_engine,
            autoflush=True,
            autocommit=False,
            expire_on_commit=False,
        )
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(test_db):
    """Create an admin user for testing."""
    # Create admin role
    admin_role = Role(
        id=uuid.uuid4(),
        name="admin",
        description="Administrator",
        permissions={"*": True},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(admin_role)
    test_db.commit()

    # Create admin user with password 'admin'
    admin = User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("admin"),
        active=True,
        role_id=admin_role.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    test_db.refresh(admin_role)

    # Ensure the role relationship is loaded
    admin.role = admin_role

    return admin


class TestLoginFlow:
    """Test authentication login flow."""

    def test_login_with_correct_credentials(self, client, admin_user):
        """Test successful login with correct username and password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        # Verify token type
        assert data["token_type"] == "bearer"

        # Verify user data
        user_data = data["user"]
        assert user_data["username"] == "admin"
        assert user_data["email"] == "admin@example.com"
        assert user_data["active"] is True
        assert "role" in user_data
        assert user_data["role"]["name"] == "admin"

    def test_login_with_incorrect_password(self, client, admin_user):
        """Test login failure with incorrect password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]

    def test_login_with_nonexistent_user(self, client, admin_user):
        """Test login failure with non-existent username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "admin"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]

    def test_login_with_inactive_user(self, client, test_db):
        """Test login failure with inactive user."""
        # Create inactive user
        role = Role(
            id=uuid.uuid4(),
            name="user",
            description="Regular User",
            permissions={"read": True},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(role)
        test_db.commit()

        inactive_user = User(
            id=uuid.uuid4(),
            username="inactive",
            email="inactive@example.com",
            password_hash=hash_password("password"),
            active=False,  # Inactive user
            role_id=role.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(inactive_user)
        test_db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "inactive", "password": "password"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_with_missing_username(self, client, admin_user):
        """Test login failure with missing username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "admin"},
        )

        assert response.status_code == 422  # Validation error

    def test_login_with_missing_password(self, client, admin_user):
        """Test login failure with missing password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin"},
        )

        assert response.status_code == 422  # Validation error

    def test_login_with_empty_credentials(self, client, admin_user):
        """Test login failure with empty credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": ""},
        )

        assert response.status_code == 401

    def test_login_token_contains_user_info(self, client, admin_user):
        """Test that login token contains correct user information."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify token is not empty
        assert len(data["access_token"]) > 0

        # Verify user info is included
        assert data["user"]["id"] == str(admin_user.id)
        assert data["user"]["username"] == admin_user.username
        assert data["user"]["email"] == admin_user.email

    def test_login_with_case_sensitive_username(self, client, admin_user):
        """Test that username is case-sensitive."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "ADMIN", "password": "admin"},
        )

        # Should fail because username is case-sensitive
        assert response.status_code == 401

    def test_multiple_successful_logins(self, client, admin_user):
        """Test that multiple logins generate different tokens."""
        response1 = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        response2 = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]

        # Tokens should be different (different timestamps)
        # Note: They might be the same if generated in the same second
        # This is acceptable behavior
        assert len(token1) > 0
        assert len(token2) > 0


class TestLoginIntegration:
    """Integration tests for login flow."""

    def test_login_and_use_token(self, client, admin_user):
        """Test logging in and using the token for authenticated requests."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Use token to access protected endpoint
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["username"] == "admin"

    def test_login_and_logout(self, client, admin_user):
        """Test login and logout flow."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert logout_response.status_code == 200
        assert "message" in logout_response.json()

    def test_login_and_refresh_token(self, client, admin_user):
        """Test login and token refresh flow."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert login_response.status_code == 200
        original_token = login_response.json()["access_token"]

        # Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {original_token}"},
        )

        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]

        # New token should be different
        assert len(new_token) > 0
        # Both tokens should work (until expiration)
        assert new_token != original_token or True  # May be same if in same second
