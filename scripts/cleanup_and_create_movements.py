"""
Cleanup duplicate SKUs and create hospital locations with movements.
"""
import requests
import random
import time

# API Configuration
API_BASE_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"
USERNAME = "admin"
PASSWORD = "admin"

# Global session with auth token
session = requests.Session()


def login():
    """Login and get access token."""
    print("Logging in...")
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("Login successful!\n")


def get_all_parent_items():
    """Get all parent items."""
    response = session.get(f"{API_BASE_URL}/api/v1/items/parent?limit=1000")
    if response.status_code != 200:
        raise Exception(f"Failed to get parent items: {response.text}")
    return response.json()


def get_all_child_items():
    """Get all child items."""
    response = session.get(f"{API_BASE_URL}/api/v1/items/child?limit=1000")
    if response.status_code != 200:
        raise Exception(f"Failed to get child items: {response.text}")
    return response.json()


def delete_parent_item(item_id: str):
    """Delete a parent item."""
    response = session.delete(f"{API_BASE_URL}/api/v1/items/parent/{item_id}")
    if response.status_code in [200, 204]:
        return True
    else:
        print(f"Warning: Failed to delete parent item {item_id}: {response.text[:200]}")
        return False


def delete_child_item(item_id: str):
    """Delete a child item."""
    response = session.delete(f"{API_BASE_URL}/api/v1/items/child/{item_id}")
    if response.status_code in [200, 204]:
        return True
    else:
        print(f"Warning: Failed to delete child item {item_id}: {response.text[:200]}")
        return False


def get_location_types():
    """Get all location types."""
    response = session.get(f"{API_BASE_URL}/api/v1/locations/types")
    if response.status_code != 200:
        raise Exception(f"Failed to get location types: {response.text}")
    return response.json()


def create_location(name: str, location_type_id: str, address: str = ""):
    """Create a location."""
    response = session.post(
        f"{API_BASE_URL}/api/v1/locations/locations",
        json={"name": name, "location_type_id": location_type_id, "address": address}
    )
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Warning: Failed to create location {name}: {response.text[:200]}")
        return None


def get_all_locations():
    """Get all locations."""
    response = session.get(f"{API_BASE_URL}/api/v1/locations/locations")
    if response.status_code != 200:
        raise Exception(f"Failed to get locations: {response.text}")
    return response.json()


def move_parent_item(parent_item_id: str, to_location_id: str, notes: str = ""):
    """Move a parent item to a new location."""
    response = session.post(
        f"{API_BASE_URL}/api/v1/movements",
        json={
            "parent_item_id": parent_item_id,
            "to_location_id": to_location_id,
            "notes": notes
        }
    )
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Warning: Failed to move item: {response.text[:200]}")
        return None


def cleanup_duplicates():
    """Remove duplicate SKUs, keeping only the first occurrence."""
    print("=" * 60)
    print("CLEANING UP DUPLICATE SKUs")
    print("=" * 60)
    
    # Get all parent items
    print("\nFetching parent items...")
    parent_items = get_all_parent_items()
    print(f"Found {len(parent_items)} parent items")
    
    # Find duplicates
    sku_map = {}
    duplicates_to_delete = []
    
    for item in parent_items:
        sku = item['sku']
        if sku in sku_map:
            # This is a duplicate
            duplicates_to_delete.append(item)
            print(f"  Duplicate parent SKU found: {sku} (ID: {item['id']})")
        else:
            sku_map[sku] = item
    
    # Delete duplicates
    print(f"\nDeleting {len(duplicates_to_delete)} duplicate parent items...")
    for item in duplicates_to_delete:
        if delete_parent_item(item['id']):
            print(f"  Deleted parent item: {item['sku']} (ID: {item['id']})")
        time.sleep(0.5)
    
    # Get all child items
    print("\nFetching child items...")
    child_items = get_all_child_items()
    print(f"Found {len(child_items)} child items")
    
    # Find duplicates
    sku_map = {}
    duplicates_to_delete = []
    
    for item in child_items:
        sku = item['sku']
        if sku in sku_map:
            # This is a duplicate
            duplicates_to_delete.append(item)
            print(f"  Duplicate child SKU found: {sku} (ID: {item['id']})")
        else:
            sku_map[sku] = item
    
    # Delete duplicates
    print(f"\nDeleting {len(duplicates_to_delete)} duplicate child items...")
    for item in duplicates_to_delete:
        if delete_child_item(item['id']):
            print(f"  Deleted child item: {item['sku']} (ID: {item['id']})")
        time.sleep(0.5)
    
    print("\nDuplicate cleanup complete!")


