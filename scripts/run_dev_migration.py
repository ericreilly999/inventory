"""Run database migration in dev environment."""

import requests
import sys

DEV_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"

def login():
    """Login and get token."""
    response = requests.post(
        f"{DEV_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None
    return response.json()["access_token"]

def run_migration(token):
    """Run database migration."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Running migration...")
    response = requests.post(
        f"{DEV_URL}/api/v1/admin/run-migrations",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Migration completed successfully!")
        print(f"Message: {result.get('message', 'No message')}")
        if 'migrations_applied' in result:
            print(f"Migrations applied: {result['migrations_applied']}")
        return True
    else:
        print(f"\n✗ Migration failed: {response.status_code}")
        print(response.text)
        return False

def main():
    """Main function."""
    print("=" * 60)
    print("Running Database Migration in Dev Environment")
    print("=" * 60)
    
    # Login
    print("\n1. Logging in...")
    token = login()
    if not token:
        sys.exit(1)
    print("✓ Login successful")
    
    # Run migration
    print("\n2. Running migration...")
    if run_migration(token):
        print("\n" + "=" * 60)
        print("✓ Migration completed!")
        print("=" * 60)
        print("\nYou can now test location deletion:")
        print("python scripts/test_dev_location_deletion.py")
    else:
        print("\n" + "=" * 60)
        print("✗ Migration failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
