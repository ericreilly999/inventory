"""Property-based tests for movement audit trail functionality.

**Feature: inventory-management, Property 4: Movement Audit Trail**
**Validates: Requirements 2.3, 5.1**
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.models.base import Base
from shared.models.item import ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory
from shared.models.user import Role, User


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


@st.composite
def parent_item_with_location(draw):
    """Generate a parent item with a valid location."""
    # Generate item type
    item_type = ItemType(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        category=ItemCategory.PARENT,
    )

    # Generate location type
    location_type = LocationType(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
    )

    # Generate locations
    from_location = Location(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        location_type_id=location_type.id,
        location_type=location_type,
    )

    to_location = Location(
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

    # Generate parent item
    parent_item = ParentItem(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=100)),
        description=draw(st.text(min_size=0, max_size=200)),
        item_type_id=item_type.id,
        current_location_id=from_location.id,
        created_by=user.id,
        item_type=item_type,
        current_location=from_location,
        creator=user,
    )

    return {
        "parent_item": parent_item,
        "from_location": from_location,
        "to_location": to_location,
        "user": user,
        "item_type": item_type,
        "location_type": location_type,
        "role": role,
    }


@given(data=parent_item_with_location())
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_movement_audit_trail_property(data):
    """
    Property 4: Movement Audit Trail

    For any item movement between locations, the movement should be recorded
    in the audit trail with complete details.

    **Validates: Requirements 2.3, 5.1**
    """
    session, engine = get_test_session()

    try:
        # Setup test data
        parent_item = data["parent_item"]
        from_location = data["from_location"]
        to_location = data["to_location"]
        user = data["user"]
        item_type = data["item_type"]
        location_type = data["location_type"]
        role = data["role"]

        # Add all entities to database
        session.add(role)
        session.add(user)
        session.add(location_type)
        session.add(from_location)
        session.add(to_location)
        session.add(item_type)
        session.add(parent_item)
        session.commit()

        # Record the time before movement
        before_move_time = datetime.now(timezone.utc)

        # Simulate item movement by creating move history record
        original_location_id = parent_item.current_location_id
        parent_item.current_location_id = to_location.id

        move_history = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=original_location_id,
            to_location_id=to_location.id,
            moved_at=datetime.now(timezone.utc),
            moved_by=user.id,
            notes="Test movement",
        )

        session.add(move_history)
        session.commit()
        session.refresh(move_history)

        # Record the time after movement
        after_move_time = datetime.now(timezone.utc)

        # Verify move history properties
        assert move_history.id is not None
        assert move_history.parent_item_id == parent_item.id
        assert move_history.from_location_id == from_location.id
        assert move_history.to_location_id == to_location.id
        assert move_history.moved_by == user.id
        
        # Make moved_at timezone-aware if it's naive (SQLite returns naive datetimes)
        moved_at = move_history.moved_at
        if moved_at.tzinfo is None:
            moved_at = moved_at.replace(tzinfo=timezone.utc)
        
        assert before_move_time <= moved_at <= after_move_time
        assert parent_item.current_location_id == to_location.id

        # Query tests
        history_records = (
            session.query(MoveHistory)
            .filter(MoveHistory.parent_item_id == parent_item.id)
            .all()
        )
        assert len(history_records) == 1

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@given(data=parent_item_with_location())
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_chronological_move_history_ordering(data):
    """
    Test that move history is maintained in chronological order.

    **Validates: Requirements 5.1**
    """
    session, engine = get_test_session()

    try:
        # Setup test data
        parent_item = data["parent_item"]
        from_location = data["from_location"]
        to_location = data["to_location"]
        user = data["user"]
        item_type = data["item_type"]
        location_type = data["location_type"]
        role = data["role"]

        # Add all entities to database
        session.add(role)
        session.add(user)
        session.add(location_type)
        session.add(from_location)
        session.add(to_location)
        session.add(item_type)
        session.add(parent_item)
        session.commit()

        # Create multiple move history records with different timestamps
        move_times = [
            datetime.now(timezone.utc) - timedelta(hours=3),
            datetime.now(timezone.utc) - timedelta(hours=2),
            datetime.now(timezone.utc) - timedelta(hours=1),
            datetime.now(timezone.utc),
        ]

        for i, move_time in enumerate(move_times):
            # Alternate between locations
            current_from = from_location if i % 2 == 0 else to_location
            current_to = to_location if i % 2 == 0 else from_location

            move_history = MoveHistory(
                parent_item_id=parent_item.id,
                from_location_id=current_from.id,
                to_location_id=current_to.id,
                moved_at=move_time,
                moved_by=user.id,
                notes=f"Movement {i + 1}",
            )

            session.add(move_history)

        session.commit()

        # Query move history ordered by timestamp (most recent first)
        ordered_moves = (
            session.query(MoveHistory)
            .filter(MoveHistory.parent_item_id == parent_item.id)
            .order_by(MoveHistory.moved_at.desc())
            .all()
        )

        # Verify chronological ordering (most recent first)
        assert len(ordered_moves) == 4
        for i in range(len(ordered_moves) - 1):
            # Make moved_at timezone-aware if it's naive (SQLite returns naive datetimes)
            current_at = ordered_moves[i].moved_at
            next_at = ordered_moves[i + 1].moved_at
            if current_at.tzinfo is None:
                current_at = current_at.replace(tzinfo=timezone.utc)
            if next_at.tzinfo is None:
                next_at = next_at.replace(tzinfo=timezone.utc)
            
            assert current_at >= next_at

        # Verify the most recent movement is first
        first_at = ordered_moves[0].moved_at
        last_at = ordered_moves[-1].moved_at
        if first_at.tzinfo is None:
            first_at = first_at.replace(tzinfo=timezone.utc)
        if last_at.tzinfo is None:
            last_at = last_at.replace(tzinfo=timezone.utc)
        
        assert first_at == move_times[-1]
        assert last_at == move_times[0]

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@given(data=parent_item_with_location())
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_move_history_filtering_by_date_range(data):
    """
    Test that move history can be filtered by date ranges.

    **Validates: Requirements 5.1**
    """
    session, engine = get_test_session()

    try:
        # Setup test data
        parent_item = data["parent_item"]
        from_location = data["from_location"]
        to_location = data["to_location"]
        user = data["user"]
        item_type = data["item_type"]
        location_type = data["location_type"]
        role = data["role"]

        # Add all entities to database
        session.add(role)
        session.add(user)
        session.add(location_type)
        session.add(from_location)
        session.add(to_location)
        session.add(item_type)
        session.add(parent_item)
        session.commit()

        # Create move history records across different time periods
        base_time = datetime.now(timezone.utc)

        # Movements outside the filter range
        old_move = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=from_location.id,
            to_location_id=to_location.id,
            moved_at=base_time - timedelta(days=10),
            moved_by=user.id,
            notes="Old movement",
        )

        future_move = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=to_location.id,
            to_location_id=from_location.id,
            moved_at=base_time + timedelta(days=10),
            moved_by=user.id,
            notes="Future movement",
        )

        # Movements within the filter range
        recent_move1 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=from_location.id,
            to_location_id=to_location.id,
            moved_at=base_time - timedelta(hours=2),
            moved_by=user.id,
            notes="Recent movement 1",
        )

        recent_move2 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=to_location.id,
            to_location_id=from_location.id,
            moved_at=base_time - timedelta(hours=1),
            moved_by=user.id,
            notes="Recent movement 2",
        )

        session.add_all([old_move, future_move, recent_move1, recent_move2])
        session.commit()

        # Define filter range (last 3 hours)
        start_date = base_time - timedelta(hours=3)
        end_date = base_time

        # Query with date range filter
        filtered_moves = (
            session.query(MoveHistory)
            .filter(
                MoveHistory.parent_item_id == parent_item.id,
                MoveHistory.moved_at >= start_date,
                MoveHistory.moved_at <= end_date,
            )
            .order_by(MoveHistory.moved_at.desc())
            .all()
        )

        # Verify only movements within the date range are returned
        assert len(filtered_moves) == 2
        move_ids = [m.id for m in filtered_moves]
        assert recent_move2.id in move_ids
        assert recent_move1.id in move_ids
        assert old_move.id not in move_ids
        assert future_move.id not in move_ids

        # Verify chronological ordering within filtered results
        first_at = filtered_moves[0].moved_at
        second_at = filtered_moves[1].moved_at
        if first_at.tzinfo is None:
            first_at = first_at.replace(tzinfo=timezone.utc)
        if second_at.tzinfo is None:
            second_at = second_at.replace(tzinfo=timezone.utc)
        
        assert first_at >= second_at

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
