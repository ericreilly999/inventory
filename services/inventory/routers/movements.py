"""Item movements router for Inventory Service."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, or_

from shared.database.config import get_db
from shared.models.item import ParentItem
from shared.models.location import Location
from shared.models.move_history import MoveHistory
from shared.models.assignment_history import AssignmentHistory
from shared.models.user import User
from shared.logging.config import get_logger
from ..schemas import (
    MoveItemRequest, MoveHistoryResponse, MessageResponse, ItemsAtLocationResponse,
    AssignmentHistoryResponse
)
from ..dependencies import (
    get_current_user, require_inventory_read, require_inventory_write,
    get_parent_item_or_404, get_location_or_404
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/move", response_model=MessageResponse, dependencies=[Depends(require_inventory_write)])
async def move_parent_item(
    move_data: MoveItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Move a parent item to a new location."""
    
    # Validate parent item exists
    parent_item = await get_parent_item_or_404(move_data.parent_item_id, db)
    
    # Validate destination location exists
    to_location = await get_location_or_404(move_data.to_location_id, db)
    
    # Check if item is already at the destination
    if parent_item.current_location_id == move_data.to_location_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is already at the specified location"
        )
    
    # Store the current location for move history
    from_location_id = parent_item.current_location_id
    
    # Update parent item location
    parent_item.current_location_id = move_data.to_location_id
    
    # Create move history record
    move_history = MoveHistory(
        parent_item_id=move_data.parent_item_id,
        from_location_id=from_location_id,
        to_location_id=move_data.to_location_id,
        moved_at=datetime.utcnow(),
        moved_by=current_user.id,
        notes=move_data.notes
    )
    
    db.add(move_history)
    db.commit()
    db.refresh(parent_item)
    db.refresh(move_history)
    
    logger.info(
        "Parent item moved",
        parent_item_id=str(parent_item.id),
        from_location_id=str(from_location_id),
        to_location_id=str(move_data.to_location_id),
        child_items_count=len(parent_item.child_items),
        moved_by=str(current_user.id)
    )
    
    return MessageResponse(
        message=f"Item '{parent_item.name}' moved to '{to_location.name}' successfully"
    )


@router.get("/history/{item_id}", response_model=List[MoveHistoryResponse], dependencies=[Depends(require_inventory_read)])
async def get_item_move_history(
    item_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    parent_item: ParentItem = Depends(get_parent_item_or_404)
):
    """Get move history for a parent item."""
    
    move_history = db.query(MoveHistory).filter(
        MoveHistory.parent_item_id == item_id
    ).order_by(desc(MoveHistory.moved_at)).offset(skip).limit(limit).all()
    
    return [MoveHistoryResponse.from_orm(move) for move in move_history]


@router.get("/history", response_model=List[MoveHistoryResponse], dependencies=[Depends(require_inventory_read)])
async def get_all_move_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_id: Optional[UUID] = Query(None, description="Filter by location (from or to)"),
    item_id: Optional[UUID] = Query(None, description="Filter by parent item ID"),
    item_type_id: Optional[UUID] = Query(None, description="Filter by item type"),
    start_date: Optional[datetime] = Query(None, description="Filter moves from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter moves to this date"),
    db: Session = Depends(get_db)
):
    """Get move history with comprehensive filtering options."""
    
    query = db.query(MoveHistory)
    
    # Filter by specific parent item
    if item_id:
        query = query.filter(MoveHistory.parent_item_id == item_id)
    
    # Filter by item type
    if item_type_id:
        query = query.join(ParentItem).filter(ParentItem.item_type_id == item_type_id)
    
    # Filter by location (either from or to)
    if location_id:
        query = query.filter(
            or_(
                MoveHistory.from_location_id == location_id,
                MoveHistory.to_location_id == location_id
            )
        )
    
    # Filter by date range
    if start_date:
        query = query.filter(MoveHistory.moved_at >= start_date)
    
    if end_date:
        query = query.filter(MoveHistory.moved_at <= end_date)
    
    # Order by most recent first and apply pagination
    move_history = query.order_by(desc(MoveHistory.moved_at)).offset(skip).limit(limit).all()
    
    return [MoveHistoryResponse.from_orm(move) for move in move_history]


@router.get("/location/{location_id}/items", response_model=ItemsAtLocationResponse, dependencies=[Depends(require_inventory_read)])
async def get_items_at_location(
    location_id: UUID,
    db: Session = Depends(get_db),
    location: Location = Depends(get_location_or_404)
):
    """Get all items currently at a specific location."""
    
    parent_items = db.query(ParentItem).filter(
        ParentItem.current_location_id == location_id
    ).all()
    
    # Count total child items
    total_child_items = sum(len(item.child_items) for item in parent_items)
    
    return ItemsAtLocationResponse(
        location=location,
        parent_items=parent_items,
        total_child_items=total_child_items
    )


@router.get("/assignment-history", response_model=List[AssignmentHistoryResponse], dependencies=[Depends(require_inventory_read)])
async def get_all_assignment_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    child_item_id: Optional[UUID] = Query(None, description="Filter by child item ID"),
    parent_item_id: Optional[UUID] = Query(None, description="Filter by parent item ID (from or to)"),
    start_date: Optional[datetime] = Query(None, description="Filter assignments from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter assignments to this date"),
    db: Session = Depends(get_db)
):
    """Get assignment history with comprehensive filtering options."""
    
    query = db.query(AssignmentHistory)
    
    # Filter by specific child item
    if child_item_id:
        query = query.filter(AssignmentHistory.child_item_id == child_item_id)
    
    # Filter by parent item (either from or to)
    if parent_item_id:
        query = query.filter(
            or_(
                AssignmentHistory.from_parent_item_id == parent_item_id,
                AssignmentHistory.to_parent_item_id == parent_item_id
            )
        )
    
    # Filter by date range
    if start_date:
        query = query.filter(AssignmentHistory.assigned_at >= start_date)
    
    if end_date:
        query = query.filter(AssignmentHistory.assigned_at <= end_date)
    
    # Order by most recent first and apply pagination
    assignment_history = query.order_by(desc(AssignmentHistory.assigned_at)).offset(skip).limit(limit).all()
    
    return [AssignmentHistoryResponse.from_orm(assignment) for assignment in assignment_history]