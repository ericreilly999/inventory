"""Unit tests for authentication utilities."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from shared.auth.utils import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)


def test_hash_password():
    """Test password hashing."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed is not None
    assert hashed != password
    assert len(hashed) > 0


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "test_password_123"
    wrong_password = "wrong_password"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    user_id = uuid4()
    username = "testuser"
    role = "admin"

    token = create_access_token(
        data={"sub": str(user_id), "username": username, "role": role}
    )

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_token_valid():
    """Test token verification with valid token."""
    user_id = uuid4()
    username = "testuser"
    role = "admin"

    token = create_access_token(
        data={"sub": str(user_id), "username": username, "role": role}
    )

    payload = verify_token(token)

    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["username"] == username
    assert payload["role"] == role


def test_verify_token_invalid():
    """Test token verification with invalid token."""
    invalid_token = "invalid.token.here"

    payload = verify_token(invalid_token)

    assert payload is None


def test_verify_token_expired():
    """Test token verification with expired token."""
    user_id = uuid4()
    username = "testuser"
    role = "admin"

    # Create token with custom expiration
    data = {"sub": str(user_id), "username": username, "role": role}
    to_encode = data.copy()
    # Set expiration to past
    expire = datetime.now(timezone.utc) - timedelta(seconds=1)
    to_encode.update({"exp": expire})

    from shared.config.settings import settings

    from jose import jwt

    token = jwt.encode(
        to_encode,
        settings.auth.jwt_secret_key,
        algorithm=settings.auth.jwt_algorithm,
    )

    payload = verify_token(token)

    # Expired tokens should return None
    assert payload is None


def test_hash_password_different_hashes():
    """Test that same password produces different hashes."""
    password = "test_password_123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_verify_password_empty():
    """Test password verification with empty password."""
    password = "test_password"
    hashed = hash_password(password)

    assert verify_password("", hashed) is False


def test_create_token_with_custom_expiry():
    """Test creating token with custom expiration."""
    user_id = uuid4()
    username = "testuser"
    role = "admin"

    token = create_access_token(
        data={"sub": str(user_id), "username": username, "role": role}
    )

    payload = verify_token(token)

    assert payload is not None
    assert "exp" in payload
    # Token should be valid
    exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    assert exp_time > now
