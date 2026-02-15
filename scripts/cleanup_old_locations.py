"""
Clean up old locations and location types, moving all inventory to new JDM locations.
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


def delete_location(location_id):
    """Delete a location."""
    response = requests.delete(
        f"{API_BASE_URL}/locations/locations/{location_id}",
        headers=get_headers()
    )
    response.raise_for_status()
    return response.json()


def delete_location_type(location_type_id):
    """Delete a location type."""
    response = requests.delete(
        f"{API_BASE_URL}/locations/types/{location_type_id}",
        headers=get_headers()
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
        location_types = get_all_location_types()
        parent_items = get_all_parent_items()
        
        # Define what we want to keep
        KEEP_LOCATION_TYPES = {"Warehouse", "Client Site", "Quarantine"}
        
        # Organize locations by type
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
        
        client_sites = [
            loc for loc in locations 
            if loc.get("location_type", {}).get("name") == "Client Site"
            and loc["name"] in ["Hospital A", "Hospital B", "Surgery Center C"]
        ]
        
        print(f"Target locations:")
        print(f"  - JDM Warehouses: {len(jdm_warehouses)}")
        print(f"  - JDM Quarantines: {len(jdm_quarantines)}")
        print(f"  - Client Sites: {len(client_sites)}\n")
        
        # Find items at old locations
        items_to_move = []
        for item in parent_items:
            current_loc = item.get("current_location", {})
            current_loc_type = current_loc.get("location_type", {}).get("name", "")
            current_loc_name = current_loc.get("name", "")
            
            # Check if item is at an old location
            is_old_warehouse = (
                current_loc_type == "Warehouse" 
                and not current_loc_name.startswith("JDM")
            )
            
            is_old_quarantine = current_loc_type in [
                "Quarantine - Damage", 
                "Quarantine - Repair", 
                "Quarantine - Cleaning"
            ]
            
            is_old_other = current_loc_type in ["Office", "Storage Room"]
            
            is_old_client = (
                current_loc_type == "Client Site" 
                and current_loc_name not in ["Hospital A", "Hospital B", "Surgery Center C"]
            )
            
            if is_old_warehouse or is_old_quarantine or is_old_other or is_old_client:
                items_to_move.append({
                    "item": item,
                    "reason": "old_warehouse" if is_old_warehouse 
                             else "old_quarantine" if is_old_quarantine
                             else "old_client" if is_old_client
                             else "old_other"
                })
        
        print(f"=== Moving {len(items_to_move)} Items from Old Locations ===\n")
        
        moved_count = 0
        for item_info in items_to_move:
            item = item_info["item"]
            reason = item_info["reason"]
            
            # Determine new location based on reason
            if reason == "old_warehouse":
                new_location = random.choice(jdm_warehouses)
            elif reason == "old_quarantine":
                new_location = random.choice(jdm_quarantines)
            elif reason == "old_client":
                new_location = random.choice(client_sites)
            else:  # old_other (Office, Storage Room)
                new_location = random.choice(jdm_warehouses)
            
            try:
                move_item(
                    item["id"],
                    new_location["id"],
                    "Cleanup: Moving from old location"
                )
                moved_count += 1
                
                item_type = item.get("item_type", {}).get("name", "Unknown")
                old_loc = item["current_location"]["name"]
                print(f"  ✓ Moved {item_type} (SKU: {item['sku']}) from {old_loc} to {new_location['name']}")
                
                if moved_count % 10 == 0:
                    print(f"    ... {moved_count} items moved so far")
                
            except Exception as e:
                print(f"  ✗ Failed to move item {item['sku']}: {e}")
        
        print(f"\n✓ Moved {moved_count} items\n")
        
        # Refresh locations to see which are now empty
        locations = get_all_locations()
        
        # Find old locations to delete
        old_locations = []
        for loc in locations:
            loc_type = loc.get("location_type", {}).get("name", "")
            loc_name = loc.get("name", "")
            
            # Skip if it's a location we want to keep
            if loc_type == "Warehouse" and loc_name.startswith("JDM"):
                continue
            if loc_type == "Quarantine" and loc_name.startswith("JDM"):
                continue
            if loc_type == "Client Site" and loc_name in ["Hospital A", "Hospital B", "Surgery Center C"]:
                continue
            
            # This is an old location
            old_locations.append(loc)
        
        print(f"=== Deleting {len(old_locations)} Old Locations ===\n")
        
        deleted_locs = 0
        for loc in old_locations:
            try:
                delete_location(loc["id"])
                deleted_locs += 1
                print(f"  ✓ Deleted location: {loc['name']} ({loc.get('location_type', {}).get('name', 'Unknown')})")
            except Exception as e:
                if "409" in str(e) or "Conflict" in str(e):
                    print(f"  ⚠ Cannot delete {loc['name']}: Has historical data (this is OK)")
                else:
                    print(f"  ✗ Failed to delete {loc['name']}: {e}")
        
        print(f"\n✓ Deleted {deleted_locs} old locations\n")
        
        # Find old location types to delete
        old_location_types = []
        for lt in location_types:
            if lt["name"] not in KEEP_LOCATION_TYPES:
                old_location_types.append(lt)
        
        print(f"=== Deleting {len(old_location_types)} Old Location Types ===\n")
        
        deleted_types = 0
        for lt in old_location_types:
            try:
                delete_location_type(lt["id"])
                deleted_types += 1
                print(f"  ✓ Deleted location type: {lt['name']}")
            except Exception as e:
                if "409" in str(e) or "Conflict" in str(e):
                    print(f"  ⚠ Cannot delete {lt['name']}: Has historical data (this is OK)")
                else:
                    print(f"  ✗ Failed to delete {lt['name']}: {e}")
        
        print(f"\n✓ Deleted {deleted_types} old location types\n")
        
        print("="*50)
        print("CLEANUP COMPLETE!")
        print("="*50)
        print(f"✓ Items moved: {moved_count}")
        print(f"✓ Locations deleted: {deleted_locs}")
        print(f"✓ Location types deleted: {deleted_types}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
