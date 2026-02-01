"""Pydantic schemas for Reporting Service."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base response schemas
class LocationSummary(BaseModel):
    """Location summary for reports."""

    id: UUID
    name: str
    location_type: str

    class Config:
        from_attributes = True


class ItemTypeSummary(BaseModel):
    """Item type summary for reports."""

    id: UUID
    name: str
    category: str

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """User summary for reports."""

    id: UUID
    username: str

    class Config:
        from_attributes = True


class ChildItemDetail(BaseModel):
    """Detailed child item information for reports."""

    id: UUID
    sku: str
    child_item_type: str
    parent_item_sku: str
    parent_item_type: str
    location_name: str
    location_type: str

    class Config:
        from_attributes = True


class ParentItemDetail(BaseModel):
    """Detailed parent item information for reports."""

    id: UUID
    sku: str
    parent_item_type: str
    location_name: str
    location_type: str

    class Config:
        from_attributes = True


# Dashboard schemas
class InventoryByLocationItem(BaseModel):
    """Inventory count by location and item type for dashboard."""

    location_name: str
    item_type_name: str
    count: int


class ThroughputByLocationItem(BaseModel):
    """Throughput by location and item type for dashboard."""

    location_name: str
    item_type_name: str
    count: int


class DashboardData(BaseModel):
    """Dashboard data response."""

    inventory_by_location: List[InventoryByLocationItem]
    inbound_throughput: List[ThroughputByLocationItem]
    outbound_throughput: List[ThroughputByLocationItem]


# Inventory status report schemas
class InventoryStatusByLocation(BaseModel):
    """Inventory status by location."""

    location: LocationSummary
    parent_items_count: int
    child_items_count: int
    parent_items: List[Dict] = []  # Detailed item info if requested


class InventoryStatusReport(BaseModel):
    """Complete inventory status report."""

    generated_at: datetime
    total_locations: int
    total_parent_items: int
    total_child_items: int
    locations: List[InventoryStatusByLocation]


# Movement history report schemas
class MovementRecord(BaseModel):
    """Movement record for reports."""

    id: UUID
    parent_item_id: UUID
    parent_item_sku: str
    from_location: Optional[LocationSummary] = None
    to_location: LocationSummary
    moved_at: datetime
    moved_by: UserSummary
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MovementHistoryReport(BaseModel):
    """Movement history report."""

    generated_at: datetime
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    total_movements: int
    movements: List[MovementRecord]


# Inventory count report schemas
class InventoryCountByParentType(BaseModel):
    """Inventory count by parent item type."""

    item_type: ItemTypeSummary
    parent_items_count: int


class InventoryCountByChildType(BaseModel):
    """Inventory count by child item type."""

    item_type: ItemTypeSummary
    child_items_count: int


class InventoryCountByLocationAndType(BaseModel):
    """Inventory count by location and item type."""

    location: LocationSummary
    item_type: ItemTypeSummary
    parent_items_count: int
    child_items_count: int


class InventoryCountReport(BaseModel):
    """Inventory count report."""

    generated_at: datetime
    by_parent_item_type: List[InventoryCountByParentType]
    by_child_item_type: List[InventoryCountByChildType]
    by_location_and_type: List[InventoryCountByLocationAndType]
    parent_items_detail: List[ParentItemDetail] = []
    child_items_detail: List[ChildItemDetail] = []


# Request schemas
class ReportDateRange(BaseModel):
    """Date range for reports."""

    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")


class InventoryStatusRequest(BaseModel):
    """Request schema for inventory status report."""

    location_ids: Optional[List[UUID]] = Field(
        None, description="Filter by specific locations"
    )
    include_item_details: bool = Field(
        False, description="Include detailed item information"
    )


class MovementHistoryRequest(ReportDateRange):
    """Request schema for movement history report."""

    location_ids: Optional[List[UUID]] = Field(
        None, description="Filter by specific locations"
    )
    item_type_ids: Optional[List[UUID]] = Field(
        None, description="Filter by specific item types"
    )
    user_ids: Optional[List[UUID]] = Field(None, description="Filter by specific users")


class InventoryCountRequest(BaseModel):
    """Request schema for inventory count report."""

    location_type_ids: Optional[List[UUID]] = Field(
        None, description="Filter by location types"
    )
    item_type_ids: Optional[List[UUID]] = Field(
        None, description="Filter by item types"
    )


# Error response schemas
class ReportError(BaseModel):
    """Report error response."""

    error_code: str
    message: str
    details: Optional[Dict] = None


class ValidationError(BaseModel):
    """Validation error response."""

    field: str
    message: str
    value: Optional[str] = None
