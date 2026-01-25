"""Comprehensive router tests to increase coverage."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from shared.auth.utils import create_access_token, hash_password
from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory
from shared.models.user import Role, User


# Fixtures for common test data
@pytest.fixture
def admin_role(test_db_session):
    """Create admin role."""
    role = Role(
        id=uuid4(),
        name="admin",
        description="Administrator",
        permissions={"*": ["read", "write", "admin"]},
    )
    test_db_session.add(role)
    test_db_session.commit()
    return role


@pytest.fixture
def admin_user(test_db_session, admin_role):
    """Create admin user."""
    user = User(
        id=uuid4(),
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        role_id=admin_role.id,
        active=True,
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def location_type(test_db_session):
    """Create location type."""
    loc_type = LocationType(
        id=uuid4(), name="Warehouse", description="Storage facility"
    )
    test_db_session.add(loc_type)
    test_db_session.commit()
    return loc_type


@pytest.fixture
def location(test_db_session, location_type):
    """Create location."""
    loc = Location(
        id=uuid4(),
        name="Main Warehouse",
        description="Primary storage",
        location_type_id=location_type.id,
        location_metadata={},
    )
    test_db_session.add(loc)
    test_db_session.commit()
    return loc


@pytest.fixture
def parent_item_type(test_db_session):
    """Create parent item type."""
    item_type = ItemType(
        id=uuid4(),
        name="Equipment",
        description="Equipment items",
        category=ItemCategory.PARENT,
    )
    test_db_session.add(item_type)
    test_db_session.commit()
    return item_type


@pytest.fixture
def child_item_type(test_db_session):
    """Create child item type."""
    item_type = ItemType(
        id=uuid4(),
        name="Component",
        description="Component items",
        category=ItemCategory.CHILD,
    )
    test_db_session.add(item_type)
    test_db_session.commit()
    return item_type


@pytest.fixture
def parent_item(test_db_session, parent_item_type, location, admin_user):
    """Create parent item."""
    item = ParentItem(
        id=uuid4(),
        name="Server Rack",
        description="Main server rack",
        item_type_id=parent_item_type.id,
        current_location_id=location.id,
        created_by=admin_user.id,
    )
    test_db_session.add(item)
    test_db_session.commit()
    return item


@pytest.fixture
def child_item(test_db_session, child_item_type, parent_item, admin_user):
    """Create child item."""
    item = ChildItem(
        id=uuid4(),
        name="Power Supply",
        description="Backup power",
        item_type_id=child_item_type.id,
        parent_item_id=parent_item.id,
        created_by=admin_user.id,
    )
    test_db_session.add(item)
    test_db_session.commit()
    return item


# Test Location Types
def test_location_type_creation(test_db_session):
    """Test creating a location type."""
    loc_type = LocationType(id=uuid4(), name="Office", description="Office space")
    test_db_session.add(loc_type)
    test_db_session.commit()

    assert loc_type.id is not None
    assert loc_type.name == "Office"


def test_location_type_query(test_db_session, location_type):
    """Test querying location types."""
    result = test_db_session.query(LocationType).filter_by(name="Warehouse").first()
    assert result is not None
    assert result.id == location_type.id


def test_location_type_update(test_db_session, location_type):
    """Test updating a location type."""
    location_type.description = "Updated description"
    test_db_session.commit()

    updated = test_db_session.query(LocationType).filter_by(id=location_type.id).first()
    assert updated.description == "Updated description"


def test_location_type_delete(test_db_session):
    """Test deleting a location type."""
    loc_type = LocationType(id=uuid4(), name="Temporary")
    test_db_session.add(loc_type)
    test_db_session.commit()

    loc_type_id = loc_type.id
    test_db_session.delete(loc_type)
    test_db_session.commit()

    deleted = test_db_session.query(LocationType).filter_by(id=loc_type_id).first()
    assert deleted is None


# Test Locations
def test_location_creation(test_db_session, location_type):
    """Test creating a location."""
    loc = Location(
        id=uuid4(),
        name="Storage Room",
        location_type_id=location_type.id,
        location_metadata={"capacity": 100},
    )
    test_db_session.add(loc)
    test_db_session.commit()

    assert loc.id is not None
    assert loc.name == "Storage Room"


def test_location_with_metadata(test_db_session, location_type):
    """Test location with metadata."""
    metadata = {"capacity": 500, "temperature_controlled": True}
    loc = Location(
        id=uuid4(),
        name="Cold Storage",
        location_type_id=location_type.id,
        location_metadata=metadata,
    )
    test_db_session.add(loc)
    test_db_session.commit()

    assert loc.location_metadata["capacity"] == 500
    assert loc.location_metadata["temperature_controlled"] is True


def test_location_update(test_db_session, location):
    """Test updating a location."""
    location.description = "Updated warehouse"
    test_db_session.commit()

    updated = test_db_session.query(Location).filter_by(id=location.id).first()
    assert updated.description == "Updated warehouse"


# Test Item Types
def test_item_type_parent_creation(test_db_session):
    """Test creating a parent item type."""
    item_type = ItemType(
        id=uuid4(),
        name="Furniture",
        description="Office furniture",
        category=ItemCategory.PARENT,
    )
    test_db_session.add(item_type)
    test_db_session.commit()

    assert item_type.category == ItemCategory.PARENT


def test_item_type_child_creation(test_db_session):
    """Test creating a child item type."""
    item_type = ItemType(
        id=uuid4(),
        name="Accessory",
        description="Equipment accessories",
        category=ItemCategory.CHILD,
    )
    test_db_session.add(item_type)
    test_db_session.commit()

    assert item_type.category == ItemCategory.CHILD


# Test Parent Items
def test_parent_item_creation(test_db_session, parent_item_type, location, admin_user):
    """Test creating a parent item."""
    item = ParentItem(
        id=uuid4(),
        name="Desk",
        item_type_id=parent_item_type.id,
        current_location_id=location.id,
        created_by=admin_user.id,
    )
    test_db_session.add(item)
    test_db_session.commit()

    assert item.id is not None
    assert item.name == "Desk"


def test_parent_item_with_children(test_db_session, parent_item, child_item):
    """Test parent item with children."""
    # Refresh to load relationships
    test_db_session.refresh(parent_item)

    assert len(parent_item.child_items) == 1
    assert parent_item.child_items[0].id == child_item.id


def test_parent_item_location_change(test_db_session, parent_item, location_type):
    """Test changing parent item location."""
    new_location = Location(
        id=uuid4(),
        name="New Warehouse",
        location_type_id=location_type.id,
        location_metadata={},
    )
    test_db_session.add(new_location)
    test_db_session.commit()

    parent_item.current_location_id = new_location.id
    test_db_session.commit()

    updated = test_db_session.query(ParentItem).filter_by(id=parent_item.id).first()
    assert updated.current_location_id == new_location.id


# Test Child Items
def test_child_item_parent_relationship(test_db_session, child_item, parent_item):
    """Test child item parent relationship."""
    assert child_item.parent_item_id == parent_item.id


def test_child_item_update(test_db_session, child_item):
    """Test updating child item."""
    child_item.description = "Updated power supply"
    test_db_session.commit()

    updated = test_db_session.query(ChildItem).filter_by(id=child_item.id).first()
    assert updated.description == "Updated power supply"


# Test Move History
def test_move_history_creation(
    test_db_session, parent_item, location, location_type, admin_user
):
    """Test creating move history."""
    new_location = Location(
        id=uuid4(),
        name="Destination",
        location_type_id=location_type.id,
        location_metadata={},
    )
    test_db_session.add(new_location)
    test_db_session.commit()

    move = MoveHistory(
        id=uuid4(),
        parent_item_id=parent_item.id,
        from_location_id=location.id,
        to_location_id=new_location.id,
        moved_by=admin_user.id,
        moved_at=datetime.now(timezone.utc),
    )
    test_db_session.add(move)
    test_db_session.commit()

    assert move.id is not None
    assert move.from_location_id == location.id
    assert move.to_location_id == new_location.id


def test_move_history_with_notes(
    test_db_session, parent_item, location, location_type, admin_user
):
    """Test move history with notes."""
    new_location = Location(
        id=uuid4(),
        name="Destination",
        location_type_id=location_type.id,
        location_metadata={},
    )
    test_db_session.add(new_location)
    test_db_session.commit()

    move = MoveHistory(
        id=uuid4(),
        parent_item_id=parent_item.id,
        from_location_id=location.id,
        to_location_id=new_location.id,
        moved_by=admin_user.id,
        moved_at=datetime.now(timezone.utc),
        notes="Scheduled maintenance",
    )
    test_db_session.add(move)
    test_db_session.commit()

    assert move.notes == "Scheduled maintenance"


# Test User and Role
def test_user_creation(test_db_session, admin_role):
    """Test creating a user."""
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("password123"),
        role_id=admin_role.id,
        active=True,
    )
    test_db_session.add(user)
    test_db_session.commit()

    assert user.id is not None
    assert user.username == "testuser"


def test_user_role_relationship(test_db_session, admin_user, admin_role):
    """Test user role relationship."""
    test_db_session.refresh(admin_user)
    assert admin_user.role_id == admin_role.id


def test_user_inactive(test_db_session, admin_role):
    """Test inactive user."""
    user = User(
        id=uuid4(),
        username="inactive",
        email="inactive@example.com",
        password_hash=hash_password("password"),
        role_id=admin_role.id,
        active=False,
    )
    test_db_session.add(user)
    test_db_session.commit()

    assert user.active is False


def test_role_permissions(test_db_session):
    """Test role with permissions."""
    role = Role(
        id=uuid4(),
        name="viewer",
        description="Read-only access",
        permissions={"inventory": ["read"], "location": ["read"]},
    )
    test_db_session.add(role)
    test_db_session.commit()

    assert "inventory" in role.permissions
    assert "read" in role.permissions["inventory"]


# Test JWT Token Operations
def test_create_jwt_token():
    """Test JWT token creation."""
    token = create_access_token(
        data={"sub": str(uuid4()), "username": "test", "role": "admin"}
    )
    assert token is not None
    assert isinstance(token, str)


def test_password_hashing():
    """Test password hashing."""
    password = "secure_password_123"
    hashed = hash_password(password)
    assert hashed is not None
    assert hashed != password


# Test Query Operations
def test_query_locations_by_type(test_db_session, location_type, location):
    """Test querying locations by type."""
    locations = (
        test_db_session.query(Location)
        .filter_by(location_type_id=location_type.id)
        .all()
    )
    assert len(locations) >= 1
    assert location.id in [loc.id for loc in locations]


def test_query_items_by_location(test_db_session, location, parent_item):
    """Test querying items by location."""
    items = (
        test_db_session.query(ParentItem)
        .filter_by(current_location_id=location.id)
        .all()
    )
    assert len(items) >= 1
    assert parent_item.id in [item.id for item in items]


def test_query_child_items_by_parent(test_db_session, parent_item, child_item):
    """Test querying child items by parent."""
    children = (
        test_db_session.query(ChildItem).filter_by(parent_item_id=parent_item.id).all()
    )
    assert len(children) >= 1
    assert child_item.id in [c.id for c in children]


def test_count_items_by_type(test_db_session, parent_item_type, parent_item):
    """Test counting items by type."""
    count = (
        test_db_session.query(ParentItem)
        .filter_by(item_type_id=parent_item_type.id)
        .count()
    )
    assert count >= 1
