"""Delete test users created during debugging."""
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


def get_all_users(token):
    """Get all users."""
    response = requests.get(
        f"{API_BASE_URL}/api/v1/users?limit=1000&active_only=false",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return []


def delete_user(token, user_id, username):
    """Delete a user."""
    response = requests.delete(
        f"{API_BASE_URL}/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        print(f"  ✓ Deleted: {username}")
        return True
    else:
        print(f"  ✗ Failed to delete {username}: {response.text[:100]}")
        return False


def main():
    """Main function."""
    token = login()
    if not token:
        return
    
    print("Fetching all users...")
    users = get_all_users(token)
    print(f"Found {len(users)} users\n")
    
    # List of test usernames to delete
    test_usernames = [
        'mikey',
        'testuser1',
        'testuser2',
        'testuser3',
        'testuser123',
        'validuser123',
        'nopassword',
        'invalidrole',
        'emptyrole'
    ]
    
    print("Deleting test users...")
    deleted_count = 0
    
    for user in users:
        if user['username'] in test_usernames:
            if delete_user(token, user['id'], user['username']):
                deleted_count += 1
    
    print(f"\n{'='*70}")
    print(f"Deleted {deleted_count} test user(s)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
