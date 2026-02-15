#!/usr/bin/env python3
"""Quick test to check staging database state."""

import sys
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://inventory_user:InventoryDB2025!@staging-inventory-db.c47e2qi82sp6.us-east-1.rds.amazonaws.com:5432/inventory_management"

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check admin user
        result = conn.execute(text("SELECT username, email, active, password_hash FROM users WHERE username='admin'"))
        user = result.fetchone()
        
        if user:
            print(f"✓ Admin user EXISTS")
            print(f"  Username: {user[0]}")
            print(f"  Email: {user[1]}")
            print(f"  Active: {user[2]}")
            print(f"  Password hash: {user[3]}")
        else:
            print("✗ Admin user NOT FOUND!")
            sys.exit(1)
        
        # Check all users
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.fetchone()[0]
        print(f"\nTotal users: {count}")
        
        # Check roles
        result = conn.execute(text("SELECT name FROM roles"))
        roles = result.fetchall()
        print(f"\nRoles: {[r[0] for r in roles]}")
        
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
