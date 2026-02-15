"""
Add shelf stock items to JDM warehouses.
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


def get_all_parent_items():
    """Get all parent items."""
    response = requests.get(f"{API_BASE_URL}/items/parent", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else data.get("items", [])


def get_all_item_types():
    """Get all item types."""
    response = requests.get(f"{API_BASE_URL}/items/types", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else data.get("items", [])


def create_item_type(name, description, category):
    """Create an item type."""
    response = requests.post(
        f"{API_BASE_URL}/items/types",
        headers=get_headers(),
        json={
            "name": name,
            "description": description,
            "category": category
        }
    )
    response.raise_for_status()
    return response.json()


def create_parent_item(sku, item_type_id, location_id):
    """Create a parent item."""
    response = requests.post(
        f"{API_BASE_URL}/items/parent",
        headers=get_headers(),
        json={
            "sku": sku,
            "item_type_id": item_type_id,
            "current_location_id": location_id
        }
    )
    response.raise_for_status()
    return response.json()


def create_child_item(serial_number, item_type_id, parent_item_id):
    """Create a child item."""
    response = requests.post(
        f"{API_BASE_URL}/items/child",
        headers=get_headers(),
        json={
            "sku": serial_number,
            "item_type_id": item_type_id,
            "parent_item_id": parent_item_id
        }
    )
    response.raise_for_status()
    return response.json()


def generate_serial():
    """Generate a random serial number."""
    return f"{random.randint(1000, 9999)}{random.choice('ABCDEF')}{random.choice('ABCDEF')}{random.randint(1000, 9999)}"


def main():
    """Main function."""
    try:
        login()
        print("✓ Logged in\n")
        
        # Get all data
        locations = get_all_locations()
        parent_items = get_all_parent_items()
        item_types = {it["name"]: it for it in get_all_item_types()}
        
        # Find JDM warehouses
        jdm_warehouses = [
            loc for loc in locations 
            if loc.get("location_type", {}).get("name") == "Warehouse" 
            and loc["name"].startswith("JDM")
        ]
        
        print(f"Found {len(jdm_warehouses)} JDM warehouses:")
        for wh in jdm_warehouses:
            print(f"  - {wh['name']}")
        
        # Get or create Shelf Stock item type
        if "Shelf Stock" not in item_types:
            print("\nCreating Shelf Stock item type...")
            shelf_stock_type = create_item_type(
                "Shelf Stock",
                "Extra components not tied to a specific tower",
                "parent"
            )
            print("✓ Created Shelf Stock item type")
        else:
            shelf_stock_type = item_types["Shelf Stock"]
            print("\n✓ Using existing Shelf Stock item type")
        
        # Find highest SKU
        max_sku = 0
        for item in parent_items:
            try:
                sku_num = int(item["sku"])
                max_sku = max(max_sku, sku_num)
            except (ValueError, KeyError):
                pass
        
        sku_counter = max_sku + 1
        print(f"Starting SKU counter at {sku_counter}\n")
        
        # Check which warehouses already have shelf stock
        warehouses_with_shelf_stock = set()
        for item in parent_items:
            if item.get("item_type", {}).get("name") == "Shelf Stock":
                loc_id = item["current_location"]["id"]
                warehouses_with_shelf_stock.add(loc_id)
                loc_name = item["current_location"]["name"]
                print(f"  ✓ {loc_name} already has Shelf Stock (SKU: {item['sku']})")
        
        if warehouses_with_shelf_stock:
            print()
        
        # Get child item types for components
        child_types = [it for it in item_types.values() if it.get("category") == "child"]
        common_child_types = [
            it for it in child_types 
            if any(name in it["name"] for name in ["CCU", "Light Source", "Monitor", "Printer", "Pinpoint"])
        ]
        
        if not common_child_types:
            common_child_types = child_types[:5]  # Just take first 5 if no matches
        
        print(f"Using {len(common_child_types)} child item types for components\n")
        
        # Create shelf stock for each JDM warehouse
        print("=== Creating Shelf Stock Items ===")
        for warehouse in jdm_warehouses:
            # Skip if warehouse already has shelf stock
            if warehouse["id"] in warehouses_with_shelf_stock:
                print(f"✓ {warehouse['name']} already has Shelf Stock")
                continue
            
            # Try to create with incrementing SKU
            created = False
            for attempt in range(20):  # Try up to 20 SKUs
                try:
                    sku = str(sku_counter)
                    sku_counter += 1
                    
                    shelf_stock = create_parent_item(sku, shelf_stock_type["id"], warehouse["id"])
                    print(f"✓ Created Shelf Stock #{sku} at {warehouse['name']}")
                    created = True
                    
                    # Add 3-5 random child items
                    num_children = random.randint(3, 5)
                    for _ in range(num_children):
                        child_type = random.choice(common_child_types)
                        serial = generate_serial()
                        create_child_item(serial, child_type["id"], shelf_stock["id"])
                        print(f"  ✓ Added {child_type['name']} ({serial})")
                    
                    break
                    
                except requests.exceptions.HTTPError as e:
                    if "already exists" in str(e.response.text):
                        continue  # Try next SKU
                    else:
                        print(f"  ✗ Error creating shelf stock: {e}")
                        break
            
            if not created:
                print(f"  ✗ Could not create Shelf Stock at {warehouse['name']}")
        
        print("\n✓ Shelf Stock creation complete!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
