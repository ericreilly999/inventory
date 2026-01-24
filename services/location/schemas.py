"""Pydantic schemas for Location Service."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base schemas
class LocationTypeBase(BaseModel):
    """Base location type schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class LocationBase(BaseModel):
    """Base location schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    location_metadata: Dict[str, Any] = Field(default_factory=dict)
    location_type_id: UUID


# Request schemas
class LocationTypeCreate(LocationTypeBase):
    """Schema for creating a location type."""


class LocationTypeUpdate(BaseModel):
    """Schema for updating a location type."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class LocationCreate(LocationBase):
    """Schema for creating a location."""


class LocationUpdate(BaseModel):
    """Schema for updating a location."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    location_metadata: Optional[Dict[str, Any]] = None
    location_type_id: Optional[UUID] = None


class ItemMoveRequest(BaseModel):
    """Schema for moving an item."""

    item_id: UUID
    to_location_id: UUID
    notes: Optional[str] = None


# Response schemas
class LocationTypeResponse(LocationTypeBase):
    """Schema for location type response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationResponse(LocationBase):
    """Schema for location response."""

    id: UUID
    location_type: LocationTypeResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationWithItemsResponse(LocationResponse):
    """Schema for location response with item counts."""

    item_count: int = 0


class MoveHistoryResponse(BaseModel):
    """Schema for move history response."""

    id: UUID
    parent_item_id: UUID
    from_location_id: Optional[UUID]
    to_location_id: UUID
    moved_at: datetime
    moved_by: UUID
    notes: Optional[str]

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for message response."""

    message: str


class ValidationErrorResponse(BaseModel):
    """Schema for validation error response."""

    error: str
    details: Optional[Dict[str, Any]] = None
