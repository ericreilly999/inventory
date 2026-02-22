"""Test location deletion in staging and diagnose issues."""

import requests
import sys
import json

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

def check_migration_status(token):
    """Check if migration has been applied."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nChecking database schema...")
    
    # Try to get locations
    try:
        response = requests.get(
            f"{STAGING_URL}/api/v1/locations",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            locations = response.json()
            print(f"✓ Found {len(locations)} locations")
            return True
        else:
            print(f"✗ Failed to get locations: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def find_deletable_location(token):
    """Find a location with no items."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nLooking for locations with no items...")
    
    try:
        # Get all locations with item counts
        response = requests.get(
            f"{STAGING_URL}/api/v1/locations/with-items",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"✗ Failed to get locations: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        locations = response.json()
        
        # Find locations with 0 items
        for location in locations:
            item_count = location.get("item_count", 0)
            print(f"  {location['name']}: {item_count} items")
            
            if item_count == 0:
                return location
        
        print("\n⚠ No locations without items found")
        return None
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_location_deletion(token, location):
    """Test deleting a location."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\nAttempting to delete location: {location['name']}")
    print(f"Location ID: {location['id']}")
    print(f"Item count: {location.get('item_count', 'unknown')}")
    
    try:
        response = requests.delete(
            f"{STAGING_URL}/api/v1/locations/{location['id']}",
            headers=headers,
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✓ Location deleted successfully!")
            try:
                result = response.json()
                print(f"Message: {result.get('message', 'Deleted')}")
            except:
                pass
            return True
        elif response.status_code == 409:
            print("\n✗ Deletion blocked (409 Conflict)")
            try:
                error = response.json()
                detail = error.get('detail', 'Unknown error')
                print(f"Error: {detail}")
                
                # Analyze the error message
                if "items are still assigned" in detail:
                    print("\n⚠ Validation detected active items (this shouldn't happen!)")
                elif "may be referenced by existing items" in detail:
                    print("\n⚠ IntegrityError from database constraint")
                    print("This suggests the foreign key constraint is still RESTRICT")
                elif "historical" in detail.lower() or "movement" in detail.lower():
                    print("\n⚠ Blocked by historical movement data")
                    print("The migration may not have been applied correctly")
            except:
                print(f"Error: {response.text}")
            return False
        elif response.status_code == 404:
            print("\n✗ Location not found (404)")
            return False
        else:
            print(f"\n✗ Unexpected status code: {response.status_code}")
            try:
                error = response.json()
                print(f"Error detail: {error}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"\n✗ Error during deletion: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_move_history_constraints(token):
    """Check if move_history constraints have been updated."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nChecking move_history table constraints...")
    
    # This would require a direct database query
    # For now, we'll infer from deletion behavior
    print("(Constraint check requires database access)")
    
def main():
    """Main test function."""
    print("=" * 70)
    print("Staging Location Deletion Diagnostic")
    print("=" * 70)
    
    # Login
    print("\n1. Logging in to staging...")
    token = login()
    if not token:
        print("\n✗ Cannot access staging")
        sys.exit(1)
    print("✓ Login successful")
    
    # Check migration status
    print("\n2. Checking API status...")
    if not check_migration_status(token):
        print("\n✗ API not accessible")
        sys.exit(1)
    
    # Find deletable location
    print("\n3. Finding location to delete...")
    location = find_deletable_location(token)
    
    if not location:
        print("\n⚠ Cannot test deletion - no empty locations found")
        print("\nTo create a test location:")
        print("1. Create a new location via UI")
        print("2. Don't assign any items to it")
        print("3. Try to delete it")
        sys.exit(1)
    
    # Test deletion
    print("\n4. Testing location deletion...")
    success = test_location_deletion(token, location)
    
    print("\n" + "=" * 70)
    if success:
        print("✓ Location deletion is working!")
    else:
        print("✗ Location deletion failed")
        print("\nPossible causes:")
        print("1. Migration not applied yet")
        print("2. Foreign key constraints still RESTRICT")
        print("3. Location has historical movement data")
        print("\nNext steps:")
        print("1. Check if migration has been run")
        print("2. Verify database constraints")
        print("3. Check CloudWatch logs for errors")
    print("=" * 70)

if __name__ == "__main__":
    main()
