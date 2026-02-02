"""Test creating user with username 'mikey' to debug the issue."""
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
    response = requests.get(
        f"{API_BASE_URL}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return []


def test_create_mikey(token, role_id):
    """Test creating user 'mikey'."""
    print("="*70)
    print("TEST: Creating user 'mikey'")
    print("="*70)
    
    payload = {
        "username": "mikey",
        "email": "mikey@example.com",
        "password": "MikeyPassword123!",
        "role_id": role_id
    }
    
    print(f"Request payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'content-length', 'date']:
            print(f"  {key}: {value}")
    print()
    
    print(f"Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print()
    
    # If it failed, try to get more details
    if response.status_code != 200:
        print("ERROR DETAILS:")
        print(f"  Status: {response.status_code}")
        print(f"  Reason: {response.reason}")
        if response.text:
            print(f"  Body: {response.text[:500]}")


def check_existing_mikey(token):
    """Check if user 'mikey' already exists."""
    print("="*70)
    print("Checking if 'mikey' already exists")
    print("="*70)
    
    response = requests.get(
        f"{API_BASE_URL}/api/v1/users?search=mikey",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        users = response.json()
        if users:
            print(f"Found {len(users)} user(s) matching 'mikey':")
            for user in users:
                print(f"  - {user['username']} ({user['email']}) - ID: {user['id']}")
        else:
            print("No existing user named 'mikey' found")
    else:
        print(f"Failed to search users: {response.status_code}")
    print()


def main():
    """Main function."""
    token = login()
    if not token:
        return
    
    roles = get_roles(token)
    if not roles:
        print("No roles found!")
        return
    
    # Check if mikey already exists
    check_existing_mikey(token)
    
    # Try to create mikey
    test_create_mikey(token, roles[0]['id'])


if __name__ == "__main__":
    main()
