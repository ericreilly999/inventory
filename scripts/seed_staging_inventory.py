"""
Seed staging inventory with parent and child items.
"""
import os
import sys
import random
import requests
from datetime import datetime, timedelta

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


def move_item(parent_item_id, to_location_id, notes=""):
    """Move a parent item to a new location."""
    response = requests.post(
        f"{API_BASE_URL}/movements/move",
        headers=get_headers(),
        json={
            "parent_item_id": parent_item_id,
            "to_location_id": to_location_id,
            "notes": notes
        }
    )
    response.raise_for_status()
    return response.json()


def generate_serial():
    """Generate a random serial number."""
    return f"{random.randint(1000, 9999)}{random.choice('ABCDEF')}{random.choice('ABCDEF')}{random.randint(1000, 9999)}"


def main():
    """Main seeding function."""
    try:
        # Login
        login()
        
        print("\n=== Creating Location Types ===")
        # Get or create location types
        response = requests.get(f"{API_BASE_URL}/locations/types", headers=get_headers())
        existing_types = {lt["name"]: lt for lt in response.json()}
        
        location_types = {}
        for name, desc in [
            ("Warehouse", "Storage and distribution facility"),
            ("Client Site", "Customer location"),
            ("Quarantine - Damage", "Items with physical damage"),
            ("Quarantine - Repair", "Items awaiting repair"),
            ("Quarantine - Cleaning", "Items being cleaned/sterilized"),
        ]:
            if name in existing_types:
                location_types[name] = existing_types[name]
                print(f"✓ Using existing location type: {name}")
            else:
                location_types[name] = create_location_type(name, desc)
                print(f"✓ Created location type: {name}")
        
        print("\n=== Creating Locations ===")
        # Get or create locations - try different endpoint patterns
        try:
            response = requests.get(f"{API_BASE_URL}/locations/locations", headers=get_headers())
            response.raise_for_status()
        except:
            # Try without the extra path
            response = requests.get(f"{API_BASE_URL}/location/locations", headers=get_headers())
            response.raise_for_status()
        
        locations_data = response.json()
        print(f"DEBUG: Locations response type: {type(locations_data)}")
        
        # Handle both list and dict responses
        if isinstance(locations_data, dict) and "items" in locations_data:
            locations_list = locations_data["items"]
        elif isinstance(locations_data, list):
            locations_list = locations_data
        else:
            locations_list = []
        
        existing_locs = {loc["name"]: loc for loc in locations_list}
        
        locations = {}
        location_configs = [
            ("Warehouse A", "Main warehouse facility", "Warehouse"),
            ("Warehouse B", "Secondary warehouse", "Warehouse"),
            ("Warehouse C", "Overflow storage", "Warehouse"),
            ("Test Client Site", "Test customer location", "Client Site"),
            ("Damage Quarantine", "Damaged items holding area", "Quarantine - Damage"),
            ("Repair Quarantine", "Items awaiting repair", "Quarantine - Repair"),
            ("Cleaning Quarantine", "Sterilization area", "Quarantine - Cleaning"),
        ]
        
        for name, desc, type_name in location_configs:
            if name in existing_locs:
                locations[name] = existing_locs[name]
                print(f"✓ Using existing location: {name}")
            else:
                locations[name] = create_location(name, desc, location_types[type_name]["id"])
                print(f"✓ Created location: {name}")
        
        print("\n=== Creating Item Types ===")
        # Get or create item types
        response = requests.get(f"{API_BASE_URL}/items/types", headers=get_headers())
        response.raise_for_status()
        item_types_data = response.json()
        
        # Handle both list and dict responses
        if isinstance(item_types_data, dict) and "items" in item_types_data:
            item_types_list = item_types_data["items"]
        elif isinstance(item_types_data, list):
            item_types_list = item_types_data
        else:
            item_types_list = []
        
        existing_items = {it["name"]: it for it in item_types_list}
        
        item_types = {}
        
        # Parent item types
        parent_types = [
            ("RISE Tower", "RISE Tower system", "parent"),
            ("1788 Roll Stand", "1788 Roll Stand", "parent"),
            ("1688 Roll Stand", "1688 Roll Stand", "parent"),
            ("MedEd 1688", "MedEd 1688 system", "parent"),
            ("Clinical 1788", "Clinical 1788 system", "parent"),
            ("Clinical 1688", "Clinical 1688 system", "parent"),
            ("MedEd 1788", "MedEd 1788 system", "parent"),
            ("Sports Tower", "Sports Tower system", "parent"),
        ]
        
        for name, desc, category in parent_types:
            if name in existing_items:
                item_types[name] = existing_items[name]
                print(f"✓ Using existing item type: {name}")
            else:
                item_types[name] = create_item_type(name, desc, category)
                print(f"✓ Created parent item type: {name}")
        
        # Child item types
        child_types = [
            ("Crossfire", "Crossfire component"),
            ("1688 CCU", "1688 CCU component"),
            ("L12 Light Source", "L12 Light Source"),
            ("L11 Light Source", "L11 Light Source"),
            ("L10 Light Source", "L10 Light Source"),
            ("L9000 Light Source", "L9000 Light Source"),
            ("1588 CCU", "1588 CCU component"),
            ("1488 CCU", "1488 CCU component"),
            ("1288 CCU", "1288 CCU component"),
            ("OR Hub", "OR Hub component"),
            ("Pinpoint", "Pinpoint component"),
            ("Printer", "Printer component"),
            ("Roll Stand Pole", "Roll stand pole"),
            ("Roll Stand Base", "Roll stand base"),
            ("Pneumoclear", "Pneumoclear component"),
            ("Crossflow", "Crossflow component"),
            ("1788 CCU", "1788 CCU component"),
            ("Vision Pro Monitor", "Vision Pro Monitor"),
            ("OLED Monitor", "OLED Monitor"),
        ]
        
        for name, desc in child_types:
            if name in existing_items:
                item_types[name] = existing_items[name]
                print(f"✓ Using existing item type: {name}")
            else:
                item_types[name] = create_item_type(name, desc, "child")
                print(f"✓ Created child item type: {name}")
        
        print("\n=== Creating Parent Items and Components ===")
        
        # Configuration for each parent type
        parent_configs = {
            "Sports Tower": ["Crossfire", "Crossflow", "L12 Light Source", "Vision Pro Monitor"],
            "MedEd 1688": ["1688 CCU", "L11 Light Source", "Pneumoclear", "OLED Monitor"],
            "MedEd 1788": ["1788 CCU", "L12 Light Source", "Pneumoclear"],
            "Clinical 1788": ["OR Hub", "1788 CCU", "L12 Light Source", "Printer", "Pinpoint", "OLED Monitor"],
            "Clinical 1688": ["OR Hub", "1688 CCU", "L11 Light Source", "Printer", "Pinpoint"],
            "1788 Roll Stand": ["Roll Stand Pole", "Roll Stand Base", "OLED Monitor"],
            "1688 Roll Stand": ["Roll Stand Pole", "Roll Stand Base"],
            "RISE Tower": ["Crossfire", "1788 CCU", "L12 Light Source"],
        }
        
        # Warehouse locations for distribution
        warehouse_locs = [locations["Warehouse A"], locations["Warehouse B"], locations["Warehouse C"]]
        
        all_parent_items = []
        
        # Get existing parent items to determine starting SKU
        try:
            response = requests.get(f"{API_BASE_URL}/items/parent", headers=get_headers())
            response.raise_for_status()
            existing_parents_data = response.json()
            
            # Handle both list and dict responses
            if isinstance(existing_parents_data, dict) and "items" in existing_parents_data:
                existing_parents = existing_parents_data["items"]
            elif isinstance(existing_parents_data, list):
                existing_parents = existing_parents_data
            else:
                existing_parents = []
            
            # Find highest numeric SKU
            max_sku = 0
            for item in existing_parents:
                try:
                    sku_num = int(item["sku"])
                    max_sku = max(max_sku, sku_num)
                except (ValueError, KeyError):
                    pass
            
            sku_counter = max_sku + 1
            print(f"Starting SKU counter at {sku_counter} (found {len(existing_parents)} existing items)")
        except Exception as e:
            print(f"Could not fetch existing items, starting at SKU 1: {e}")
            sku_counter = 1
        
        for parent_type_name, child_type_names in parent_configs.items():
            print(f"\n--- Creating {parent_type_name} items ---")
            parent_type_id = item_types[parent_type_name]["id"]
            
            for i in range(1, 11):  # Create 10 of each
                # Determine location
                if i == 1:
                    location = locations["Test Client Site"]
                elif i == 2:
                    location = locations["Damage Quarantine"]
                elif i == 3:
                    location = locations["Repair Quarantine"]
                elif i == 4:
                    location = locations["Cleaning Quarantine"]
                else:
                    location = random.choice(warehouse_locs)
                
                # Create parent item with unique SKU
                sku = str(sku_counter)
                sku_counter += 1
                parent = create_parent_item(sku, parent_type_id, location["id"])
                all_parent_items.append(parent)
                print(f"  ✓ Created {parent_type_name} #{i} (SKU: {sku}) at {location['name']}")
                
                # Create child items
                for child_type_name in child_type_names:
                    # Optional OR Hub for some MedEd items
                    if child_type_name == "OR Hub" and "MedEd" in parent_type_name:
                        if random.random() < 0.5:  # 50% chance
                            continue
                    
                    serial = generate_serial()
                    child_type_id = item_types[child_type_name]["id"]
                    child = create_child_item(serial, child_type_id, parent["id"])
                    print(f"    ✓ Added {child_type_name} ({serial})")
        
        print(f"\n✓ Created {len(all_parent_items)} parent items with components")
        
        print("\n=== Creating Movement History ===")
        # Move items around to create history
        movements_created = 0
        for _ in range(30):  # Create 30 random movements
            parent = random.choice(all_parent_items)
            new_location = random.choice(list(locations.values()))
            
            # Don't move to same location
            if parent["current_location"]["id"] == new_location["id"]:
                continue
            
            try:
                move_item(
                    parent["id"],
                    new_location["id"],
                    f"Moved for testing - {datetime.now().strftime('%Y-%m-%d')}"
                )
                movements_created += 1
                print(f"  ✓ Moved {parent['sku']} to {new_location['name']}")
            except Exception as e:
                print(f"  ✗ Failed to move item: {e}")
        
        print(f"\n✓ Created {movements_created} movement records")
        
        print("\n" + "="*50)
        print("SEEDING COMPLETE!")
        print("="*50)
        print(f"✓ Location Types: {len(location_types)}")
        print(f"✓ Locations: {len(locations)}")
        print(f"✓ Item Types: {len(item_types)}")
        print(f"✓ Parent Items: {len(all_parent_items)}")
        print(f"✓ Movements: {movements_created}")
        
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
