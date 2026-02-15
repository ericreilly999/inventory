"""
Add movement history to existing staging inventory items.
"""
import os
import sys
import random
import requests
from datetime import datetime

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
    print("Logging in...")
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    response.raise_for_status()
    auth_token = response.json()["access_token"]
    print("✓ Logged in successfully")
    return auth_token


def get_headers():
    """Get headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


def get_all_parent_items():
    """Get all parent items."""
    response = requests.get(f"{API_BASE_URL}/items/parent", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    
    # Handle both list and dict responses
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    elif isinstance(data, list):
        return data
    else:
        return []


def get_all_locations():
    """Get all locations."""
    response = requests.get(f"{API_BASE_URL}/locations/locations", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    
    # Handle both list and dict responses
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    elif isinstance(data, list):
        return data
    else:
        return []


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
        # Login
        login()
        
        print("\n=== Fetching Data ===")
        parent_items = get_all_parent_items()
        locations = get_all_locations()
        
        print(f"✓ Found {len(parent_items)} parent items")
        print(f"✓ Found {len(locations)} locations")
        
        if not parent_items or not locations:
            print("✗ No items or locations found")
            return
        
        print("\n=== Creating Movement History ===")
        movements_created = 0
        movements_attempted = 0
        
        # Create 50 random movements
        for _ in range(50):
            parent = random.choice(parent_items)
            new_location = random.choice(locations)
            
            # Don't move to same location
            if parent["current_location"]["id"] == new_location["id"]:
                continue
            
            movements_attempted += 1
            try:
                move_item(
                    parent["id"],
                    new_location["id"],
                    f"Moved for testing - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                movements_created += 1
                
                # Get item type name
                item_type = parent.get("item_type", {}).get("name", "Unknown")
                print(f"  ✓ Moved {item_type} (SKU: {parent['sku']}) to {new_location['name']}")
                
            except Exception as e:
                print(f"  ✗ Failed to move item: {e}")
        
        print(f"\n{'='*50}")
        print(f"MOVEMENT HISTORY COMPLETE!")
        print(f"{'='*50}")
        print(f"✓ Movements attempted: {movements_attempted}")
        print(f"✓ Movements created: {movements_created}")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
