"""Rollback problematic migrations and reapply them in dev."""

import requests
import sys
import time

DEV_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"

def login():
    """Login and get token."""
    try:
        response = requests.post(
            f"{DEV_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
            timeout=10
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            return None
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login error: {e}")
        return None

def rollback_migration(token, steps=1):
    """Rollback migrations."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\nRolling back {steps} migration(s)...")
    try:
        response = requests.post(
            f"{DEV_URL}/api/v1/admin/rollback-migrations",
            headers=headers,
            json={"steps": steps},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Rollback successful: {result.get('message', 'Done')}")
            return True
        else:
            print(f"Rollback returned: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Rollback error: {e}")
        return False

def run_migration(token):
    """Run migrations."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nRunning migrations...")
    try:
        response = requests.post(
            f"{DEV_URL}/api/v1/admin/run-migrations",
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Migrations successful: {result.get('message', 'Done')}")
            return True
        else:
            print(f"✗ Migration failed: {response.status_code}")
            error_text = response.text
            print(error_text)
            
            # Check if it's the SKU duplicate issue
            if "UniqueViolation" in error_text and "sku" in error_text:
                print("\n⚠ Duplicate SKU issue detected")
                return False
            return False
    except Exception as e:
        print(f"Migration error: {e}")
        return False

def main():
    """Main function."""
    print("=" * 70)
    print("Dev Database Migration Rollback & Reapply")
    print("=" * 70)
    
    print("\nThis script will:")
    print("1. Rollback the SKU unique constraint migration")
    print("2. Reapply migrations")
    print("")
    
    # Login
    print("1. Logging in...")
    token = login()
    if not token:
        print("\n✗ Cannot access dev environment")
        sys.exit(1)
    print("✓ Login successful")
    
    # Try to rollback the problematic migration
    print("\n2. Rolling back SKU unique constraint migration...")
    if rollback_migration(token, steps=2):
        print("✓ Rollback successful")
        
        # Wait a bit
        print("\nWaiting 5 seconds...")
        time.sleep(5)
        
        # Try to run migrations again
        print("\n3. Reapplying migrations...")
        if run_migration(token):
            print("\n" + "=" * 70)
            print("✓ Dev database is now functional!")
            print("=" * 70)
        else:
            print("\n✗ Migration still failing")
            print("\nThe database has duplicate SKUs that need manual cleanup.")
            print("Options:")
            print("1. Connect to RDS directly and clean up duplicates")
            print("2. Drop and recreate the dev database")
            print("3. Use staging environment for testing (recommended)")
            sys.exit(1)
    else:
        print("\n⚠ Rollback endpoint not available")
        print("\nThe dev database needs manual intervention.")
        print("\nRecommended approach:")
        print("1. Use staging environment for testing (clean database)")
        print("2. Or manually clean up dev database via RDS")
        sys.exit(1)

if __name__ == "__main__":
    main()
