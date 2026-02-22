"""Check why Warehouse C can't be deleted."""

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

def get_locations_with_items(token):
    """Get all locations with item counts."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{STAGING_URL}/api/v1/locations/with-items",
        headers=headers,
        timeout=10
    )
    return response.json()

def get_items_at_location(token, location_id):
    """Get items at a specific location."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{STAGING_URL}/api/v1/items/parent-items",
        headers=headers,
        params={"location_id": location_id},
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    return []

def try_delete_location(token, location_id, location_name):
    """Try to delete a location."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{STAGING_URL}/api/v1/locations/{location_id}",
        headers=headers,
        timeout=10
    )
    return response

def main():
    """Main function."""
    print("=" * 70)
    print("Warehouse C Deletion Diagnostic")
    print("=" * 70)
    
    token = login()
    print("\n✓ Logged in")
    
    # Find Warehouse C
    print("\nFinding Warehouse C...")
    locations = get_locations_with_items(token)
    
    warehouse_c = None
    for loc in locations:
        if loc['name'] == 'Warehouse C':
            warehouse_c = loc
            break
    
    if not warehouse_c:
        print("✗ Warehouse C not found")
        sys.exit(1)
    
    print(f"✓ Found Warehouse C")
    print(f"  ID: {warehouse_c['id']}")
    print(f"  Item count: {warehouse_c.get('item_count', 'unknown')}")
    
    # Check if it has items
    item_count = warehouse_c.get('item_count', 0)
    
    if item_count > 0:
        print(f"\n⚠ Warehouse C has {item_count} items assigned to it")
        print("You must move all items to another location before deleting")
        
        # Show some items
        print("\nGetting items at this location...")
        items = get_items_at_location(token, warehouse_c['id'])
        
        if items:
            print(f"\nShowing first 5 items:")
            for i, item in enumerate(items[:5], 1):
                print(f"  {i}. {item.get('name', 'Unknown')} (SKU: {item.get('sku', 'N/A')})")
            
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more items")
        
        print("\n" + "=" * 70)
        print("SOLUTION:")
        print("1. Go to Inventory page")
        print("2. Filter by location: Warehouse C")
        print("3. Move all items to another location")
        print("4. Then try deleting Warehouse C again")
        print("=" * 70)
        return
    
    # Try to delete
    print("\nAttempting to delete Warehouse C...")
    response = try_delete_location(token, warehouse_c['id'], warehouse_c['name'])
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("\n✓ Warehouse C deleted successfully!")
    else:
        print("\n✗ Deletion failed")
        try:
            error = response.json()
            print(f"Error: {error.get('detail', 'Unknown error')}")
        except:
            pass

if __name__ == "__main__":
    main()
