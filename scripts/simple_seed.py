#!/usr/bin/env python3
"""Simple script to create admin user - can be run from container."""

import os
import sys
import uuid
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, '/app')

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("psycopg2 not available, trying to install...")
    os.system("pip install psycopg2-binary")
    import psycopg2
    from psycopg2.extras import RealDictCursor

def main():
    # Database connection details
    db_host = "dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com"
    db_port = "5432"
    db_name = "inventory_management"
    db_user = "inventory_user"
    db_password = "InventoryDB2025!"
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Create admin role
        cursor.execute("""
            INSERT INTO roles (id, name, description, permissions, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (
            str(uuid.uuid4()),
            'admin',
            'System Administrator with full access',
            '["*"]',
            datetime.now(timezone.utc),
            datetime.now(timezone.utc)
        ))
        
        # Get admin role ID
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        admin_role = cursor.fetchone()
        admin_role_id = str(admin_role['id'])
        
        # Create admin user (password is 'secret')
        cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, active, role_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                active = EXCLUDED.active,
                role_id = EXCLUDED.role_id,
                updated_at = EXCLUDED.updated_at
        """, (
            str(uuid.uuid4()),
            'admin',
            'admin@inventory.local',
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  # bcrypt hash for 'secret'
            True,
            admin_role_id,
            datetime.now(timezone.utc),
            datetime.now(timezone.utc)
        ))
        
        # Create location types
        location_types = [
            ('Warehouse', 'Storage and distribution facility'),
            ('Office', 'Administrative office space'),
            ('Storage Room', 'Small storage area')
        ]
        
        for name, desc in location_types:
            cursor.execute("""
                INSERT INTO location_types (id, name, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (
                str(uuid.uuid4()),
                name,
                desc,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
        
        # Get location type IDs
        cursor.execute("SELECT id, name FROM location_types")
        location_types_map = {row['name']: str(row['id']) for row in cursor.fetchall()}
        
        # Create sample locations
        locations = [
            ('Main Warehouse', 'Primary storage facility', 'Warehouse'),
            ('Corporate Office', 'Main administrative office', 'Office'),
            ('IT Storage', 'IT equipment storage room', 'Storage Room')
        ]
        
        for name, desc, type_name in locations:
            if type_name in location_types_map:
                cursor.execute("""
                    INSERT INTO locations (id, name, description, location_metadata, location_type_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    name,
                    desc,
                    '{}',
                    location_types_map[type_name],
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc)
                ))
        
        # Create item types
        item_types = [
            ('Equipment', 'Physical equipment and machinery', 'PARENT'),
            ('Furniture', 'Office and warehouse furniture', 'PARENT'),
            ('Component', 'Individual components and parts', 'CHILD'),
            ('Accessory', 'Equipment accessories', 'CHILD')
        ]
        
        for name, desc, category in item_types:
            cursor.execute("""
                INSERT INTO item_types (id, name, description, category, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                str(uuid.uuid4()),
                name,
                desc,
                category,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
        
        conn.commit()
        
        print("✅ Admin user and sample data created successfully!")
        print("   Username: admin")
        print("   Password: secret")
        print("   Role: admin")
        print("✅ Sample data created (location types, locations, item types)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()