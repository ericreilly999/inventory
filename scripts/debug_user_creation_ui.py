"""Debug user creation to see exact error response."""
import requests
import json

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
    if response.status_code == 200:
        roles = response.json()
        print(f"Found {len(roles)} roles\n")
        return roles
    else:
        print(f"Error fetching roles: {response.text}")
        return []


def test_user_creation_scenarios(token, roles):
    """Test various user creation scenarios."""
    
    if not roles:
        print("No roles available!")
        return
    
    # Test 1: Valid user creation
    print("="*70)
    print("TEST 1: Valid user creation")
    print("="*70)
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "validuser123",
            "email": "validuser123@example.com",
            "password": "ValidPassword123!",
            "role_id": roles[0]['id']
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test 2: Missing password
    print("="*70)
    print("TEST 2: Missing password")
    print("="*70)
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "nopassword",
            "email": "nopassword@example.com",
            "role_id": roles[0]['id']
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test 3: Invalid role_id
    print("="*70)
    print("TEST 3: Invalid role_id")
    print("="*70)
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "invalidrole",
            "email": "invalidrole@example.com",
            "password": "ValidPassword123!",
            "role_id": "00000000-0000-0000-0000-000000000000"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test 4: Duplicate username
    print("="*70)
    print("TEST 4: Duplicate username")
    print("="*70)
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "admin",
            "email": "duplicate@example.com",
            "password": "ValidPassword123!",
            "role_id": roles[0]['id']
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test 5: Empty role_id (what UI might be sending)
    print("="*70)
    print("TEST 5: Empty role_id string")
    print("="*70)
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "emptyrole",
            "email": "emptyrole@example.com",
            "password": "ValidPassword123!",
            "role_id": ""
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def main():
    """Main function."""
    token = login()
    if not token:
        return
    
    roles = get_roles(token)
    test_user_creation_scenarios(token, roles)


if __name__ == "__main__":
    main()
