"""Diagnose why locations can't be deleted in staging."""

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
    print(f"  Error getting items: {response.status_code}")
    try:
        print(f"  Response: {response.json()}")
    except:
        print(f"  Response text: {response.text}")
    return []

def try_delete_location(token, location_id, location_name):
    """Try to delete a location and show the error."""
    response = requests.delete(
        f"{STAGING_URL}/api/v1/locations/{location_id}",
        headers=get_headers(token),
        timeout=10
    )
    
    if response.status_code == 200:
        print(f"  ✓ Successfully deleted!")
        return True
    else:
        print(f"  ✗ Failed with status {response.status_code}")
        try:
            error = response.json()
            print(f"  Error: {error.get('detail', 'Unknown')}")
        except:
            print(f"  Response text: {response.text}")
        return False

def main():
    """Main diagnostic function."""
    print("=" * 70)
    print("Location Deletion Diagnostic")
    print("=" * 70)
    
    token = login()
    print("\n✓ Logged in")
    
    # Get all locations
    print("\nGetting all locations...")
    locations = get_locations_with_items(token)
    
    # Find locations that should be deletable (0 items)
    print("\n" + "=" * 70)
    print("Locations with 0 items:")
    print("=" * 70)
    
    zero_item_locations = []
    for loc in locations:
        item_count = loc.get('item_count', 0)
        if item_count == 0:
            zero_item_locations.append(loc)
            print(f"\n{loc['name']} ({loc.get('location_type', {}).get('name', 'Unknown')})")
            print(f"  ID: {loc['id']}")
            print(f"  Item count from API: {item_count}")
            
            # Double-check by querying items directly
            items = get_items_at_location(token, loc['id'])
            print(f"  Items from direct query: {len(items)}")
            
            if len(items) > 0:
                print(f"  ⚠ MISMATCH! Location shows 0 items but query returned {len(items)}")
                print(f"  Items found:")
                for item in items[:5]:  # Show first 5
                    print(f"    - {item.get('sku', 'Unknown')}: {item.get('description', 'No description')}")
            
            # Try to delete
            print(f"  Attempting deletion...")
            try_delete_location(token, loc['id'], loc['name'])
    
    if not zero_item_locations:
        print("\nNo locations with 0 items found.")
    
    # Show locations with items
    print("\n" + "=" * 70)
    print("Locations with items:")
    print("=" * 70)
    
    for loc in locations:
        item_count = loc.get('item_count', 0)
        if item_count > 0:
            print(f"\n{loc['name']} ({loc.get('location_type', {}).get('name', 'Unknown')})")
            print(f"  ID: {loc['id']}")
            print(f"  Item count: {item_count}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
