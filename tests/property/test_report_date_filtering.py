"""Property tests for report date filtering.

Feature: inventory-management, Property 7: Report Date Filtering
Validates: Requirements 3.2, 5.2
"""

import uuid
from datetime import datetime, timedelta, timezone

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
    MoveHistory,
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
        name="Location 1",
        description="Test location 1",
        location_type_id=location_type.id,
    )
    location2 = Location(
        id=uuid.uuid4(),
        name="Location 2",
        description="Test location 2",
        location_type_id=location_type.id,
    )
    session.add_all([location1, location2])

    # Create parent item type
    parent_item_type = ItemType(
        id=uuid.uuid4(),
        name="parent_item_type",
        description="Parent item type",
        category=ItemCategory.PARENT,
    )
    session.add(parent_item_type)

    session.commit()
    return user, location1, location2, parent_item_type


@given(
    movement_configs=st.lists(
        st.tuples(
            st.integers(min_value=-30, max_value=30),  # days offset from now
            st.integers(min_value=0, max_value=23),  # hour of day
            st.sampled_from([0, 1]),  # location index (0 or 1)
        ),
        min_size=1,
        max_size=10,
    ),
    filter_start_days=st.integers(min_value=-15, max_value=15),
    filter_end_days=st.integers(min_value=-15, max_value=15),
)
def test_report_date_filtering_property(
    movement_configs, filter_start_days, filter_end_days
):
    """
    Property 7: Report Date Filtering

    For any movement history report with date range filters, only movements
    within the specified date range should be included in chronological order.

    **Validates: Requirements 3.2, 5.2**
    """
    setup_test_database()

    try:
        session = SessionLocal()

        # Create test data
        user, location1, location2, parent_item_type = create_test_data(session)
        locations = [location1, location2]

        # Base time for generating movements
        base_time = datetime.now(timezone.utc)

        # Ensure filter dates are in correct order
        if filter_start_days > filter_end_days:
            filter_start_days, filter_end_days = (
                filter_end_days,
                filter_start_days,
            )

        filter_start_date = base_time + timedelta(days=filter_start_days)
        filter_end_date = base_time + timedelta(days=filter_end_days)

        # Create parent items and movements based on the generated
        # configuration
        movements_created = []
        expected_filtered_movements = []

        for i, (days_offset, hour, location_idx) in enumerate(movement_configs):
            # Create parent item
            parent_item = ParentItem(
                id=uuid.uuid4(),
                name=f"Parent_Item_{i}",
                description=f"Test parent item {i}",
                item_type_id=parent_item_type.id,
                current_location_id=locations[0].id,  # Start at location 0
                created_by=user.id,
            )
            session.add(parent_item)
            session.commit()

            # Create movement with specific timestamp
            movement_time = base_time + timedelta(days=days_offset, hours=hour)

            movement = MoveHistory(
                id=uuid.uuid4(),
                parent_item_id=parent_item.id,
                from_location_id=locations[0].id,
                to_location_id=locations[location_idx].id,
                moved_at=movement_time,
                moved_by=user.id,
                notes=f"Test movement {i}",
            )
            session.add(movement)
            movements_created.append((movement, movement_time))

            # Check if this movement should be included in filtered results
            # Requirement 3.2: Only movements within specified date range
            if filter_start_date <= movement_time <= filter_end_date:
                expected_filtered_movements.append((movement, movement_time))

        session.commit()

        # Query movements with date filtering (simulating report logic)
        # Requirement 3.2: Movement history within specified date ranges
        query = session.query(MoveHistory).filter(
            MoveHistory.moved_at >= filter_start_date,
            MoveHistory.moved_at <= filter_end_date,
        )

        # Requirement 5.2: Chronologically ordered movement records
        filtered_movements = query.order_by(MoveHistory.moved_at.desc()).all()

        # Verify filtering accuracy
        assert len(filtered_movements) == len(
            expected_filtered_movements
        ), f"Filtered movements count mismatch: expected {len(expected_filtered_movements)}, got {len(filtered_movements)}"

        # Verify all filtered movements are within the date range
        for movement in filtered_movements:
            assert filter_start_date <= movement.moved_at <= filter_end_date, (
                f"Movement {movement.id} at {movement.moved_at} is outside "
                f"filter range [{filter_start_date}, {filter_end_date}]"
            )

        # Verify chronological ordering (most recent first)
        # Requirement 5.2: Chronologically ordered movement records
        if len(filtered_movements) > 1:
            for i in range(len(filtered_movements) - 1):
                current_time = filtered_movements[i].moved_at
                next_time = filtered_movements[i + 1].moved_at
                assert (
                    current_time >= next_time
                ), f"Movements not in chronological order: {current_time} should be >= {next_time}"

        # Verify no movements outside the date range are included
        all_movements = session.query(MoveHistory).all()
        for movement in all_movements:
            if movement not in filtered_movements:
                # This movement should be outside the date range
                assert not (
                    filter_start_date <= movement.moved_at <= filter_end_date
                ), (
                    f"Movement {movement.id} at {movement.moved_at} should be "
                    f"excluded but is within range [{filter_start_date}, "
                    f"{filter_end_date}]"
                )

        # Test edge cases: exact boundary conditions
        # Movements exactly at start_date should be included
        boundary_movements_start = (
            session.query(MoveHistory)
            .filter(MoveHistory.moved_at == filter_start_date)
            .all()
        )
        for movement in boundary_movements_start:
            assert (
                movement in filtered_movements
            ), f"Movement at start boundary {filter_start_date} should be included"

        # Movements exactly at end_date should be included
        boundary_movements_end = (
            session.query(MoveHistory)
            .filter(MoveHistory.moved_at == filter_end_date)
            .all()
        )
        for movement in boundary_movements_end:
            assert (
                movement in filtered_movements
            ), f"Movement at end boundary {filter_end_date} should be included"

        # Test with no date filters (should return all movements in
        # chronological order)
        all_movements_ordered = (
            session.query(MoveHistory).order_by(MoveHistory.moved_at.desc()).all()
        )

        # Verify chronological ordering for all movements
        if len(all_movements_ordered) > 1:
            for i in range(len(all_movements_ordered) - 1):
                current_time = all_movements_ordered[i].moved_at
                next_time = all_movements_ordered[i + 1].moved_at
                assert (
                    current_time >= next_time
                ), f"All movements not in chronological order: {current_time} should be >= {next_time}"

        session.close()

    finally:
        teardown_test_database()


if __name__ == "__main__":
    # Run a simple test to verify the property works
    test_report_date_filtering_property(
        [(-5, 10, 0), (0, 14, 1), (5, 8, 0)],  # movements at -5, 0, +5 days
        -3,  # filter start: -3 days
        3,  # filter end: +3 days
    )
    print("Property test passed!")
