"""Dependencies for Location Service."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from shared.auth.utils import verify_token
from shared.database.config import get_db
from shared.models.item import ParentItem
from shared.models.location import Location, LocationType
from shared.models.user import User

# Security scheme
security = HTTPBearer()


class TokenData:
    """Token data class."""

    def __init__(
        self,
        user_id: UUID,
        username: str,
        role_id: Optional[UUID] = None,
        permissions: Optional[dict] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.role_id = role_id
        self.permissions = permissions or {}


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
        role_id=(UUID(payload.get("role_id")) if payload.get("role_id") else None),
        permissions=payload.get("permissions", {}),
    )


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: Session = Depends(get_db),
) -> User:
    """Get current user from database."""
    user = (
        db.query(User)
        .filter(User.id == token_data.user_id, User.active.is_(True))
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
        from shared.logging.config import get_logger

        logger = get_logger(__name__)

        logger.info(
            f"Checking permission '{permission}' for user " f"{token_data.username}"
        )
        logger.info(f"User permissions: {token_data.permissions}")

        permissions = token_data.permissions or {}

        # Check for wildcard permission (admin access)
        if permissions.get("*", False):
            logger.info("User has wildcard permission")
            return token_data

        # Check for specific permission
        if not permissions.get(permission, False):
            logger.error(
                f"User {token_data.username} missing permission '{permission}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )

        logger.info(f"Permission check passed for '{permission}'")
        return token_data

    return check_permission


# Common permission dependencies
require_location_read = require_permission("location:read")
require_location_write = require_permission("location:write")
require_location_admin = require_permission("location:admin")


async def get_location_by_id(
    location_id: UUID, db: Session = Depends(get_db)
) -> Location:
    """Get location by ID or raise 404."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found",
        )
    return location


async def get_location_type_by_id(
    location_type_id: UUID, db: Session = Depends(get_db)
) -> LocationType:
    """Get location type by ID or raise 404."""
    location_type = (
        db.query(LocationType).filter(LocationType.id == location_type_id).first()
    )
    if not location_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location type with id {location_type_id} not found",
        )
    return location_type


async def get_parent_item_by_id(
    item_id: UUID, db: Session = Depends(get_db)
) -> ParentItem:
    """Get parent item by ID or raise 404."""
    item = db.query(ParentItem).filter(ParentItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent item with id {item_id} not found",
        )
    return item


def validate_location_deletion(location: Location, db: Session) -> None:
    """Validate that a location can be deleted (no items assigned)."""
    from shared.models.move_history import MoveHistory

    # Check if any parent items are currently at this location
    items_count = (
        db.query(ParentItem)
        .filter(ParentItem.current_location_id == location.id)
        .count()
    )

    if items_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete location '{location.name}' - {items_count} "
                f"item(s) are currently assigned to it. Move all items to another location first."
            ),
        )

    # Check if location is referenced in move history
    history_count = (
        db.query(MoveHistory)
        .filter(
            (MoveHistory.from_location_id == location.id)
            | (MoveHistory.to_location_id == location.id)
        )
        .count()
    )

    if history_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete location '{location.name}' - it is referenced in "
                f"{history_count} historical movement record(s). Locations with movement "
                f"history cannot be deleted to maintain audit trail integrity."
            ),
        )


def validate_location_type_deletion(location_type: LocationType, db: Session) -> None:
    """Validate that a location type can be deleted (no locations using it)."""
    from shared.models.move_history import MoveHistory

    # Check if any locations are using this location type
    locations_count = (
        db.query(Location).filter(Location.location_type_id == location_type.id).count()
    )

    if locations_count > 0:
        # Get the location names for better error message
        locations = (
            db.query(Location)
            .filter(Location.location_type_id == location_type.id)
            .limit(5)
            .all()
        )
        location_names = [loc.name for loc in locations]

        if locations_count > 5:
            location_list = (
                ", ".join(location_names) + f", and {locations_count - 5} more"
            )
        else:
            location_list = ", ".join(location_names)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete location type '{location_type.name}' - "
                f"{locations_count} location(s) are using it: {location_list}. "
                f"Delete or reassign these locations first."
            ),
        )
