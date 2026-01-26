"""Child items router for Inventory Service."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from shared.database.config import get_db
from shared.logging.config import get_logger
from shared.models.assignment_history import AssignmentHistory
from shared.models.item import ChildItem
from shared.models.user import User

from ..dependencies import (
    get_child_item_or_404,
    get_current_user,
    get_item_type_or_404,
    get_parent_item_or_404,
    require_inventory_admin,
    require_inventory_read,
    require_inventory_write,
    validate_item_type_category,
)
from ..schemas import (
    AssignmentHistoryResponse,
    ChildItemCreate,
    ChildItemResponse,
    ChildItemUpdate,
    MessageResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ChildItemResponse,
    dependencies=[Depends(require_inventory_write)],
)
async def create_child_item(
    item_data: ChildItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new child item."""

    # Validate item type exists and is for child items
    item_type = await get_item_type_or_404(item_data.item_type_id, db)
    await validate_item_type_category(item_type, "child")

    # Validate parent item exists
    await get_parent_item_or_404(item_data.parent_item_id, db)

    # Create new child item
    child_item = ChildItem(
        sku=item_data.sku,
        description=item_data.description,
        item_type_id=item_data.item_type_id,
        parent_item_id=item_data.parent_item_id,
        created_by=current_user.id,
    )

    db.add(child_item)
    db.flush()  # Flush to get the child_item.id

    # Create assignment history record for initial assignment
    assignment_history = AssignmentHistory(
        child_item_id=child_item.id,
        from_parent_item_id=None,  # Initial assignment
        to_parent_item_id=item_data.parent_item_id,
        assigned_at=datetime.utcnow(),
        assigned_by=current_user.id,
        notes="Initial assignment",
    )

    db.add(assignment_history)
    db.commit()
    db.refresh(child_item)

    logger.info(
        "Child item created",
        child_item_id=str(child_item.id),
        sku=child_item.sku,
        parent_item_id=str(child_item.parent_item_id),
        created_by=str(current_user.id),
    )

    return ChildItemResponse.from_orm(child_item)


@router.get(
    "/",
    response_model=List[ChildItemResponse],
    dependencies=[Depends(require_inventory_read)],
)
async def list_child_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    parent_item_id: Optional[UUID] = Query(None),
    item_type_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List child items with optional filtering."""

    query = db.query(ChildItem)

    # Filter by parent item
    if parent_item_id:
        query = query.filter(ChildItem.parent_item_id == parent_item_id)

    # Filter by item type
    if item_type_id:
        query = query.filter(ChildItem.item_type_id == item_type_id)

    # Search filter
    if search:
        search_filter = or_(
            ChildItem.sku.ilike(f"%{search}%"),
            ChildItem.description.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    # Apply pagination
    child_items = query.offset(skip).limit(limit).all()

    return [ChildItemResponse.from_orm(item) for item in child_items]


@router.get(
    "/{item_id}",
    response_model=ChildItemResponse,
    dependencies=[Depends(require_inventory_read)],
)
async def get_child_item(
    child_item: ChildItem = Depends(get_child_item_or_404),
):
    """Get child item by ID."""
    return ChildItemResponse.from_orm(child_item)


@router.put(
    "/{item_id}",
    response_model=ChildItemResponse,
    dependencies=[Depends(require_inventory_write)],
)
async def update_child_item(
    item_id: UUID,
    item_data: ChildItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    child_item: ChildItem = Depends(get_child_item_or_404),
):
    """Update child item information."""

    # Update sku
    if item_data.sku is not None:
        child_item.sku = item_data.sku

    # Update description
    if item_data.description is not None:
        child_item.description = item_data.description

    # Update item type if provided
    if item_data.item_type_id is not None:
        item_type = await get_item_type_or_404(item_data.item_type_id, db)
        await validate_item_type_category(item_type, "child")
        child_item.item_type_id = item_data.item_type_id

    # Update parent item assignment if provided
    if item_data.parent_item_id is not None:
        # Validate new parent item exists
        await get_parent_item_or_404(item_data.parent_item_id, db)

        old_parent_id = child_item.parent_item_id
        child_item.parent_item_id = item_data.parent_item_id

        # Create assignment history record for reassignment
        assignment_history = AssignmentHistory(
            child_item_id=child_item.id,
            from_parent_item_id=old_parent_id,
            to_parent_item_id=item_data.parent_item_id,
            assigned_at=datetime.utcnow(),
            assigned_by=current_user.id,
            notes="Reassignment via update",
        )

        db.add(assignment_history)

        logger.info(
            "Child item reassigned",
            child_item_id=str(child_item.id),
            old_parent_id=str(old_parent_id),
            new_parent_id=str(item_data.parent_item_id),
            reassigned_by=str(current_user.id),
        )

    db.commit()
    db.refresh(child_item)

    logger.info(
        "Child item updated",
        child_item_id=str(child_item.id),
        updated_by=str(current_user.id),
    )

    return ChildItemResponse.from_orm(child_item)


@router.delete(
    "/{item_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_inventory_admin)],
)
async def delete_child_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    child_item: ChildItem = Depends(get_child_item_or_404),
):
    """Delete child item."""

    db.delete(child_item)
    db.commit()

    logger.info(
        "Child item deleted",
        child_item_id=str(child_item.id),
        sku=child_item.sku,
        deleted_by=str(current_user.id),
    )

    return MessageResponse(message="Child item deleted successfully")


@router.get(
    "/{item_id}/assignment-history",
    response_model=List[AssignmentHistoryResponse],
    dependencies=[Depends(require_inventory_read)],
)
async def get_child_item_assignment_history(
    item_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    child_item: ChildItem = Depends(get_child_item_or_404),
):
    """Get assignment history for a child item."""

    assignment_history = (
        db.query(AssignmentHistory)
        .filter(AssignmentHistory.child_item_id == item_id)
        .order_by(AssignmentHistory.assigned_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        AssignmentHistoryResponse.from_orm(assignment)
        for assignment in assignment_history
    ]


@router.post(
    "/{item_id}/reassign/{new_parent_id}",
    response_model=ChildItemResponse,
    dependencies=[Depends(require_inventory_write)],
)
async def reassign_child_item(
    item_id: UUID,
    new_parent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    child_item: ChildItem = Depends(get_child_item_or_404),
):
    """Reassign child item to a different parent item."""

    # Validate new parent item exists
    await get_parent_item_or_404(new_parent_id, db)

    old_parent_id = child_item.parent_item_id
    child_item.parent_item_id = new_parent_id

    # Create assignment history record for reassignment
    assignment_history = AssignmentHistory(
        child_item_id=child_item.id,
        from_parent_item_id=old_parent_id,
        to_parent_item_id=new_parent_id,
        assigned_at=datetime.utcnow(),
        assigned_by=current_user.id,
        notes="Direct reassignment",
    )

    db.add(assignment_history)
    db.commit()
    db.refresh(child_item)

    logger.info(
        "Child item reassigned",
        child_item_id=str(child_item.id),
        old_parent_id=str(old_parent_id),
        new_parent_id=str(new_parent_id),
        reassigned_by=str(current_user.id),
    )

    return ChildItemResponse.from_orm(child_item)
