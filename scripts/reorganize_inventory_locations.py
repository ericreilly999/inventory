#!/usr/bin/env python3
"""
Reorganize inventory locations according to business requirements.

Requirements:
1. Keep only location types: Warehouse, Quarantine, Client Site
2. For Warehouse and Quarantine types, keep only locations with "JDM" in the name
3. Move all inventory from locations to be deleted to appropriate JDM locations
4. Delete empty locations that don't meet criteria
"""

import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from shared.models.item import ParentItem
from shared.models.location import Location, LocationType

# Simple logging
def log(msg):
    print(msg)


def get_or_create_default_jdm_warehouse(session):
    """Get or create a default JDM warehouse for relocated inventory."""
    # Try to find existing JDM warehouse
    jdm_warehouse = (
        session.query(Location)
        .join(LocationType)
        .filter(LocationType.name == "Warehouse")
        .filter(Location.name.ilike("%JDM%"))
        .first()
    )

    if jdm_warehouse:
        log(f"Using existing JDM warehouse: {jdm_warehouse.name}")
        return jdm_warehouse

    # Create a default JDM warehouse if none exists
    warehouse_type = (
        session.query(LocationType).filter(LocationType.name == "Warehouse").first()
    )

    if not warehouse_type:
        log("ERROR: Warehouse location type not found!")
        raise ValueError("Warehouse location type must exist")

    jdm_warehouse = Location(
        name="JDM Main Warehouse",
        description="Default warehouse for relocated inventory",
        location_type_id=warehouse_type.id,
    )
    session.add(jdm_warehouse)
    session.flush()
    log(f"Created default JDM warehouse: {jdm_warehouse.name}")
    return jdm_warehouse


def main():
    """Main execution function."""
    log("=" * 80)
    log("Starting inventory location reorganization")
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
        # Step 1: Identify location types to keep
        log("\n" + "=" * 80)
        log("Step 1: Identifying location types")
        log("=" * 80)

        allowed_types = ["Warehouse", "Quarantine", "Client Site"]
        location_types = session.query(LocationType).all()

        log(f"Total location types: {len(location_types)}")
        for lt in location_types:
            keep = "KEEP" if lt.name in allowed_types else "DELETE"
            log(f"  - {lt.name}: {keep}")

        # Step 2: Identify locations to keep and delete
        log("\n" + "=" * 80)
        log("Step 2: Identifying locations to keep/delete")
        log("=" * 80)

        all_locations = session.query(Location).join(LocationType).all()
        locations_to_keep = []
        locations_to_delete = []

        for location in all_locations:
            location_type_name = location.location_type.name

            # Check if location type is allowed
            if location_type_name not in allowed_types:
                locations_to_delete.append(location)
                log(
                    f"DELETE (wrong type): {location.name} "
                    f"(Type: {location_type_name})"
                )
                continue

            # For Warehouse and Quarantine, must have JDM in name
            if location_type_name in ["Warehouse", "Quarantine"]:
                if "JDM" in location.name.upper():
                    locations_to_keep.append(location)
                    log(
                        f"KEEP: {location.name} (Type: {location_type_name})"
                    )
                else:
                    locations_to_delete.append(location)
                    log(
                        f"DELETE (no JDM): {location.name} "
                        f"(Type: {location_type_name})"
                    )
            else:
                # Client Site - keep all
                locations_to_keep.append(location)
                log(f"KEEP: {location.name} (Type: {location_type_name})")

        log(f"\nSummary:")
        log(f"  Locations to keep: {len(locations_to_keep)}")
        log(f"  Locations to delete: {len(locations_to_delete)}")

        # Step 3: Get or create default JDM warehouse for relocations
        log("\n" + "=" * 80)
        log("Step 3: Preparing default relocation warehouse")
        log("=" * 80)

        default_warehouse = get_or_create_default_jdm_warehouse(session)
        session.commit()

        # Step 4: Move inventory from locations to be deleted
        log("\n" + "=" * 80)
        log("Step 4: Relocating inventory")
        log("=" * 80)

        total_items_moved = 0
        for location in locations_to_delete:
            # Find all parent items at this location
            items = (
                session.query(ParentItem)
                .filter(ParentItem.current_location_id == location.id)
                .all()
            )

            if items:
                log(
                    f"\nRelocating {len(items)} items from "
                    f"'{location.name}' to '{default_warehouse.name}'"
                )

                for item in items:
                    log(f"  - Moving item SKU: {item.sku}")
                    item.current_location_id = default_warehouse.id
                    total_items_moved += 1

        log(f"\nTotal items relocated: {total_items_moved}")
        session.commit()

        # Step 5: Verify no items remain in locations to be deleted
        log("\n" + "=" * 80)
        log("Step 5: Verifying relocation")
        log("=" * 80)

        for location in locations_to_delete:
            item_count = (
                session.query(ParentItem)
                .filter(ParentItem.current_location_id == location.id)
                .count()
            )
            if item_count > 0:
                log(
                    f"ERROR: Location '{location.name}' still has "
                    f"{item_count} items!"
                )
                raise ValueError(
                    f"Failed to relocate all items from {location.name}"
                )
            else:
                log(f"✓ Location '{location.name}' is empty")

        # Step 6: Delete empty locations
        log("\n" + "=" * 80)
        log("Step 6: Deleting empty locations")
        log("=" * 80)

        for location in locations_to_delete:
            log(f"Deleting location: {location.name}")
            session.delete(location)

        session.commit()
        log(f"Deleted {len(locations_to_delete)} locations")

        # Step 7: Delete unused location types
        log("\n" + "=" * 80)
        log("Step 7: Cleaning up unused location types")
        log("=" * 80)

        for location_type in location_types:
            if location_type.name not in allowed_types:
                # Check if any locations still use this type
                location_count = (
                    session.query(Location)
                    .filter(Location.location_type_id == location_type.id)
                    .count()
                )

                if location_count == 0:
                    log(f"Deleting location type: {location_type.name}")
                    session.delete(location_type)
                else:
                    log(
                        f"Cannot delete location type '{location_type.name}' "
                        f"- still has {location_count} locations"
                    )

        session.commit()

        # Step 8: Final summary
        log("\n" + "=" * 80)
        log("Step 8: Final Summary")
        log("=" * 80)

        remaining_types = session.query(LocationType).all()
        log(f"Remaining location types: {len(remaining_types)}")
        for lt in remaining_types:
            location_count = (
                session.query(Location)
                .filter(Location.location_type_id == lt.id)
                .count()
            )
            log(f"  - {lt.name}: {location_count} locations")

        remaining_locations = session.query(Location).all()
        log(f"\nRemaining locations: {len(remaining_locations)}")
        for loc in remaining_locations:
            item_count = (
                session.query(ParentItem)
                .filter(ParentItem.current_location_id == loc.id)
                .count()
            )
            log(
                f"  - {loc.name} ({loc.location_type.name}): "
                f"{item_count} items"
            )

        total_items = session.query(ParentItem).count()
        log(f"\nTotal items in system: {total_items}")

        log("\n" + "=" * 80)
        log("✓ Inventory location reorganization completed successfully!")
        log("=" * 80)

    except Exception as e:
        log(f"Error during reorganization: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