def create_hospital_locations():
    """Create hospital locations."""
    print("\n" + "=" * 60)
    print("CREATING HOSPITAL LOCATIONS")
    print("=" * 60)
    
    # Get location types
    location_types = get_location_types()
    client_site_type = next((lt for lt in location_types if lt['name'] == "Client Site"), None)
    
    if not client_site_type:
        raise Exception("Client Site location type not found")
    
    hospitals = []
    hospital_names = ["Hospital A", "Hospital B", "Hospital C", "Hospital D", "Hospital E"]
    
    for hospital_name in hospital_names:
        print(f"\nCreating {hospital_name}...")
        hospital = create_location(
            name=hospital_name,
            location_type_id=client_site_type['id'],
            address=f"{hospital_name} Medical Center"
        )
        if hospital:
            hospitals.append(hospital)
            print(f"  Created: {hospital_name}")
        time.sleep(0.5)
    
    print(f"\nCreated {len(hospitals)} hospital locations")
    return hospitals


def create_movements_to_hospitals(hospitals):
    """Create movements from warehouses to hospitals."""
    print("\n" + "=" * 60)
    print("CREATING MOVEMENTS TO HOSPITALS")
    print("=" * 60)
    
    # Get all locations
    all_locations = get_all_locations()
    warehouse_locations = [loc for loc in all_locations if loc['location_type']['name'] == "Warehouse"]
    
    # Re-fetch all parent items after cleanup
    parent_items = get_all_parent_items()
    warehouse_items = [item for item in parent_items if any(loc['id'] == item['current_location_id'] for loc in warehouse_locations)]
    
    print(f"\nFound {len(warehouse_items)} items in warehouses")
    print(f"Moving items to {len(hospitals)} hospitals...")
    
    movements_created = 0
    
    # Move 3-5 items to each hospital
    for hospital in hospitals:
        if not warehouse_items:
            print(f"\nNo more warehouse items available")
            break
            
        num_items_to_move = min(random.randint(3, 5), len(warehouse_items))
        items_to_move = random.sample(warehouse_items, num_items_to_move)
        
        print(f"\nMoving {len(items_to_move)} items to {hospital['name']}:")
        for item in items_to_move:
            movement = move_parent_item(
                parent_item_id=item['id'],
                to_location_id=hospital['id'],
                notes=f"Deployed to {hospital['name']}"
            )
            if movement:
                print(f"  Moved {item['sku']} ({item['item_type']['name']}) to {hospital['name']}")
                movements_created += 1
                # Remove from warehouse_items so we don't move it again
                warehouse_items.remove(item)
            time.sleep(1.0)
    
    print(f"\nCreated {movements_created} movements to hospitals")


def create_additional_movements():
    """Create additional random movements for movement history."""
    print("\n" + "=" * 60)
    print("CREATING ADDITIONAL MOVEMENTS")
    print("=" * 60)
    
    # Re-fetch all locations and parent items after previous operations
    all_locations = get_all_locations()
    parent_items = get_all_parent_items()
    
    if not parent_items:
        print("\nNo parent items available for movements")
        return
    
    print(f"\nCreating 50 random movements...")
    movements_created = 0
    
    for i in range(50):
        # Select random item and location
        item = random.choice(parent_items)
        current_location_id = item['current_location_id']
        
        # Select a different location
        available_locations = [loc for loc in all_locations if loc['id'] != current_location_id]
        if not available_locations:
            continue
        
        to_location = random.choice(available_locations)
        
        movement = move_parent_item(
            parent_item_id=item['id'],
            to_location_id=to_location['id'],
            notes=f"Movement #{i+1}"
        )
        
        if movement:
            # Update local copy
            item['current_location_id'] = to_location['id']
            movements_created += 1
            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1} movements...")
        
        time.sleep(1.0)
    
    print(f"\nCreated {movements_created} additional movements")


def main():
    """Main function."""
    try:
        print("Starting cleanup and movement creation...\n")
        
        # Login
        login()
        
        # Step 1: Cleanup duplicates
        cleanup_duplicates()
        
        # Step 2: Create hospital locations
        hospitals = create_hospital_locations()
        
        # Step 3: Move items to hospitals
        if hospitals:
            create_movements_to_hospitals(hospitals)
        
        # Step 4: Create additional movements
        create_additional_movements()
        
        print("\n" + "=" * 60)
        print("ALL OPERATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
