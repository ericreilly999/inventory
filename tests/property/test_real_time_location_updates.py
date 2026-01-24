"""Property tests for real-time location updates.

Feature: inventory-management, Property 2: Real-time Location Updates
Validates: Requirements 1.3, 1.4
"""

import uuid

from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.models import (
    Base,
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

    # Create two locations
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
        name="parent_item_type",
        description="Parent item type",
        category=ItemCategory.PARENT,
    )
    session.add(item_type)

    session.commit()
    return user, location1, location2, item_type


@given(
    item_names=st.lists(
        st.text(min_size=1, max_size=50), min_size=1, max_size=3
    )
)
def test_real_time_location_updates_property(item_names):
    """
    Property 2: Real-time Location Updates

    For any item location update, immediately querying that item should
    return the new location.

    **Validates: Requirements 1.3, 1.4**
    """
    setup_test_database()

    try:
        session = SessionLocal()

        # Create test data
        user, location1, location2, item_type = create_test_data(session)

        # Create parent items at location1
        parent_items = []
        for i, item_name in enumerate(item_names):
            parent_item = ParentItem(
                id=uuid.uuid4(),
                name=f"{item_name}_{i}",
                description=f"Test parent item {i}",
                item_type_id=item_type.id,
                current_location_id=location1.id,
                created_by=user.id,
            )
            session.add(parent_item)
            parent_items.append(parent_item)

        session.commit()

        # Verify initial state: all items are at location1
        for parent_item in parent_items:
            session.refresh(parent_item)
            assert parent_item.current_location_id == location1.id

        # Update each item's location to location2
        for parent_item in parent_items:
            # Requirement 1.3: System maintains accurate location data in
            # real-time
            parent_item.current_location_id = location2.id
            session.commit()

            # Requirement 1.4: Location change reflects immediately in queries
            # Immediately query the item after update
            session.refresh(parent_item)
            updated_item = (
                session.query(ParentItem)
                .filter(ParentItem.id == parent_item.id)
                .first()
            )

            # Property verification: immediate query returns new location
            assert updated_item is not None
            assert updated_item.current_location_id == location2.id
            assert updated_item.current_location.id == location2.id
            assert updated_item.current_location.name == location2.name

        # Additional verification: Query all items and verify they're all at
        # location2
        all_items_at_location2 = (
            session.query(ParentItem)
            .filter(ParentItem.current_location_id == location2.id)
            .all()
        )

        # All items should now be at location2
        assert len(all_items_at_location2) == len(parent_items)

        # No items should be at location1
        items_at_location1 = (
            session.query(ParentItem)
            .filter(ParentItem.current_location_id == location1.id)
            .all()
        )
        assert len(items_at_location1) == 0

        # Test reverse update: move all items back to location1
        for parent_item in parent_items:
            parent_item.current_location_id = location1.id
            session.commit()

            # Immediate verification
            session.refresh(parent_item)
            assert parent_item.current_location_id == location1.id

        # Final verification: all items back at location1
        final_items_at_location1 = (
            session.query(ParentItem)
            .filter(ParentItem.current_location_id == location1.id)
            .all()
        )
        assert len(final_items_at_location1) == len(parent_items)

        session.close()

    finally:
        teardown_test_database()


if __name__ == "__main__":
    # Run a simple test to verify the property works
    test_real_time_location_updates_property(["TestItem1", "TestItem2"])
    print("Property test passed!")
