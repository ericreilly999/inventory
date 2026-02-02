"""
Generate movement history for all parent items.
Each item will be moved 0-4 times randomly.
"""
import requests
import random
import time
import os

# Environment-specific configuration
ENVIRONMENTS = {
    "dev": "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com",
    "staging": "http://staging-inventory-alb.us-east-1.elb.amazonaws.com"  # Will be updated after deployment
}

API_BASE_URL = ENVIRONMENTS.get(os.environ.get("ENVIRONMENT", "dev"))
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


def get_all_locations():
    """Get all locations."""
    response = session.get(f"{API_BASE_URL}/api/v1/locations/locations?limit=1000")
    if response.status_code != 200:
        raise Exception(f"Failed to get locations: {response.text}")
    return response.json()


def move_parent_item(parent_item_id: str, to_location_id: str, notes: str = ""):
    """Move a parent item."""
    response = session.post(
        f"{API_BASE_URL}/api/v1/movements/move",
        json={
            "item_id": parent_item_id,
            "to_location_id": to_location_id,
            "notes": notes
        }
    )
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"  Warning: Failed to move item - {response.status_code}: {response.text[:100]}")
        return None


def main():
    """Main function."""
    try:
        environment = os.environ.get("ENVIRONMENT", "dev")
        print("="*70)
        print(f"GENERATING MOVEMENT HISTORY - {environment.upper()} ENVIRONMENT")
        print(f"API URL: {API_BASE_URL}")
        print("="*70)
        
        # Login
        login()
        
        # Get all parent items and locations
        print("Fetching parent items...")
        parent_items = get_all_parent_items()
        print(f"Found {len(parent_items)} parent items")
        
        print("\nFetching locations...")
        all_locations = get_all_locations()
        print(f"Found {len(all_locations)} locations")
        
        if not parent_items:
            print("\nNo parent items found!")
            return
        
        if not all_locations:
            print("\nNo locations found!")
            return
        
        print("\n" + "="*70)
        print("CREATING MOVEMENTS")
        print("="*70)
        
        total_movements = 0
        items_moved = 0
        items_not_moved = 0
        
        # Process each parent item
        for idx, item in enumerate(parent_items, 1):
            # Randomly decide how many times to move this item (0-4)
            num_moves = random.randint(0, 4)
            
            if num_moves == 0:
                items_not_moved += 1
                print(f"[{idx}/{len(parent_items)}] {item['sku']} ({item['item_type']['name']}): No movements")
                continue
            
            items_moved += 1
            current_location_id = item['current_location_id']
            item_movements = 0
            
            print(f"[{idx}/{len(parent_items)}] {item['sku']} ({item['item_type']['name']}): {num_moves} movements")
            
            for move_num in range(num_moves):
                # Get available locations (different from current)
                available_locations = [loc for loc in all_locations if loc['id'] != current_location_id]
                
                if not available_locations:
                    print(f"  Movement {move_num + 1}: No available locations")
                    break
                
                # Select random location
                to_location = random.choice(available_locations)
                
                # Create movement
                movement = move_parent_item(
                    parent_item_id=item['id'],
                    to_location_id=to_location['id'],
                    notes=f"Movement {move_num + 1} of {num_moves}"
                )
                
                if movement:
                    print(f"  Movement {move_num + 1}: -> {to_location['name']} ({to_location['location_type']['name']})")
                    current_location_id = to_location['id']
                    item_movements += 1
                    total_movements += 1
                else:
                    print(f"  Movement {move_num + 1}: Failed")
                
                # Delay between movements
                time.sleep(1.5)
        
        print("\n" + "="*70)
        print("MOVEMENT GENERATION COMPLETED!")
        print("="*70)
        print(f"Total parent items: {len(parent_items)}")
        print(f"Items moved: {items_moved}")
        print(f"Items not moved: {items_not_moved}")
        print(f"Total movements created: {total_movements}")
        print(f"Average movements per item: {total_movements / len(parent_items):.2f}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
