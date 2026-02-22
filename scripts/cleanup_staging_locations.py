"""Clean up staging locations - keep only Warehouse, Client Site, and Quarantine."""

import requests
import sys

STAGING_URL = "http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com"

def login():
    """Login and get token."""
    response = requests.post(
        f"{STAGING_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
        timeout=10
    )
    return response.json()["access_token"]

def get_headers(token):
    """Get request headers."""
    return {"Authorization": f"Bearer {token}"}

def get_location_types(token):
    """Get all location types."""
    response = requests.get(
        f"{STAGING_URL}/api/v1/location-types",
        headers=get_headers(token),
        timeout=10
    )
    return response.json()

def get_locations_with_items(token):
    """Get all locations with item counts."""
    response = requests.get(
        f"{STAGING_URL}/api/v1/locations/with-items",
        headers=get_headers(token),
        timeout=10
    )
    return response.json()

def get_items_at_location(token, location_id):
    """Get items at a specific location."""
    response = requests.get(
        f"{STAGING_URL}/api/v1/items/parent",
        headers=get_headers(token),
        params={"location_id": location_id, "limit": 1000},
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    return []

def move_item(token, item_id, new_location_id):
    """Move an item to a new location."""
    response = requests.post(
        f"{STAGING_URL}/api/v1/movements/move",
        headers=get_headers(token),
        json={
            "item_id": item_id,
            "to_location_id": new_location_id,
            "notes": "Automated cleanup - consolidating locations"
        },
        timeout=10
    )
    return response.status_code in [200, 201], response

def delete_location(token, location_id):
    """Delete a location."""
    response = requests.delete(
        f"{STAGING_URL}/api/v1/locations/{location_id}",
        headers=get_headers(token),
        timeout=10
    )
    return response.status_code == 200, response

def delete_location_type(token, location_type_id):
    """Delete a location type."""
    response = requests.delete(
        f"{STAGING_URL}/api/v1/location-types/{location_type_id}",
        headers=get_headers(token),
        timeout=10
    )
    return response.status_code == 200, response

def main():
    """Main cleanup function."""
    print("=" * 70)
    print("Staging Location Cleanup")
    print("=" * 70)
    print("\nThis will:")
    print("1. Keep only: Warehouse, Client Site, Quarantine location types")
    print("2. Move all items to appropriate JDM locations")
    print("3. Delete all old locations")
    print("4. Delete all old location types")
    print("=" * 70)
    
    token = login()
    print("\n✓ Logged in")
    
    # Get current state
    print("\nGetting current location types...")
    location_types = get_location_types(token)
    
    # Identify which to keep
    keep_types = {"Warehouse", "Client Site", "Quarantine"}
    keep_type_ids = {}
    delete_type_ids = {}
    
    for lt in location_types:
        if lt['name'] in keep_types:
            keep_type_ids[lt['name']] = lt['id']
            print(f"  ✓ Keeping: {lt['name']}")
        else:
            delete_type_ids[lt['name']] = lt['id']
            print(f"  ✗ Will delete: {lt['name']}")
    
    # Get all locations
    print("\nGetting all locations...")
    locations = get_locations_with_items(token)
    
    # Identify JDM warehouses and other keep locations
    jdm_warehouses = []
    keep_locations = []
    delete_locations = []
    
    for loc in locations:
        loc_type_name = loc.get('location_type', {}).get('name', '')
        
        if loc_type_name in keep_types:
            keep_locations.append(loc)
            if loc_type_name == "Warehouse" and loc['name'].startswith('JDM'):
                jdm_warehouses.append(loc)
                print(f"  ✓ Keeping: {loc['name']} ({loc_type_name})")
        else:
            delete_locations.append(loc)
            print(f"  ✗ Will delete: {loc['name']} ({loc_type_name}) - {loc.get('item_count', 0)} items")
    
    if not jdm_warehouses:
        print("\n✗ No JDM warehouses found! Cannot proceed.")
        sys.exit(1)
    
    # Use first JDM warehouse as default destination
    default_warehouse = jdm_warehouses[0]
    print(f"\nDefault destination: {default_warehouse['name']}")
    
    # Move items from locations to be deleted
    print("\n" + "=" * 70)
    print("Moving items from old locations...")
    print("=" * 70)
    
    total_moved = 0
    for loc in delete_locations:
        item_count = loc.get('item_count', 0)
        if item_count == 0:
            continue
        
        print(f"\nMoving {item_count} items from {loc['name']}...")
        items = get_items_at_location(token, loc['id'])
        
        print(f"  Retrieved {len(items)} items from API")
        
        if len(items) == 0:
            print(f"  ⚠ No items returned from API, but location shows {item_count} items")
            print(f"  This might be a filtering issue. Skipping...")
            continue
        
        moved = 0
        failed = 0
        for item in items:
            success, response = move_item(token, item['id'], default_warehouse['id'])
            if success:
                moved += 1
                print(f"  ✓ Moved: {item.get('name', 'Unknown')}")
            else:
                failed += 1
                print(f"  ✗ Failed: {item.get('name', 'Unknown')} - Status: {response.status_code}")
                if response.status_code != 200:
                    try:
                        error = response.json()
                        print(f"     Error: {error.get('detail', 'Unknown')}")
                    except:
                        pass
        
        total_moved += moved
        print(f"  Summary: {moved} moved, {failed} failed")
    
    print(f"\nTotal items moved: {total_moved}")
    
    # Delete old locations
    print("\n" + "=" * 70)
    print("Deleting old locations...")
    print("=" * 70)
    
    # Refresh location data before attempting deletion
    print("\nRefreshing location data...")
    locations = get_locations_with_items(token)
    delete_locations = [loc for loc in locations if loc.get('location_type', {}).get('name', '') not in keep_types]
    
    deleted_locations = 0
    failed_locations = 0
    
    for loc in delete_locations:
        # Double-check item count before deletion
        item_count = loc.get('item_count', 0)
        print(f"\n  {loc['name']}: {item_count} items")
        
        if item_count > 0:
            print(f"    ⚠ Skipping - still has items")
            failed_locations += 1
            continue
        
        success, response = delete_location(token, loc['id'])
        if success:
            deleted_locations += 1
            print(f"    ✓ Deleted")
        else:
            failed_locations += 1
            print(f"    ✗ Failed")
            try:
                error = response.json()
                print(f"       Error: {error.get('detail', 'Unknown')}")
            except:
                print(f"       Status: {response.status_code}")
    
    print(f"\nLocations deleted: {deleted_locations}/{len(delete_locations)}")
    
    # Delete old location types
    print("\n" + "=" * 70)
    print("Deleting old location types...")
    print("=" * 70)
    
    deleted_types = 0
    failed_types = 0
    
    for type_name, type_id in delete_type_ids.items():
        success, response = delete_location_type(token, type_id)
        if success:
            deleted_types += 1
            print(f"  ✓ Deleted: {type_name}")
        else:
            failed_types += 1
            print(f"  ✗ Failed to delete: {type_name}")
            try:
                error = response.json()
                print(f"     Error: {error.get('detail', 'Unknown')}")
            except:
                print(f"     Status: {response.status_code}")
    
    print(f"\nLocation types deleted: {deleted_types}/{len(delete_type_ids)}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)
    print(f"Items moved: {total_moved}")
    print(f"Locations deleted: {deleted_locations}")
    print(f"Location types deleted: {deleted_types}")
    
    if failed_locations > 0 or failed_types > 0:
        print(f"\n⚠ Some deletions failed:")
        if failed_locations > 0:
            print(f"  - {failed_locations} locations")
        if failed_types > 0:
            print(f"  - {failed_types} location types")
        print("\nYou may need to manually check and delete these.")
    else:
        print("\n✓ All cleanup operations successful!")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
