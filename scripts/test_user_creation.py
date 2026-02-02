"""Test user creation to identify issues."""
import requests

API_BASE_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"
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
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None
    
    token = response.json()["access_token"]
    print("Login successful!\n")
    return token


def get_roles(token):
    """Get all roles."""
    print("Fetching roles...")
    response = requests.get(
        f"{API_BASE_URL}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        roles = response.json()
        print(f"Found {len(roles)} roles:")
        for role in roles:
            print(f"  - {role['name']} (ID: {role['id']})")
            print(f"    Permissions: {role['permissions']}")
        return roles
    else:
        print(f"Error: {response.text}")
        return []


def create_test_user(token, role_id):
    """Try to create a test user."""
    print("\nAttempting to create test user...")
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "testuser123",
            "email": "testuser123@example.com",
            "password": "TestPassword123!",
            "role_id": role_id
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.status_code == 200


def main():
    """Main function."""
    token = login()
    if not token:
        return
    
    roles = get_roles(token)
    if not roles:
        print("\nNo roles found! This is the issue - we need to create default roles.")
        return
    
    # Try to create a user with the first role
    if roles:
        create_test_user(token, roles[0]['id'])


if __name__ == "__main__":
    main()
