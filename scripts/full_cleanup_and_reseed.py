"""
Full cleanup and reseed with correct SKU format.
Parent items: Simple numbers (1, 2, 3...) per item type
Child items: Serial numbers (e.g., 2204FE3842)
"""
import requests
import random
import time

# API Configuration
API_BASE_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"
USERNAME = "admin"
PASSWORD = "admin"

session = requests.Session()
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


def delete_all_inventory():
    """Delete ALL parent items (cascades to children)."""
    print("="*70)
    print("DELETING ALL EXISTING INVENTORY")
    print("="*70)
    
    response = session.get(f"{API_BASE_URL}/api/v1/items/parent?limit=1000")
    if response.status_code == 200:
        items = response.json()
        print(f"\nFound {len(items)} parent items to delete...")
        
        for i, item in enumerate(items, 1):
            response = session.delete(f"{API_BASE_URL}/api/v1/items/parent/{item['id']}")
            if response.status_code in [200, 204]:
                if i % 10 == 0:
                    print(f"  Deleted {i}/{len(items)}...")
            time.sleep(0.3)
        
        print(f"Deleted all {len(items)} parent items\n")


def get_next_parent_sku(item_type_name: str) -> str:
    """Get next numeric SKU for a parent item type."""
    if item_type_name not in parent_sku_counters:
        parent_sku_counters[item_type_name] = 1
    else:
        parent_sku_counters[item_type_name] += 1
    return str(parent_sku_counters[item_type_name])


def generate_child_sku() -> str:
    """Generate serial number style SKU."""
    digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    hex_chars = ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
    return f"{digits}{hex_chars}"


def get_or_create_item_type(name: str, category: str):
    """Get or create an item type."""
    response = session.get(f"{API_BASE_URL}/api/v1/items/types?category={category}")
    if response.status_code == 200:
        for item_type in response.json():
            if item_type['name'] == name:
                return item_type
    
    response = session.post(
        f"{API_BASE_URL}/api/v1/items/types",
        json={"name": name, "category": category, "description": name}
    )
    if response.status_code in [200, 201]:
        return response.json()
    raise Exception(f"Failed to create item type {name}")


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
    print(f"Warning: Failed to create parent {sku}: {response.text[:200]}")
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
    return response.json() if response.status_code in [200, 201] else None


def create_parent_with_children(parent_type, child_configs, location):
    """Create parent with children."""
    sku = get_next_parent_sku(parent_type['name'])
    
    parent_item = create_parent_item(
        sku=sku,
        description=f"{parent_type['name']} unit {sku}",
        item_type_id=parent_type['id'],
        location_id=location['id']
    )
    
    if not parent_item:
        time.sleep(2.0)
        return None
    
    print(f"  SKU {sku} ({parent_type['name']}) at {location['name']}")
    
    for child_config in child_configs:
        child_type = child_config['type']
        is_optional = child_config.get('optional', False)
        
        if is_optional and random.random() < 0.5:
            continue
        
        child_sku = generate_child_sku()
        child_item = create_child_item(
            sku=child_sku,
            description=f"{child_type['name']}",
            item_type_id=child_type['id'],
            parent_item_id=parent_item['id']
        )
        if child_item:
            print(f"    + {child_sku} ({child_type['name']})")
        
        time.sleep(2.0)
    
    time.sleep(2.0)
    return parent_item


