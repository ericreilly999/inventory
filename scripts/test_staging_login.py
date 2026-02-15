"""Test staging login and database state."""

import os
import sys
import requests
from sqlalchemy import create_engine, text

# Staging database URL
DATABASE_URL = "postgresql://inventory_user:InventoryDB2025!@staging-inventory-db.c47e2qi82sp6.us-east-1.rds.amazonaws.com:5432/inventory_management"
API_URL = "http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com"

def check_database():
    """Check database state."""
    print("=" * 60)
    print("Checking Database State")
    print("=" * 60)
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if admin user exists
        result = conn.execute(text("SELECT username, email, active, password_hash FROM users WHERE username='admin'"))
        user = result.fetchone()
        
        if user:
            print(f"✓ Admin user found:")
            print(f"  Username: {user[0]}")
            print(f"  Email: {user[1]}")
            print(f"  Active: {user[2]}")
            print(f"  Password hash: {user[3][:30]}...")
        else:
            print("✗ Admin user NOT found!")
            return False
        
        # Check roles
        result = conn.execute(text("SELECT COUNT(*) FROM roles"))
        role_count = result.fetchone()[0]
        print(f"\n✓ Roles in database: {role_count}")
        
        # Check location types
        result = conn.execute(text("SELECT COUNT(*) FROM location_types"))
        location_type_count = result.fetchone()[0]
        print(f"✓ Location types in database: {location_type_count}")
        
        # Check locations
        result = conn.execute(text("SELECT COUNT(*) FROM locations"))
        location_count = result.fetchone()[0]
        print(f"✓ Locations in database: {location_count}")
        
        # Check item types
        result = conn.execute(text("SELECT COUNT(*) FROM item_types"))
        item_type_count = result.fetchone()[0]
        print(f"✓ Item types in database: {item_type_count}")
        
    return True

def test_login():
    """Test login via API."""
    print("\n" + "=" * 60)
    print("Testing Login via API")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✓ Login successful!")
            return True
        else:
            print("\n✗ Login failed!")
            return False
            
    except Exception as e:
        print(f"\n✗ Login request failed: {e}")
        return False

def main():
    """Main function."""
    print("\nStaging Environment Login Test")
    print("=" * 60)
    
    db_ok = check_database()
    if not db_ok:
        print("\n✗ Database check failed!")
        sys.exit(1)
    
    login_ok = test_login()
    if not login_ok:
        print("\n✗ Login test failed!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
