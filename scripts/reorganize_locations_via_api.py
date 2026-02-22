#!/usr/bin/env python3
"""
Reorganize inventory locations using the API.

This script can be run locally and will work against any environment
by hitting the public API endpoints.

Usage:
    # Preview changes
    python scripts/reorganize_locations_via_api.py --preview

    # Execute changes
    python scripts/reorganize_locations_via_api.py --execute

    # Specify custom API URL
    python scripts/reorganize_locations_via_api.py --preview --api-url https://staging.example.com
"""

import argparse
import getpass
import sys
from typing import Dict, List, Optional

import requests


class LocationReorganizer:
    def __init__(self, api_url: str, username: str, password: str):
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()

    def login(self) -> bool:
        """Authenticate and get JWT token."""
        print(f"Authenticating as {self.username}...")
        
        try:
            response = self.session.post(
                f"{self.api_url}/api/auth/login",
                json={"username": self.username, "password": self.password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✓ Authentication successful")
                return True
            else:
                print(f"✗ Authentication failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False

    def get_location_types(self) -> List[Dict]:
        """Get all location types."""
        response = self.session.get(f"{self.api_url}/api/location-types")
        response.raise_for_status()
        return response.json()

    def get_locations(self) -> List[Dict]:
        """Get all locations with item counts."""
        response = self.session.get(f"{self.api_url}/api/locations/with-items?limit=1000")
        response.raise_for_status()
        return response.json()

    def get_location_items(self, location_id: str) -> List[Dict]:
        """Get all items at a location."""
        response = self.session.get(f"{self.api_url}/api/locations/{location_id}/items")
        response.raise_for_status()
        return response.json()

    def move_item(self, item_id: str, to_location_id: str, notes: str = "") -> bool:
        """Move an item to a new location."""
        try:
            response = self.session.post(
                f"{self.api_url}/api/movements/move",
                json={
                    "item_id": item_id,
                    "to_location_id": to_location_id,
                    "notes": notes
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"  ✗ Failed to move item {item_id}: {e}")
            return False

    def delete_location(self, location_id: str) -> bool:
        """Delete a location."""
        try:
            response = self.session.delete(f"{self.api_url}/api/locations/{location_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"  ✗ Failed to delete location: {e}")
            return False

    def delete_location_type(self, location_type_id: str) -> bool:
        """Delete a location type."""
        try:
            response = self.session.delete(f"{self.api_url}/api/location-types/{location_type_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"  ✗ Failed to delete location type: {e}")
            return False

    def create_jdm_warehouse(self, warehouse_type_id: str) -> Optional[Dict]:
        """Create a default JDM warehouse."""
        try:
            response = self.session.post(
                f"{self.api_url}/api/locations",
                json={
                    "name": "JDM Main Warehouse",
                    "description": "Default warehouse for relocated inventory",
                    "location_type_id": warehouse_type_id
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ✗ Failed to create JDM warehouse: {e}")
            return None

    def preview(self):
        """Preview what changes will be made."""
        print("\n" + "=" * 80)
        print("PREVIEW: Location Reorganization")
        print("=" * 80)

        # Get location types
        print("\nFetching location types...")
        location_types = self.get_location_types()
        
        allowed_types = ["Warehouse", "Quarantine", "Client Site"]
        types_to_keep = []
        types_to_delete = []

        print("\nLocation Types:")
        print("-" * 80)
        for lt in location_types:
            if lt["name"] in allowed_types:
                types_to_keep.append(lt)
                print(f"  [KEEP] {lt['name']}")
            else:
                types_to_delete.append(lt)
                print(f"  [DELETE] {lt['name']}")

        # Get locations
        print("\nFetching locations...")
        locations = self.get_locations()

        locations_to_keep = []
        locations_to_delete = []
        total_items_to_move = 0

        print("\nLocation Analysis:")
        print("-" * 80)
        
        for location in locations:
            location_type_name = location["location_type"]["name"]
            item_count = location.get("item_count", 0)
            
            should_keep = False
            reason = ""

            if location_type_name not in allowed_types:
                reason = f"Wrong type: {location_type_name}"
            elif location_type_name in ["Warehouse", "Quarantine"]:
                if "JDM" in location["name"].upper():
                    should_keep = True
                    reason = "JDM location"
                else:
                    reason = "No JDM in name"
            else:  # Client Site
                should_keep = True
                reason = "Client Site (keep all)"

            if should_keep:
                locations_to_keep.append(location)
                print(f"  [KEEP] {location['name']} ({location_type_name}) - {item_count} items - {reason}")
            else:
                locations_to_delete.append(location)
                total_items_to_move += item_count
                print(f"  [DELETE] {location['name']} ({location_type_name}) - {item_count} items - {reason}")

        # Find JDM warehouse
        print("\nRelocation Target:")
        print("-" * 80)
        
        jdm_warehouse = None
        for loc in locations_to_keep:
            if loc["location_type"]["name"] == "Warehouse" and "JDM" in loc["name"].upper():
                jdm_warehouse = loc
                break

        if jdm_warehouse:
            current_items = jdm_warehouse.get("item_count", 0)
            print(f"  Existing JDM Warehouse: {jdm_warehouse['name']}")
            print(f"  Current items: {current_items}")
            print(f"  After relocation: {current_items + total_items_to_move}")
        else:
            print("  No existing JDM warehouse found")
            print("  Will create: 'JDM Main Warehouse'")
            print(f"  Items to relocate: {total_items_to_move}")

        # Summary
        print("\n" + "=" * 80)
        print("Summary:")
        print("=" * 80)
        print(f"Location types to keep: {len(types_to_keep)}")
        print(f"Location types to delete: {len(types_to_delete)}")
        print(f"Locations to keep: {len(locations_to_keep)}")
        print(f"Locations to delete: {len(locations_to_delete)}")
        print(f"Items to relocate: {total_items_to_move}")

        print("\n" + "=" * 80)
        print("This is a PREVIEW only - no changes have been made")
        print("Run with --execute to apply changes")
        print("=" * 80)

    def execute(self):
        """Execute the reorganization."""
        print("\n" + "=" * 80)
        print("EXECUTING: Location Reorganization")
        print("=" * 80)

        # Get location types
        print("\nStep 1: Fetching location types...")
        location_types = self.get_location_types()
        
        allowed_types = ["Warehouse", "Quarantine", "Client Site"]
        warehouse_type = None
        types_to_delete = []

        for lt in location_types:
            if lt["name"] == "Warehouse":
                warehouse_type = lt
            elif lt["name"] not in allowed_types:
                types_to_delete.append(lt)

        if not warehouse_type:
            print("✗ ERROR: Warehouse location type not found!")
            return False

        # Get locations
        print("\nStep 2: Fetching locations...")
        locations = self.get_locations()

        locations_to_keep = []
        locations_to_delete = []

        for location in locations:
            location_type_name = location["location_type"]["name"]
            
            should_keep = False

            if location_type_name not in allowed_types:
                should_keep = False
            elif location_type_name in ["Warehouse", "Quarantine"]:
                should_keep = "JDM" in location["name"].upper()
            else:  # Client Site
                should_keep = True

            if should_keep:
                locations_to_keep.append(location)
            else:
                locations_to_delete.append(location)

        print(f"  Locations to keep: {len(locations_to_keep)}")
        print(f"  Locations to delete: {len(locations_to_delete)}")

        # Find or create JDM warehouse
        print("\nStep 3: Preparing relocation target...")
        jdm_warehouse = None
        for loc in locations_to_keep:
            if loc["location_type"]["name"] == "Warehouse" and "JDM" in loc["name"].upper():
                jdm_warehouse = loc
                break

        if jdm_warehouse:
            print(f"  Using existing JDM warehouse: {jdm_warehouse['name']}")
        else:
            print("  Creating JDM Main Warehouse...")
            jdm_warehouse = self.create_jdm_warehouse(warehouse_type["id"])
            if not jdm_warehouse:
                print("✗ ERROR: Failed to create JDM warehouse!")
                return False
            print(f"  ✓ Created: {jdm_warehouse['name']}")

        # Move items from locations to be deleted
        print("\nStep 4: Relocating items...")
        total_moved = 0
        total_failed = 0

        for location in locations_to_delete:
            item_count = location.get("item_count", 0)
            if item_count == 0:
                continue

            print(f"\n  Processing: {location['name']} ({item_count} items)")
            
            # Get items at this location
            items = self.get_location_items(location["id"])
            
            for item in items:
                if self.move_item(
                    item["id"],
                    jdm_warehouse["id"],
                    f"Relocated during location reorganization from {location['name']}"
                ):
                    total_moved += 1
                    print(f"    ✓ Moved item {item.get('name', item['id'])}")
                else:
                    total_failed += 1

        print(f"\n  Total items moved: {total_moved}")
        if total_failed > 0:
            print(f"  Failed moves: {total_failed}")

        # Delete empty locations
        print("\nStep 5: Deleting empty locations...")
        deleted_count = 0
        failed_count = 0

        for location in locations_to_delete:
            print(f"  Deleting: {location['name']}")
            if self.delete_location(location["id"]):
                deleted_count += 1
                print(f"    ✓ Deleted")
            else:
                failed_count += 1

        print(f"\n  Locations deleted: {deleted_count}")
        if failed_count > 0:
            print(f"  Failed deletions: {failed_count}")

        # Delete unused location types
        print("\nStep 6: Deleting unused location types...")
        deleted_types = 0

        for lt in types_to_delete:
            print(f"  Deleting location type: {lt['name']}")
            if self.delete_location_type(lt["id"]):
                deleted_types += 1
                print(f"    ✓ Deleted")

        print(f"\n  Location types deleted: {deleted_types}")

        # Final summary
        print("\n" + "=" * 80)
        print("✓ Location reorganization completed!")
        print("=" * 80)
        print(f"Items relocated: {total_moved}")
        print(f"Locations deleted: {deleted_count}")
        print(f"Location types deleted: {deleted_types}")
        
        if total_failed > 0 or failed_count > 0:
            print(f"\n⚠ Some operations failed - check logs above")
            return False
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize inventory locations via API"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview changes without executing"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the reorganization"
    )
    parser.add_argument(
        "--api-url",
        default="https://staging.inventory.example.com",
        help="API base URL (default: staging)"
    )
    parser.add_argument(
        "--username",
        help="Username for authentication (will prompt if not provided)"
    )
    parser.add_argument(
        "--password",
        help="Password for authentication (will prompt if not provided)"
    )

    args = parser.parse_args()

    if not args.preview and not args.execute:
        print("Error: Must specify either --preview or --execute")
        parser.print_help()
        sys.exit(1)

    if args.preview and args.execute:
        print("Error: Cannot specify both --preview and --execute")
        sys.exit(1)

    # Get credentials
    username = args.username or input("Username: ")
    password = args.password or getpass.getpass("Password: ")

    # Create reorganizer
    reorganizer = LocationReorganizer(args.api_url, username, password)

    # Authenticate
    if not reorganizer.login():
        print("\n✗ Failed to authenticate")
        sys.exit(1)

    # Execute action
    try:
        if args.preview:
            reorganizer.preview()
        else:
            success = reorganizer.execute()
            sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
