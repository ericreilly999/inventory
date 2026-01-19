#!/usr/bin/env python3
"""Run database migrations."""

import os
import sys
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run database migrations."""
    # Set the database URL from environment variable
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://inventory_user:inventory_password@localhost:5432/inventory_management"
    )
    
    print(f"Running migrations with DATABASE_URL: {database_url}")
    
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    
    try:
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)