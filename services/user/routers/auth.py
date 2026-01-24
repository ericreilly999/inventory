"""Authentication router for User Service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from shared.auth.utils import create_access_token, verify_password
from shared.config.settings import settings
from shared.database.config import get_db
from shared.logging.config import get_logger
from shared.models.user import User

from ..dependencies import get_current_user
from ..schemas import MessageResponse, TokenResponse, UserLogin, UserResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login")
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""

    # Find user by username with role relationship loaded
    from sqlalchemy.orm import joinedload

    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(
            User.username == user_credentials.username, User.active is True
        )
        .first()
    )

    if not user or not verify_password(
        user_credentials.password, user.password_hash
    ):
        logger.warning(
            "Failed login attempt", username=user_credentials.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    # Convert permissions array to dictionary format
    permissions_dict = {}
    if user.role and user.role.permissions:
        if isinstance(user.role.permissions, list):
            # Convert array format ["*", "user:read"] to dict format {"*": True, "user:read": True}
            for perm in user.role.permissions:
                permissions_dict[perm] = True
        elif isinstance(user.role.permissions, dict):
            # Already in dict format
            permissions_dict = user.role.permissions

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role_id": str(user.role_id),
        "permissions": permissions_dict,
    }

    access_token = create_access_token(token_data)

    logger.info(
        "User logged in successfully",
        user_id=str(user.id),
        username=user.username,
    )

    # Return simple response without complex nested objects
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.auth.jwt_expiration_hours * 3600,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "active": user.active,
            "role": {
                "id": str(user.role.id) if user.role else None,
                "name": user.role.name if user.role else None,
                "permissions": user.role.permissions if user.role else [],
            },
        },
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user."""

    logger.info(
        "User logged out",
        user_id=str(current_user.id),
        username=current_user.username,
    )

    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""

    return UserResponse.from_orm(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token for current user."""

    # Create new access token
    # Convert permissions array to dictionary format
    permissions_dict = {}
    if current_user.role and current_user.role.permissions:
        if isinstance(current_user.role.permissions, list):
            # Convert array format ["*", "user:read"] to dict format {"*": True, "user:read": True}
            for perm in current_user.role.permissions:
                permissions_dict[perm] = True
        elif isinstance(current_user.role.permissions, dict):
            # Already in dict format
            permissions_dict = current_user.role.permissions

    token_data = {
        "sub": str(current_user.id),
        "username": current_user.username,
        "role_id": str(current_user.role_id),
        "permissions": permissions_dict,
    }

    access_token = create_access_token(token_data)

    logger.info(
        "Token refreshed",
        user_id=str(current_user.id),
        username=current_user.username,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.auth.jwt_expiration_hours * 3600,
        user=UserResponse.from_orm(current_user),
    )
