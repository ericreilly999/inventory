"""
Complete inventory reseeding with proper SKU management per item type.
Parent items: Simple numeric SKUs (1, 2, 3...) per item type
Child items: Serial number format (e.g., 2204FE3842)
"""
import requests
import random
from datetime import datetime
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

# Global session with auth token
session = requests.Session()

# SKU counters per parent item type (simple numbers)
parent_sku_counters = {}


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


def get_next_parent_sku(item_type_name: str) -> str:
    """Get next numeric SKU for a parent item type."""
    if item_type_name not in parent_sku_counters:
        parent_sku_counters[item_type_name] = 1
    else:
        parent_sku_counters[item_type_name] += 1
    return str(parent_sku_counters[item_type_name])


def generate_child_sku() -> str:
    """Generate a serial number style SKU for child items."""
    # Format: 4 digits + 6 hex characters (e.g., 2204FE3842)
    digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    hex_chars = ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
    return f"{digits}{hex_chars}"


def delete_all_parent_items():
    """Delete all parent items."""
    response = session.get(f"{API_BASE_URL}/api/v1/items/parent?limit=1000")
    if response.status_code == 200:
        items = response.json()
        print(f"Deleting {len(items)} parent items...")
        for item in items:
            session.delete(f"{API_BASE_URL}/api/v1/items/parent/{item['id']}")
            time.sleep(0.2)
        print("All parent items deleted")


def get_or_create_item_type(name: str, category: str, description: str = ""):
    """Get or create an item type."""
    response = session.get(f"{API_BASE_URL}/api/v1/items/types?category={category}")
    if response.status_code == 200:
        item_types = response.json()
        for item_type in item_types:
            if item_type['name'] == name:
                return item_type
    
    response = session.post(
        f"{API_BASE_URL}/api/v1/items/types",
        json={"name": name, "category": category, "description": description}
    )
    if response.status_code in [200, 201]:
        return response.json()
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
    return None


