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
from shared.models.item import ChildItem, ItemType, ParentItem
from shared.models.location import Location
from shared.models.move_history import MoveHistory

from ..dependencies import require_reports_read
from ..schemas import (
    InventoryCountByLocationAndType,
    InventoryCountByType,
    InventoryCountReport,
    InventoryStatusByLocation,
    InventoryStatusReport,
    ItemTypeSummary,
    LocationSummary,
    MovementHistoryReport,
    MovementRecord,
    UserSummary,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/inventory/status",
    response_model=InventoryStatusReport,
    summary="Get inventory status report",
    description="Generate a report showing current inventory status by location",
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
                        "name": item.name,
                        "description": item.description,
                        "item_type": item.item_type.name,
                        "child_items_count": len(item.child_items),
                        "child_items": [
                            {
                                "id": str(child.id),
                                "name": child.name,
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
    description="Generate a report showing item movement history with optional date filtering",
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
                    parent_item_name=movement.parent_item.name,
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
    description="Generate a report showing inventory counts by item type and location type",
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
        # Get counts by item type
        item_type_query = (
            db.query(
                ItemType,
                func.count(func.distinct(ParentItem.id)).label("parent_count"),
                func.count(func.distinct(ChildItem.id)).label("child_count"),
            )
            .outerjoin(ParentItem, ParentItem.item_type_id == ItemType.id)
            .outerjoin(ChildItem, ChildItem.parent_item_id == ParentItem.id)
        )

        if item_type_ids:
            item_type_query = item_type_query.filter(ItemType.id.in_(item_type_ids))

        item_type_counts = item_type_query.group_by(ItemType.id).all()

        by_item_type = []
        for item_type, parent_count, child_count in item_type_counts:
            by_item_type.append(
                InventoryCountByType(
                    item_type=ItemTypeSummary(
                        id=item_type.id,
                        name=item_type.name,
                        category=item_type.category.value,
                    ),
                    parent_items_count=parent_count or 0,
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

        return InventoryCountReport(
            generated_at=datetime.now(timezone.utc),
            by_item_type=by_item_type,
            by_location_and_type=by_location_and_type,
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
                "parent_item_name": item.name,
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
                            "child_item_name": child.name,
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
                        "child_item_name": None,
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
