"""Unit tests for inventory service routers."""

from uuid import uuid4

from fastapi import HTTPException  # noqa: F401

from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.user import Role, User


class TestItemTypesRouter:
    """Test item types router functionality."""

    def test_create_item_type(self, test_db_session):
        """Test creating an item type."""
        item_type = ItemType(
            id=uuid4(),
            name="Test Equipment",
            description="Test equipment type",
            category=ItemCategory.PARENT,
        )
        test_db_session.add(item_type)
        test_db_session.commit()
        test_db_session.refresh(item_type)

        assert item_type.id is not None
        assert item_type.name == "Test Equipment"
        assert item_type.category == ItemCategory.PARENT

    def test_get_item_type(self, test_db_session):
        """Test retrieving an item type."""
        item_type = ItemType(
            id=uuid4(),
            name="Test Equipment",
            description="Test equipment type",
            category=ItemCategory.PARENT,
        )
        test_db_session.add(item_type)
        test_db_session.commit()

        retrieved = (
            test_db_session.query(ItemType).filter(ItemType.id == item_type.id).first()
        )
        assert retrieved is not None
        assert retrieved.name == "Test Equipment"


class TestParentItemsRouter:
    """Test parent items router functionality."""

    def test_create_parent_item(self, test_db_session):
        """Test creating a parent item."""
        # Create dependencies
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role_id=role.id,
            active=True,
        )
        test_db_session.add(user)
        test_db_session.flush()

        location_type = LocationType(name="Warehouse", description="Storage")
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        item_type = ItemType(
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )
        test_db_session.add(item_type)
        test_db_session.flush()

        # Create parent item
        parent_item = ParentItem(
            name="Laptop",
            description="Dell Laptop",
            item_type_id=item_type.id,
            current_location_id=location.id,
            created_by=user.id,
        )
        test_db_session.add(parent_item)
        test_db_session.commit()
        test_db_session.refresh(parent_item)

        assert parent_item.id is not None
        assert parent_item.name == "Laptop"
        assert parent_item.current_location_id == location.id


class TestChildItemsRouter:
    """Test child items router functionality."""

    def test_create_child_item(self, test_db_session):
        """Test creating a child item."""
        # Create dependencies
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role_id=role.id,
            active=True,
        )
        test_db_session.add(user)
        test_db_session.flush()

        location_type = LocationType(name="Warehouse", description="Storage")
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        parent_item_type = ItemType(
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )
        child_item_type = ItemType(
            name="Component",
            description="Component items",
            category=ItemCategory.CHILD,
        )
        test_db_session.add_all([parent_item_type, child_item_type])
        test_db_session.flush()

        parent_item = ParentItem(
            name="Laptop",
            description="Dell Laptop",
            item_type_id=parent_item_type.id,
            current_location_id=location.id,
            created_by=user.id,
        )
        test_db_session.add(parent_item)
        test_db_session.flush()

        # Create child item
        child_item = ChildItem(
            name="Mouse",
            description="Wireless mouse",
            item_type_id=child_item_type.id,
            parent_item_id=parent_item.id,
            created_by=user.id,
        )
        test_db_session.add(child_item)
        test_db_session.commit()
        test_db_session.refresh(child_item)

        assert child_item.id is not None
        assert child_item.name == "Mouse"
        assert child_item.parent_item_id == parent_item.id
