"""Item types router for Inventory Service."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from shared.database.config import get_db
from shared.logging.config import get_logger
from shared.models.item import ChildItem, ItemType, ParentItem

from ..dependencies import (
    get_current_user,
    get_item_type_or_404,
    require_inventory_admin,
    require_inventory_read,
    require_inventory_write,
)
from ..schemas import ItemTypeCreate, ItemTypeResponse, ItemTypeUpdate, MessageResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ItemTypeResponse,
    dependencies=[Depends(require_inventory_admin)],
)
async def create_item_type(
    item_type_data: ItemTypeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new item type."""

    # Check if name already exists
    existing_type = (
        db.query(ItemType).filter(ItemType.name == item_type_data.name).first()
    )
    if existing_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item type name already exists",
        )

    # Create new item type
    item_type = ItemType(
        name=item_type_data.name,
        description=item_type_data.description,
        category=item_type_data.category,
    )

    db.add(item_type)
    db.commit()
    db.refresh(item_type)

    logger.info(
        "Item type created",
        item_type_id=str(item_type.id),
        name=item_type.name,
        category=item_type.category.value,
        created_by=str(current_user.id),
    )

    return ItemTypeResponse.from_orm(item_type)


@router.get(
    "/",
    response_model=List[ItemTypeResponse],
    dependencies=[Depends(require_inventory_read)],
)
async def list_item_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(
        None, description="Filter by category: 'parent' or 'child'"
    ),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List item types with optional filtering by category."""

    query = db.query(ItemType)

    # Filter by category
    if category:
        query = query.filter(ItemType.category == category)

    # Search filter
    if search:
        search_filter = or_(
            ItemType.name.ilike(f"%{search}%"),
            ItemType.description.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    # Apply pagination
    item_types = query.offset(skip).limit(limit).all()

    return [ItemTypeResponse.from_orm(item_type) for item_type in item_types]


@router.get(
    "/{type_id}",
    response_model=ItemTypeResponse,
    dependencies=[Depends(require_inventory_read)],
)
async def get_item_type(item_type: ItemType = Depends(get_item_type_or_404)):
    """Get item type by ID."""
    return ItemTypeResponse.from_orm(item_type)


@router.put(
    "/{type_id}",
    response_model=ItemTypeResponse,
    dependencies=[Depends(require_inventory_write)],
)
async def update_item_type(
    type_id: UUID,
    item_type_data: ItemTypeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    item_type: ItemType = Depends(get_item_type_or_404),
):
    """Update item type information."""

    # Check for name conflicts
    if item_type_data.name and item_type_data.name != item_type.name:
        existing = (
            db.query(ItemType)
            .filter(ItemType.name == item_type_data.name, ItemType.id != type_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item type name already exists",
            )
        item_type.name = item_type_data.name

    # Update other fields
    if item_type_data.description is not None:
        item_type.description = item_type_data.description

    if item_type_data.category is not None:
        item_type.category = item_type_data.category

    db.commit()
    db.refresh(item_type)

    logger.info(
        "Item type updated",
        item_type_id=str(item_type.id),
        updated_by=str(current_user.id),
    )

    return ItemTypeResponse.from_orm(item_type)


@router.delete(
    "/{type_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_inventory_admin)],
)
async def delete_item_type(
    type_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    item_type: ItemType = Depends(get_item_type_or_404),
):
    """Delete item type if not in use."""

    # Check if item type is in use
    parent_items_count = (
        db.query(ParentItem).filter(ParentItem.item_type_id == type_id).count()
    )
    child_items_count = (
        db.query(ChildItem).filter(ChildItem.item_type_id == type_id).count()
    )

    if parent_items_count > 0 or child_items_count > 0:
        total_items = parent_items_count + child_items_count
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot delete item type: {total_items} items are using " f"this type"
            ),
        )

    db.delete(item_type)
    db.commit()

    logger.info(
        "Item type deleted",
        item_type_id=str(item_type.id),
        name=item_type.name,
        deleted_by=str(current_user.id),
    )

    return MessageResponse(message="Item type deleted successfully")
