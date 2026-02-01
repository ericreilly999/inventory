"""
Rollback seeded inventory data by deleting all parent items, child items, and custom item types.
"""
import requests

# API Configuration
API_BASE_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"
USERNAME = "admin"
PASSWORD = "admin"

# Global session with auth token
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

def delete_all_parent_items():
    """Delete all parent items."""
    print("Fetching all parent items...")
    response = session.get(f"{API_BASE_URL}/api/v1/items/parent")
    if response.status_code != 200:
        print(f"Failed to fetch parent items: {response.text}")
        return
    
    parent_items = response.json()
    print(f"Found {len(parent_items)} parent items to delete")
    
    for item in parent_items:
        response = session.delete(f"{API_BASE_URL}/api/v1/items/parent/{item['id']}")
        if response.status_code in [200, 204]:
            print(f"Deleted parent item: {item['sku']}")
        else:
            print(f"Failed to delete parent item {item['sku']}: {response.text[:100]}")

def delete_all_item_types():
    """Delete all custom item types (keep only the default ones)."""
    print("\nFetching all item types...")
    
    # Get parent item types
    response = session.get(f"{API_BASE_URL}/api/v1/items/types?category=parent")
    if response.status_code == 200:
        parent_types = response.json()
        print(f"Found {len(parent_types)} parent item types")
        
        # Delete custom types (not the default ones)
        default_types = ["Equipment", "Furniture"]
        for item_type in parent_types:
            if item_type['name'] not in default_types:
                response = session.delete(f"{API_BASE_URL}/api/v1/items/types/{item_type['id']}")
                if response.status_code in [200, 204]:
                    print(f"Deleted parent item type: {item_type['name']}")
                else:
                    print(f"Failed to delete item type {item_type['name']}: {response.text[:100]}")
    
    # Get child item types
    response = session.get(f"{API_BASE_URL}/api/v1/items/types?category=child")
    if response.status_code == 200:
        child_types = response.json()
        print(f"Found {len(child_types)} child item types")
        
        # Delete custom types (not the default ones)
        default_types = ["Component", "Accessory"]
        for item_type in child_types:
            if item_type['name'] not in default_types:
                response = session.delete(f"{API_BASE_URL}/api/v1/items/types/{item_type['id']}")
                if response.status_code in [200, 204]:
                    print(f"Deleted child item type: {item_type['name']}")
                else:
                    print(f"Failed to delete item type {item_type['name']}: {response.text[:100]}")

def main():
    """Main rollback function."""
    try:
        print("Starting data rollback...\n")
        login()
        
        # Delete parent items first (this will cascade delete child items)
        delete_all_parent_items()
        
        # Delete custom item types
        delete_all_item_types()
        
        print("\n" + "="*50)
        print("Data rollback completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\nError during rollback: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
