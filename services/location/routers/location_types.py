"""Location types router for Location Service."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from shared.database.config import get_db
from shared.models.location import LocationType
from shared.models.user import User
from ..dependencies import (
    get_current_user, 
    get_location_type_by_id,
    validate_location_type_deletion,
    require_location_read,
    require_location_write,
    require_location_admin
)
from ..schemas import (
    LocationTypeCreate,
    LocationTypeUpdate,
    LocationTypeResponse,
    MessageResponse,
    ValidationErrorResponse
)

router = APIRouter()


@router.get("/", response_model=List[LocationTypeResponse])
async def list_location_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_location_read)
):
    """List all location types."""
    location_types = db.query(LocationType).offset(skip).limit(limit).all()
    return location_types


@router.get("/{location_type_id}", response_model=LocationTypeResponse)
async def get_location_type(
    location_type: LocationType = Depends(get_location_type_by_id),
    _: User = Depends(require_location_read)
):
    """Get a specific location type by ID."""
    return location_type


@router.post("/", response_model=LocationTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_location_type(
    location_type_data: LocationTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_write)
):
    """Create a new location type."""
    try:
        # Check if location type with same name already exists
        existing = db.query(LocationType).filter(
            LocationType.name == location_type_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Location type with name '{location_type_data.name}' already exists"
            )
        
        # Create new location type
        location_type = LocationType(**location_type_data.model_dump())
        db.add(location_type)
        db.commit()
        db.refresh(location_type)
        
        return location_type
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location type with this name already exists"
        )


@router.put("/{location_type_id}", response_model=LocationTypeResponse)
async def update_location_type(
    location_type_data: LocationTypeUpdate,
    location_type: LocationType = Depends(get_location_type_by_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_write)
):
    """Update a location type."""
    try:
        # Check for name conflicts if name is being updated
        if location_type_data.name and location_type_data.name != location_type.name:
            existing = db.query(LocationType).filter(
                LocationType.name == location_type_data.name,
                LocationType.id != location_type.id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Location type with name '{location_type_data.name}' already exists"
                )
        
        # Update fields
        update_data = location_type_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location_type, field, value)
        
        db.commit()
        db.refresh(location_type)
        
        return location_type
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location type with this name already exists"
        )


@router.delete("/{location_type_id}", response_model=MessageResponse)
async def delete_location_type(
    location_type: LocationType = Depends(get_location_type_by_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_admin)
):
    """Delete a location type."""
    # Validate that location type can be deleted
    validate_location_type_deletion(location_type, db)
    
    try:
        db.delete(location_type)
        db.commit()
        
        return MessageResponse(message=f"Location type '{location_type.name}' deleted successfully")
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete location type - it may be referenced by existing locations"
        )