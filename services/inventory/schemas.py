"""Pydantic schemas for Inventory Service."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.models.item import ItemCategory


# Base schemas
class ItemTypeBase(BaseModel):
    """Base item type schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: ItemCategory


class ParentItemBase(BaseModel):
    """Base parent item schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    item_type_id: UUID
    current_location_id: UUID


class ChildItemBase(BaseModel):
    """Base child item schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    item_type_id: UUID
    parent_item_id: UUID


class MoveItemBase(BaseModel):
    """Base schema for item movement."""

    parent_item_id: UUID
    to_location_id: UUID
    notes: Optional[str] = None


# Request schemas
class ItemTypeCreate(ItemTypeBase):
    """Schema for creating an item type."""

    pass


class ItemTypeUpdate(BaseModel):
    """Schema for updating an item type."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[ItemCategory] = None


class ParentItemCreate(ParentItemBase):
    """Schema for creating a parent item."""

    pass


class ParentItemUpdate(BaseModel):
    """Schema for updating a parent item."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    item_type_id: Optional[UUID] = None


class ChildItemCreate(ChildItemBase):
    """Schema for creating a child item."""

    pass


class ChildItemUpdate(BaseModel):
    """Schema for updating a child item."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    item_type_id: Optional[UUID] = None
    parent_item_id: Optional[UUID] = None


class MoveItemRequest(MoveItemBase):
    """Schema for moving an item."""

    pass


# Response schemas
class ItemTypeResponse(ItemTypeBase):
    """Schema for item type response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationResponse(BaseModel):
    """Schema for location response (minimal)."""

    id: UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response (minimal)."""

    id: UUID
    username: str

    class Config:
        from_attributes = True


class ChildItemResponse(ChildItemBase):
    """Schema for child item response."""

    id: UUID
    item_type: ItemTypeResponse
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class ParentItemResponse(ParentItemBase):
    """Schema for parent item response."""

    id: UUID
    item_type: ItemTypeResponse
    current_location: LocationResponse
    child_items: List[ChildItemResponse] = []
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class MoveHistoryResponse(BaseModel):
    """Schema for move history response."""

    id: UUID
    parent_item_id: UUID
    from_location: Optional[LocationResponse] = None
    to_location: LocationResponse
    moved_at: datetime
    moved_by_user: UserResponse
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AssignmentHistoryResponse(BaseModel):
    """Schema for assignment history response."""

    id: UUID
    child_item_id: UUID
    from_parent_item: Optional[ParentItemResponse] = None
    to_parent_item: ParentItemResponse
    assigned_at: datetime
    assigned_by_user: UserResponse
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for message response."""

    message: str


# Query schemas
class ItemLocationQuery(BaseModel):
    """Schema for item location query response."""

    parent_item: ParentItemResponse
    child_items: List[ChildItemResponse]


class ItemsAtLocationResponse(BaseModel):
    """Schema for items at location response."""

    location: LocationResponse
    parent_items: List[ParentItemResponse]
    total_child_items: int
