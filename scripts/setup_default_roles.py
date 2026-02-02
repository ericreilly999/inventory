"""Setup default roles with granular permissions."""
import requests
import os

# Environment-specific configuration
ENVIRONMENTS = {
    "dev": "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com",
    "staging": "http://staging-inventory-alb.us-east-1.elb.amazonaws.com"  # Will be updated after deployment
}

API_BASE_URL = ENVIRONMENTS.get(os.environ.get("ENVIRONMENT", "dev"))
USERNAME = "admin"
PASSWORD = "admin"


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
    print("Login successful!\n")
    return token


def get_existing_roles(token):
    """Get existing roles."""
    response = requests.get(
        f"{API_BASE_URL}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return {role['name']: role for role in response.json()}
    return {}


def create_role(token, name, description, permissions):
    """Create a role."""
    response = requests.post(
        f"{API_BASE_URL}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "description": description,
            "permissions": permissions
        }
    )
    if response.status_code == 200:
        print(f"✓ Created role: {name}")
        return response.json()
    else:
        print(f"✗ Failed to create {name}: {response.text}")
        return None


def main():
    """Main function."""
    environment = os.environ.get("ENVIRONMENT", "dev")
    print("="*70)
    print(f"SETTING UP DEFAULT ROLES - {environment.upper()} ENVIRONMENT")
    print(f"API URL: {API_BASE_URL}")
    print("="*70)
    
    token = login()
    existing_roles = get_existing_roles(token)
    
    # Define default roles with granular permissions
    default_roles = [
        {
            "name": "Warehouse Manager",
            "description": "Full access to inventory and location management",
            "permissions": {
                "inventory:read": True,
                "inventory:write": True,
                "inventory:delete": True,
                "location:read": True,
                "location:write": True,
                "location:delete": True,
                "reporting:read": True,
                "user:read": False,
                "user:write": False,
                "user:delete": False,
                "user:admin": False,
                "role:admin": False
            }
        },
        {
            "name": "Inventory Clerk",
            "description": "Read and write access to inventory, read-only for locations",
            "permissions": {
                "inventory:read": True,
                "inventory:write": True,
                "inventory:delete": False,
                "location:read": True,
                "location:write": False,
                "location:delete": False,
                "reporting:read": True,
                "user:read": False,
                "user:write": False,
                "user:delete": False,
                "user:admin": False,
                "role:admin": False
            }
        },
        {
            "name": "Viewer",
            "description": "Read-only access to inventory and locations",
            "permissions": {
                "inventory:read": True,
                "inventory:write": False,
                "inventory:delete": False,
                "location:read": True,
                "location:write": False,
                "location:delete": False,
                "reporting:read": True,
                "user:read": False,
                "user:write": False,
                "user:delete": False,
                "user:admin": False,
                "role:admin": False
            }
        },
        {
            "name": "Location Manager",
            "description": "Full access to locations, read access to inventory",
            "permissions": {
                "inventory:read": True,
                "inventory:write": False,
                "inventory:delete": False,
                "location:read": True,
                "location:write": True,
                "location:delete": True,
                "reporting:read": True,
                "user:read": False,
                "user:write": False,
                "user:delete": False,
                "user:admin": False,
                "role:admin": False
            }
        },
        {
            "name": "User Manager",
            "description": "Manage users but not roles",
            "permissions": {
                "inventory:read": True,
                "inventory:write": False,
                "inventory:delete": False,
                "location:read": True,
                "location:write": False,
                "location:delete": False,
                "reporting:read": True,
                "user:read": True,
                "user:write": True,
                "user:delete": True,
                "user:admin": True,
                "role:admin": False
            }
        }
    ]
    
    print("\nCreating default roles...")
    print("-" * 70)
    
    created_count = 0
    skipped_count = 0
    
    for role_def in default_roles:
        if role_def["name"] in existing_roles:
            print(f"⊘ Skipped (already exists): {role_def['name']}")
            skipped_count += 1
        else:
            result = create_role(
                token,
                role_def["name"],
                role_def["description"],
                role_def["permissions"]
            )
            if result:
                created_count += 1
    
    print("\n" + "="*70)
    print("SETUP COMPLETED!")
    print("="*70)
    print(f"Roles created: {created_count}")
    print(f"Roles skipped: {skipped_count}")
    print(f"Total roles: {len(existing_roles) + created_count}")


if __name__ == "__main__":
    main()
