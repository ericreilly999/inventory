"""Authentication utilities."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from shared.config.settings import settings
from shared.logging.config import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    try:
        # Ensure password is a string and not too long
        password_str = str(password)
        if len(password_str.encode("utf-8")) > 72:
            password_str = password_str[:72]

        # Try to use bcrypt with explicit configuration to avoid version detection issues
        from passlib.handlers.bcrypt import bcrypt

        return bcrypt.using(rounds=12).hash(password_str)
    except Exception as e:
        logger.error(f"Bcrypt hashing failed: {e}, falling back to SHA256")
        # Fallback to SHA256 with salt for now
        salt = "inventory_salt_2025"
        return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        # Try bcrypt first
        if len(plain_password.encode("utf-8")) > 72:
            plain_password = plain_password[:72]

        # Try to verify with bcrypt directly to avoid version detection
        from passlib.handlers.bcrypt import bcrypt

        if (
            hashed_password.startswith("$2b$")
            or hashed_password.startswith("$2a$")
            or hashed_password.startswith("$2y$")
        ):
            return bcrypt.verify(plain_password, hashed_password)
        else:
            # Try the context method as fallback
            return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(
            f"Bcrypt verification failed: {e}, trying SHA256 fallback"
        )
        # Fallback to SHA256 verification
        salt = "inventory_salt_2025"
        expected_hash = hashlib.sha256(
            (plain_password + salt).encode()
        ).hexdigest()
        return expected_hash == hashed_password


def create_access_token(data: Dict[str, Any]) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.auth.jwt_expiration_hours
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.auth.jwt_secret_key,
        algorithm=settings.auth.jwt_algorithm,
    )

    logger.info("Access token created", user_id=data.get("sub"))
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.auth.jwt_secret_key,
            algorithms=[settings.auth.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        return None


def extract_user_id(token: str) -> Optional[str]:
    """Extract user ID from JWT token."""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None
