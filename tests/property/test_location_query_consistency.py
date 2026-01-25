"""Property tests for location query consistency.

Feature: inventory-management, Property 1: Location Query Consistency
Validates: Requirements 1.1, 1.2
"""

import uuid

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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


def get_test_session():
    """Create a fresh test database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal(), engine


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

    # Create location
    location = Location(
        id=uuid.uuid4(),
        name="Test Location",
        description="Test location",
        location_type_id=location_type.id,
    )
    session.add(location)

    # Create parent item type
    parent_item_type = ItemType(
        id=uuid.uuid4(),
        name="parent_item_type",
        description="Parent item type",
        category=ItemCategory.PARENT,
    )
    session.add(parent_item_type)

    # Create child item type
    child_item_type = ItemType(
        id=uuid.uuid4(),
        name="child_item_type",
        description="Child item type",
        category=ItemCategory.CHILD,
    )
    session.add(child_item_type)

    session.commit()
    return user, location, parent_item_type, child_item_type


@given(
    parent_names=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
    child_counts=st.lists(
        st.integers(min_value=0, max_value=3), min_size=1, max_size=5
    ),
)
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_location_query_consistency_property(parent_names, child_counts):
    """
    Property 1: Location Query Consistency

    For any inventory query, all parent items should return their current location
    and all child items should appear at their parent item's location.

    **Validates: Requirements 1.1, 1.2**
    """
    session, engine = get_test_session()

    try:

        # Create test data
        user, location, parent_item_type, child_item_type = create_test_data(session)

        # Create parent items and their child items
        parent_items = []
        all_child_items = []

        for i, (parent_name, child_count) in enumerate(zip(parent_names, child_counts)):
            # Create parent item
            parent_item = ParentItem(
                id=uuid.uuid4(),
                name=f"{parent_name}_{i}",
                description=f"Test parent item {i}",
                item_type_id=parent_item_type.id,
                current_location_id=location.id,
                created_by=user.id,
            )
            session.add(parent_item)
            session.commit()  # Commit to get the ID
            parent_items.append(parent_item)

            # Create child items for this parent
            parent_child_items = []
            for j in range(child_count):
                child_item = ChildItem(
                    id=uuid.uuid4(),
                    name=f"Child_{i}_{j}",
                    description=f"Test child item {i}-{j}",
                    item_type_id=child_item_type.id,
                    parent_item_id=parent_item.id,
                    created_by=user.id,
                )
                session.add(child_item)
                parent_child_items.append(child_item)
                all_child_items.append(child_item)

            session.commit()

        # Property verification: Query all parent items and verify location
        # consistency
        queried_parent_items = session.query(ParentItem).all()

        # Requirement 1.1: All parent items should return their current
        # location
        for parent_item in queried_parent_items:
            assert parent_item.current_location_id is not None
            assert parent_item.current_location_id == location.id

            # Verify the location relationship is properly loaded
            assert parent_item.current_location is not None
            assert parent_item.current_location.id == location.id

        # Property verification: Query all child items and verify location
        # consistency
        queried_child_items = session.query(ChildItem).all()

        # Requirement 1.2: All child items should appear at their parent item's
        # location
        for child_item in queried_child_items:
            assert child_item.parent_item_id is not None
            assert child_item.parent_item is not None

            # Child item's effective location is its parent's location
            parent_location_id = child_item.parent_item.current_location_id
            assert parent_location_id == location.id

            # Verify the parent-child relationship is consistent
            assert child_item.parent_item.current_location.id == location.id

        # Additional consistency check: Verify parent-child relationships are
        # bidirectional
        for parent_item in queried_parent_items:
            for child_item in parent_item.child_items:
                # Each child should reference this parent
                assert child_item.parent_item_id == parent_item.id
                # Each child should be at the same effective location as parent
                assert (
                    child_item.parent_item.current_location_id
                    == parent_item.current_location_id
                )

        session.close()

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


if __name__ == "__main__":
    # Run a simple test to verify the property works
    test_location_query_consistency_property(["TestParent1", "TestParent2"], [2, 1])
    print("Property test passed!")
