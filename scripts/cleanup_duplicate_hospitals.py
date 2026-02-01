"""
Cleanup duplicate hospital locations.
Keep only one of each Hospital A, B, C, D, E.
"""
import requests
import time

# API Configuration
API_BASE_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"
USERNAME = "admin"
PASSWORD = "admin"

session = requests.Session()


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


def get_all_locations():
    """Get all locations."""
    response = session.get(f"{API_BASE_URL}/api/v1/locations/locations?limit=1000")
    if response.status_code != 200:
        raise Exception(f"Failed to get locations: {response.text}")
    return response.json()


def delete_location(location_id: str):
    """Delete a location."""
    response = session.delete(f"{API_BASE_URL}/api/v1/locations/locations/{location_id}")
    return response.status_code in [200, 204]


def main():
    """Main function."""
    try:
        print("="*70)
        print("CLEANING UP DUPLICATE HOSPITAL LOCATIONS")
        print("="*70)
        
        # Login
        login()
        
        # Get all locations
        print("Fetching all locations...")
        all_locations = get_all_locations()
        print(f"Found {len(all_locations)} total locations\n")
        
        # Find hospital duplicates
        hospital_names = ["Hospital A", "Hospital B", "Hospital C", "Hospital D", "Hospital E"]
        
        for hospital_name in hospital_names:
            # Find all locations with this name
            matching_locations = [loc for loc in all_locations if loc['name'] == hospital_name]
            
            if len(matching_locations) == 0:
                print(f"{hospital_name}: Not found")
            elif len(matching_locations) == 1:
                print(f"{hospital_name}: OK (1 location)")
            else:
                print(f"{hospital_name}: Found {len(matching_locations)} duplicates")
                
                # Keep the first one, delete the rest
                to_keep = matching_locations[0]
                to_delete = matching_locations[1:]
                
                print(f"  Keeping: {to_keep['id']}")
                for loc in to_delete:
                    if delete_location(loc['id']):
                        print(f"  Deleted: {loc['id']}")
                    else:
                        print(f"  Failed to delete: {loc['id']}")
                    time.sleep(0.5)
        
        print("\n" + "="*70)
        print("CLEANUP COMPLETED!")
        print("="*70)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
