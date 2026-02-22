"""Test backward compatibility for location API paths."""

import requests

STAGING_URL = "http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com"

def login():
    """Login and get token."""
    response = requests.post(
        f"{STAGING_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
        timeout=10
    )
    return response.json()["access_token"]

def test_paths(token):
    """Test both old and new paths."""
    headers = {"Authorization": f"Bearer {token}"}
    
    paths = [
        ("/api/v1/locations/types", "Old location types path"),
        ("/api/v1/location-types", "New location types path"),
        ("/api/v1/locations/locations", "Old locations path"),
        ("/api/v1/locations", "New locations path"),
    ]
    
    print("=" * 70)
    print("Testing Backward Compatibility")
    print("=" * 70)
    
    for path, description in paths:
        try:
            response = requests.get(
                f"{STAGING_URL}{path}",
                headers=headers,
                timeout=10
            )
            status = "✓" if response.status_code == 200 else "✗"
            print(f"\n{status} {description}")
            print(f"   Path: {path}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "N/A"
                print(f"   Results: {count} items")
        except Exception as e:
            print(f"\n✗ {description}")
            print(f"   Path: {path}")
            print(f"   Error: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    token = login()
    test_paths(token)
