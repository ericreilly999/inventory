"""Property-based tests for movement audit trail functionality.

**Feature: inventory-management, Property 4: Movement Audit Trail**
**Validates: Requirements 2.3, 5.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from uuid import uuid4

from shared.models.item import ParentItem, ItemType, ItemCategory
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory
from shared.models.user import User, Role


@st.composite
def parent_item_with_location(draw):
    """Generate a parent item with a valid location."""
    # Generate item type
    item_type = ItemType(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        category=ItemCategory.PARENT
    )
    
    # Generate location type
    location_type = LocationType(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200))
    )
    
    # Generate locations
    from_location = Location(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        location_type_id=location_type.id,
        location_type=location_type
    )
    
    to_location = Location(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        location_type_id=location_type.id,
        location_type=location_type
    )
    
    # Generate user
    role = Role(
        id=uuid4(),
        name="inventory_manager",
        description="Inventory Manager Role",
        permissions={"inventory": ["read", "write"]}
    )
    
    user = User(
        id=uuid4(),
        username=draw(st.text(min_size=1, max_size=50)),
        email=draw(st.emails()),
        password_hash="hashed_password",
        active=True,
        role_id=role.id,
        role=role
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
        creator=user
    )
    
    return {
        'parent_item': parent_item,
        'from_location': from_location,
        'to_location': to_location,
        'user': user,
        'item_type': item_type,
        'location_type': location_type,
        'role': role
    }


@given(data=parent_item_with_location())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_movement_audit_trail_property(test_db_session, data):
    """
    Property 4: Movement Audit Trail
    
    For any parent item movement, a move history record should be created containing 
    source location, destination location, timestamp, and user information.
    
    **Validates: Requirements 2.3, 5.1**
    """
    # Setup test data
    parent_item = data['parent_item']
    from_location = data['from_location']
    to_location = data['to_location']
    user = data['user']
    item_type = data['item_type']
    location_type = data['location_type']
    role = data['role']
    
    # Add all entities to database
    test_db_session.add(role)
    test_db_session.add(user)
    test_db_session.add(location_type)
    test_db_session.add(from_location)
    test_db_session.add(to_location)
    test_db_session.add(item_type)
    test_db_session.add(parent_item)
    test_db_session.commit()
    
    # Record the time before movement
    before_move_time = datetime.now(timezone.utc)
    
    # Simulate item movement by creating move history record
    # (This simulates what the API would do when moving an item)
    original_location_id = parent_item.current_location_id
    parent_item.current_location_id = to_location.id
    
    move_history = MoveHistory(
        parent_item_id=parent_item.id,
        from_location_id=original_location_id,
        to_location_id=to_location.id,
        moved_at=datetime.now(timezone.utc),
        moved_by=user.id,
        notes="Test movement"
    )
    
    test_db_session.add(move_history)
    test_db_session.commit()
    test_db_session.refresh(move_history)
    
    # Record the time after movement
    after_move_time = datetime.now(timezone.utc)
    
    # Verify audit trail properties
    # 1. Move history record exists
    assert move_history.id is not None
    
    # 2. Contains correct source location
    assert move_history.from_location_id == from_location.id
    
    # 3. Contains correct destination location
    assert move_history.to_location_id == to_location.id
    
    # 4. Contains correct parent item reference
    assert move_history.parent_item_id == parent_item.id
    
    # 5. Contains user information
    assert move_history.moved_by == user.id
    
    # 6. Contains timestamp within reasonable bounds
    assert before_move_time <= move_history.moved_at <= after_move_time
    
    # 7. Parent item location is updated
    assert parent_item.current_location_id == to_location.id
    
    # 8. Move history can be queried by parent item
    history_records = test_db_session.query(MoveHistory).filter(
        MoveHistory.parent_item_id == parent_item.id
    ).all()
    assert len(history_records) == 1
    assert history_records[0].id == move_history.id
    
    # 9. Move history can be queried by location
    from_location_moves = test_db_session.query(MoveHistory).filter(
        MoveHistory.from_location_id == from_location.id
    ).all()
    assert len(from_location_moves) == 1
    
    to_location_moves = test_db_session.query(MoveHistory).filter(
        MoveHistory.to_location_id == to_location.id
    ).all()
    assert len(to_location_moves) == 1
    
    # 10. Move history can be queried by date range
    date_filtered_moves = test_db_session.query(MoveHistory).filter(
        MoveHistory.moved_at >= before_move_time,
        MoveHistory.moved_at <= after_move_time
    ).all()
    assert len(date_filtered_moves) == 1


@given(data=parent_item_with_location())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_chronological_move_history_ordering(test_db_session, data):
    """
    Test that move history is maintained in chronological order.
    
    **Validates: Requirements 5.2**
    """
    # Setup test data
    parent_item = data['parent_item']
    from_location = data['from_location']
    to_location = data['to_location']
    user = data['user']
    item_type = data['item_type']
    location_type = data['location_type']
    role = data['role']
    
    # Add all entities to database
    test_db_session.add(role)
    test_db_session.add(user)
    test_db_session.add(location_type)
    test_db_session.add(from_location)
    test_db_session.add(to_location)
    test_db_session.add(item_type)
    test_db_session.add(parent_item)
    test_db_session.commit()
    
    # Create multiple move history records with different timestamps
    move_times = [
        datetime.now(timezone.utc) - timedelta(hours=3),
        datetime.now(timezone.utc) - timedelta(hours=2),
        datetime.now(timezone.utc) - timedelta(hours=1),
        datetime.now(timezone.utc)
    ]
    
    move_records = []
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
            notes=f"Move {i+1}"
        )
        
        test_db_session.add(move_history)
        move_records.append(move_history)
    
    test_db_session.commit()
    
    # Query move history ordered by timestamp (most recent first)
    ordered_moves = test_db_session.query(MoveHistory).filter(
        MoveHistory.parent_item_id == parent_item.id
    ).order_by(MoveHistory.moved_at.desc()).all()
    
    # Verify chronological ordering (most recent first)
    assert len(ordered_moves) == 4
    for i in range(len(ordered_moves) - 1):
        assert ordered_moves[i].moved_at >= ordered_moves[i + 1].moved_at
    
    # Verify the most recent move is first
    assert ordered_moves[0].moved_at == move_times[-1]
    assert ordered_moves[-1].moved_at == move_times[0]


@given(data=parent_item_with_location())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_move_history_filtering_by_date_range(test_db_session, data):
    """
    Test that move history can be filtered by date ranges.
    
    **Validates: Requirements 5.2, 5.5**
    """
    # Setup test data
    parent_item = data['parent_item']
    from_location = data['from_location']
    to_location = data['to_location']
    user = data['user']
    item_type = data['item_type']
    location_type = data['location_type']
    role = data['role']
    
    # Add all entities to database
    test_db_session.add(role)
    test_db_session.add(user)
    test_db_session.add(location_type)
    test_db_session.add(from_location)
    test_db_session.add(to_location)
    test_db_session.add(item_type)
    test_db_session.add(parent_item)
    test_db_session.commit()
    
    # Create move history records across different time periods
    base_time = datetime.now(timezone.utc)
    
    # Moves outside the filter range
    old_move = MoveHistory(
        parent_item_id=parent_item.id,
        from_location_id=from_location.id,
        to_location_id=to_location.id,
        moved_at=base_time - timedelta(days=10),
        moved_by=user.id,
        notes="Old move"
    )
    
    future_move = MoveHistory(
        parent_item_id=parent_item.id,
        from_location_id=to_location.id,
        to_location_id=from_location.id,
        moved_at=base_time + timedelta(days=10),
        moved_by=user.id,
        notes="Future move"
    )
    
    # Moves within the filter range
    recent_move1 = MoveHistory(
        parent_item_id=parent_item.id,
        from_location_id=from_location.id,
        to_location_id=to_location.id,
        moved_at=base_time - timedelta(hours=2),
        moved_by=user.id,
        notes="Recent move 1"
    )
    
    recent_move2 = MoveHistory(
        parent_item_id=parent_item.id,
        from_location_id=to_location.id,
        to_location_id=from_location.id,
        moved_at=base_time - timedelta(hours=1),
        moved_by=user.id,
        notes="Recent move 2"
    )
    
    test_db_session.add_all([old_move, future_move, recent_move1, recent_move2])
    test_db_session.commit()
    
    # Define filter range (last 3 hours)
    start_date = base_time - timedelta(hours=3)
    end_date = base_time
    
    # Query with date range filter
    filtered_moves = test_db_session.query(MoveHistory).filter(
        MoveHistory.parent_item_id == parent_item.id,
        MoveHistory.moved_at >= start_date,
        MoveHistory.moved_at <= end_date
    ).order_by(MoveHistory.moved_at.desc()).all()
    
    # Verify only moves within the date range are returned
    assert len(filtered_moves) == 2
    assert recent_move2.id in [move.id for move in filtered_moves]
    assert recent_move1.id in [move.id for move in filtered_moves]
    assert old_move.id not in [move.id for move in filtered_moves]
    assert future_move.id not in [move.id for move in filtered_moves]
    
    # Verify chronological ordering within filtered results
    assert filtered_moves[0].moved_at >= filtered_moves[1].moved_at