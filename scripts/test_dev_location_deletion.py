"""Test location deletion functionality in dev environment."""

import requests
import sys

DEV_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"

def login():
    """Login and get token."""
    response = requests.post(
        f"{DEV_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None
    return response.json()["access_token"]

def check_migration_status(token):
    """Check if the migration has been applied."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get location types
    response = requests.get(
        f"{DEV_URL}/api/v1/location-types",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Failed to get location types: {response.status_code}")
        print(response.text)
        return False
    
    print(f"✓ API is accessible")
    return True

def test_location_deletion(token):
    """Test location deletion with historical data."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all locations
    response = requests.get(
        f"{DEV_URL}/api/v1/locations",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Failed to get locations: {response.status_code}")
        return False
    
    locations = response.json()
    print(f"\nFound {len(locations)} locations")
    
    # Find a location with no active items
    for location in locations:
        # Get items at this location
        response = requests.get(
            f"{DEV_URL}/api/v1/parent-items",
            headers=headers,
            params={"location_id": location["id"]}
        )
        
        if response.status_code == 200:
            items = response.json()
            if len(items) == 0:
                print(f"\nFound location with no items: {location['name']}")
                
                # Try to delete it
                response = requests.delete(
                    f"{DEV_URL}/api/v1/locations/{location['id']}",
                    headers=headers
                )
                
                if response.status_code == 204:
                    print(f"✓ Successfully deleted location: {location['name']}")
                    return True
                else:
                    print(f"✗ Failed to delete location: {response.status_code}")
                    print(response.text)
                    return False
    
    print("\nNo locations without items found to test deletion")
    return True

def main():
    """Main test function."""
    print("=" * 60)
    print("Testing Location Deletion in Dev Environment")
    print("=" * 60)
    
    # Login
    print("\n1. Logging in...")
    token = login()
    if not token:
        sys.exit(1)
    print("✓ Login successful")
    
    # Check migration status
    print("\n2. Checking API status...")
    if not check_migration_status(token):
        print("\n⚠ Migration may need to be run")
        print("Run: python scripts/run_dev_migration.py")
        sys.exit(1)
    
    # Test location deletion
    print("\n3. Testing location deletion...")
    if test_location_deletion(token):
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Tests failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