def create_parent_item(sku: str, description: str, item_type_id: str, location_id: str):
    """Create a parent item."""
    response = session.post(
        f"{API_BASE_URL}/api/v1/items/parent",
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
        print(f"Warning: Failed to create parent item {sku}: {response.text[:200]}")
        return None


def create_child_item(sku: str, description: str, item_type_id: str, parent_item_id: str):
    """Create a child item."""
    response = session.post(
        f"{API_BASE_URL}/api/v1/items/child",
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
        print(f"Warning: Failed to create child item {sku}: {response.text[:200]}")
        return None


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


def create_parent_with_children(parent_type, child_configs, location):
    """Create a parent item with its child items."""
    # Get simple numeric SKU for this parent type
    sku = get_next_parent_sku(parent_type['name'])
    
    # Create parent item
    parent_item = create_parent_item(
        sku=sku,
        description=f"{parent_type['name']} unit {sku}",
        item_type_id=parent_type['id'],
        location_id=location['id']
    )
    
    if not parent_item:
        time.sleep(2.0)
        return None
    
    print(f"  Created: {sku} at {location['name']}")
    
    # Create child items
    for child_config in child_configs:
        child_type = child_config['type']
        is_optional = child_config.get('optional', False)
        
        # Skip optional items randomly (50% chance)
        if is_optional and random.random() < 0.5:
            continue
        
        # Generate serial number style SKU for child
        child_sku = generate_child_sku()
        child_item = create_child_item(
            sku=child_sku,
            description=f"{child_type['name']} for {parent_type['name']} {sku}",
            item_type_id=child_type['id'],
            parent_item_id=parent_item['id']
        )
        if child_item:
            print(f"    + {child_sku} ({child_type['name']})")
        
        time.sleep(2.0)
    
    time.sleep(2.0)
    return parent_item


def main():
    """Main seeding function."""
    try:
        environment = os.environ.get("ENVIRONMENT", "dev")
        print("="*70)
        print(f"COMPLETE INVENTORY RESEEDING - {environment.upper()} ENVIRONMENT")
        print(f"API URL: {API_BASE_URL}")
        print("="*70)
        
        # Login
        login()
        
        # Step 1: Clear existing data
        print("\n[1/6] Clearing existing inventory...")
        delete_all_parent_items()
        
        # Step 2: Create/verify item types
        print("\n[2/6] Setting up item types...")
        
        # Parent types
        sports_tower = get_or_create_item_type("Sports Tower", "parent")
        meded_1688 = get_or_create_item_type("MedEd 1688", "parent")
        meded_1788 = get_or_create_item_type("MedEd 1788", "parent")
        clinical_1788 = get_or_create_item_type("Clinical 1788", "parent")
        rise_tower = get_or_create_item_type("RISE Tower", "parent")
        roll_1788 = get_or_create_item_type("1788 Roll Stand", "parent")
        roll_1688 = get_or_create_item_type("1688 Roll Stand", "parent")
        
        # Child types
        crossfire = get_or_create_item_type("Crossfire", "child")
        crossflow = get_or_create_item_type("Crossflow", "child")
        pneumoclear = get_or_create_item_type("Pneumoclear", "child")
        ccu_1688 = get_or_create_item_type("1688 CCU", "child")
        ccu_1788 = get_or_create_item_type("1788 CCU", "child")
        ccu_1588 = get_or_create_item_type("1588 CCU", "child")
        ccu_1488 = get_or_create_item_type("1488 CCU", "child")
        ccu_1288 = get_or_create_item_type("1288 CCU", "child")
        light_l12 = get_or_create_item_type("L12 Light Source", "child")
        light_l11 = get_or_create_item_type("L11 Light Source", "child")
        light_l10 = get_or_create_item_type("L10 Light Source", "child")
        light_l9000 = get_or_create_item_type("L9000 Light Source", "child")
        or_hub = get_or_create_item_type("OR Hub", "child")
        pinpoint = get_or_create_item_type("Pinpoint", "child")
        printer = get_or_create_item_type("Printer", "child")
        pole = get_or_create_item_type("roll stand pole", "child")
        base = get_or_create_item_type("roll stand base", "child")
        vision_pro = get_or_create_item_type("vision pro monitor", "child")
        oled = get_or_create_item_type("OLED Monitor", "child")
        
        print("Item types ready!")
        
        # Step 3: Setup locations
        print("\n[3/6] Setting up locations...")
        all_locations = get_locations()
        location_types = get_location_types()
        
        warehouse_type = next((lt for lt in location_types if lt['name'] == "Warehouse"), None)
        client_site_type = next((lt for lt in location_types if lt['name'] == "Client Site"), None)
        quarantine_type = next((lt for lt in location_types if lt['name'] == "Quarantine"), None)
        
        warehouse_locs = [loc for loc in all_locations if loc['location_type']['id'] == warehouse_type['id']]
        client_site_locs = [loc for loc in all_locations if loc['location_type']['id'] == client_site_type['id']]
        quarantine_locs = [loc for loc in all_locations if loc['location_type']['id'] == quarantine_type['id']]
        
        # Create hospital locations
        hospitals = []
        for name in ["Hospital A", "Hospital B", "Hospital C", "Hospital D", "Hospital E"]:
            hospital = create_location(name, client_site_type['id'], f"{name} Medical Center")
            if hospital:
                hospitals.append(hospital)
                print(f"  Created: {name}")
                time.sleep(0.5)
        
        client_site_locs.extend(hospitals)
        
        print(f"Locations: {len(warehouse_locs)} warehouses, {len(client_site_locs)} client sites, {len(quarantine_locs)} quarantine")
        
        # Step 4: Create inventory
        print("\n[4/6] Creating inventory...")
        all_parent_items = []
        
        light_sources = [light_l12, light_l11, light_l10, light_l9000]
        
        # Define configurations
        configs = [
            {
                'type': sports_tower,
                'children': [
                    {'type': crossfire},
                    {'type': crossflow},
                    {'type': random.choice(light_sources)},
                    {'type': vision_pro}
                ]
            },
            {
                'type': meded_1688,
                'children': [
                    {'type': ccu_1688},
                    {'type': light_l11},
                    {'type': pneumoclear},
                    {'type': oled},
                    {'type': or_hub, 'optional': True}
                ]
            },
            {
                'type': meded_1788,
                'children': [
                    {'type': ccu_1788},
                    {'type': light_l12},
                    {'type': pneumoclear},
                    {'type': or_hub, 'optional': True}
                ]
            },
            {
                'type': clinical_1788,
                'children': [
                    {'type': or_hub},
                    {'type': ccu_1788},
                    {'type': light_l12},
                    {'type': printer},
                    {'type': pinpoint},
                    {'type': oled}
                ]
            },
            {
                'type': rise_tower,
                'children': [
                    {'type': or_hub},
                    {'type': ccu_1688},
                    {'type': light_l11},
                    {'type': printer},
                    {'type': pinpoint}
                ]
            },
            {
                'type': roll_1788,
                'children': [
                    {'type': pole},
                    {'type': base},
                    {'type': oled}
                ]
            },
            {
                'type': roll_1688,
                'children': [
                    {'type': pole},
                    {'type': base}
                ]
            }
        ]
        
        # Create 10 of each type
        for config in configs:
            parent_type = config['type']
            child_configs = config['children']
            
            print(f"\nCreating {parent_type['name']} items:")
            
            # 8 in warehouses
            for i in range(8):
                if warehouse_locs:
                    location = random.choice(warehouse_locs)
                    item = create_parent_with_children(parent_type, child_configs, location)
                    if item:
                        all_parent_items.append(item)
            
            # 1 at first client site
            if client_site_locs:
                item = create_parent_with_children(parent_type, child_configs, client_site_locs[0])
                if item:
                    all_parent_items.append(item)
            
            # 1 in quarantine
            if quarantine_locs:
                location = random.choice(quarantine_locs)
                item = create_parent_with_children(parent_type, child_configs, location)
                if item:
                    all_parent_items.append(item)
        
        print(f"\nTotal parent items created: {len(all_parent_items)}")
        
        # Step 5: Move items to hospitals
        print("\n[5/6] Moving items to hospitals...")
        movements_created = 0
        
        # Get fresh list of items in warehouses
        all_items_fresh = []
        response = session.get(f"{API_BASE_URL}/api/v1/items/parent?limit=1000")
        if response.status_code == 200:
            all_items_fresh = response.json()
        
        warehouse_items = [item for item in all_items_fresh 
                          if any(loc['id'] == item['current_location_id'] for loc in warehouse_locs)]
        
        for hospital in hospitals:
            num_to_move = min(3, len(warehouse_items))
            items_to_move = random.sample(warehouse_items, num_to_move)
            
            print(f"\n  Moving to {hospital['name']}:")
            for item in items_to_move:
                movement = move_parent_item(item['id'], hospital['id'], f"Deployed to {hospital['name']}")
                if movement:
                    print(f"    Moved {item['sku']}")
                    movements_created += 1
                    warehouse_items.remove(item)
                time.sleep(1.5)
        
        # Step 6: Create additional movements
        print(f"\n[6/6] Creating additional movement history...")
        
        # Refresh item list
        response = session.get(f"{API_BASE_URL}/api/v1/items/parent?limit=1000")
        if response.status_code == 200:
            all_items_fresh = response.json()
        
        all_locs = warehouse_locs + client_site_locs + quarantine_locs
        
        for i in range(30):
            if not all_items_fresh:
                break
            
            item = random.choice(all_items_fresh)
            current_loc_id = item['current_location_id']
            available_locs = [loc for loc in all_locs if loc['id'] != current_loc_id]
            
            if available_locs:
                to_loc = random.choice(available_locs)
                movement = move_parent_item(item['id'], to_loc['id'], f"Movement #{i+1}")
                if movement:
                    item['current_location_id'] = to_loc['id']
                    movements_created += 1
                    if (i + 1) % 10 == 0:
                        print(f"  Created {i + 1} movements...")
                time.sleep(1.5)
        
        print(f"\nTotal movements created: {movements_created}")
        
        print("\n" + "="*70)
        print("RESEEDING COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"Parent items: {len(all_parent_items)}")
        print(f"Movements: {movements_created}")
        print(f"Hospitals: {len(hospitals)}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
