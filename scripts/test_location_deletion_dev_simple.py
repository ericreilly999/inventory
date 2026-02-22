"""Simple test for location deletion in dev - tests current behavior."""

import requests
import sys

DEV_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"

def login():
    """Login and get token."""
    try:
        response = requests.post(
            f"{DEV_URL}/api/v1/auth/login",
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

def test_current_behavior(token):
    """Test current location deletion behavior."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "=" * 60)
    print("Testing Current Location Deletion Behavior")
    print("=" * 60)
    
    # Get all locations
    try:
        response = requests.get(
            f"{DEV_URL}/api/v1/locations",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"\n✗ Failed to get locations: {response.status_code}")
            print(response.text)
            return False
        
        locations = response.json()
        print(f"\n✓ Found {len(locations)} locations in dev")
        
        # Show location summary
        for loc in locations[:5]:  # Show first 5
            print(f"  - {loc['name']} (ID: {loc['id'][:8]}...)")
        
        if len(locations) > 5:
            print(f"  ... and {len(locations) - 5} more")
        
        print("\n" + "=" * 60)
        print("Current Status:")
        print("=" * 60)
        print("✓ Dev environment is accessible")
        print("✓ API is responding")
        print(f"✓ {len(locations)} locations exist")
        print("\nNote: Migration needs to be applied to test deletion")
        print("      with historical data.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("Dev Environment Location Deletion Test")
    print("=" * 60)
    
    # Login
    print("\n1. Logging in to dev environment...")
    token = login()
    if not token:
        print("\n✗ Cannot access dev environment")
        sys.exit(1)
    print("✓ Login successful")
    
    # Test current behavior
    print("\n2. Checking current state...")
    if test_current_behavior(token):
        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        print("The dev environment is accessible and working.")
        print("\nTo fully test the location deletion feature:")
        print("1. The migration needs to be applied")
        print("2. Or we can deploy to staging (fresh database)")
        print("\nRecommendation: Deploy to staging for clean testing")
    else:
        print("\n✗ Test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
