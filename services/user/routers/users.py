"""Users router for User Service."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from shared.auth.utils import hash_password, verify_password
from shared.database.config import get_db
from shared.logging.config import get_logger
from shared.models.user import Role, User

from ..dependencies import (
    get_current_user,
    require_user_admin,
    require_user_read,
    require_user_write,
)
from ..schemas import (
    MessageResponse,
    PasswordChange,
    UserCreate,
    UserResponse,
    UserUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    dependencies=[Depends(require_user_admin)],
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new user."""

    # Check if username or email already exists
    existing_user = (
        db.query(User)
        .filter(
            or_(
                User.username == user_data.username,
                User.email == user_data.email,
            )
        )
        .first()
    )

    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

    # Check if role exists
    role = db.query(Role).filter(Role.id == user_data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found"
        )

    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role_id=user_data.role_id,
        active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(
        "User created",
        user_id=str(user.id),
        username=user.username,
        created_by=str(current_user.id),
    )

    return UserResponse.from_orm(user)


@router.get(
    "/",
    response_model=List[UserResponse],
    dependencies=[Depends(require_user_read)],
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List users with optional filtering."""

    query = db.query(User)

    # Filter by active status
    if active_only:
        query = query.filter(User.active == True)

    # Search filter
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Apply pagination
    users = query.offset(skip).limit(limit).all()

    return [UserResponse.from_orm(user) for user in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_user_read)],
)
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Get user by ID."""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse.from_orm(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_user_write)],
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user information."""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check for username/email conflicts
    if user_data.username and user_data.username != user.username:
        existing = (
            db.query(User)
            .filter(
                and_(User.username == user_data.username, User.id != user_id)
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
        user.username = user_data.username

    if user_data.email and user_data.email != user.email:
        existing = (
            db.query(User)
            .filter(and_(User.email == user_data.email, User.id != user_id))
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )
        user.email = user_data.email

    # Update role if provided
    if user_data.role_id and user_data.role_id != user.role_id:
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role not found",
            )
        user.role_id = user_data.role_id

    # Update active status
    if user_data.active is not None:
        user.active = user_data.active

    db.commit()
    db.refresh(user)

    logger.info(
        "User updated", user_id=str(user.id), updated_by=str(current_user.id)
    )

    return UserResponse.from_orm(user)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_user_admin)],
)
async def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate user (soft delete)."""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent self-deactivation
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    user.active = False
    db.commit()

    logger.info(
        "User deactivated",
        user_id=str(user.id),
        deactivated_by=str(current_user.id),
    )

    return MessageResponse(message="User deactivated successfully")


@router.post("/{user_id}/change-password", response_model=MessageResponse)
async def change_user_password(
    user_id: UUID,
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change user password."""

    # Users can only change their own password unless they're admin
    if user_id != current_user.id:
        # Check if current user has admin permission
        if not current_user.role.permissions.get("user:admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only change your own password",
            )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify current password (only for self-change)
    if user_id == current_user.id:
        if not verify_password(
            password_data.current_password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

    # Update password
    user.password_hash = hash_password(password_data.new_password)
    db.commit()

    logger.info(
        "Password changed",
        user_id=str(user.id),
        changed_by=str(current_user.id),
    )

    return MessageResponse(message="Password changed successfully")
