"""Seed admin user and basic data

Revision ID: 20260201214107
Revises: 20260201184930
Create Date: 2026-02-01 21:41:07

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime, timezone
import uuid


# revision identifiers, used by Alembic.
revision = "20260201214107"
down_revision = "20260201184930"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed admin user and basic reference data."""
    # Get connection
    conn = op.get_bind()
    
    # Create admin role
    admin_role_id = str(uuid.uuid4())
    conn.execute(
        sa.text("""
            INSERT INTO roles (id, name, description, permissions, created_at, updated_at)
            VALUES (:id, :name, :description, :permissions, :created_at, :updated_at)
            ON CONFLICT (name) DO NOTHING
        """),
        {
            "id": admin_role_id,
            "name": "admin",
            "description": "System Administrator with full access",
            "permissions": '{"*": true}',
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    )
    
    # Get admin role ID (in case it already existed)
    result = conn.execute(
        sa.text("SELECT id FROM roles WHERE name = 'admin'")
    )
    admin_role_id = str(result.fetchone()[0])
    
    # Create admin user with password 'admin'
    # Password hash generated with bcrypt for 'admin' (cost factor 12)
    # Hash: $2b$12$SD4NhDwd632jUZahyAguMu8BdxCXZGUhwbB.uWTln/KDFTsnYaXay
    conn.execute(
        sa.text("""
            INSERT INTO users (id, username, email, password_hash, active, role_id, created_at, updated_at)
            VALUES (:id, :username, :email, :password_hash, :active, :role_id, :created_at, :updated_at)
            ON CONFLICT (username) DO UPDATE SET
                email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                active = EXCLUDED.active,
                role_id = EXCLUDED.role_id,
                updated_at = EXCLUDED.updated_at
        """),
        {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@inventory.local",
            "password_hash": "$2b$12$SD4NhDwd632jUZahyAguMu8BdxCXZGUhwbB.uWTln/KDFTsnYaXay",
            "active": True,
            "role_id": admin_role_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    )
    
    # Create basic location types
    location_types_data = [
        ("Warehouse", "Storage and distribution facility"),
        ("Office", "Administrative office space"),
        ("Storage Room", "Small storage area"),
    ]
    
    location_type_ids = {}
    for name, description in location_types_data:
        location_type_id = str(uuid.uuid4())
        conn.execute(
            sa.text("""
                INSERT INTO location_types (id, name, description, created_at, updated_at)
                VALUES (:id, :name, :description, :created_at, :updated_at)
                ON CONFLICT (name) DO NOTHING
            """),
            {
                "id": location_type_id,
                "name": name,
                "description": description,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        
        # Get location type ID (in case it already existed)
        result = conn.execute(
            sa.text("SELECT id FROM location_types WHERE name = :name"),
            {"name": name}
        )
        location_type_ids[name] = str(result.fetchone()[0])
    
    # Create sample locations
    locations_data = [
        ("Main Warehouse", "Primary storage facility", "Warehouse"),
        ("Corporate Office", "Main administrative office", "Office"),
        ("IT Storage", "IT equipment storage room", "Storage Room"),
    ]
    
    for name, description, type_name in locations_data:
        # Check if location already exists
        result = conn.execute(
            sa.text("SELECT COUNT(*) FROM locations WHERE name = :name"),
            {"name": name}
        )
        if result.fetchone()[0] == 0:
            conn.execute(
                sa.text("""
                    INSERT INTO locations (id, name, description, location_metadata, location_type_id, created_at, updated_at)
                    VALUES (:id, :name, :description, :location_metadata, :location_type_id, :created_at, :updated_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "description": description,
                    "location_metadata": "{}",
                    "location_type_id": location_type_ids[type_name],
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            )
    
    # Create sample item types
    item_types_data = [
        ("Equipment", "Physical equipment and machinery", "PARENT"),
        ("Furniture", "Office and warehouse furniture", "PARENT"),
        ("Component", "Individual components and parts", "CHILD"),
        ("Accessory", "Equipment accessories", "CHILD"),
    ]
    
    for name, description, category in item_types_data:
        # Check if item type already exists
        result = conn.execute(
            sa.text("SELECT COUNT(*) FROM item_types WHERE name = :name"),
            {"name": name}
        )
        if result.fetchone()[0] == 0:
            conn.execute(
                sa.text("""
                    INSERT INTO item_types (id, name, description, category, created_at, updated_at)
                    VALUES (:id, :name, :description, :category, :created_at, :updated_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "description": description,
                    "category": category,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            )


def downgrade() -> None:
    """Remove seeded data."""
    conn = op.get_bind()
    
    # Remove sample item types
    conn.execute(
        sa.text("""
            DELETE FROM item_types 
            WHERE name IN ('Equipment', 'Furniture', 'Component', 'Accessory')
        """)
    )
    
    # Remove sample locations
    conn.execute(
        sa.text("""
            DELETE FROM locations 
            WHERE name IN ('Main Warehouse', 'Corporate Office', 'IT Storage')
        """)
    )
    
    # Remove location types
    conn.execute(
        sa.text("""
            DELETE FROM location_types 
            WHERE name IN ('Warehouse', 'Office', 'Storage Room')
        """)
    )
    
    # Remove admin user
    conn.execute(
        sa.text("DELETE FROM users WHERE username = 'admin'")
    )
    
    # Remove admin role
    conn.execute(
        sa.text("DELETE FROM roles WHERE name = 'admin'")
    )
