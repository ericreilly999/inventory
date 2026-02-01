"""
Seed inventory data with parent items, child items, and movement history using API calls.
"""
import requests
import random
from datetime import datetime, timedelta
import time

# API Configuration
API_BASE_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"
USERNAME = "admin"
PASSWORD = "Admin123!"  # Update with actual admin password

# Global session with auth token
session = requests.Session()


def login():
    """Login and get access token."""
    print("Logging in...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/users/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text[:500]}")
        
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        
        token = response.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("Login successful!\n")
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise

def get_or_create_item_type(name: str, category: str, description: str = ""):
    """Get or create an item type."""
    # Try to find existing
    response = session.get(f"{API_BASE_URL}/api/v1/inventory/item-types?category={category}")
    if response.status_code == 200:
        item_types = response.json()
        for item_type in item_types:
            if item_type['name'] == name:
                print(f"Found existing {category} item type: {name}")
                return item_type
    
    # Create new
    response = session.post(
        f"{API_BASE_URL}/api/v1/inventory/item-types",
        json={"name": name, "category": category, "description": description}
    )
    if response.status_code in [200, 201]:
        item_type = response.json()
        print(f"Created {category} item type: {name}")
        return item_type
    else:
        raise Exception(f"Failed to create item type {name}: {response.text}")

def get_locations():
    """Get all locations."""
    response = session.get(f"{API_BASE_URL}/api/v1/locations/locations")
    if response.status_code != 200:
        raise Exception(f"Failed to get locations: {response.text}")
    return response.json()

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
        raise Exception(f"Failed to create location {name}: {response.text}")

def create_parent_item(sku: str, description: str, item_type_id: str, location_id: str):
    """Create a parent item."""
    response = session.post(
        f"{API_BASE_URL}/api/v1/inventory/parent-items",
        json={
            "sku": sku,
            "description": description,
            "item_type_id": item_type_id,
            "current_location_id": location_id
        }
    )
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Failed to create parent item {sku}: {response.text}")

def create_child_item(sku: str, description: str, item_type_id: str, parent_item_id: str):
    """Create a child item."""
    response = session.post(
        f"{API_BASE_URL}/api/v1/inventory/child-items",
        json={
            "sku": sku,
            "description": description,
            "item_type_id": item_type_id,
            "parent_item_id": parent_item_id
        }
    )
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Warning: Failed to create child item {sku}: {response.text}")
        return None

def move_parent_item(parent_item_id: str, to_location_id: str, notes: str = ""):
    """Move a parent item to a new location."""
    response = session.post(
        f"{API_BASE_URL}/api/v1/inventory/movements",
        json={
            "parent_item_id": parent_item_id,
            "to_location_id": to_location_id,
            "notes": notes
        }
    )
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Warning: Failed to move item: {response.text}")
        return None


def create_parent_items_with_children(parent_type, child_types_config, count, locations):
    """Create parent items with their child items."""
    parent_items = []
    
    for i in range(1, count + 1):
        # Create parent item SKU
        sku = f"{parent_type['name']} {i}"
        
        # Select a random location
        location = random.choice(locations)
        
        # Create parent item
        parent_item = create_parent_item(
            sku=sku,
            description=f"{parent_type['name']} unit {i}",
            item_type_id=parent_type['id'],
            location_id=location['id']
        )
        
        if not parent_item:
            continue
        
        print(f"Created parent item: {sku} at {location['name']}")
        
        # Create child items based on configuration
        for child_config in child_types_config:
            child_type = child_config['type']
            is_optional = child_config.get('optional', False)
            
            # Skip optional items randomly (50% chance)
            if is_optional and random.random() < 0.5:
                continue
            
            # Create child item
            child_sku = f"{sku}-{child_type['name']}"
            child_item = create_child_item(
                sku=child_sku,
                description=f"{child_type['name']} for {sku}",
                item_type_id=child_type['id'],
                parent_item_id=parent_item['id']
            )
            if child_item:
                print(f"  - Added child item: {child_sku}")
        
        parent_items.append(parent_item)
        time.sleep(0.1)  # Small delay to avoid overwhelming the API
    
    return parent_items

