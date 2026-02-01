"""
Cleanup improperly named items and create movements.
- Delete parent items with SKUs containing item type names (e.g., "Sports Tower-1")
- Keep parent items with simple numeric SKUs (e.g., "1", "2", "3")
- Delete child items with item type names in SKUs
- Keep child items with serial number format SKUs
- Create movements for remaining items
"""
import requests
import random
import time

# API Configuration
API_BASE_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"
USERNAME = "admin"
PASSWORD = "admin"

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
    return response.status_code in [200, 204]


def delete_child_item(item_id: str):
    """Delete a child item."""
    response = session.delete(f"{API_BASE_URL}/api/v1/items/child/{item_id}")
    return response.status_code in [200, 204]


def get_all_locations():
    """Get all locations."""
    response = session.get(f"{API_BASE_URL}/api/v1/locations/locations")
    if response.status_code != 200:
        raise Exception(f"Failed to get locations: {response.text}")
    return response.json()


def move_parent_item(parent_item_id: str, to_location_id: str, notes: str = ""):
    """Move a parent item."""
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
    return None


def is_bad_parent_sku(sku: str) -> bool:
    """Check if parent SKU contains item type name (bad format)."""
    # Bad SKUs contain letters or hyphens (e.g., "Sports Tower-1", "RISE Tower-2")
    # Good SKUs are just numbers (e.g., "1", "2", "3")
    return not sku.isdigit()


def is_bad_child_sku(sku: str) -> bool:
    """Check if child SKU contains item type name (bad format)."""
    # Bad SKUs contain item type names with hyphens (e.g., "Crossfire-1")
    # Good SKUs are serial numbers (e.g., "2204FE3842")
    # Serial numbers should be 10 characters: 4 digits + 6 hex
    if '-' in sku:
        return True
    if len(sku) != 10:
        return True
    # Check if first 4 chars are digits and last 6 are hex
    try:
        int(sku[:4])  # First 4 should be digits
        int(sku[4:], 16)  # Last 6 should be hex
        return False
    except ValueError:
        return True


def cleanup_bad_skus():
    """Remove items with improperly formatted SKUs."""
    print("="*70)
    print("CLEANING UP IMPROPERLY NAMED ITEMS")
    print("="*70)
    
    # Get all parent items
    print("\nFetching parent items...")
    parent_items = get_all_parent_items()
    print(f"Found {len(parent_items)} parent items")
    
    # Find bad parent SKUs
    bad_parents = []
    good_parents = []
    
    for item in parent_items:
        if is_bad_parent_sku(item['sku']):
            bad_parents.append(item)
            print(f"  BAD: {item['sku']} ({item['item_type']['name']})")
        else:
            good_parents.append(item)
    
    print(f"\nFound {len(bad_parents)} parent items with bad SKUs")
    print(f"Found {len(good_parents)} parent items with good SKUs")
    
    # Delete bad parent items
    if bad_parents:
        print(f"\nDeleting {len(bad_parents)} parent items with bad SKUs...")
        for item in bad_parents:
            if delete_parent_item(item['id']):
                print(f"  Deleted: {item['sku']}")
            time.sleep(0.5)
    
    # Get all child items
    print("\nFetching child items...")
    child_items = get_all_child_items()
    print(f"Found {len(child_items)} child items")
    
    # Find bad child SKUs
    bad_children = []
    good_children = []
    
    for item in child_items:
        if is_bad_child_sku(item['sku']):
            bad_children.append(item)
            print(f"  BAD: {item['sku']} ({item['item_type']['name']})")
        else:
            good_children.append(item)
    
    print(f"\nFound {len(bad_children)} child items with bad SKUs")
    print(f"Found {len(good_children)} child items with good SKUs")
    
    # Delete bad child items
    if bad_children:
        print(f"\nDeleting {len(bad_children)} child items with bad SKUs...")
        for item in bad_children:
            if delete_child_item(item['id']):
                print(f"  Deleted: {item['sku']}")
            time.sleep(0.5)
    
    print("\nCleanup complete!")
    print(f"Remaining: {len(good_parents)} parent items, {len(good_children)} child items")
    
    return len(good_parents)


def create_movements():
    """Create movements for remaining items."""
    print("\n" + "="*70)
    print("CREATING MOVEMENT HISTORY")
    print("="*70)
    
    # Get fresh list of parent items
    parent_items = get_all_parent_items()
    all_locations = get_all_locations()
    
    if not parent_items:
        print("\nNo parent items available for movements")
        return 0
    
    if not all_locations:
        print("\nNo locations available for movements")
        return 0
    
    print(f"\nCreating 50 random movements...")
    print(f"Available items: {len(parent_items)}")
    print(f"Available locations: {len(all_locations)}")
    
    movements_created = 0
    
    for i in range(50):
        # Select random item
        item = random.choice(parent_items)
        current_location_id = item['current_location_id']
        
        # Select different location
        available_locations = [loc for loc in all_locations if loc['id'] != current_location_id]
        if not available_locations:
            continue
        
        to_location = random.choice(available_locations)
        
        # Create movement
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
        
        time.sleep(1.5)
    
    print(f"\nTotal movements created: {movements_created}")
    return movements_created


def main():
    """Main function."""
    try:
        print("Starting cleanup and movement creation...\n")
        
        # Login
        login()
        
        # Step 1: Cleanup bad SKUs
        remaining_items = cleanup_bad_skus()
        
        # Step 2: Create movements if we have items
        if remaining_items > 0:
            movements_created = create_movements()
        else:
            print("\nNo items remaining - skipping movement creation")
            movements_created = 0
        
        print("\n" + "="*70)
        print("OPERATIONS COMPLETED!")
        print("="*70)
        print(f"Remaining parent items: {remaining_items}")
        print(f"Movements created: {movements_created}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
