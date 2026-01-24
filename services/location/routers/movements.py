"""Movements router for Location Service."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from shared.database.config import get_db
from shared.models.item import ParentItem
from shared.models.location import Location
from shared.models.move_history import MoveHistory
from shared.models.user import User

from ..dependencies import (
    get_current_user,
    get_location_by_id,
    get_parent_item_by_id,
    require_location_read,
    require_location_write,
)
from ..schemas import ItemMoveRequest, MessageResponse, MoveHistoryResponse

router = APIRouter()


@router.post("/move", response_model=MessageResponse)
async def move_item(
    move_request: ItemMoveRequest,
    db: Session = Depends(get_db),
    token_data=Depends(require_location_write),
):
    """Move a parent item to a new location."""
    import traceback

    from shared.logging.config import get_logger

    logger = get_logger(__name__)

    try:
        logger.info(
            "Processing move request",
            item_id=str(move_request.item_id),
            to_location_id=str(move_request.to_location_id),
            user_id=str(token_data.user_id),
        )

        # Get the parent item
        parent_item = await get_parent_item_by_id(move_request.item_id, db)

        # Get the destination location
        to_location = await get_location_by_id(move_request.to_location_id, db)

        # Check if item is already at the destination
        if parent_item.current_location_id == move_request.to_location_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item '{parent_item.name}' is already at location '{to_location.name}'",
            )

        # Store the original location for history
        from_location_id = parent_item.current_location_id

        # Update the parent item's location
        parent_item.current_location_id = move_request.to_location_id

        # Create move history record
        move_history = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=from_location_id,
            to_location_id=move_request.to_location_id,
            moved_at=datetime.utcnow(),
            moved_by=token_data.user_id,
            notes=move_request.notes,
        )

        db.add(move_history)
        db.commit()

        logger.info(
            "Item moved successfully",
            item_id=str(parent_item.id),
            from_location_id=str(from_location_id),
            to_location_id=str(move_request.to_location_id),
        )

        return MessageResponse(
            message=f"Item '{parent_item.name}' moved to location '{to_location.name}' successfully"
        )

    except HTTPException:
        # Re-raise validation errors
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to move item",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
            item_id=str(move_request.item_id) if move_request else None,
            to_location_id=(
                str(move_request.to_location_id) if move_request else None
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move item: {str(e)}",
        )


@router.get(
    "/history",
    response_model=List[MoveHistoryResponse],
    dependencies=[Depends(require_location_read)],
)
async def get_move_history(
    skip: int = 0,
    limit: int = 100,
    item_id: Optional[UUID] = Query(
        None, description="Filter by parent item ID"
    ),
    location_id: Optional[UUID] = Query(
        None, description="Filter by location ID (from or to)"
    ),
    from_date: Optional[datetime] = Query(
        None, description="Filter moves from this date"
    ),
    to_date: Optional[datetime] = Query(
        None, description="Filter moves to this date"
    ),
    db: Session = Depends(get_db),
):
    """Get move history with optional filtering."""
    query = db.query(MoveHistory).order_by(MoveHistory.moved_at.desc())

    # Apply filters
    if item_id:
        query = query.filter(MoveHistory.parent_item_id == item_id)

    if location_id:
        query = query.filter(
            (MoveHistory.from_location_id == location_id)
            | (MoveHistory.to_location_id == location_id)
        )

    if from_date:
        query = query.filter(MoveHistory.moved_at >= from_date)

    if to_date:
        query = query.filter(MoveHistory.moved_at <= to_date)

    moves = query.offset(skip).limit(limit).all()
    return moves


@router.get(
    "/history/{item_id}",
    response_model=List[MoveHistoryResponse],
    dependencies=[Depends(require_location_read)],
)
async def get_item_move_history(
    item_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get move history for a specific parent item."""
    # Verify the item exists
    await get_parent_item_by_id(item_id, db)

    moves = (
        db.query(MoveHistory)
        .filter(MoveHistory.parent_item_id == item_id)
        .order_by(MoveHistory.moved_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return moves


@router.get(
    "/recent",
    response_model=List[MoveHistoryResponse],
    dependencies=[Depends(require_location_read)],
)
async def get_recent_moves(
    limit: int = Query(
        50, le=100, description="Number of recent moves to return"
    ),
    db: Session = Depends(get_db),
):
    """Get recent item movements."""
    moves = (
        db.query(MoveHistory)
        .order_by(MoveHistory.moved_at.desc())
        .limit(limit)
        .all()
    )

    return moves