def create_movements(parent_items, locations, num_movements=50):
    """Create random movement history."""
    print(f"\nCreating {num_movements} movements...")
    
    movements_created = 0
    for _ in range(num_movements):
        if not parent_items:
            break
            
        # Select random parent item
        parent_item = random.choice(parent_items)
        
        # Get current location
        from_location_id = parent_item['current_location_id']
        
        # Select random new location (different from current)
        available_locations = [loc for loc in locations if loc['id'] != from_location_id]
        if not available_locations:
            continue
        
        to_location = random.choice(available_locations)
        
        # Create movement
        movement = move_parent_item(
            parent_item_id=parent_item['id'],
            to_location_id=to_location['id'],
            notes=f"Seeding movement to {to_location['name']}"
        )
        
        if movement:
            # Update parent item location in our local copy
            parent_item['current_location_id'] = to_location['id']
            print(f"Moved {parent_item['sku']} to {to_location['name']}")
            movements_created += 1
        
        time.sleep(0.1)  # Small delay
    
    print(f"Created {movements_created} movements")



def main():
    """Main seeding function."""
    try:
        print("Starting data seeding...\n")
        
        # Login
        login()
        
        # ===== CREATE PARENT ITEM TYPES =====
        print("Creating parent item types...")
        rise_tower = get_or_create_item_type("RISE Tower", "parent", "RISE Tower system")
        roll_stand_1788 = get_or_create_item_type("1788 Roll Stand", "parent", "1788 Roll Stand")
        roll_stand_1688 = get_or_create_item_type("1688 Roll Stand", "parent", "1688 Roll Stand")
        meded_1688 = get_or_create_item_type("MedEd 1688", "parent", "MedEd 1688 system")
        
        # Existing parent types
        clinical_1788 = get_or_create_item_type("Clinical 1788", "parent", "Clinical 1788 system")
        meded_1788 = get_or_create_item_type("MedEd 1788", "parent", "MedEd 1788 system")
        sports_tower = get_or_create_item_type("Sports Tower", "parent", "Sports Tower system")
        
        print()
        
        # ===== CREATE CHILD ITEM TYPES =====
        print("Creating child item types...")
        crossfire = get_or_create_item_type("Crossfire", "child", "Crossfire component")
        ccu_1688 = get_or_create_item_type("1688 CCU", "child", "1688 CCU")
        light_l12 = get_or_create_item_type("L12 Light Source", "child", "L12 Light Source")
        light_l11 = get_or_create_item_type("L11 Light Source", "child", "L11 Light Source")
        light_l10 = get_or_create_item_type("L10 Light Source", "child", "L10 Light Source")
        light_l9000 = get_or_create_item_type("L9000 Light Source", "child", "L9000 Light Source")
        ccu_1588 = get_or_create_item_type("1588 CCU", "child", "1588 CCU")
        ccu_1488 = get_or_create_item_type("1488 CCU", "child", "1488 CCU")
        ccu_1288 = get_or_create_item_type("1288 CCU", "child", "1288 CCU")
        or_hub = get_or_create_item_type("OR Hub", "child", "OR Hub")
        pinpoint = get_or_create_item_type("Pinpoint", "child", "Pinpoint")
        printer = get_or_create_item_type("Printer", "child", "Printer")
        pole = get_or_create_item_type("roll stand pole", "child", "Roll stand pole")
        base = get_or_create_item_type("roll stand base", "child", "Roll stand base")
        
        # Existing child types
        pneumoclear = get_or_create_item_type("Pneumoclear", "child", "Pneumoclear")
        crossflow = get_or_create_item_type("Crossflow", "child", "Crossflow")
        ccu_1788 = get_or_create_item_type("1788 CCU", "child", "1788 CCU")
        vision_pro = get_or_create_item_type("vision pro monitor", "child", "Vision Pro Monitor")
        oled_monitor = get_or_create_item_type("OLED Monitor", "child", "OLED Monitor")
        
        print()
        
        # ===== GET LOCATIONS =====
        print("Fetching locations...")
        all_locations = get_locations()
        location_types = get_location_types()
        
        # Find location types
        warehouse_type = next((lt for lt in location_types if lt['name'] == "Warehouse"), None)
        client_site_type = next((lt for lt in location_types if lt['name'] == "Client Site"), None)
        quarantine_type = next((lt for lt in location_types if lt['name'] == "Quarantine"), None)
        
        if not warehouse_type or not client_site_type or not quarantine_type:
            raise Exception("Required location types not found")
        
        warehouse_locations = [loc for loc in all_locations if loc['location_type']['id'] == warehouse_type['id']]
        client_site_locations = [loc for loc in all_locations if loc['location_type']['id'] == client_site_type['id']]
        quarantine_locations = [loc for loc in all_locations if loc['location_type']['id'] == quarantine_type['id']]
        
        # Find or create Test Client Site
        test_client_site = next((loc for loc in client_site_locations if loc['name'] == "Test Client Site"), None)
        if not test_client_site:
            print("Creating Test Client Site...")
            test_client_site = create_location("Test Client Site", client_site_type['id'], "123 Test Street")
            client_site_locations.append(test_client_site)
        
        print(f"Found {len(warehouse_locations)} warehouse locations")
        print(f"Found {len(client_site_locations)} client site locations")
        print(f"Found {len(quarantine_locations)} quarantine locations")
        print()
        
        # ===== CREATE PARENT ITEMS WITH CHILDREN =====
        all_parent_items = []
        
        # Light source options for random selection
        light_sources = [light_l12, light_l11, light_l10, light_l9000]
        
        # Sports Tower: crossfire, crossflow, any Light source, vision pro monitor
        print("Creating Sports Tower items...")
        sports_config = [
            {'type': crossfire},
            {'type': crossflow},
            {'type': random.choice(light_sources)},
            {'type': vision_pro}
        ]
        # 9 in warehouses, 1 at test client site
        if warehouse_locations:
            sports_items = create_parent_items_with_children(sports_tower, sports_config, 9, warehouse_locations)
            all_parent_items.extend(sports_items)
        sports_items = create_parent_items_with_children(sports_tower, sports_config, 1, [test_client_site])
        all_parent_items.extend(sports_items)
        print()
        
        # MedEd 1688: 1688 CCU, L11, Pneumoclear, OLED, optionally OR Hub
        print("Creating MedEd 1688 items...")
        meded_1688_config = [
            {'type': ccu_1688},
            {'type': light_l11},
            {'type': pneumoclear},
            {'type': oled_monitor},
            {'type': or_hub, 'optional': True}
        ]
        if warehouse_locations:
            meded_1688_items = create_parent_items_with_children(meded_1688, meded_1688_config, 9, warehouse_locations)
            all_parent_items.extend(meded_1688_items)
        meded_1688_items = create_parent_items_with_children(meded_1688, meded_1688_config, 1, [test_client_site])
        all_parent_items.extend(meded_1688_items)
        print()
        
        # MedEd 1788: 1788 CCU, L12, Pneumoclear, optionally OR Hub
        print("Creating MedEd 1788 items...")
        meded_1788_config = [
            {'type': ccu_1788},
            {'type': light_l12},
            {'type': pneumoclear},
            {'type': or_hub, 'optional': True}
        ]
        if warehouse_locations:
            meded_1788_items = create_parent_items_with_children(meded_1788, meded_1788_config, 9, warehouse_locations)
            all_parent_items.extend(meded_1788_items)
        meded_1788_items = create_parent_items_with_children(meded_1788, meded_1788_config, 1, [test_client_site])
        all_parent_items.extend(meded_1788_items)
        print()
        
        # Clinical 1788: Hub, 1788 CCU, L12, Printer, pinpoint, OLED monitor
        print("Creating Clinical 1788 items...")
        clinical_1788_config = [
            {'type': or_hub},
            {'type': ccu_1788},
            {'type': light_l12},
            {'type': printer},
            {'type': pinpoint},
            {'type': oled_monitor}
        ]
        if warehouse_locations:
            clinical_1788_items = create_parent_items_with_children(clinical_1788, clinical_1788_config, 9, warehouse_locations)
            all_parent_items.extend(clinical_1788_items)
        clinical_1788_items = create_parent_items_with_children(clinical_1788, clinical_1788_config, 1, [test_client_site])
        all_parent_items.extend(clinical_1788_items)
        print()
        
        # Clinical 1688 (RISE Tower): Hub, 1688 CCU, L11, Printer, pinpoint
        print("Creating RISE Tower items...")
        clinical_1688_config = [
            {'type': or_hub},
            {'type': ccu_1688},
            {'type': light_l11},
            {'type': printer},
            {'type': pinpoint}
        ]
        if warehouse_locations:
            rise_items = create_parent_items_with_children(rise_tower, clinical_1688_config, 9, warehouse_locations)
            all_parent_items.extend(rise_items)
        rise_items = create_parent_items_with_children(rise_tower, clinical_1688_config, 1, [test_client_site])
        all_parent_items.extend(rise_items)
        print()
        
        # 1788 Roll Stand: pole, base, OLED monitor
        print("Creating 1788 Roll Stand items...")
        roll_1788_config = [
            {'type': pole},
            {'type': base},
            {'type': oled_monitor}
        ]
        if warehouse_locations:
            roll_1788_items = create_parent_items_with_children(roll_stand_1788, roll_1788_config, 9, warehouse_locations)
            all_parent_items.extend(roll_1788_items)
        roll_1788_items = create_parent_items_with_children(roll_stand_1788, roll_1788_config, 1, [test_client_site])
        all_parent_items.extend(roll_1788_items)
        print()
        
        # 1688 Roll Stand: pole, base
        print("Creating 1688 Roll Stand items...")
        roll_1688_config = [
            {'type': pole},
            {'type': base}
        ]
        if warehouse_locations:
            roll_1688_items = create_parent_items_with_children(roll_stand_1688, roll_1688_config, 9, warehouse_locations)
            all_parent_items.extend(roll_1688_items)
        roll_1688_items = create_parent_items_with_children(roll_stand_1688, roll_1688_config, 1, [test_client_site])
        all_parent_items.extend(roll_1688_items)
        print()
        
        # ===== PLACE ITEMS IN QUARANTINE =====
        if quarantine_locations:
            print("Placing one of each type in quarantine locations...")
            quarantine_types = [
                (sports_tower, sports_config),
                (meded_1688, meded_1688_config),
                (meded_1788, meded_1788_config),
                (clinical_1788, clinical_1788_config),
                (rise_tower, clinical_1688_config),
                (roll_stand_1788, roll_1788_config),
                (roll_stand_1688, roll_1688_config)
            ]
            
            for parent_type, config in quarantine_types:
                quarantine_location = random.choice(quarantine_locations)
                items = create_parent_items_with_children(parent_type, config, 1, [quarantine_location])
                all_parent_items.extend(items)
            print()
        
        # ===== CREATE MOVEMENT HISTORY =====
        all_location_list = warehouse_locations + client_site_locations + quarantine_locations
        if all_parent_items and all_location_list:
            create_movements(all_parent_items, all_location_list, num_movements=100)
        
        print("\n" + "="*50)
        print("Data seeding completed successfully!")
        print("="*50)
        print(f"Total parent items created: {len(all_parent_items)}")
        
    except Exception as e:
        print(f"\nError during seeding: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
