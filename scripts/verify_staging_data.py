"""
Verify staging data structure.
"""
import os
import sys
import requests
from collections import defaultdict

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


def main():
    """Main function."""
    try:
        login()
        print("✓ Logged in\n")
        
        # Get location types
        response = requests.get(f"{API_BASE_URL}/locations/types", headers=get_headers())
        location_types = response.json()
        print(f"=== Location Types ({len(location_types)}) ===")
        for lt in location_types:
            print(f"  - {lt['name']}")
        
        # Get locations
        response = requests.get(f"{API_BASE_URL}/locations/locations", headers=get_headers())
        locations_data = response.json()
        locations = locations_data if isinstance(locations_data, list) else locations_data.get("items", [])
        
        print(f"\n=== Locations ({len(locations)}) ===")
        by_type = defaultdict(list)
        for loc in locations:
            type_name = loc.get("location_type", {}).get("name", "Unknown")
            by_type[type_name].append(loc["name"])
        
        for type_name, locs in sorted(by_type.items()):
            print(f"\n{type_name}:")
            for loc_name in sorted(locs):
                print(f"  - {loc_name}")
        
        # Get parent items
        response = requests.get(f"{API_BASE_URL}/items/parent", headers=get_headers())
        items_data = response.json()
        items = items_data if isinstance(items_data, list) else items_data.get("items", [])
        
        print(f"\n=== Parent Items ({len(items)}) ===")
        by_type = defaultdict(int)
        by_location = defaultdict(int)
        
        for item in items:
            item_type = item.get("item_type", {}).get("name", "Unknown")
            by_type[item_type] += 1
            
            loc_name = item.get("current_location", {}).get("name", "Unknown")
            by_location[loc_name] += 1
        
        print("\nBy Item Type:")
        for item_type, count in sorted(by_type.items()):
            print(f"  - {item_type}: {count}")
        
        print("\nBy Location:")
        for loc_name, count in sorted(by_location.items()):
            print(f"  - {loc_name}: {count}")
        
        # Check shelf stock specifically
        shelf_stock_items = [i for i in items if i.get("item_type", {}).get("name") == "Shelf Stock"]
        print(f"\n=== Shelf Stock Items ({len(shelf_stock_items)}) ===")
        for item in shelf_stock_items:
            loc_name = item.get("current_location", {}).get("name", "Unknown")
            child_count = len(item.get("child_items", []))
            print(f"  - SKU {item['sku']} at {loc_name} ({child_count} components)")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
