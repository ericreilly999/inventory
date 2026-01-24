"""Parent items router for Inventory Service."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from shared.database.config import get_db
from shared.logging.config import get_logger
from shared.models.item import ItemCategory, ItemType, ParentItem
from shared.models.location import Location
from shared.models.user import User

from ..dependencies import (
    get_current_user,
    get_item_type_or_404,
    get_location_or_404,
    get_parent_item_or_404,
    require_inventory_admin,
    require_inventory_read,
    require_inventory_write,
    validate_item_type_category,
)
from ..schemas import (
    ItemLocationQuery,
    MessageResponse,
    ParentItemCreate,
    ParentItemResponse,
    ParentItemUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ParentItemResponse,
    dependencies=[Depends(require_inventory_write)],
)
async def create_parent_item(
    item_data: ParentItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new parent item."""

    # Validate item type exists and is for parent items
    item_type = await get_item_type_or_404(item_data.item_type_id, db)
    await validate_item_type_category(item_type, "parent")

    # Validate location exists
    location = await get_location_or_404(item_data.current_location_id, db)

    # Create new parent item
    parent_item = ParentItem(
        name=item_data.name,
        description=item_data.description,
        item_type_id=item_data.item_type_id,
        current_location_id=item_data.current_location_id,
        created_by=current_user.id,
    )

    db.add(parent_item)
    db.commit()
    db.refresh(parent_item)

    logger.info(
        "Parent item created",
        parent_item_id=str(parent_item.id),
        name=parent_item.name,
        location_id=str(parent_item.current_location_id),
        created_by=str(current_user.id),
    )

    return ParentItemResponse.from_orm(parent_item)


@router.get(
    "/",
    response_model=List[ParentItemResponse],
    dependencies=[Depends(require_inventory_read)],
)
async def list_parent_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_id: Optional[UUID] = Query(None),
    item_type_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List parent items with optional filtering."""

    query = db.query(ParentItem)

    # Filter by location
    if location_id:
        query = query.filter(ParentItem.current_location_id == location_id)

    # Filter by item type
    if item_type_id:
        query = query.filter(ParentItem.item_type_id == item_type_id)

    # Search filter
    if search:
        search_filter = or_(
            ParentItem.name.ilike(f"%{search}%"),
            ParentItem.description.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    # Apply pagination
    parent_items = query.offset(skip).limit(limit).all()

    return [ParentItemResponse.from_orm(item) for item in parent_items]


@router.get(
    "/{item_id}",
    response_model=ParentItemResponse,
    dependencies=[Depends(require_inventory_read)],
)
async def get_parent_item(
    parent_item: ParentItem = Depends(get_parent_item_or_404),
):
    """Get parent item by ID."""
    return ParentItemResponse.from_orm(parent_item)


@router.get(
    "/{item_id}/location",
    response_model=ItemLocationQuery,
    dependencies=[Depends(require_inventory_read)],
)
async def get_parent_item_location(
    parent_item: ParentItem = Depends(get_parent_item_or_404),
):
    """Get parent item location with all child items."""
    return ItemLocationQuery(
        parent_item=ParentItemResponse.from_orm(parent_item),
        child_items=[child for child in parent_item.child_items],
    )


@router.put(
    "/{item_id}",
    response_model=ParentItemResponse,
    dependencies=[Depends(require_inventory_write)],
)
async def update_parent_item(
    item_id: UUID,
    item_data: ParentItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    parent_item: ParentItem = Depends(get_parent_item_or_404),
):
    """Update parent item information."""

    # Update name
    if item_data.name is not None:
        parent_item.name = item_data.name

    # Update description
    if item_data.description is not None:
        parent_item.description = item_data.description

    # Update item type if provided
    if item_data.item_type_id is not None:
        item_type = await get_item_type_or_404(item_data.item_type_id, db)
        await validate_item_type_category(item_type, "parent")
        parent_item.item_type_id = item_data.item_type_id

    db.commit()
    db.refresh(parent_item)

    logger.info(
        "Parent item updated",
        parent_item_id=str(parent_item.id),
        updated_by=str(current_user.id),
    )

    return ParentItemResponse.from_orm(parent_item)


@router.delete(
    "/{item_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_inventory_admin)],
)
async def delete_parent_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    parent_item: ParentItem = Depends(get_parent_item_or_404),
):
    """Delete parent item and all associated child items."""

    child_count = len(parent_item.child_items)

    db.delete(parent_item)
    db.commit()

    logger.info(
        "Parent item deleted",
        parent_item_id=str(parent_item.id),
        name=parent_item.name,
        child_items_deleted=child_count,
        deleted_by=str(current_user.id),
    )

    return MessageResponse(
        message=f"Parent item deleted successfully (including {child_count} child items)"
    )
