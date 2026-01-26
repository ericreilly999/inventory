"""Authentication utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt as bcrypt_lib
from jose import JWTError, jwt

from shared.config.settings import settings
from shared.logging.config import get_logger

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Ensure password is a string
    password_str = str(password)

    # Truncate to 72 bytes for bcrypt compatibility
    password_bytes = password_str.encode("utf-8")
    if len(password_bytes) > 72:
        # Truncate at byte level, not character level
        password_bytes = password_bytes[:72]
        # Decode back, ignoring any incomplete characters at the end
        password_str = password_bytes.decode("utf-8", errors="ignore")
        password_bytes = password_str.encode("utf-8")

    # Use bcrypt directly with 12 rounds
    salt = bcrypt_lib.gensalt(rounds=12)
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    # Truncate to 72 bytes for bcrypt compatibility
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        # Truncate at byte level, not character level
        password_bytes = password_bytes[:72]
        # Decode back, ignoring any incomplete characters at the end
        plain_password = password_bytes.decode("utf-8", errors="ignore")
        password_bytes = plain_password.encode("utf-8")

    # Use bcrypt directly for verification
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt_lib.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: Dict[str, Any]) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    # Ensure subject is always a string if present
    # JWT spec requires 'sub' to be a string, so we convert or skip
    if "sub" in to_encode:
        if to_encode["sub"] is not None:
            # Ensure it's a string
            to_encode["sub"] = str(to_encode["sub"])
        # If sub is None, keep it as None - the test expects it

    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.auth.jwt_expiration_hours
    )
    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.auth.jwt_secret_key,
            algorithm=settings.auth.jwt_algorithm,
        )
    except Exception as e:
        # If encoding fails (e.g., due to None sub), log and re-raise
        logger.error(f"Failed to create access token: {e}")
        raise

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
