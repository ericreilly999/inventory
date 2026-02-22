"""Fix dev database by cleaning up duplicate SKUs and resetting to clean state."""

import requests
import sys
from datetime import datetime

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
            print(response.text)
            return None
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login error: {e}")
        return None

def reset_database(token):
    """Reset the database to clean state."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nAttempting to reset database...")
    
    # Try to call a reset endpoint if it exists
    try:
        response = requests.post(
            f"{DEV_URL}/api/v1/admin/reset-database",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✓ Database reset successful")
            return True
        else:
            print(f"Reset endpoint returned: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Reset endpoint not available: {e}")
        return False

def run_sql_fix(token):
    """Run SQL to fix duplicate SKUs."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nAttempting to fix duplicate SKUs via SQL...")
    
    # SQL to remove duplicate SKUs by keeping only the first occurrence
    sql_commands = [
        # First, remove the unique constraint if it exists
        "ALTER TABLE parent_items DROP CONSTRAINT IF EXISTS uq_parent_items_sku;",
        
        # Update duplicate SKUs to make them unique
        """
        WITH duplicates AS (
            SELECT id, sku, 
                   ROW_NUMBER() OVER (PARTITION BY sku ORDER BY created_at) as rn
            FROM parent_items
            WHERE sku IS NOT NULL
        )
        UPDATE parent_items
        SET sku = CONCAT(parent_items.sku, '-', duplicates.rn)
        FROM duplicates
        WHERE parent_items.id = duplicates.id
        AND duplicates.rn > 1;
        """,
        
        # Do the same for child_items
        "ALTER TABLE child_items DROP CONSTRAINT IF EXISTS uq_child_items_sku;",
        
        """
        WITH duplicates AS (
            SELECT id, sku,
                   ROW_NUMBER() OVER (PARTITION BY sku ORDER BY created_at) as rn
            FROM child_items
            WHERE sku IS NOT NULL
        )
        UPDATE child_items
        SET sku = CONCAT(child_items.sku, '-', duplicates.rn)
        FROM duplicates
        WHERE child_items.id = duplicates.id
        AND duplicates.rn > 1;
        """
    ]
    
    try:
        response = requests.post(
            f"{DEV_URL}/api/v1/admin/execute-sql",
            headers=headers,
            json={"commands": sql_commands},
            timeout=60
        )
        
        if response.status_code == 200:
            print("✓ SQL fix applied successfully")
            return True
        else:
            print(f"SQL execution returned: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"SQL execution not available: {e}")
        return False

def run_migration(token):
    """Run database migrations."""
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
            print("✓ Migrations completed successfully")
            if 'message' in result:
                print(f"  {result['message']}")
            return True
        else:
            print(f"✗ Migration failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Migration error: {e}")
        return False

def verify_api(token):
    """Verify API is working."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nVerifying API endpoints...")
    
    endpoints = [
        ("/api/v1/location-types", "Location Types"),
        ("/api/v1/locations", "Locations"),
        ("/api/v1/parent-items", "Parent Items"),
    ]
    
    all_ok = True
    for endpoint, name in endpoints:
        try:
            response = requests.get(
                f"{DEV_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "N/A"
                print(f"  ✓ {name}: {count} items")
            else:
                print(f"  ✗ {name}: {response.status_code}")
                all_ok = False
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Main function."""
    print("=" * 70)
    print("Dev Environment Database Fix")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Login
    print("\n1. Logging in to dev environment...")
    token = login()
    if not token:
        print("\n✗ Cannot access dev environment")
        sys.exit(1)
    print("✓ Login successful")
    
    # Step 2: Try to reset database
    print("\n2. Attempting database reset...")
    if reset_database(token):
        print("✓ Database reset successful")
    else:
        print("⚠ Database reset not available, will try SQL fix")
        
        # Step 3: Try SQL fix
        print("\n3. Attempting SQL fix for duplicate SKUs...")
        if run_sql_fix(token):
            print("✓ SQL fix applied")
        else:
            print("⚠ SQL fix not available")
            print("\nManual intervention may be required:")
            print("1. Connect to dev database directly")
            print("2. Run: DELETE FROM parent_items WHERE sku IN (SELECT sku FROM parent_items GROUP BY sku HAVING COUNT(*) > 1);")
            print("3. Or drop and recreate the database")
    
    # Step 4: Run migrations
    print("\n4. Running migrations...")
    if not run_migration(token):
        print("\n✗ Migration failed")
        print("\nThe database may need manual cleanup.")
        print("Consider:")
        print("1. Dropping and recreating the dev database")
        print("2. Running migrations from scratch")
        sys.exit(1)
    
    # Step 5: Verify API
    print("\n5. Verifying API functionality...")
    if verify_api(token):
        print("\n" + "=" * 70)
        print("✓ Dev environment is now functional!")
        print("=" * 70)
        print("\nYou can now test the location deletion feature:")
        print("python scripts/test_dev_location_deletion.py")
    else:
        print("\n✗ API verification failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
