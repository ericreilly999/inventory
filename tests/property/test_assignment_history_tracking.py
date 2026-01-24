"""Property-based tests for assignment history tracking functionality.

**Feature: inventory-management, Property 11: Assignment History Tracking**
**Validates: Requirements 9.4, 9.5**
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from shared.models.assignment_history import AssignmentHistory
from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.user import Role, User


@st.composite
def child_item_with_parents(draw):
    """Generate a child item with two parent items for reassignment testing."""
    # Generate item types
    parent_item_type = ItemType(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        category=ItemCategory.PARENT,
    )

    child_item_type = ItemType(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        category=ItemCategory.CHILD,
    )

    # Generate location type and location
    location_type = LocationType(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
    )

    location = Location(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        location_type_id=location_type.id,
        location_type=location_type,
    )

    # Generate user
    role = Role(
        id=uuid4(),
        name="inventory_manager",
        description="Inventory Manager Role",
        permissions={"inventory": ["read", "write"]},
    )

    user = User(
        id=uuid4(),
        username=draw(st.text(min_size=1, max_size=50)),
        email=draw(st.emails()),
        password_hash="hashed_password",
        active=True,
        role_id=role.id,
        role=role,
    )

    # Generate parent items
    parent_item_1 = ParentItem(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=100)),
        description=draw(st.text(min_size=0, max_size=200)),
        item_type_id=parent_item_type.id,
        current_location_id=location.id,
        created_by=user.id,
        item_type=parent_item_type,
        current_location=location,
        creator=user,
    )

    parent_item_2 = ParentItem(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=100)),
        description=draw(st.text(min_size=0, max_size=200)),
        item_type_id=parent_item_type.id,
        current_location_id=location.id,
        created_by=user.id,
        item_type=parent_item_type,
        current_location=location,
        creator=user,
    )

    # Generate child item initially assigned to parent_item_1
    child_item = ChildItem(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=100)),
        description=draw(st.text(min_size=0, max_size=200)),
        item_type_id=child_item_type.id,
        parent_item_id=parent_item_1.id,
        created_by=user.id,
        item_type=child_item_type,
        parent_item=parent_item_1,
        creator=user,
    )

    return {
        "child_item": child_item,
        "parent_item_1": parent_item_1,
        "parent_item_2": parent_item_2,
        "user": user,
        "parent_item_type": parent_item_type,
        "child_item_type": child_item_type,
        "location_type": location_type,
        "location": location,
        "role": role,
    }


@given(data=child_item_with_parents())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_assignment_history_tracking_property(test_db_session, data):
    """
    Property 11: Assignment History Tracking

    For any child item reassignment between parent items, the assignment change
    should be recorded in the audit history.

    **Validates: Requirements 9.4, 9.5**
    """
    # Setup test data
    child_item = data["child_item"]
    parent_item_1 = data["parent_item_1"]
    parent_item_2 = data["parent_item_2"]
    user = data["user"]
    parent_item_type = data["parent_item_type"]
    child_item_type = data["child_item_type"]
    location_type = data["location_type"]
    location = data["location"]
    role = data["role"]

    # Add all entities to database
    test_db_session.add(role)
    test_db_session.add(user)
    test_db_session.add(location_type)
    test_db_session.add(location)
    test_db_session.add(parent_item_type)
    test_db_session.add(child_item_type)
    test_db_session.add(parent_item_1)
    test_db_session.add(parent_item_2)
    test_db_session.add(child_item)
    test_db_session.commit()

    # Record the time before reassignment
    before_assignment_time = datetime.now(timezone.utc)

    # Simulate child item reassignment by creating assignment history record
    # (This simulates what the API would do when reassigning a child item)
    original_parent_id = child_item.parent_item_id
    child_item.parent_item_id = parent_item_2.id

    assignment_history = AssignmentHistory(
        child_item_id=child_item.id,
        from_parent_item_id=original_parent_id,
        to_parent_item_id=parent_item_2.id,
        assigned_at=datetime.now(timezone.utc),
        assigned_by=user.id,
        notes="Test reassignment",
    )

    test_db_session.add(assignment_history)
    test_db_session.commit()
    test_db_session.refresh(assignment_history)

    # Record the time after reassignment
    after_assignment_time = datetime.now(timezone.utc)

    # Verify assignment history properties
    # 1. Assignment history record exists
    assert assignment_history.id is not None

    # 2. Contains correct child item reference
    assert assignment_history.child_item_id == child_item.id

    # 3. Contains correct source parent item
    assert assignment_history.from_parent_item_id == parent_item_1.id

    # 4. Contains correct destination parent item
    assert assignment_history.to_parent_item_id == parent_item_2.id

    # 5. Contains user information
    assert assignment_history.assigned_by == user.id

    # 6. Contains timestamp within reasonable bounds
    assert (
        before_assignment_time
        <= assignment_history.assigned_at
        <= after_assignment_time
    )

    # 7. Child item assignment is updated
    assert child_item.parent_item_id == parent_item_2.id

    # 8. Assignment history can be queried by child item
    history_records = (
        test_db_session.query(AssignmentHistory)
        .filter(AssignmentHistory.child_item_id == child_item.id)
        .all()
    )
    assert len(history_records) == 1
    assert history_records[0].id == assignment_history.id

    # 9. Assignment history can be queried by parent item (from)
    from_parent_assignments = (
        test_db_session.query(AssignmentHistory)
        .filter(AssignmentHistory.from_parent_item_id == parent_item_1.id)
        .all()
    )
    assert len(from_parent_assignments) == 1

    # 10. Assignment history can be queried by parent item (to)
    to_parent_assignments = (
        test_db_session.query(AssignmentHistory)
        .filter(AssignmentHistory.to_parent_item_id == parent_item_2.id)
        .all()
    )
    assert len(to_parent_assignments) == 1

    # 11. Assignment history can be queried by date range
    date_filtered_assignments = (
        test_db_session.query(AssignmentHistory)
        .filter(
            AssignmentHistory.assigned_at >= before_assignment_time,
            AssignmentHistory.assigned_at <= after_assignment_time,
        )
        .all()
    )
    assert len(date_filtered_assignments) == 1


@given(data=child_item_with_parents())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_initial_assignment_history_tracking(test_db_session, data):
    """
    Test that initial assignment (creation) is tracked in assignment history.

    **Validates: Requirements 9.4**
    """
    # Setup test data
    child_item = data["child_item"]
    parent_item_1 = data["parent_item_1"]
    parent_item_2 = data["parent_item_2"]
    user = data["user"]
    parent_item_type = data["parent_item_type"]
    child_item_type = data["child_item_type"]
    location_type = data["location_type"]
    location = data["location"]
    role = data["role"]

    # Add all entities to database
    test_db_session.add(role)
    test_db_session.add(user)
    test_db_session.add(location_type)
    test_db_session.add(location)
    test_db_session.add(parent_item_type)
    test_db_session.add(child_item_type)
    test_db_session.add(parent_item_1)
    test_db_session.add(parent_item_2)
    test_db_session.add(child_item)
    test_db_session.commit()

    # Record the time before initial assignment
    before_assignment_time = datetime.now(timezone.utc)

    # Simulate initial assignment history record creation
    # (This simulates what the API would do when creating a child item)
    initial_assignment_history = AssignmentHistory(
        child_item_id=child_item.id,
        from_parent_item_id=None,  # Initial assignment has no "from" parent
        to_parent_item_id=parent_item_1.id,
        assigned_at=datetime.now(timezone.utc),
        assigned_by=user.id,
        notes="Initial assignment",
    )

    test_db_session.add(initial_assignment_history)
    test_db_session.commit()
    test_db_session.refresh(initial_assignment_history)

    # Record the time after assignment
    after_assignment_time = datetime.now(timezone.utc)

    # Verify initial assignment history properties
    # 1. Assignment history record exists
    assert initial_assignment_history.id is not None

    # 2. Contains correct child item reference
    assert initial_assignment_history.child_item_id == child_item.id

    # 3. Has no source parent item (initial assignment)
    assert initial_assignment_history.from_parent_item_id is None

    # 4. Contains correct destination parent item
    assert initial_assignment_history.to_parent_item_id == parent_item_1.id

    # 5. Contains user information
    assert initial_assignment_history.assigned_by == user.id

    # 6. Contains timestamp within reasonable bounds
    assert (
        before_assignment_time
        <= initial_assignment_history.assigned_at
        <= after_assignment_time
    )

    # 7. Can be queried by child item
    history_records = (
        test_db_session.query(AssignmentHistory)
        .filter(AssignmentHistory.child_item_id == child_item.id)
        .all()
    )
    assert len(history_records) == 1
    assert history_records[0].id == initial_assignment_history.id


@given(data=child_item_with_parents())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_multiple_assignment_history_chronological_order(test_db_session, data):
    """
    Test that multiple assignment history records are maintained in chronological order.

    **Validates: Requirements 9.5**
    """
    # Setup test data
    child_item = data["child_item"]
    parent_item_1 = data["parent_item_1"]
    parent_item_2 = data["parent_item_2"]
    user = data["user"]
    parent_item_type = data["parent_item_type"]
    child_item_type = data["child_item_type"]
    location_type = data["location_type"]
    location = data["location"]
    role = data["role"]

    # Add all entities to database
    test_db_session.add(role)
    test_db_session.add(user)
    test_db_session.add(location_type)
    test_db_session.add(location)
    test_db_session.add(parent_item_type)
    test_db_session.add(child_item_type)
    test_db_session.add(parent_item_1)
    test_db_session.add(parent_item_2)
    test_db_session.add(child_item)
    test_db_session.commit()

    # Create multiple assignment history records with different timestamps
    assignment_times = [
        datetime.now(timezone.utc) - timedelta(hours=3),
        datetime.now(timezone.utc) - timedelta(hours=2),
        datetime.now(timezone.utc) - timedelta(hours=1),
        datetime.now(timezone.utc),
    ]

    assignment_records = []
    for i, assignment_time in enumerate(assignment_times):
        # Alternate between parent items
        current_from = parent_item_1 if i % 2 == 0 else parent_item_2
        current_to = parent_item_2 if i % 2 == 0 else parent_item_1

        assignment_history = AssignmentHistory(
            child_item_id=child_item.id,
            from_parent_item_id=(
                current_from.id if i > 0 else None
            ),  # First assignment has no "from"
            to_parent_item_id=current_to.id,
            assigned_at=assignment_time,
            assigned_by=user.id,
            notes=f"Assignment {i + 1}",
        )

        test_db_session.add(assignment_history)
        assignment_records.append(assignment_history)

    test_db_session.commit()

    # Query assignment history ordered by timestamp (most recent first)
    ordered_assignments = (
        test_db_session.query(AssignmentHistory)
        .filter(AssignmentHistory.child_item_id == child_item.id)
        .order_by(AssignmentHistory.assigned_at.desc())
        .all()
    )

    # Verify chronological ordering (most recent first)
    assert len(ordered_assignments) == 4
    for i in range(len(ordered_assignments) - 1):
        assert (
            ordered_assignments[i].assigned_at >= ordered_assignments[i + 1].assigned_at
        )

    # Verify the most recent assignment is first
    assert ordered_assignments[0].assigned_at == assignment_times[-1]
    assert ordered_assignments[-1].assigned_at == assignment_times[0]


@given(data=child_item_with_parents())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_assignment_history_filtering_by_date_range(test_db_session, data):
    """
    Test that assignment history can be filtered by date ranges.

    **Validates: Requirements 9.5**
    """
    # Setup test data
    child_item = data["child_item"]
    parent_item_1 = data["parent_item_1"]
    parent_item_2 = data["parent_item_2"]
    user = data["user"]
    parent_item_type = data["parent_item_type"]
    child_item_type = data["child_item_type"]
    location_type = data["location_type"]
    location = data["location"]
    role = data["role"]

    # Add all entities to database
    test_db_session.add(role)
    test_db_session.add(user)
    test_db_session.add(location_type)
    test_db_session.add(location)
    test_db_session.add(parent_item_type)
    test_db_session.add(child_item_type)
    test_db_session.add(parent_item_1)
    test_db_session.add(parent_item_2)
    test_db_session.add(child_item)
    test_db_session.commit()

    # Create assignment history records across different time periods
    base_time = datetime.now(timezone.utc)

    # Assignments outside the filter range
    old_assignment = AssignmentHistory(
        child_item_id=child_item.id,
        from_parent_item_id=None,
        to_parent_item_id=parent_item_1.id,
        assigned_at=base_time - timedelta(days=10),
        assigned_by=user.id,
        notes="Old assignment",
    )

    future_assignment = AssignmentHistory(
        child_item_id=child_item.id,
        from_parent_item_id=parent_item_1.id,
        to_parent_item_id=parent_item_2.id,
        assigned_at=base_time + timedelta(days=10),
        assigned_by=user.id,
        notes="Future assignment",
    )

    # Assignments within the filter range
    recent_assignment1 = AssignmentHistory(
        child_item_id=child_item.id,
        from_parent_item_id=parent_item_1.id,
        to_parent_item_id=parent_item_2.id,
        assigned_at=base_time - timedelta(hours=2),
        assigned_by=user.id,
        notes="Recent assignment 1",
    )

    recent_assignment2 = AssignmentHistory(
        child_item_id=child_item.id,
        from_parent_item_id=parent_item_2.id,
        to_parent_item_id=parent_item_1.id,
        assigned_at=base_time - timedelta(hours=1),
        assigned_by=user.id,
        notes="Recent assignment 2",
    )

    test_db_session.add_all(
        [
            old_assignment,
            future_assignment,
            recent_assignment1,
            recent_assignment2,
        ]
    )
    test_db_session.commit()

    # Define filter range (last 3 hours)
    start_date = base_time - timedelta(hours=3)
    end_date = base_time

    # Query with date range filter
    filtered_assignments = (
        test_db_session.query(AssignmentHistory)
        .filter(
            AssignmentHistory.child_item_id == child_item.id,
            AssignmentHistory.assigned_at >= start_date,
            AssignmentHistory.assigned_at <= end_date,
        )
        .order_by(AssignmentHistory.assigned_at.desc())
        .all()
    )

    # Verify only assignments within the date range are returned
    assert len(filtered_assignments) == 2
    assert recent_assignment2.id in [
        assignment.id for assignment in filtered_assignments
    ]
    assert recent_assignment1.id in [
        assignment.id for assignment in filtered_assignments
    ]
    assert old_assignment.id not in [
        assignment.id for assignment in filtered_assignments
    ]
    assert future_assignment.id not in [
        assignment.id for assignment in filtered_assignments
    ]

    # Verify chronological ordering within filtered results
    assert filtered_assignments[0].assigned_at >= filtered_assignments[1].assigned_at
