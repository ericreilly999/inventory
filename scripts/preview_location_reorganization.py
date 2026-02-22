#!/usr/bin/env python3
"""
Preview inventory location reorganization without making changes.

This script shows what will happen when reorganize_inventory_locations.py runs.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models.item import ParentItem
from shared.models.location import Location, LocationType

# Simple logging
def log(msg):
    print(msg)


def main():
    """Preview the reorganization."""
    log("=" * 80)
    log("PREVIEW: Inventory Location Reorganization")
    log("=" * 80)

    # Get database URL from environment
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    log(f"Using DATABASE_URL: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Identify location types
        log("\nCurrent Location Types:")
        log("-" * 80)

        allowed_types = ["Warehouse", "Quarantine", "Client Site"]
        location_types = session.query(LocationType).all()

        for lt in location_types:
            location_count = (
                session.query(Location)
                .filter(Location.location_type_id == lt.id)
                .count()
            )
            action = "KEEP" if lt.name in allowed_types else "DELETE"
            log(
                f"  [{action}] {lt.name}: {location_count} locations"
            )

        # Analyze locations
        log("\nLocation Analysis:")
        log("-" * 80)

        all_locations = session.query(Location).join(LocationType).all()
        locations_to_keep = []
        locations_to_delete = []
        items_to_relocate = 0

        for location in all_locations:
            location_type_name = location.location_type.name
            item_count = (
                session.query(ParentItem)
                .filter(ParentItem.current_location_id == location.id)
                .count()
            )

            # Determine if location should be kept
            should_keep = False
            reason = ""

            if location_type_name not in allowed_types:
                reason = f"Wrong type: {location_type_name}"
            elif location_type_name in ["Warehouse", "Quarantine"]:
                if "JDM" in location.name.upper():
                    should_keep = True
                    reason = "JDM location"
                else:
                    reason = "No JDM in name"
            else:  # Client Site
                should_keep = True
                reason = "Client Site (keep all)"

            if should_keep:
                locations_to_keep.append(location)
                log(
                    f"  [KEEP] {location.name} ({location_type_name})"
                    f" - {item_count} items - {reason}"
                )
            else:
                locations_to_delete.append(location)
                items_to_relocate += item_count
                log(
                    f"  [DELETE] {location.name} ({location_type_name})"
                    f" - {item_count} items - {reason}"
                )

        # Check for existing JDM warehouse
        log("\nRelocation Target:")
        log("-" * 80)

        jdm_warehouse = (
            session.query(Location)
            .join(LocationType)
            .filter(LocationType.name == "Warehouse")
            .filter(Location.name.ilike("%JDM%"))
            .first()
        )

        if jdm_warehouse:
            current_items = (
                session.query(ParentItem)
                .filter(ParentItem.current_location_id == jdm_warehouse.id)
                .count()
            )
            log(
                f"  Existing JDM Warehouse: {jdm_warehouse.name}"
            )
            log(f"  Current items: {current_items}")
            log(
                f"  After relocation: {current_items + items_to_relocate}"
            )
        else:
            log(
                "  No existing JDM warehouse found"
            )
            log(
                "  Will create: 'JDM Main Warehouse'"
            )
            log(f"  Items to relocate: {items_to_relocate}")

        # Summary
        log("\nSummary:")
        log("=" * 80)
        log(f"Locations to keep: {len(locations_to_keep)}")
        log(f"Locations to delete: {len(locations_to_delete)}")
        log(f"Items to relocate: {items_to_relocate}")

        log("\nLocations that will be kept:")
        for loc in locations_to_keep:
            item_count = (
                session.query(ParentItem)
                .filter(ParentItem.current_location_id == loc.id)
                .count()
            )
            log(
                f"  - {loc.name} ({loc.location_type.name}): "
                f"{item_count} items"
            )

        log("\nLocations that will be deleted:")
        for loc in locations_to_delete:
            item_count = (
                session.query(ParentItem)
                .filter(ParentItem.current_location_id == loc.id)
                .count()
            )
            log(
                f"  - {loc.name} ({loc.location_type.name}): "
                f"{item_count} items → will be moved"
            )

        log("\n" + "=" * 80)
        log("This is a PREVIEW only - no changes have been made")
        log("Run 'reorganize_inventory_locations.py' to apply changes")
        log("=" * 80)

    except Exception as e:
        log(f"Error during preview: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
