"""Location types router for Location Service."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shared.database.config import get_db
from shared.models.location import LocationType
from shared.models.user import User

from ..dependencies import (
    get_location_type_by_id,
    require_location_admin,
    require_location_read,
    require_location_write,
    validate_location_type_deletion,
)
from ..schemas import (
    LocationTypeCreate,
    LocationTypeResponse,
    LocationTypeUpdate,
    MessageResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=List[LocationTypeResponse],
    dependencies=[Depends(require_location_read)],
)
async def list_location_types(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all location types."""
    from shared.logging.config import get_logger

    logger = get_logger(__name__)
    logger.info(
        f"INSIDE list_location_types handler - skip={skip}, limit={limit}"
    )

    try:
        location_types = db.query(LocationType).offset(skip).limit(limit).all()
        logger.info(f"Found {len(location_types)} location types")
        return location_types
    except Exception as e:
        logger.error(f"Error in list_location_types: {str(e)}", exc_info=True)
        raise


@router.get(
    "/{location_type_id}",
    response_model=LocationTypeResponse,
    dependencies=[Depends(require_location_read)],
)
async def get_location_type(
    location_type: LocationType = Depends(get_location_type_by_id),
):
    """Get a specific location type by ID."""
    return location_type


@router.post(
    "/",
    response_model=LocationTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_location_type(
    location_type_data: LocationTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_write),
):
    """Create a new location type."""
    try:
        # Check if location type with same name already exists
        existing = (
            db.query(LocationType)
            .filter(LocationType.name == location_type_data.name)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Location type with name "
                    f"'{location_type_data.name}' already exists"
                ),
            )

        # Create new location type
        location_type = LocationType(**location_type_data.model_dump())
        db.add(location_type)
        db.commit()
        db.refresh(location_type)

        return location_type

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location type with this name already exists",
        )


@router.put("/{location_type_id}", response_model=LocationTypeResponse)
async def update_location_type(
    location_type_data: LocationTypeUpdate,
    location_type: LocationType = Depends(get_location_type_by_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_write),
):
    """Update a location type."""
    try:
        # Check for name conflicts if name is being updated
        if (
            location_type_data.name
            and location_type_data.name != location_type.name
        ):
            existing = (
                db.query(LocationType)
                .filter(
                    LocationType.name == location_type_data.name,
                    LocationType.id != location_type.id,
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Location type with name "
                        f"'{location_type_data.name}' already exists"
                    ),
                )

        # Update fields
        update_data = location_type_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location_type, field, value)

        db.commit()
        db.refresh(location_type)

        return location_type

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location type with this name already exists",
        )


@router.delete("/{location_type_id}", response_model=MessageResponse)
async def delete_location_type(
    location_type: LocationType = Depends(get_location_type_by_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_admin),
):
    """Delete a location type."""
    # Validate that location type can be deleted
    validate_location_type_deletion(location_type, db)

    try:
        db.delete(location_type)
        db.commit()

        return MessageResponse(
            message=f"Location type '{location_type.name}' deleted successfully"
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete location type - it may be referenced by existing locations",
        )