def main():
    """Main function."""
    try:
        login()
        
        # Step 1: Delete everything
        delete_all_inventory()
        
        # Step 2: Setup item types
        print("="*70)
        print("SETTING UP ITEM TYPES")
        print("="*70 + "\n")
        
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
        
        print("Item types ready!\n")
        
        # Step 3: Get locations
        print("="*70)
        print("SETTING UP LOCATIONS")
        print("="*70 + "\n")
        
        all_locs = session.get(f"{API_BASE_URL}/api/v1/locations/locations").json()
        loc_types = session.get(f"{API_BASE_URL}/api/v1/locations/types").json()
        
        warehouse_type = next(lt for lt in loc_types if lt['name'] == "Warehouse")
        client_type = next(lt for lt in loc_types if lt['name'] == "Client Site")
        quarantine_type = next(lt for lt in loc_types if lt['name'] == "Quarantine")
        
        warehouses = [l for l in all_locs if l['location_type']['id'] == warehouse_type['id']]
        clients = [l for l in all_locs if l['location_type']['id'] == client_type['id']]
        quarantines = [l for l in all_locs if l['location_type']['id'] == quarantine_type['id']]
        
        # Create hospitals
        hospitals = []
        for name in ["Hospital A", "Hospital B", "Hospital C", "Hospital D", "Hospital E"]:
            resp = session.post(
                f"{API_BASE_URL}/api/v1/locations/locations",
                json={"name": name, "location_type_id": client_type['id'], "address": f"{name} Medical Center"}
            )
            if resp.status_code in [200, 201]:
                hospitals.append(resp.json())
                print(f"Created: {name}")
            time.sleep(0.5)
        
        clients.extend(hospitals)
        test_client = clients[0]
        
        print(f"\nLocations: {len(warehouses)} warehouses, {len(clients)} clients, {len(quarantines)} quarantines\n")
        
        # Step 4: Create inventory
        print("="*70)
        print("CREATING INVENTORY")
        print("="*70 + "\n")
        
        light_sources = [light_l12, light_l11, light_l10, light_l9000]
        all_items = []
        
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
        
        for config in configs:
            parent_type = config['type']
            print(f"\n{parent_type['name']}:")
            
            # 8 in warehouses
            for _ in range(8):
                item = create_parent_with_children(parent_type, config['children'], random.choice(warehouses))
                if item:
                    all_items.append(item)
            
            # 1 at test client
            item = create_parent_with_children(parent_type, config['children'], test_client)
            if item:
                all_items.append(item)
            
            # 1 in quarantine
            item = create_parent_with_children(parent_type, config['children'], random.choice(quarantines))
            if item:
                all_items.append(item)
        
        print(f"\n\nTotal created: {len(all_items)} parent items")
        
        # Step 5: Create movements
        print("\n" + "="*70)
        print("CREATING MOVEMENTS")
        print("="*70 + "\n")
        
        # Refresh items
        fresh_items = session.get(f"{API_BASE_URL}/api/v1/items/parent?limit=1000").json()
        warehouse_items = [i for i in fresh_items if any(w['id'] == i['current_location_id'] for w in warehouses)]
        
        movements = 0
        
        # Move to hospitals
        for hospital in hospitals:
            num = min(3, len(warehouse_items))
            items_to_move = random.sample(warehouse_items, num)
            
            print(f"Moving to {hospital['name']}:")
            for item in items_to_move:
                if move_parent_item(item['id'], hospital['id'], f"Deployed to {hospital['name']}"):
                    print(f"  Moved SKU {item['sku']}")
                    movements += 1
                    warehouse_items.remove(item)
                time.sleep(1.5)
        
        # Additional movements
        print("\nCreating additional movements:")
        fresh_items = session.get(f"{API_BASE_URL}/api/v1/items/parent?limit=1000").json()
        all_locs_combined = warehouses + clients + quarantines
        
        for i in range(30):
            if not fresh_items:
                break
            
            item = random.choice(fresh_items)
            available = [l for l in all_locs_combined if l['id'] != item['current_location_id']]
            
            if available:
                to_loc = random.choice(available)
                if move_parent_item(item['id'], to_loc['id'], f"Movement #{i+1}"):
                    item['current_location_id'] = to_loc['id']
                    movements += 1
                    if (i + 1) % 10 == 0:
                        print(f"  Created {i + 1} movements...")
                time.sleep(1.5)
        
        print(f"\nTotal movements: {movements}")
        
        print("\n" + "="*70)
        print("RESEEDING COMPLETE!")
        print("="*70)
        print(f"Parent items: {len(all_items)}")
        print(f"Movements: {movements}")
        print(f"Hospitals: {len(hospitals)}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
