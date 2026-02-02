"""Test user creation exactly as the UI would do it."""
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
    print(f"Roles response: {response.status_code}")
    if response.status_code == 200:
        roles = response.json()
        print(f"Found {len(roles)} roles")
        for role in roles:
            print(f"  - {role['name']} (ID: {role['id']})")
        return roles
    return []


def test_scenarios(token, roles):
    """Test various user creation scenarios."""
    
    if not roles:
        print("No roles available!")
        return
    
    test_cases = [
        {
            "name": "Valid user with all fields",
            "data": {
                "username": "testuser1",
                "email": "testuser1@example.com",
                "password": "TestPassword123!",
                "role_id": roles[0]['id'],
                "active": True
            }
        },
        {
            "name": "User with empty role_id (UI bug?)",
            "data": {
                "username": "testuser2",
                "email": "testuser2@example.com",
                "password": "TestPassword123!",
                "role_id": "",
                "active": True
            }
        },
        {
            "name": "User without active field",
            "data": {
                "username": "testuser3",
                "email": "testuser3@example.com",
                "password": "TestPassword123!",
                "role_id": roles[0]['id']
            }
        },
        {
            "name": "User 'mikey' with Viewer role",
            "data": {
                "username": "mikey",
                "email": "mikey@example.com",
                "password": "MikeyPassword123!",
                "role_id": next((r['id'] for r in roles if r['name'] == 'Viewer'), roles[0]['id']),
                "active": True
            }
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print("\n" + "="*70)
        print(f"TEST {i}: {test_case['name']}")
        print("="*70)
        
        print("Request:")
        print(json.dumps(test_case['data'], indent=2))
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/users",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=test_case['data']
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        try:
            response_data = response.json()
            print("Response Body:")
            print(json.dumps(response_data, indent=2))
            
            if response.status_code == 200:
                print(f"✓ SUCCESS: User created with ID {response_data.get('id')}")
            else:
                print(f"✗ FAILED: {response_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"Response Text: {response.text}")
            print(f"Error parsing response: {e}")


def main():
    """Main function."""
    token = login()
    if not token:
        return
    
    roles = get_roles(token)
    test_scenarios(token, roles)


if __name__ == "__main__":
    main()
