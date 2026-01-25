"""Tests for router dependencies and authentication."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from jose import jwt

from services.inventory.dependencies import (
    get_current_user as inventory_get_current_user,
)
from services.inventory.dependencies import (
    require_permission as inventory_require_permission,
)
from services.location.dependencies import get_current_user as location_get_current_user
from services.location.dependencies import (
    require_permission as location_require_permission,
)
from services.reporting.dependencies import (
    get_current_user as reporting_get_current_user,
)
from services.user.dependencies import get_current_user as user_get_current_user
from services.user.dependencies import require_permission as user_require_permission
from shared.auth.utils import create_access_token, hash_password, verify_password
from shared.config.settings import Settings
from shared.models.user import Role, User


@pytest.fixture
def test_user(test_db_session):
    """Create a test user with role."""
    role = Role(
        id=uuid4(),
        name="test_role",
        description="Test Role",
        permissions={"inventory": ["read", "write"], "location": ["read"]},
    )
    test_db_session.add(role)
    test_db_session.commit()

    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpass"),
        role_id=role.id,
        active=True,
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


def test_create_access_token():
    """Test JWT token creation."""
    data = {"sub": "user123", "username": "testuser"}
    token = create_access_token(data)
    assert token is not None
    assert isinstance(token, str)


def test_create_access_token_with_expiry():
    """Test JWT token creation with custom expiry."""
    data = {"sub": "user123"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta=expires_delta)
    assert token is not None


def test_hash_password():
    """Test password hashing."""
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > 0


def test_verify_password():
    """Test password verification."""
    password = "testpassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_verify_password_invalid():
    """Test password verification with invalid hash."""
    assert verify_password("password", "invalid_hash") is False


@pytest.mark.asyncio
async def test_inventory_get_current_user_valid(test_db_session, test_user):
    """Test getting current user with valid token."""
    token = create_access_token(
        {"sub": str(test_user.id), "username": test_user.username}
    )

    user = await inventory_get_current_user(token, test_db_session)
    assert user.id == test_user.id
    assert user.username == test_user.username


@pytest.mark.asyncio
async def test_inventory_get_current_user_invalid_token(test_db_session):
    """Test getting current user with invalid token."""
    with pytest.raises(HTTPException) as exc_info:
        await inventory_get_current_user("invalid_token", test_db_session)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_inventory_get_current_user_expired_token(test_db_session, test_user):
    """Test getting current user with expired token."""
    settings = Settings()
    expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
    token_data = {
        "sub": str(test_user.id),
        "username": test_user.username,
        "exp": expired_time,
    }
    token = jwt.encode(token_data, settings.JWT_SECRET_KEY, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        await inventory_get_current_user(token, test_db_session)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_inventory_get_current_user_nonexistent(test_db_session):
    """Test getting current user that doesn't exist."""
    fake_id = str(uuid4())
    token = create_access_token({"sub": fake_id, "username": "nonexistent"})

    with pytest.raises(HTTPException) as exc_info:
        await inventory_get_current_user(token, test_db_session)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_location_get_current_user_valid(test_db_session, test_user):
    """Test location service get current user."""
    token = create_access_token(
        {"sub": str(test_user.id), "username": test_user.username}
    )

    user = await location_get_current_user(token, test_db_session)
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_user_get_current_user_valid(test_db_session, test_user):
    """Test user service get current user."""
    token = create_access_token(
        {"sub": str(test_user.id), "username": test_user.username}
    )

    user = await user_get_current_user(token, test_db_session)
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_reporting_get_current_user_valid(test_db_session, test_user):
    """Test reporting service get current user."""
    token = create_access_token(
        {"sub": str(test_user.id), "username": test_user.username}
    )

    user = await reporting_get_current_user(token, test_db_session)
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_inventory_require_permission_valid(test_user):
    """Test permission check with valid permission."""
    # User has inventory:read permission
    checker = inventory_require_permission("inventory", "read")
    result = await checker(test_user)
    assert result is True


@pytest.mark.asyncio
async def test_inventory_require_permission_invalid(test_user):
    """Test permission check with invalid permission."""
    # User doesn't have inventory:admin permission
    checker = inventory_require_permission("inventory", "admin")
    with pytest.raises(HTTPException) as exc_info:
        await checker(test_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_location_require_permission_valid(test_user):
    """Test location permission check."""
    checker = location_require_permission("location", "read")
    result = await checker(test_user)
    assert result is True


@pytest.mark.asyncio
async def test_location_require_permission_invalid(test_user):
    """Test location permission check with invalid permission."""
    checker = location_require_permission("location", "write")
    with pytest.raises(HTTPException) as exc_info:
        await checker(test_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_user_require_permission_valid(test_user):
    """Test user permission check."""
    # Update user role to have user permissions
    test_user.role.permissions = {"user": ["read"]}
    checker = user_require_permission("user", "read")
    result = await checker(test_user)
    assert result is True


@pytest.mark.asyncio
async def test_user_require_permission_invalid(test_user):
    """Test user permission check with invalid permission."""
    checker = user_require_permission("user", "admin")
    with pytest.raises(HTTPException) as exc_info:
        await checker(test_user)
    assert exc_info.value.status_code == 403


def test_settings_loading():
    """Test settings configuration loading."""
    settings = Settings()
    assert settings.JWT_SECRET_KEY is not None
    assert settings.DATABASE_URL is not None
    assert settings.ENVIRONMENT in ["development", "test", "production"]


def test_settings_jwt_expiry():
    """Test JWT expiry settings."""
    settings = Settings()
    assert settings.JWT_EXPIRY_MINUTES > 0


def test_inactive_user_authentication(test_db_session):
    """Test authentication with inactive user."""
    role = Role(
        id=uuid4(),
        name="inactive_role",
        description="Inactive Role",
        permissions={},
    )
    test_db_session.add(role)

    inactive_user = User(
        id=uuid4(),
        username="inactive",
        email="inactive@example.com",
        password_hash=hash_password("password"),
        role_id=role.id,
        active=False,
    )
    test_db_session.add(inactive_user)
    test_db_session.commit()

    token = create_access_token(
        {"sub": str(inactive_user.id), "username": inactive_user.username}
    )

    # Should raise exception for inactive user
    with pytest.raises(HTTPException):
        import asyncio

        asyncio.run(inventory_get_current_user(token, test_db_session))
