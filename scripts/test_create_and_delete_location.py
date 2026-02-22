"""Test creating and immediately deleting a location in staging."""

import requests
import sys

STAGING_URL = "http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com"

def login():
    """Login and get token."""
    try:
        response = requests.post(
            f"{STAGING_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
            timeout=10
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            print(response.text)
            return None
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login error: {e}")
        return None

def get_location_types(token):
    """Get location types."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{STAGING_URL}/api/v1/location-types/",
        headers=headers,
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    return []

def create_location(token, location_type_id):
    """Create a test location."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Test Location for Deletion",
        "location_type_id": location_type_id,
        "address": "Test Address"
    }
    response = requests.post(
        f"{STAGING_URL}/api/v1/locations/",
        headers=headers,
        json=data,
        timeout=10
    )
    return response

def delete_location(token, location_id):
    """Delete a location."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{STAGING_URL}/api/v1/locations/{location_id}",
        headers=headers,
        timeout=10
    )
    return response

def main():
    """Main test function."""
    print("=" * 70)
    print("Test: Create and Delete Location")
    print("=" * 70)
    
    # Login
    print("\n1. Logging in...")
    token = login()
    if not token:
        print("✗ Login failed")
        sys.exit(1)
    print("✓ Login successful")
    
    # Get location types
    print("\n2. Getting location types...")
    location_types = get_location_types(token)
    if not location_types:
        print("✗ No location types found")
        sys.exit(1)
    print(f"✓ Found {len(location_types)} location types")
    location_type_id = location_types[0]["id"]
    print(f"Using location type: {location_types[0]['name']}")
    
    # Create location
    print("\n3. Creating test location...")
    response = create_location(token, location_type_id)
    if response.status_code not in [200, 201]:
        print(f"✗ Failed to create location: {response.status_code}")
        print(response.text)
        sys.exit(1)
    location = response.json()
    print(f"✓ Created location: {location['name']} (ID: {location['id']})")
    
    # Delete location immediately
    print("\n4. Deleting location...")
    response = delete_location(token, location['id'])
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("\n✓ Location deleted successfully!")
        print("\n" + "=" * 70)
        print("SUCCESS: Location deletion is working!")
        print("=" * 70)
        return True
    else:
        print("\n✗ Location deletion failed")
        print("\n" + "=" * 70)
        print("FAILURE: Location deletion is still broken")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
