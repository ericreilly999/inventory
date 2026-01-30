#!/usr/bin/env python3
"""
Direct migration runner - connects to database and runs Alembic migrations.
Use this when ECS task infrastructure isn't available yet.
"""
import os
import sys
from alembic import command
from alembic.config import Config

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inventory_user:InventoryDB2025!@dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com:5432/inventory_management"
)

print("=" * 60)
print("Running Database Migrations")
print("=" * 60)
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")
print()

try:
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    
    # Show current version
    print("Checking current database version...")
    command.current(alembic_cfg)
    print()
    
    # Run migrations
    print("Running migrations...")
    command.upgrade(alembic_cfg, "head")
    print()
    
    # Show new version
    print("Migration complete! New version:")
    command.current(alembic_cfg)
    print()
    
    print("=" * 60)
    print("✅ SUCCESS: Database migrations completed")
    print("=" * 60)
    sys.exit(0)
    
except Exception as e:
    print()
    print("=" * 60)
    print(f"❌ ERROR: Migration failed")
    print("=" * 60)
    print(f"Error: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
