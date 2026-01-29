"""Unit tests for inventory child items router."""

from uuid import uuid4

from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.user import Role, User


def test_create_child_item(test_db_session):
    """Test creating a child item."""
    # Create test data
    role = Role(
        id=uuid4(),
        name="admin",
        description="Admin role",
        permissions={"inventory": ["read", "write", "admin"]},
    )
    test_db_session.add(role)

    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
        role_id=role.id,
        active=True,
    )
    test_db_session.add(user)

    location_type = LocationType(
        id=uuid4(), name="Warehouse", description="Storage facility"
    )
    test_db_session.add(location_type)

    location = Location(
        id=uuid4(),
        name="Main Warehouse",
        description="Primary storage",
        location_type_id=location_type.id,
        location_metadata={},
    )
    test_db_session.add(location)

    parent_item_type = ItemType(
        id=uuid4(),
        name="Equipment",
        description="Equipment type",
        category=ItemCategory.PARENT,
    )
    test_db_session.add(parent_item_type)

    child_item_type = ItemType(
        id=uuid4(),
        name="Component",
        description="Component type",
        category=ItemCategory.CHILD,
    )
    test_db_session.add(child_item_type)

    parent_item = ParentItem(
        id=uuid4(),
        sku="Server Rack",
        description="Main server rack",
        item_type_id=parent_item_type.id,
        current_location_id=location.id,
        created_by=user.id,
    )
    test_db_session.add(parent_item)
    test_db_session.commit()

    # Create child item
    child_item = ChildItem(
        id=uuid4(),
        sku="Power Supply",
        description="Backup power supply",
        item_type_id=child_item_type.id,
        parent_item_id=parent_item.id,
        created_by=user.id,
    )
    test_db_session.add(child_item)
    test_db_session.commit()

    # Verify
    assert child_item.id is not None
    assert child_item.sku == "Power Supply"
    assert child_item.parent_item_id == parent_item.id


def test_list_child_items(test_db_session):
    """Test listing child items."""
    # Create test data
    role = Role(id=uuid4(), name="admin", permissions={})
    test_db_session.add(role)

    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
        role_id=role.id,
        active=True,
    )
    test_db_session.add(user)

    location_type = LocationType(id=uuid4(), name="Warehouse")
    test_db_session.add(location_type)

    location = Location(
        id=uuid4(),
        name="Warehouse",
        location_type_id=location_type.id,
        location_metadata={},
    )
    test_db_session.add(location)

    parent_type = ItemType(id=uuid4(), name="Equipment", category=ItemCategory.PARENT)
    child_type = ItemType(id=uuid4(), name="Component", category=ItemCategory.CHILD)
    test_db_session.add_all([parent_type, child_type])

    parent = ParentItem(
        id=uuid4(),
        sku="Parent",
        item_type_id=parent_type.id,
        current_location_id=location.id,
        created_by=user.id,
    )
    test_db_session.add(parent)
    test_db_session.commit()

    # Create multiple child items
    for i in range(3):
        child = ChildItem(
            id=uuid4(),
            sku=f"Child {i}",
            item_type_id=child_type.id,
            parent_item_id=parent.id,
            created_by=user.id,
        )
        test_db_session.add(child)
    test_db_session.commit()

    # Query
    children = test_db_session.query(ChildItem).all()
    assert len(children) == 3


def test_update_child_item(test_db_session):
    """Test updating a child item."""
    role = Role(id=uuid4(), name="admin", permissions={})
    test_db_session.add(role)

    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
        role_id=role.id,
        active=True,
    )
    test_db_session.add(user)

    location_type = LocationType(id=uuid4(), name="Warehouse")
    test_db_session.add(location_type)

    location = Location(
        id=uuid4(),
        name="Warehouse",
        location_type_id=location_type.id,
        location_metadata={},
    )
    test_db_session.add(location)

    parent_type = ItemType(id=uuid4(), name="Equipment", category=ItemCategory.PARENT)
    child_type = ItemType(id=uuid4(), name="Component", category=ItemCategory.CHILD)
    test_db_session.add_all([parent_type, child_type])

    parent = ParentItem(
        id=uuid4(),
        sku="Parent",
        item_type_id=parent_type.id,
        current_location_id=location.id,
        created_by=user.id,
    )
    test_db_session.add(parent)

    child = ChildItem(
        id=uuid4(),
        sku="Original Name",
        item_type_id=child_type.id,
        parent_item_id=parent.id,
        created_by=user.id,
    )
    test_db_session.add(child)
    test_db_session.commit()

    # Update
    child.name = "Updated Name"
    child.description = "New description"
    test_db_session.commit()

    # Verify
    updated = test_db_session.query(ChildItem).filter_by(id=child.id).first()
    assert updated.name == "Updated Name"
    assert updated.description == "New description"


def test_delete_child_item(test_db_session):
    """Test deleting a child item."""
    role = Role(id=uuid4(), name="admin", permissions={})
    test_db_session.add(role)

    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
        role_id=role.id,
        active=True,
    )
    test_db_session.add(user)

    location_type = LocationType(id=uuid4(), name="Warehouse")
    test_db_session.add(location_type)

    location = Location(
        id=uuid4(),
        name="Warehouse",
        location_type_id=location_type.id,
        location_metadata={},
    )
    test_db_session.add(location)

    parent_type = ItemType(id=uuid4(), name="Equipment", category=ItemCategory.PARENT)
    child_type = ItemType(id=uuid4(), name="Component", category=ItemCategory.CHILD)
    test_db_session.add_all([parent_type, child_type])

    parent = ParentItem(
        id=uuid4(),
        sku="Parent",
        item_type_id=parent_type.id,
        current_location_id=location.id,
        created_by=user.id,
    )
    test_db_session.add(parent)

    child = ChildItem(
        id=uuid4(),
        sku="To Delete",
        item_type_id=child_type.id,
        parent_item_id=parent.id,
        created_by=user.id,
    )
    test_db_session.add(child)
    test_db_session.commit()

    child_id = child.id

    # Delete
    test_db_session.delete(child)
    test_db_session.commit()

    # Verify
    deleted = test_db_session.query(ChildItem).filter_by(id=child_id).first()
    assert deleted is None
