"""Run migration in staging environment."""

import requests
import sys

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

def run_migration(token):
    """Run database migration."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nRunning database migration...")
    
    try:
        response = requests.post(
            f"{STAGING_URL}/api/v1/admin/migrate",
            headers=headers,
            timeout=60
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✓ Migration completed successfully!")
            return True
        else:
            print(f"\n✗ Migration failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error running migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("=" * 70)
    print("Staging Migration Runner")
    print("=" * 70)
    
    # Login
    print("\nLogging in...")
    token = login()
    if not token:
        print("\n✗ Cannot login to staging")
        sys.exit(1)
    print("✓ Login successful")
    
    # Run migration
    success = run_migration(token)
    
    print("\n" + "=" * 70)
    if success:
        print("✓ Migration completed!")
    else:
        print("✗ Migration failed")
        print("\nNote: Migration endpoint may not be available.")
        print("Migrations are typically run automatically during deployment.")
        print("Check CloudWatch logs for migration status.")
    print("=" * 70)

if __name__ == "__main__":
    main()
