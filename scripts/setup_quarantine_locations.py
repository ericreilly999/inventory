"""
Setup quarantine locations for each JDM hub.
"""
import os
import sys
import random
import requests

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Staging API Gateway URL
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com/api/v1"
)

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# Global token storage
auth_token = None


def login():
    """Login and get auth token."""
    global auth_token
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    response.raise_for_status()
    auth_token = response.json()["access_token"]
    return auth_token


def get_headers():
    """Get headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


def get_all_locations():
    """Get all locations."""
    response = requests.get(f"{API_BASE_URL}/locations/locations", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else data.get("items", [])


def get_all_location_types():
    """Get all location types."""
    response = requests.get(f"{API_BASE_URL}/locations/types", headers=get_headers())
    response.raise_for_status()
    return response.json()


def get_all_parent_items():
    """Get all parent items."""
    response = requests.get(f"{API_BASE_URL}/items/parent", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else data.get("items", [])


def update_location(location_id, name, description, location_type_id):
    """Update a location."""
    response = requests.put(
        f"{API_BASE_URL}/locations/locations/{location_id}",
        headers=get_headers(),
        json={
            "name": name,
            "description": description,
            "location_type_id": location_type_id
        }
    )
    response.raise_for_status()
    return response.json()


def move_item(parent_item_id, to_location_id, notes=""):
    """Move a parent item to a new location."""
    response = requests.post(
        f"{API_BASE_URL}/movements/move",
        headers=get_headers(),
        json={
            "item_id": parent_item_id,
            "to_location_id": to_location_id,
            "notes": notes
        }
    )
    response.raise_for_status()
    return response.json()


def main():
    """Main function."""
    try:
        login()
        print("✓ Logged in\n")
        
        # Get all data
        locations = get_all_locations()
        location_types = {lt["name"]: lt for lt in get_all_location_types()}
        parent_items = get_all_parent_items()
        
        # Get quarantine location type
        quarantine_type = location_types.get("Quarantine")
        if not quarantine_type:
            print("✗ Quarantine location type not found")
            sys.exit(1)
        
        # Find JDM warehouses and quarantines
        jdm_warehouses = [
            loc for loc in locations 
            if loc.get("location_type", {}).get("name") == "Warehouse" 
            and loc["name"].startswith("JDM")
        ]
        
        jdm_quarantines = [
            loc for loc in locations 
            if loc.get("location_type", {}).get("name") == "Quarantine"
            and loc["name"].startswith("JDM")
        ]
        
        print(f"Found {len(jdm_warehouses)} JDM warehouses")
        print(f"Found {len(jdm_quarantines)} existing JDM quarantine locations\n")
        
        # Map quarantines to hubs
        hub_names = ["Austin", "Tampa", "Chicago", "Las Vegas", "NY"]
        quarantine_map = {}
        
        print("=== Renaming Quarantine Locations ===\n")
        
        for i, hub in enumerate(hub_names):
            new_name = f"JDM {hub} - Quarantine"
            
            if i < len(jdm_quarantines):
                # Update existing quarantine
                old_loc = jdm_quarantines[i]
                updated_loc = update_location(
                    old_loc["id"],
                    new_name,
                    f"Quarantine area for JDM {hub}",
                    quarantine_type["id"]
                )
                quarantine_map[hub] = updated_loc
                print(f"  ✓ Renamed '{old_loc['name']}' to '{new_name}'")
            else:
                print(f"  ⚠ No quarantine location available for {hub}")
        
        print(f"\n✓ Renamed {len(quarantine_map)} quarantine locations\n")
        
        # Now move 1-3 items from each warehouse to its quarantine
        print("=== Moving Items to Quarantine ===\n")
        
        total_moved = 0
        for warehouse in jdm_warehouses:
            # Extract hub name from warehouse name (e.g., "JDM Austin" -> "Austin")
            hub = warehouse["name"].replace("JDM ", "")
            
            if hub not in quarantine_map:
                print(f"  ⚠ No quarantine location for {hub}")
                continue
            
            quarantine_loc = quarantine_map[hub]
            
            # Find items at this warehouse (excluding Shelf Stock)
            warehouse_items = [
                item for item in parent_items
                if item["current_location"]["id"] == warehouse["id"]
                and item.get("item_type", {}).get("name") != "Shelf Stock"
            ]
            
            if not warehouse_items:
                print(f"  ⚠ No items at {warehouse['name']} to move")
                continue
            
            # Move 1-3 random items to quarantine
            num_to_move = min(random.randint(1, 3), len(warehouse_items))
            items_to_move = random.sample(warehouse_items, num_to_move)
            
            for item in items_to_move:
                try:
                    move_item(
                        item["id"],
                        quarantine_loc["id"],
                        f"Moved to quarantine for inspection"
                    )
                    total_moved += 1
                    
                    item_type = item.get("item_type", {}).get("name", "Unknown")
                    print(f"  ✓ Moved {item_type} (SKU: {item['sku']}) from {warehouse['name']} to {quarantine_loc['name']}")
                    
                except Exception as e:
                    print(f"  ✗ Failed to move item {item['sku']}: {e}")
        
        print(f"\n{'='*50}")
        print("QUARANTINE SETUP COMPLETE!")
        print(f"{'='*50}")
        print(f"✓ Quarantine locations configured: {len(quarantine_map)}")
        print(f"✓ Items moved to quarantine: {total_moved}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
