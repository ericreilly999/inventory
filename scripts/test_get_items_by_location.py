"""Test getting items by location."""

import requests

STAGING_URL = "http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com"

def login():
    response = requests.post(
        f"{STAGING_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
        timeout=10
    )
    return response.json()["access_token"]

token = login()
headers = {"Authorization": f"Bearer {token}"}

# Get locations with items
response = requests.get(
    f"{STAGING_URL}/api/v1/locations/with-items",
    headers=headers,
    timeout=10
)

locations = response.json()

# Find Damage Quarantine
damage_q = None
for loc in locations:
    if loc['name'] == 'Damage Quarantine':
        damage_q = loc
        break

if damage_q:
    print(f"Damage Quarantine:")
    print(f"  ID: {damage_q['id']}")
    print(f"  Item count: {damage_q.get('item_count', 0)}")
    
    # Try to get items
    print(f"\nTrying to get items...")
    response = requests.get(
        f"{STAGING_URL}/api/v1/items/parent-items",
        headers=headers,
        params={"location_id": damage_q['id']},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        items = response.json()
        print(f"Items returned: {len(items)}")
        if items:
            for item in items[:3]:
                print(f"  - {item.get('name', 'Unknown')} (SKU: {item.get('sku', 'N/A')})")
    else:
        print(f"Error: {response.text}")
