"""Locations router for Location Service."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from shared.database.config import get_db
from shared.logging.config import get_logger
from shared.models.item import ParentItem
from shared.models.location import Location
from shared.models.user import User

from ..dependencies import (
    get_location_by_id,
    get_location_type_by_id,
    require_location_admin,
    require_location_read,
    require_location_write,
    validate_location_deletion,
)
from ..schemas import (
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    LocationWithItemsResponse,
    MessageResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=List[LocationResponse],
    dependencies=[Depends(require_location_read)],
)
async def list_locations(
    skip: int = 0,
    limit: int = 100,
    location_type_id: Optional[UUID] = Query(
        None, description="Filter by location type"
    ),
    db: Session = Depends(get_db),
):
    """List all locations with optional filtering."""
    query = db.query(Location).options(joinedload(Location.location_type))

    if location_type_id:
        query = query.filter(Location.location_type_id == location_type_id)

    locations = query.offset(skip).limit(limit).all()
    return locations


@router.get(
    "/with-items",
    response_model=List[LocationWithItemsResponse],
    dependencies=[Depends(require_location_read)],
)
async def list_locations_with_item_counts(
    skip: int = 0,
    limit: int = 100,
    location_type_id: Optional[UUID] = Query(
        None, description="Filter by location type"
    ),
    db: Session = Depends(get_db),
):
    """List all locations with item counts."""
    query = db.query(Location).options(joinedload(Location.location_type))

    if location_type_id:
        query = query.filter(Location.location_type_id == location_type_id)

    locations = query.offset(skip).limit(limit).all()

    # Add item counts
    result = []
    for location in locations:
        item_count = (
            db.query(ParentItem)
            .filter(ParentItem.current_location_id == location.id)
            .count()
        )

        location_dict = LocationWithItemsResponse.model_validate(location).model_dump()
        location_dict["item_count"] = item_count
        result.append(LocationWithItemsResponse(**location_dict))

    return result


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    dependencies=[Depends(require_location_read)],
)
async def get_location(location: Location = Depends(get_location_by_id)):
    """Get a specific location by ID."""
    return location


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_write),
):
    """Create a new location."""
    try:
        # Validate that location type exists
        await get_location_type_by_id(location_data.location_type_id, db)

        # Create new location
        location = Location(**location_data.model_dump())
        db.add(location)
        db.commit()
        db.refresh(location)

        # Load the location type relationship
        db.refresh(location)
        location = (
            db.query(Location)
            .options(joinedload(Location.location_type))
            .filter(Location.id == location.id)
            .first()
        )

        return location

    except HTTPException:
        # Re-raise validation errors from get_location_type_by_id
        raise
    except IntegrityError as e:
        db.rollback()
        if "uq_location_name_type" in str(e) or "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Location with name '{location_data.name}' already exists "
                    f"for this location type"
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location creation failed due to constraint violation",
        )


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_data: LocationUpdate,
    location: Location = Depends(get_location_by_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_write),
):
    """Update a location."""
    try:
        # Validate location type if it's being updated
        if location_data.location_type_id:
            await get_location_type_by_id(location_data.location_type_id, db)

        # Update fields
        update_data = location_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location, field, value)

        db.commit()
        db.refresh(location)

        # Load the location type relationship
        location = (
            db.query(Location)
            .options(joinedload(Location.location_type))
            .filter(Location.id == location.id)
            .first()
        )

        return location

    except HTTPException:
        # Re-raise validation errors
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location update failed due to constraint violation",
        )


@router.delete("/{location_id}", response_model=MessageResponse)
async def delete_location(
    location: Location = Depends(get_location_by_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_admin),
):
    """Delete a location."""
    # Validate that location can be deleted
    validate_location_deletion(location, db)

    try:
        location_name = location.name
        db.delete(location)
        db.commit()

        return MessageResponse(
            message=f"Location '{location_name}' deleted successfully"
        )

    except IntegrityError as e:
        db.rollback()
        # This should not happen if validation passed, but handle it anyway
        error_msg = str(e).lower()

        # Log the full error for debugging
        logger.error(f"IntegrityError deleting location {location.id}: {e}")

        if "parent_items" in error_msg or "current_location" in error_msg:
            detail = (
                f"Cannot delete location '{location.name}' - items are still "
                "assigned to it. Move all items to another location first."
            )
        else:
            detail = (
                f"Cannot delete location '{location.name}' - it may be referenced by "
                f"existing items. Error: {str(e)[:200]}"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.get(
    "/{location_id}/items",
    response_model=List[dict],
    dependencies=[Depends(require_location_read)],
)
async def get_location_items(
    location: Location = Depends(get_location_by_id),
    db: Session = Depends(get_db),
):
    """Get all items currently at this location."""
    items = (
        db.query(ParentItem).filter(ParentItem.current_location_id == location.id).all()
    )

    # Return basic item information
    return [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "item_type_id": item.item_type_id,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in items
    ]
