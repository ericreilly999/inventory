"""Dependencies for User Service."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from shared.auth.utils import verify_token
from shared.database.config import get_db
from shared.models.user import User

from .schemas import TokenData

# Security scheme
security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenData(
        user_id=UUID(user_id),
        username=payload.get("username"),
        role_id=(
            UUID(payload.get("role_id")) if payload.get("role_id") else None
        ),
        permissions=payload.get("permissions", {}),
    )


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: Session = Depends(get_db),
) -> User:
    """Get current user from database."""
    user = (
        db.query(User)
        .filter(User.id == token_data.user_id, User.active is True)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_permission(permission: str):
    """Dependency factory for permission-based access control."""

    def check_permission(
        token_data: TokenData = Depends(get_current_user_token),
    ) -> TokenData:
        """Check if user has required permission."""
        permissions = token_data.permissions or {}

        # Check for wildcard permission (admin access)
        if permissions.get("*", False):
            return token_data

        # Check for specific permission
        if not permissions.get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )

        return token_data

    return check_permission


def require_role(role_name: str):
    """Dependency factory for role-based access control."""

    def check_role(current_user: User = Depends(get_current_user)) -> User:
        """Check if user has required role."""
        if current_user.role.name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required",
            )

        return current_user

    return check_role


# Common permission dependencies
require_user_read = require_permission("user:read")
require_user_write = require_permission("user:write")
require_user_admin = require_permission("user:admin")
require_role_admin = require_permission("role:admin")


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None."""
    if credentials is None:
        return None

    try:
        token_data = await get_current_user_token(credentials)
        return await get_current_user(token_data, db)
    except HTTPException:
        return None
