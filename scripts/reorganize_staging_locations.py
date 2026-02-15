"""
Reorganize staging locations and add shelf stock items.
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


def get_all_location_types():
    """Get all location types."""
    response = requests.get(f"{API_BASE_URL}/locations/types", headers=get_headers())
    response.raise_for_status()
    return response.json()


def get_all_locations():
    """Get all locations."""
    response = requests.get(f"{API_BASE_URL}/locations/locations", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data if isinstance(data, list) else []


def get_all_parent_items():
    """Get all parent items."""
    response = requests.get(f"{API_BASE_URL}/items/parent", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data if isinstance(data, list) else []


def get_all_item_types():
    """Get all item types."""
    response = requests.get(f"{API_BASE_URL}/items/types", headers=get_headers())
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data if isinstance(data, list) else []


def create_location_type(name, description):
    """Create a location type."""
    response = requests.post(
        f"{API_BASE_URL}/locations/types",
        headers=get_headers(),
        json={"name": name, "description": description}
    )
    response.raise_for_status()
    return response.json()


def create_location(name, description, location_type_id):
    """Create a location."""
    response = requests.post(
        f"{API_BASE_URL}/locations/locations",
        headers=get_headers(),
        json={
            "name": name,
            "description": description,
            "location_type_id": location_type_id,
            "location_metadata": {}
        }
    )
    response.raise_for_status()
    return response.json()


def update_location(location_id, name, description, location_type_id):
    """Update a location."""
    response = requests.put(
        f"{API_BASE_URL}/locations/locations/{location_id}",
        headers=get_headers(),
        json={
            "name": name,
            "description": description,
            "location_type_id": location_type_id
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
        # Login
        login()
        
        print("\n=== Step 1: Creating New Location Types ===")
        existing_types = {lt["name"]: lt for lt in get_all_location_types()}
        
        new_location_types = {
            "Warehouse": "JDM warehouse facilities",
            "Client Site": "Customer hospital and surgery center locations",
            "Quarantine": "Quarantine storage areas"
        }
        
        location_types = {}
        for name, desc in new_location_types.items():
            if name in existing_types:
                location_types[name] = existing_types[name]
                print(f"✓ Using existing location type: {name}")
            else:
                location_types[name] = create_location_type(name, desc)
                print(f"✓ Created location type: {name}")
        
        print("\n=== Step 2: Creating New Locations ===")
        existing_locs_list = get_all_locations()
        # Create a map with both name and type for proper matching
        existing_locs = {}
        for loc in existing_locs_list:
            type_name = loc.get("location_type", {}).get("name", "")
            key = f"{loc['name']} ({type_name})"
            existing_locs[key] = loc
        
        new_locations_config = [
            # Warehouses
            ("JDM Austin", "JDM Austin warehouse", "Warehouse"),
            ("JDM Tampa", "JDM Tampa warehouse", "Warehouse"),
            ("JDM Chicago", "JDM Chicago warehouse", "Warehouse"),
            ("JDM Las Vegas", "JDM Las Vegas warehouse", "Warehouse"),
            ("JDM NY", "JDM New York warehouse", "Warehouse"),
            # Quarantine
            ("JDM Austin", "JDM Austin quarantine", "Quarantine"),
            ("JDM Tampa", "JDM Tampa quarantine", "Quarantine"),
            ("JDM Chicago", "JDM Chicago quarantine", "Quarantine"),
            ("JDM Las Vegas", "JDM Las Vegas quarantine", "Quarantine"),
            ("JDM NY", "JDM New York quarantine", "Quarantine"),
            # Client Sites
            ("Hospital A", "Hospital A client site", "Client Site"),
            ("Hospital B", "Hospital B client site", "Client Site"),
            ("Surgery Center C", "Surgery Center C client site", "Client Site"),
        ]
        
        locations = {}
        for name, desc, type_name in new_locations_config:
            # Create unique key for locations with same name but different types
            key = f"{name} ({type_name})"
            
            if key in existing_locs:
                # Use existing location
                locations[key] = existing_locs[key]
                print(f"✓ Using existing location: {name} ({type_name})")
            else:
                # Create new location
                loc = create_location(name, desc, location_types[type_name]["id"])
                locations[key] = loc
                print(f"✓ Created location: {name} ({type_name})")
        
        print("\n=== Step 3: Moving All Items to New Locations ===")
        parent_items = get_all_parent_items()
        
        # Distribute items across new locations
        warehouse_locs = [v for k, v in locations.items() if "(Warehouse)" in k]
        quarantine_locs = [v for k, v in locations.items() if "(Quarantine)" in k]
        client_locs = [v for k, v in locations.items() if "(Client Site)" in k]
        
        moved_count = 0
        for i, item in enumerate(parent_items):
            # Distribute: first few to client sites, some to quarantine, rest to warehouses
            if i < len(client_locs):
                new_location = client_locs[i]
            elif i < len(client_locs) + len(quarantine_locs):
                new_location = quarantine_locs[i - len(client_locs)]
            else:
                new_location = random.choice(warehouse_locs)
            
            # Only move if not already at the location
            if item["current_location"]["id"] != new_location["id"]:
                try:
                    move_item(item["id"], new_location["id"], "Reorganizing locations")
                    moved_count += 1
                    if moved_count % 10 == 0:
                        print(f"  ✓ Moved {moved_count} items...")
                except Exception as e:
                    print(f"  ✗ Failed to move item {item['sku']}: {e}")
        
        print(f"✓ Moved {moved_count} items to new locations")
        
        print("\n=== Step 4: Creating Shelf Stock Item Type ===")
        item_types = {it["name"]: it for it in get_all_item_types()}
        
        if "Shelf Stock" not in item_types:
            shelf_stock_type = create_item_type(
                "Shelf Stock",
                "Extra components not tied to a specific tower",
                "parent"
            )
            print("✓ Created Shelf Stock item type")
        else:
            shelf_stock_type = item_types["Shelf Stock"]
            print("✓ Using existing Shelf Stock item type")
        
        # Get highest SKU to continue numbering - refresh the list
        parent_items = get_all_parent_items()
        max_sku = 0
        for item in parent_items:
            try:
                sku_num = int(item["sku"])
                max_sku = max(max_sku, sku_num)
            except (ValueError, KeyError):
                pass
        
        sku_counter = max_sku + 1
        print(f"  Starting SKU counter at {sku_counter}")
        
        print("\n=== Step 5: Creating Shelf Stock Items at Each Warehouse ===")
        # Get some child item types for shelf stock
        child_types = [it for it in item_types.values() if it.get("category") == "child"]
        common_child_types = [
            it for it in child_types 
            if any(name in it["name"] for name in ["CCU", "Light Source", "Monitor", "Printer"])
        ][:5]  # Take up to 5 common types
        
        # Check which warehouses already have shelf stock
        parent_items = get_all_parent_items()
        warehouses_with_shelf_stock = set()
        for item in parent_items:
            if item.get("item_type", {}).get("name") == "Shelf Stock":
                loc_id = item["current_location"]["id"]
                warehouses_with_shelf_stock.add(loc_id)
        
        created_count = 0
        for warehouse_key, warehouse_loc in [(k, v) for k, v in locations.items() if "(Warehouse)" in k]:
            if warehouse_loc["id"] in warehouses_with_shelf_stock:
                print(f"  ✓ Shelf Stock already exists at {warehouse_loc['name']}")
                continue
            
            # Create shelf stock parent item - try multiple SKUs if needed
            max_attempts = 10
            shelf_stock = None
            for attempt in range(max_attempts):
                try:
                    sku = str(sku_counter)
                    sku_counter += 1
                    shelf_stock = create_parent_item(sku, shelf_stock_type["id"], warehouse_loc["id"])
                    created_count += 1
                    print(f"  ✓ Created Shelf Stock #{sku} at {warehouse_loc['name']}")
                    break
                except requests.exceptions.HTTPError as e:
                    if "already exists" in str(e.response.text):
                        continue  # Try next SKU
                    else:
                        raise
            
            if not shelf_stock:
                print(f"  ✗ Could not create Shelf Stock at {warehouse_loc['name']} - all SKUs taken")
                continue
            
            # Add 3-5 random child items to this shelf stock
            num_children = random.randint(3, 5)
            for _ in range(num_children):
                child_type = random.choice(common_child_types)
                serial = generate_serial()
                create_child_item(serial, child_type["id"], shelf_stock["id"])
                print(f"    ✓ Added {child_type['name']} ({serial})")
        
        if created_count == 0:
            print("  ✓ All warehouses already have Shelf Stock items")
        
        print("\n=== Step 6: Cleaning Up Old Locations ===")
        # Get current locations after all moves
        current_locs = get_all_locations()
        new_location_ids = {loc["id"] for loc in locations.values()}
        
        deleted_count = 0
        for loc in current_locs:
            if loc["id"] not in new_location_ids:
                try:
                    delete_location(loc["id"])
                    deleted_count += 1
                    print(f"  ✓ Deleted old location: {loc['name']}")
                except Exception as e:
                    print(f"  ✗ Could not delete location {loc['name']}: {e}")
        
        print(f"✓ Deleted {deleted_count} old locations")
        
        print("\n=== Step 7: Cleaning Up Old Location Types ===")
        current_types = get_all_location_types()
        new_type_ids = {lt["id"] for lt in location_types.values()}
        
        deleted_type_count = 0
        for lt in current_types:
            if lt["id"] not in new_type_ids:
                try:
                    delete_location_type(lt["id"])
                    deleted_type_count += 1
                    print(f"  ✓ Deleted old location type: {lt['name']}")
                except Exception as e:
                    print(f"  ✗ Could not delete location type {lt['name']}: {e}")
        
        print(f"✓ Deleted {deleted_type_count} old location types")
        
        print("\n" + "="*50)
        print("REORGANIZATION COMPLETE!")
        print("="*50)
        print(f"✓ Location Types: {len(location_types)}")
        print(f"✓ Locations: {len(locations)}")
        print(f"✓ Items moved: {moved_count}")
        print(f"✓ Shelf Stock items created: {len(warehouse_locs)}")
        
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
