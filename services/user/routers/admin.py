"""Admin operations router."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.auth.utils import hash_password
from shared.database.config import get_db
from shared.logging.config import get_logger
from shared.models.item import ItemType
from shared.models.location import Location, LocationType
from shared.models.user import Role, User

logger = get_logger(__name__)

router = APIRouter()


@router.post("/cleanup-admin")
async def cleanup_admin(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Clean up existing admin user with invalid data."""
    try:
        # Delete existing admin user and role
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            db.delete(existing_admin)

        existing_role = db.query(Role).filter(Role.name == "admin").first()
        if existing_role:
            db.delete(existing_role)

        db.commit()

        return {
            "message": "Admin user and role cleaned up successfully",
            "status": "success",
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning up admin: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error cleaning up admin: {str(e)}"
        )


@router.post("/seed-database")
async def seed_database(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Seed the database with initial admin user and sample data."""
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            # Update the password hash to ensure it's compatible with current bcrypt implementation
            existing_admin.password_hash = hash_password("admin")
            existing_admin.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "message": "Admin user already exists - password hash updated",
                "username": "admin",
                "status": "updated",
            }

        # Create admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(
                id=uuid.uuid4(),
                name="admin",
                description="System Administrator with full access",
                permissions={"*": True},  # Use dict format instead of list
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(admin_role)
            db.flush()  # Get the ID

        # Create admin user (password is 'admin')
        password_hash = hash_password("admin")
        admin_user = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",  # Use valid email domain
            password_hash=password_hash,
            active=True,
            role_id=admin_role.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(admin_user)

        # Create location types
        location_types_data = [
            ("Warehouse", "Storage and distribution facility"),
            ("Office", "Administrative office space"),
            ("Storage Room", "Small storage area"),
        ]

        location_types = {}
        for name, description in location_types_data:
            existing_type = (
                db.query(LocationType).filter(LocationType.name == name).first()
            )
            if not existing_type:
                location_type = LocationType(
                    id=uuid.uuid4(),
                    name=name,
                    description=description,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(location_type)
                location_types[name] = location_type
            else:
                location_types[name] = existing_type

        db.flush()  # Ensure location types are saved

        # Create sample locations
        locations_data = [
            ("Main Warehouse", "Primary storage facility", "Warehouse"),
            ("Corporate Office", "Main administrative office", "Office"),
            ("IT Storage", "IT equipment storage room", "Storage Room"),
        ]

        for name, description, type_name in locations_data:
            existing_location = db.query(Location).filter(Location.name == name).first()
            if not existing_location and type_name in location_types:
                location = Location(
                    id=uuid.uuid4(),
                    name=name,
                    description=description,
                    location_metadata={},
                    location_type_id=location_types[type_name].id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(location)

        # Create item types
        item_types_data = [
            ("Equipment", "Physical equipment and machinery", "PARENT"),
            ("Furniture", "Office and warehouse furniture", "PARENT"),
            ("Component", "Individual components and parts", "CHILD"),
            ("Accessory", "Equipment accessories", "CHILD"),
        ]

        for name, description, category in item_types_data:
            existing_item_type = (
                db.query(ItemType).filter(ItemType.name == name).first()
            )
            if not existing_item_type:
                item_type = ItemType(
                    id=uuid.uuid4(),
                    name=name,
                    description=description,
                    category=category,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(item_type)

        # Commit all changes
        db.commit()

        logger.info("Database seeded successfully with admin user and sample data")

        return {
            "message": "Database seeded successfully!",
            "admin_user": {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin",
                "role": "admin",
            },
            "sample_data": {
                "location_types": len(location_types_data),
                "locations": len(locations_data),
                "item_types": len(item_types_data),
            },
            "status": "success",
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise HTTPException(status_code=500, detail=f"Error seeding database: {str(e)}")


@router.get("/seed-status")
async def get_seed_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Check if the database has been seeded."""
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        location_types_count = db.query(LocationType).count()
        locations_count = db.query(Location).count()
        item_types_count = db.query(ItemType).count()

        return {
            "admin_user_exists": admin_user is not None,
            "location_types_count": location_types_count,
            "locations_count": locations_count,
            "item_types_count": item_types_count,
            "seeded": admin_user is not None and location_types_count > 0,
        }

    except Exception as e:
        logger.error(f"Error checking seed status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error checking seed status: {str(e)}"
        )


@router.get("/debug/config")
async def debug_config() -> Dict[str, Any]:
    """Debug endpoint to check configuration."""
    import os

    from shared.config.settings import settings

    return {
        "database_url_from_settings": settings.database.url,
        "database_url_from_env": os.getenv("DATABASE_URL", "NOT_SET"),
        "environment": os.getenv("ENVIRONMENT", "NOT_SET"),
        "service_name": os.getenv("SERVICE_NAME", "NOT_SET"),
    }


@router.post("/run-migrations")
async def run_migrations() -> Dict[str, Any]:
    """Run database migrations."""
    try:
        import os

        from alembic import command
        from alembic.config import Config

        # Get database URL from environment
        database_url = os.getenv(
            "DATABASE_URL",
            (
                "postgresql://inventory_user:inventory_password@"
                "localhost:5432/inventory_management"
            ),
        )

        logger.info(f"Running migrations with DATABASE_URL: {database_url}")

        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        # Run migrations
        command.upgrade(alembic_cfg, "head")

        logger.info("Database migrations completed successfully")

        return {
            "message": "Database migrations completed successfully!",
            "database_url": database_url,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error running migrations: {str(e)}"
        )


@router.post("/test-login")
async def test_login(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Test login functionality."""
    try:
        from shared.auth.utils import verify_password

        # Find admin user without eager loading
        user = (
            db.query(User)
            .filter(User.username == "admin", User.active is True)
            .first()
        )

        if not user:
            # Check if user exists but is inactive
            inactive_user = db.query(User).filter(User.username == "admin").first()
            if inactive_user:
                return {
                    "message": "Admin user found but is inactive",
                    "user_found": True,
                    "active": False,
                    "status": "error"
                }
            return {"message": "Admin user not found", "user_found": False, "status": "error"}

        # Get role separately
        role = db.query(Role).filter(Role.id == user.role_id).first() if user.role_id else None

        # Test password verification
        password_correct = verify_password("admin", user.password_hash)

        return {
            "message": "Login test completed",
            "user_found": True,
            "active": user.active,
            "password_correct": password_correct,
            "user_id": str(user.id),
            "username": user.username,
            "role_id": str(user.role_id) if user.role_id else None,
            "role_name": role.name if role else None,
            "role_permissions": role.permissions if role else None,
            "password_hash_prefix": user.password_hash[:20] if user.password_hash else "None",
            "status": "success",
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error testing login: {e}", exc_info=True)
        return {
            "message": f"Error testing login: {str(e)}",
            "error_details": error_details,
            "status": "error"
        }


@router.post("/test-password")
async def test_password() -> Dict[str, Any]:
    """Test password hashing."""
    try:
        from shared.auth.utils import hash_password

        test_password = "admin"
        logger.info(f"Testing password hashing with password: {test_password}")
        logger.info(f"Password length in bytes: {len(test_password.encode('utf-8'))}")

        password_hash = hash_password(test_password)
        logger.info(f"Password hash generated successfully: {password_hash[:20]}...")

        return {
            "message": "Password hashing test successful",
            "password": test_password,
            "password_length_bytes": len(test_password.encode("utf-8")),
            "hash_length": len(password_hash),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error testing password: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing password: {str(e)}")


@router.get("/debug/users")
async def debug_users(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Debug endpoint to check all users in database."""
    try:
        # Get all users without eager loading
        users = db.query(User).all()

        users_data = []
        for user in users:
            # Get role separately to avoid lazy loading issues
            role = db.query(Role).filter(Role.id == user.role_id).first() if user.role_id else None
            
            users_data.append({
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "active": user.active,
                "role_id": str(user.role_id) if user.role_id else None,
                "role_name": role.name if role else None,
                "password_hash_length": len(user.password_hash) if user.password_hash else 0,
                "password_hash_prefix": user.password_hash[:20] if user.password_hash else "None",
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            })

        return {
            "message": "Users retrieved successfully",
            "total_users": len(users),
            "users": users_data,
            "status": "success",
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error retrieving users: {e}", exc_info=True)
        return {
            "message": f"Error retrieving users: {str(e)}",
            "error_details": error_details,
            "status": "error"
        }


@router.get("/debug/simple")
async def debug_simple() -> Dict[str, Any]:
    """Simple debug endpoint that doesn't query database."""
    return {
        "message": "Simple debug endpoint working",
        "status": "success"
    }
