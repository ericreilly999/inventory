"""
AWS Lambda function to seed the database with admin user and sample data.
This can be deployed as a Lambda function and invoked to seed the database.
"""

import json
import uuid
import psycopg2
from datetime import datetime, timezone

def lambda_handler(event, context):
    """Lambda handler to seed the database."""
    
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
        
        cursor = conn.cursor()
        
        # Check if admin user already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()[0] > 0
        
        if admin_exists:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Admin user already exists',
                    'username': 'admin',
                    'status': 'exists'
                })
            }
        
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
        admin_role_id = str(cursor.fetchone()[0])
        
        # Create admin user (password is 'secret')
        cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, active, role_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
        location_types_data = [
            ('Warehouse', 'Storage and distribution facility'),
            ('Office', 'Administrative office space'),
            ('Storage Room', 'Small storage area')
        ]
        
        location_types = {}
        for name, desc in location_types_data:
            cursor.execute("""
                INSERT INTO location_types (id, name, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """, (
                str(uuid.uuid4()),
                name,
                desc,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
            result = cursor.fetchone()
            if result:
                location_types[name] = str(result[0])
            else:
                cursor.execute("SELECT id FROM location_types WHERE name = %s", (name,))
                location_types[name] = str(cursor.fetchone()[0])
        
        # Create sample locations
        locations_data = [
            ('Main Warehouse', 'Primary storage facility', 'Warehouse'),
            ('Corporate Office', 'Main administrative office', 'Office'),
            ('IT Storage', 'IT equipment storage room', 'Storage Room')
        ]
        
        for name, desc, type_name in locations_data:
            if type_name in location_types:
                cursor.execute("""
                    INSERT INTO locations (id, name, description, location_metadata, location_type_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    name,
                    desc,
                    '{}',
                    location_types[type_name],
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc)
                ))
        
        # Create item types
        item_types_data = [
            ('Equipment', 'Physical equipment and machinery', 'PARENT'),
            ('Furniture', 'Office and warehouse furniture', 'PARENT'),
            ('Component', 'Individual components and parts', 'CHILD'),
            ('Accessory', 'Equipment accessories', 'CHILD')
        ]
        
        for name, desc, category in item_types_data:
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
        
        # Commit all changes
        conn.commit()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Database seeded successfully!',
                'admin_user': {
                    'username': 'admin',
                    'email': 'admin@inventory.local',
                    'password': 'secret',
                    'role': 'admin'
                },
                'sample_data': {
                    'location_types': len(location_types_data),
                    'locations': len(locations_data),
                    'item_types': len(item_types_data)
                },
                'status': 'success'
            })
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to seed database'
            })
        }
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()