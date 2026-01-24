"""Property tests for data model relationships.

Feature: inventory-management, Property 3: Cascading Item Movement
Validates: Requirements 2.2, 9.3
"""

import uuid
from datetime import datetime

from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.models import (
    Base,
    ChildItem,
    ItemCategory,
    ItemType,
    Location,
    LocationType,
    ParentItem,
    Role,
    User,
)

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_database():
    """Set up test database with tables."""
    Base.metadata.create_all(bind=engine)


def teardown_test_database():
    """Clean up test database."""
    Base.metadata.drop_all(bind=engine)


def create_test_data(session):
    """Create minimal test data required for property tests."""
    # Create role
    role = Role(
        id=uuid.uuid4(),
        name="test_role",
        description="Test role",
        permissions={},
    )
    session.add(role)

    # Create user
    user = User(
        id=uuid.uuid4(),
        username="test_user",
        email="test@example.com",
        password_hash="hashed_password",
        active=True,
        role_id=role.id,
    )
    session.add(user)

    # Create location type
    location_type = LocationType(
        id=uuid.uuid4(), name="warehouse", description="Warehouse location"
    )
    session.add(location_type)

    # Create locations
    location1 = Location(
        id=uuid.uuid4(),
        name="Location A",
        description="First location",
        location_type_id=location_type.id,
    )
    location2 = Location(
        id=uuid.uuid4(),
        name="Location B",
        description="Second location",
        location_type_id=location_type.id,
    )
    session.add_all([location1, location2])

    # Create item type
    item_type = ItemType(
        id=uuid.uuid4(),
        name="test_item_type",
        description="Test item type",
        category=ItemCategory.PARENT,
    )
    session.add(item_type)

    session.commit()
    return user, location1, location2, item_type


@given(
    parent_name=st.text(min_size=1, max_size=50),
    child_names=st.lists(
        st.text(min_size=1, max_size=50), min_size=1, max_size=5
    ),
)
def test_cascading_item_movement_property(parent_name, child_names):
    """
    Property 3: Cascading Item Movement

    For any parent item with assigned child items, moving the parent item
    should result in all child items being located at the same new location.

    **Validates: Requirements 2.2, 9.3**
    """
    setup_test_database()

    try:
        session = SessionLocal()

        # Create test data
        user, location1, location2, parent_item_type = create_test_data(
            session
        )

        # Create child item type
        child_item_type = ItemType(
            id=uuid.uuid4(),
            name="child_item_type",
            description="Child item type",
            category=ItemCategory.CHILD,
        )
        session.add(child_item_type)
        session.commit()

        # Create parent item at location1
        parent_item = ParentItem(
            id=uuid.uuid4(),
            name=parent_name,
            description="Test parent item",
            item_type_id=parent_item_type.id,
            current_location_id=location1.id,
            created_by=user.id,
        )
        session.add(parent_item)
        session.commit()

        # Create child items assigned to parent
        child_items = []
        for child_name in child_names:
            child_item = ChildItem(
                id=uuid.uuid4(),
                name=child_name,
                description="Test child item",
                item_type_id=child_item_type.id,
                parent_item_id=parent_item.id,
                created_by=user.id,
            )
            child_items.append(child_item)
            session.add(child_item)

        session.commit()

        # Verify initial state: parent is at location1
        assert parent_item.current_location_id == location1.id

        # Verify initial state: all child items are conceptually at parent's location
        for child_item in child_items:
            assert child_item.parent_item_id == parent_item.id
            # Child items inherit location from parent
            assert child_item.parent_item.current_location_id == location1.id

        # Move parent item to location2
        parent_item.current_location_id = location2.id
        session.commit()

        # Refresh objects from database
        session.refresh(parent_item)
        for child_item in child_items:
            session.refresh(child_item)

        # Property verification: parent is now at location2
        assert parent_item.current_location_id == location2.id

        # Property verification: all child items are now conceptually at location2
        # (through their parent's location)
        for child_item in child_items:
            assert child_item.parent_item_id == parent_item.id
            assert child_item.parent_item.current_location_id == location2.id

        session.close()

    finally:
        teardown_test_database()


if __name__ == "__main__":
    # Run a simple test to verify the property works
    test_cascading_item_movement_property("TestParent", ["Child1", "Child2"])
    print("Property test passed!")
