"""Reports router for Reporting Service."""

import traceback
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from shared.database.config import get_db
from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory

from ..dependencies import require_reports_read
from ..schemas import (
    ChildItemDetail,
    DashboardData,
    InventoryByLocationItem,
    InventoryCountByChildType,
    InventoryCountByLocationAndType,
    InventoryCountByParentType,
    InventoryCountReport,
    InventoryStatusByLocation,
    InventoryStatusReport,
    ItemTypeSummary,
    LocationSummary,
    MovementHistoryReport,
    MovementRecord,
    ParentItemDetail,
    ThroughputByLocationItem,
    UserSummary,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/inventory/status",
    response_model=InventoryStatusReport,
    summary="Get inventory status report",
    description=("Generate a report showing current inventory status by location"),
    dependencies=[Depends(require_reports_read)],
)
async def get_inventory_status_report(
    location_ids: Optional[List[UUID]] = Query(
        None, description="Filter by specific locations"
    ),
    include_item_details: bool = Query(
        False, description="Include detailed item information"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate inventory status report by location.

    Requirements: 3.1, 3.4, 3.5
    """
    logger.info(
        "Generating inventory status report",
        location_ids=location_ids,
        include_item_details=include_item_details,
    )
    try:
        # Build base query for locations
        location_query = db.query(Location).options(joinedload(Location.location_type))

        if location_ids:
            location_query = location_query.filter(Location.id.in_(location_ids))

        locations = location_query.all()

        if location_ids and len(locations) != len(location_ids):
            found_ids = {loc.id for loc in locations}
            missing_ids = set(location_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Locations not found: {list(missing_ids)}",
            )

        # Get inventory data for each location
        location_reports = []
        total_parent_items = 0
        total_child_items = 0

        for location in locations:
            # Count parent items at this location
            parent_items_count = (
                db.query(ParentItem)
                .filter(ParentItem.current_location_id == location.id)
                .count()
            )

            # Count child items (through their parent items)
            child_items_count = (
                db.query(ChildItem)
                .join(ParentItem)
                .filter(ParentItem.current_location_id == location.id)
                .count()
            )

            # Get detailed item info if requested
            parent_items_details = []
            if include_item_details:
                parent_items = (
                    db.query(ParentItem)
                    .options(
                        joinedload(ParentItem.item_type),
                        joinedload(ParentItem.child_items).joinedload(
                            ChildItem.item_type
                        ),
                    )
                    .filter(ParentItem.current_location_id == location.id)
                    .all()
                )

                parent_items_details = [
                    {
                        "id": str(item.id),
                        "sku": item.sku,
                        "description": item.description,
                        "item_type": item.item_type.name,
                        "child_items_count": len(item.child_items),
                        "child_items": [
                            {
                                "id": str(child.id),
                                "sku": child.sku,
                                "item_type": child.item_type.name,
                            }
                            for child in item.child_items
                        ],
                    }
                    for item in parent_items
                ]

            location_reports.append(
                InventoryStatusByLocation(
                    location=LocationSummary(
                        id=location.id,
                        name=location.name,
                        location_type=location.location_type.name,
                    ),
                    parent_items_count=parent_items_count,
                    child_items_count=child_items_count,
                    parent_items=parent_items_details,
                )
            )

            total_parent_items += parent_items_count
            total_child_items += child_items_count

        return InventoryStatusReport(
            generated_at=datetime.now(timezone.utc),
            total_locations=len(locations),
            total_parent_items=total_parent_items,
            total_child_items=total_child_items,
            locations=location_reports,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error generating inventory status report",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
            location_ids=location_ids,
            include_item_details=include_item_details,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating inventory status report: {str(e)}",
        )


@router.get(
    "/movements/history",
    response_model=MovementHistoryReport,
    summary="Get movement history report",
    description=(
        "Generate a report showing item movement history "
        "with optional date filtering"
    ),
    dependencies=[Depends(require_reports_read)],
)
async def get_movement_history_report(
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    location_ids: Optional[List[UUID]] = Query(
        None, description="Filter by specific locations"
    ),
    item_type_ids: Optional[List[UUID]] = Query(
        None, description="Filter by specific item types"
    ),
    user_ids: Optional[List[UUID]] = Query(
        None, description="Filter by specific users"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate movement history report with date filtering.

    Requirements: 3.2, 5.2, 3.4, 3.5
    """
    logger.info(
        "Generating movement history report",
        start_date=start_date,
        end_date=end_date,
        location_ids=location_ids,
        item_type_ids=item_type_ids,
        user_ids=user_ids,
    )
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date",
            )

        # Build query for movement history
        query = db.query(MoveHistory).options(
            joinedload(MoveHistory.parent_item).joinedload(ParentItem.item_type),
            joinedload(MoveHistory.from_location).joinedload(Location.location_type),
            joinedload(MoveHistory.to_location).joinedload(Location.location_type),
            joinedload(MoveHistory.moved_by_user),
        )

        # Apply date filters
        if start_date:
            query = query.filter(MoveHistory.moved_at >= start_date)
        if end_date:
            query = query.filter(MoveHistory.moved_at <= end_date)

        # Apply location filters (either from or to location)
        if location_ids:
            query = query.filter(
                (MoveHistory.from_location_id.in_(location_ids))
                | (MoveHistory.to_location_id.in_(location_ids))
            )

        # Apply item type filters
        if item_type_ids:
            query = query.join(ParentItem).filter(
                ParentItem.item_type_id.in_(item_type_ids)
            )

        # Apply user filters
        if user_ids:
            query = query.filter(MoveHistory.moved_by.in_(user_ids))

        # Order by moved_at chronologically (most recent first)
        movements = query.order_by(MoveHistory.moved_at.desc()).all()

        # Convert to response format
        movement_records = []
        for movement in movements:
            from_location = None
            if movement.from_location:
                from_location = LocationSummary(
                    id=movement.from_location.id,
                    name=movement.from_location.name,
                    location_type=movement.from_location.location_type.name,
                )

            movement_records.append(
                MovementRecord(
                    id=movement.id,
                    parent_item_id=movement.parent_item_id,
                    parent_item_sku=movement.parent_item.sku,
                    from_location=from_location,
                    to_location=LocationSummary(
                        id=movement.to_location.id,
                        name=movement.to_location.name,
                        location_type=movement.to_location.location_type.name,
                    ),
                    moved_at=movement.moved_at,
                    moved_by=UserSummary(
                        id=movement.moved_by_user.id,
                        username=movement.moved_by_user.username,
                    ),
                    notes=movement.notes,
                )
            )

        return MovementHistoryReport(
            generated_at=datetime.now(timezone.utc),
            date_range_start=start_date,
            date_range_end=end_date,
            total_movements=len(movement_records),
            movements=movement_records,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error generating movement history report",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
            start_date=start_date,
            end_date=end_date,
            location_ids=location_ids,
            item_type_ids=item_type_ids,
            user_ids=user_ids,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating movement history report: {str(e)}",
        )


@router.get(
    "/inventory/counts",
    response_model=InventoryCountReport,
    summary="Get inventory count report",
    description=(
        "Generate a report showing inventory counts by item type " "and location type"
    ),
    dependencies=[Depends(require_reports_read)],
)
async def get_inventory_count_report(
    location_ids: Optional[List[UUID]] = Query(
        None, description="Filter by specific locations"
    ),
    location_type_ids: Optional[List[UUID]] = Query(
        None, description="Filter by location types"
    ),
    item_type_ids: Optional[List[UUID]] = Query(
        None, description="Filter by item types"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate inventory count report by item type and location type.

    Requirements: 3.3, 3.4, 3.5
    """
    logger.info(
        "Generating inventory count report",
        location_ids=location_ids,
        location_type_ids=location_type_ids,
        item_type_ids=item_type_ids,
    )
    try:
        # Get counts by parent item type
        parent_type_query = (
            db.query(
                ItemType,
                func.count(func.distinct(ParentItem.id)).label("parent_count"),
            )
            .outerjoin(ParentItem, ParentItem.item_type_id == ItemType.id)
            .filter(ItemType.category == ItemCategory.PARENT)
        )

        if item_type_ids:
            parent_type_query = parent_type_query.filter(ItemType.id.in_(item_type_ids))

        parent_type_counts = parent_type_query.group_by(ItemType.id).all()

        by_parent_item_type = []
        for item_type, parent_count in parent_type_counts:
            by_parent_item_type.append(
                InventoryCountByParentType(
                    item_type=ItemTypeSummary(
                        id=item_type.id,
                        name=item_type.name,
                        category=item_type.category.value,
                    ),
                    parent_items_count=parent_count or 0,
                )
            )

        # Get counts by child item type
        child_type_query = (
            db.query(
                ItemType,
                func.count(func.distinct(ChildItem.id)).label("child_count"),
            )
            .outerjoin(ChildItem, ChildItem.item_type_id == ItemType.id)
            .filter(ItemType.category == ItemCategory.CHILD)
        )

        if item_type_ids:
            child_type_query = child_type_query.filter(ItemType.id.in_(item_type_ids))

        child_type_counts = child_type_query.group_by(ItemType.id).all()

        by_child_item_type = []
        for item_type, child_count in child_type_counts:
            by_child_item_type.append(
                InventoryCountByChildType(
                    item_type=ItemTypeSummary(
                        id=item_type.id,
                        name=item_type.name,
                        category=item_type.category.value,
                    ),
                    child_items_count=child_count or 0,
                )
            )

        # Get counts by location and item type
        location_type_query = (
            db.query(
                Location,
                ItemType,
                func.count(func.distinct(ParentItem.id)).label("parent_count"),
                func.count(func.distinct(ChildItem.id)).label("child_count"),
            )
            .join(Location.location_type)
            .outerjoin(ParentItem, ParentItem.current_location_id == Location.id)
            .outerjoin(ItemType, ParentItem.item_type_id == ItemType.id)
            .outerjoin(ChildItem, ChildItem.parent_item_id == ParentItem.id)
        )

        # Apply location filter
        if location_ids:
            location_type_query = location_type_query.filter(
                Location.id.in_(location_ids)
            )

        if location_type_ids:
            location_type_query = location_type_query.filter(
                Location.location_type_id.in_(location_type_ids)
            )

        if item_type_ids:
            location_type_query = location_type_query.filter(
                ItemType.id.in_(item_type_ids)
            )

        location_type_counts = location_type_query.group_by(
            Location.id, ItemType.id
        ).all()

        by_location_and_type = []
        for (
            location,
            item_type,
            parent_count,
            child_count,
        ) in location_type_counts:
            if item_type:  # Only include if there's an item type
                by_location_and_type.append(
                    InventoryCountByLocationAndType(
                        location=LocationSummary(
                            id=location.id,
                            name=location.name,
                            location_type=location.location_type.name,
                        ),
                        item_type=ItemTypeSummary(
                            id=item_type.id,
                            name=item_type.name,
                            category=item_type.category.value,
                        ),
                        parent_items_count=parent_count or 0,
                        child_items_count=child_count or 0,
                    )
                )

        # Get detailed child item information
        child_items_query = (
            db.query(
                ChildItem.id,
                ChildItem.sku,
                ItemType.name.label("child_item_type"),
                ParentItem.sku.label("parent_item_sku"),
                ParentItem.item_type.has(name=ItemType.name).label(
                    "parent_item_type_name"
                ),
                Location.name.label("location_name"),
                LocationType.name.label("location_type"),
            )
            .join(ItemType, ChildItem.item_type_id == ItemType.id)
            .join(ParentItem, ChildItem.parent_item_id == ParentItem.id)
            .join(Location, ParentItem.current_location_id == Location.id)
            .join(LocationType, Location.location_type_id == LocationType.id)
        )

        # Apply filters to child items query
        if location_ids:
            child_items_query = child_items_query.filter(Location.id.in_(location_ids))

        if location_type_ids:
            child_items_query = child_items_query.filter(
                Location.location_type_id.in_(location_type_ids)
            )

        if item_type_ids:
            child_items_query = child_items_query.filter(
                ChildItem.item_type_id.in_(item_type_ids)
            )

        child_items_results = child_items_query.all()

        # Build child items detail list
        child_items_detail = []
        for result in child_items_results:
            # Get parent item type name
            parent_item = (
                db.query(ParentItem)
                .filter(ParentItem.sku == result.parent_item_sku)
                .first()
            )
            parent_item_type_name = (
                parent_item.item_type.name
                if parent_item and parent_item.item_type
                else ""
            )

            child_items_detail.append(
                ChildItemDetail(
                    id=result.id,
                    sku=result.sku,
                    child_item_type=result.child_item_type,
                    parent_item_sku=result.parent_item_sku,
                    parent_item_type=parent_item_type_name,
                    location_name=result.location_name,
                    location_type=result.location_type,
                )
            )

        # Get detailed parent item information
        parent_items_query = (
            db.query(
                ParentItem.id,
                ParentItem.sku,
                ItemType.name.label("parent_item_type"),
                Location.name.label("location_name"),
                LocationType.name.label("location_type"),
            )
            .join(ItemType, ParentItem.item_type_id == ItemType.id)
            .join(Location, ParentItem.current_location_id == Location.id)
            .join(LocationType, Location.location_type_id == LocationType.id)
        )

        # Apply filters to parent items query
        if location_ids:
            parent_items_query = parent_items_query.filter(
                Location.id.in_(location_ids)
            )

        if location_type_ids:
            parent_items_query = parent_items_query.filter(
                Location.location_type_id.in_(location_type_ids)
            )

        if item_type_ids:
            parent_items_query = parent_items_query.filter(
                ParentItem.item_type_id.in_(item_type_ids)
            )

        parent_items_results = parent_items_query.all()

        # Build parent items detail list
        parent_items_detail = []
        for result in parent_items_results:
            parent_items_detail.append(
                ParentItemDetail(
                    id=result.id,
                    sku=result.sku,
                    parent_item_type=result.parent_item_type,
                    location_name=result.location_name,
                    location_type=result.location_type,
                )
            )

        return InventoryCountReport(
            generated_at=datetime.now(timezone.utc),
            by_parent_item_type=by_parent_item_type,
            by_child_item_type=by_child_item_type,
            by_location_and_type=by_location_and_type,
            parent_items_detail=parent_items_detail,
            child_items_detail=child_items_detail,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error generating inventory count report",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
            location_ids=location_ids,
            location_type_ids=location_type_ids,
            item_type_ids=item_type_ids,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating inventory count report: {str(e)}",
        )


@router.get(
    "/export/inventory",
    summary="Export inventory data",
    description="Export inventory data in structured format for analysis",
    dependencies=[Depends(require_reports_read)],
)
async def export_inventory_data(
    format: str = Query("json", description="Export format (json, csv)"),
    location_ids: Optional[List[UUID]] = Query(
        None, description="Filter by specific locations"
    ),
    db: Session = Depends(get_db),
):
    """
    Export inventory data in structured format.

    Requirements: 3.4, 3.5
    """
    logger.info("Exporting inventory data", format=format, location_ids=location_ids)
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Supported formats: json, csv",
            )

        # Get all inventory data
        query = db.query(ParentItem).options(
            joinedload(ParentItem.item_type),
            joinedload(ParentItem.current_location).joinedload(Location.location_type),
            joinedload(ParentItem.child_items).joinedload(ChildItem.item_type),
        )

        if location_ids:
            query = query.filter(ParentItem.current_location_id.in_(location_ids))

        parent_items = query.all()

        # Format data for export
        export_data = []
        for item in parent_items:
            item_data = {
                "parent_item_id": str(item.id),
                "parent_item_sku": item.sku,
                "parent_item_description": item.description,
                "parent_item_type": item.item_type.name,
                "location_name": item.current_location.name,
                "location_type": item.current_location.location_type.name,
                "child_items_count": len(item.child_items),
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }

            if item.child_items:
                for child in item.child_items:
                    child_data = item_data.copy()
                    child_data.update(
                        {
                            "child_item_id": str(child.id),
                            "child_item_sku": child.sku,
                            "child_item_description": child.description,
                            "child_item_type": child.item_type.name,
                            "child_created_at": child.created_at.isoformat(),
                            "child_updated_at": child.updated_at.isoformat(),
                        }
                    )
                    export_data.append(child_data)
            else:
                item_data.update(
                    {
                        "child_item_id": None,
                        "child_item_sku": None,
                        "child_item_description": None,
                        "child_item_type": None,
                        "child_created_at": None,
                        "child_updated_at": None,
                    }
                )
                export_data.append(item_data)

        if format == "json":
            return {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "total_records": len(export_data),
                "data": export_data,
            }
        elif format == "csv":
            # For CSV, we would typically return a streaming response
            # For now, return structured data that can be converted to CSV
            return {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "format": "csv",
                "total_records": len(export_data),
                "headers": list(export_data[0].keys()) if export_data else [],
                "data": export_data,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error exporting inventory data",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
            format=format,
            location_ids=location_ids,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting inventory data: {str(e)}",
        )


@router.get(
    "/dashboard",
    response_model=DashboardData,
    summary="Get dashboard data",
    description="Get dashboard data with inventory and throughput by location",
    dependencies=[Depends(require_reports_read)],
)
async def get_dashboard_data(
    location_type_id: UUID = Query(
        ..., description="Filter by location type (required)"
    ),
    start_date: Optional[str] = Query(
        None, description="Start date for throughput (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(
        None, description="End date for throughput (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate dashboard data with inventory and throughput by location.

    Requires location_type_id filter.
    """
    logger.info(
        "Generating dashboard data",
        location_type_id=str(location_type_id),
        start_date=start_date,
        end_date=end_date,
    )
    try:
        # Get inventory by location and item type
        inventory_query = (
            db.query(
                Location.name.label("location_name"),
                ItemType.name.label("item_type_name"),
                func.count(ParentItem.id).label("count"),
            )
            .join(ParentItem, ParentItem.current_location_id == Location.id)
            .join(ItemType, ParentItem.item_type_id == ItemType.id)
            .filter(Location.location_type_id == location_type_id)
            .group_by(Location.name, ItemType.name)
            .order_by(Location.name, ItemType.name)
        )

        inventory_results = inventory_query.all()
        inventory_by_location = [
            InventoryByLocationItem(
                location_name=row.location_name,
                item_type_name=row.item_type_name,
                count=row.count,
            )
            for row in inventory_results
        ]

        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )

        # Get inbound throughput (moves TO locations of this type)
        inbound_query = (
            db.query(
                Location.name.label("location_name"),
                ItemType.name.label("item_type_name"),
                func.count(MoveHistory.id).label("count"),
            )
            .join(MoveHistory, MoveHistory.to_location_id == Location.id)
            .join(ParentItem, MoveHistory.parent_item_id == ParentItem.id)
            .join(ItemType, ParentItem.item_type_id == ItemType.id)
            .filter(Location.location_type_id == location_type_id)
        )

        if start_datetime:
            inbound_query = inbound_query.filter(MoveHistory.moved_at >= start_datetime)
        if end_datetime:
            inbound_query = inbound_query.filter(MoveHistory.moved_at <= end_datetime)

        inbound_query = inbound_query.group_by(Location.name, ItemType.name).order_by(
            Location.name, ItemType.name
        )

        inbound_results = inbound_query.all()
        inbound_throughput = [
            ThroughputByLocationItem(
                location_name=row.location_name,
                item_type_name=row.item_type_name,
                count=row.count,
            )
            for row in inbound_results
        ]

        # Get outbound throughput (moves FROM locations of this type)
        outbound_query = (
            db.query(
                Location.name.label("location_name"),
                ItemType.name.label("item_type_name"),
                func.count(MoveHistory.id).label("count"),
            )
            .join(MoveHistory, MoveHistory.from_location_id == Location.id)
            .join(ParentItem, MoveHistory.parent_item_id == ParentItem.id)
            .join(ItemType, ParentItem.item_type_id == ItemType.id)
            .filter(Location.location_type_id == location_type_id)
        )

        if start_datetime:
            outbound_query = outbound_query.filter(
                MoveHistory.moved_at >= start_datetime
            )
        if end_datetime:
            outbound_query = outbound_query.filter(MoveHistory.moved_at <= end_datetime)

        outbound_query = outbound_query.group_by(Location.name, ItemType.name).order_by(
            Location.name, ItemType.name
        )

        outbound_results = outbound_query.all()
        outbound_throughput = [
            ThroughputByLocationItem(
                location_name=row.location_name,
                item_type_name=row.item_type_name,
                count=row.count,
            )
            for row in outbound_results
        ]

        return DashboardData(
            inventory_by_location=inventory_by_location,
            inbound_throughput=inbound_throughput,
            outbound_throughput=outbound_throughput,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error generating dashboard data",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
            location_type_id=str(location_type_id),
            start_date=start_date,
            end_date=end_date,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard data: {str(e)}",
        )
