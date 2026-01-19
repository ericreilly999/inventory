#!/usr/bin/env python3
"""
Script to create an initial admin user for the inventory management system.
This script should be run after the database migrations have been applied.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from getpass import getpass

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from shared.auth.utils import hash_password


def create_admin_user(database_url: str, username: str = "admin", email: str = "admin@inventory.local", password: str = None):
    """Create an admin user and role in the database."""
    
    if not password:
        # Use default password for automated setup
        password = "admin123"
        print(f"Using default password: {password}")
    
    # Ensure password is within bcrypt limits
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        print("Password truncated to 72 bytes for bcrypt compatibility")
    
    
    # Create database connection
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as session:
        try:
            # Generate UUIDs
            admin_role_id = str(uuid.uuid4())
            admin_user_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            # Create admin role
            admin_role_query = text("""
                INSERT INTO roles (id, name, description, permissions, created_at, updated_at)
                VALUES (:id, :name, :description, :permissions, :created_at, :updated_at)
                ON CONFLICT (name) DO NOTHING
            """)
            
            session.execute(admin_role_query, {
                "id": admin_role_id,
                "name": "admin",
                "description": "System Administrator with full access",
                "permissions": '["*"]',  # JSON array with wildcard permission
                "created_at": now,
                "updated_at": now
            })
            
            # Get the admin role ID (in case it already existed)
            role_result = session.execute(text("SELECT id FROM roles WHERE name = 'admin'")).fetchone()
            if role_result:
                admin_role_id = str(role_result[0])
            
            # Hash the password
            password_hash = hash_password(password)
            
            # Create admin user
            admin_user_query = text("""
                INSERT INTO users (id, username, email, password_hash, active, role_id, created_at, updated_at)
                VALUES (:id, :username, :email, :password_hash, :active, :role_id, :created_at, :updated_at)
                ON CONFLICT (username) DO UPDATE SET
                    email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash,
                    active = EXCLUDED.active,
                    role_id = EXCLUDED.role_id,
                    updated_at = EXCLUDED.updated_at
            """)
            
            session.execute(admin_user_query, {
                "id": admin_user_id,
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "active": True,
                "role_id": admin_role_id,
                "created_at": now,
                "updated_at": now
            })
            
            # Create some basic location types and locations for testing
            warehouse_type_id = str(uuid.uuid4())
            office_type_id = str(uuid.uuid4())
            
            # Location types
            location_type_query = text("""
                INSERT INTO location_types (id, name, description, created_at, updated_at)
                VALUES (:id, :name, :description, :created_at, :updated_at)
                ON CONFLICT (name) DO NOTHING
            """)
            
            session.execute(location_type_query, {
                "id": warehouse_type_id,
                "name": "Warehouse",
                "description": "Storage and distribution facility",
                "created_at": now,
                "updated_at": now
            })
            
            session.execute(location_type_query, {
                "id": office_type_id,
                "name": "Office",
                "description": "Administrative office space",
                "created_at": now,
                "updated_at": now
            })
            
            # Get location type IDs
            warehouse_result = session.execute(text("SELECT id FROM location_types WHERE name = 'Warehouse'")).fetchone()
            office_result = session.execute(text("SELECT id FROM location_types WHERE name = 'Office'")).fetchone()
            
            if warehouse_result and office_result:
                warehouse_type_id = str(warehouse_result[0])
                office_type_id = str(office_result[0])
                
                # Create sample locations
                location_query = text("""
                    INSERT INTO locations (id, name, description, location_metadata, location_type_id, created_at, updated_at)
                    VALUES (:id, :name, :description, :location_metadata, :location_type_id, :created_at, :updated_at)
                    ON CONFLICT DO NOTHING
                """)
                
                session.execute(location_query, {
                    "id": str(uuid.uuid4()),
                    "name": "Main Warehouse",
                    "description": "Primary storage facility",
                    "location_metadata": '{}',
                    "location_type_id": warehouse_type_id,
                    "created_at": now,
                    "updated_at": now
                })
                
                session.execute(location_query, {
                    "id": str(uuid.uuid4()),
                    "name": "Corporate Office",
                    "description": "Main administrative office",
                    "location_metadata": '{}',
                    "location_type_id": office_type_id,
                    "created_at": now,
                    "updated_at": now
                })
            
            # Create sample item types
            parent_item_type_query = text("""
                INSERT INTO item_types (id, name, description, category, created_at, updated_at)
                VALUES (:id, :name, :description, :category, :created_at, :updated_at)
                ON CONFLICT DO NOTHING
            """)
            
            session.execute(parent_item_type_query, {
                "id": str(uuid.uuid4()),
                "name": "Equipment",
                "description": "Physical equipment and machinery",
                "category": "PARENT",
                "created_at": now,
                "updated_at": now
            })
            
            session.execute(parent_item_type_query, {
                "id": str(uuid.uuid4()),
                "name": "Component",
                "description": "Individual components and parts",
                "category": "CHILD",
                "created_at": now,
                "updated_at": now
            })
            
            session.commit()
            
            print(f"✅ Admin user created successfully!")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Role: admin")
            print(f"✅ Sample data created (location types, locations, item types)")
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating admin user: {e}")
            return False


def main():
    """Main function."""
    # Use AWS RDS URL directly
    db_host = "dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com"
    db_port = "5432"
    db_name = "inventory_management"
    db_user = "inventory_user"
    db_password = "inventory_password"  # Default password from terraform
    
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print("🚀 Creating admin user for Inventory Management System")
    print(f"   Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    
    # Create admin user
    success = create_admin_user(database_url)
    
    if success:
        print("\n🎉 Setup complete! You can now log in to the system at:")
        print("   http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/")
        print("   Username: admin")
        print("   Password: [the password you just set]")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()