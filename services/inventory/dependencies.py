"""Dependencies for Inventory Service."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from shared.database.config import get_db
from shared.models.user import User
from shared.models.item import ParentItem, ChildItem, ItemType
from shared.models.location import Location
from shared.auth.utils import verify_token

# Security scheme
security = HTTPBearer()


class TokenData:
    """Token data class."""
    def __init__(self, user_id: UUID, username: str, role_id: UUID, permissions: dict):
        self.user_id = user_id
        self.username = username
        self.role_id = role_id
        self.permissions = permissions


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
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
        role_id=UUID(payload.get("role_id")) if payload.get("role_id") else None,
        permissions=payload.get("permissions", {})
    )


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from database."""
    user = db.query(User).filter(
        User.id == token_data.user_id,
        User.active == True
    ).first()
    
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
        token_data: TokenData = Depends(get_current_user_token)
    ) -> TokenData:
        """Check if user has required permission."""
        permissions = token_data.permissions or {}
        
        if not permissions.get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return token_data
    
    return check_permission


# Common permission dependencies
require_inventory_read = require_permission("inventory:read")
require_inventory_write = require_permission("inventory:write")
require_inventory_admin = require_permission("inventory:admin")


async def get_parent_item_or_404(
    item_id: UUID,
    db: Session = Depends(get_db)
) -> ParentItem:
    """Get parent item by ID or raise 404."""
    item = db.query(ParentItem).filter(ParentItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent item not found"
        )
    return item


async def get_child_item_or_404(
    item_id: UUID,
    db: Session = Depends(get_db)
) -> ChildItem:
    """Get child item by ID or raise 404."""
    item = db.query(ChildItem).filter(ChildItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child item not found"
        )
    return item


async def get_item_type_or_404(
    type_id: UUID,
    db: Session = Depends(get_db)
) -> ItemType:
    """Get item type by ID or raise 404."""
    item_type = db.query(ItemType).filter(ItemType.id == type_id).first()
    if not item_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item type not found"
        )
    return item_type


async def get_location_or_404(
    location_id: UUID,
    db: Session = Depends(get_db)
) -> Location:
    """Get location by ID or raise 404."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    return location


async def validate_item_type_category(
    item_type: ItemType,
    expected_category: str
) -> ItemType:
    """Validate that item type has expected category."""
    if item_type.category.value != expected_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item type must be of category '{expected_category}'"
        )
    return item_type