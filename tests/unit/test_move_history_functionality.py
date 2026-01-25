"""Unit tests for move history functionality.

Tests history recording, querying, and filtering capabilities.
**Validates: Requirements 5.1, 5.2, 5.5**
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from shared.models.assignment_history import AssignmentHistory
from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory
from shared.models.user import Role, User


class TestMoveHistoryRecording:
    """Test move history recording functionality."""

    def test_move_history_creation(self, test_db_session):
        """Test that move history records are created correctly."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"inventory": ["read", "write"]},
        )

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            active=True,
            role_id=role.id,
            role=role,
        )

        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        from_location = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        to_location = Location(
            id=uuid4(),
            name="Warehouse B",
            description="Secondary warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        parent_item = ParentItem(
            id=uuid4(),
            name="Test Item",
            description="Test item for move history",
            item_type_id=item_type.id,
            current_location_id=from_location.id,
            created_by=user.id,
            item_type=item_type,
            current_location=from_location,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [
                role,
                user,
                location_type,
                from_location,
                to_location,
                item_type,
                parent_item,
            ]
        )
        test_db_session.commit()

        # Create move history record
        move_time = datetime.now(timezone.utc)
        move_history = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=from_location.id,
            to_location_id=to_location.id,
            moved_at=move_time,
            moved_by=user.id,
            notes="Test move",
        )

        test_db_session.add(move_history)
        test_db_session.commit()
        test_db_session.refresh(move_history)

        # Verify move history record
        assert move_history.id is not None
        assert move_history.parent_item_id == parent_item.id
        assert move_history.from_location_id == from_location.id
        assert move_history.to_location_id == to_location.id
        assert move_history.moved_by == user.id
        assert move_history.notes == "Test move"
        # SQLite doesn't preserve timezone, so compare as timezone-aware
        if move_history.moved_at.tzinfo is None:
            assert move_history.moved_at.replace(tzinfo=timezone.utc) == move_time
        else:
            assert move_history.moved_at == move_time

    def test_initial_placement_move_history(self, test_db_session):
        """Test move history for initial item placement (no from_location)."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"inventory": ["read", "write"]},
        )

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            active=True,
            role_id=role.id,
            role=role,
        )

        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        location = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        parent_item = ParentItem(
            id=uuid4(),
            name="Test Item",
            description="Test item for initial placement",
            item_type_id=item_type.id,
            current_location_id=location.id,
            created_by=user.id,
            item_type=item_type,
            current_location=location,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [role, user, location_type, location, item_type, parent_item]
        )
        test_db_session.commit()

        # Create initial placement move history record
        move_history = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=None,  # Initial placement
            to_location_id=location.id,
            moved_at=datetime.now(timezone.utc),
            moved_by=user.id,
            notes="Initial placement",
        )

        test_db_session.add(move_history)
        test_db_session.commit()
        test_db_session.refresh(move_history)

        # Verify initial placement move history
        assert move_history.id is not None
        assert move_history.from_location_id is None
        assert move_history.to_location_id == location.id
        assert move_history.notes == "Initial placement"


class TestMoveHistoryQuerying:
    """Test move history querying functionality."""

    def test_query_by_parent_item(self, test_db_session):
        """Test querying move history by parent item."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"inventory": ["read", "write"]},
        )

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            active=True,
            role_id=role.id,
            role=role,
        )

        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        location1 = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        location2 = Location(
            id=uuid4(),
            name="Warehouse B",
            description="Secondary warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        parent_item1 = ParentItem(
            id=uuid4(),
            name="Test Item 1",
            description="First test item",
            item_type_id=item_type.id,
            current_location_id=location1.id,
            created_by=user.id,
            item_type=item_type,
            current_location=location1,
            creator=user,
        )

        parent_item2 = ParentItem(
            id=uuid4(),
            name="Test Item 2",
            description="Second test item",
            item_type_id=item_type.id,
            current_location_id=location1.id,
            created_by=user.id,
            item_type=item_type,
            current_location=location1,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [
                role,
                user,
                location_type,
                location1,
                location2,
                item_type,
                parent_item1,
                parent_item2,
            ]
        )
        test_db_session.commit()

        # Create move history records for both items
        move1 = MoveHistory(
            parent_item_id=parent_item1.id,
            from_location_id=location1.id,
            to_location_id=location2.id,
            moved_at=datetime.now(timezone.utc),
            moved_by=user.id,
            notes="Move item 1",
        )

        move2 = MoveHistory(
            parent_item_id=parent_item2.id,
            from_location_id=location1.id,
            to_location_id=location2.id,
            moved_at=datetime.now(timezone.utc),
            moved_by=user.id,
            notes="Move item 2",
        )

        test_db_session.add_all([move1, move2])
        test_db_session.commit()

        # Query move history for parent_item1
        item1_moves = (
            test_db_session.query(MoveHistory)
            .filter(MoveHistory.parent_item_id == parent_item1.id)
            .all()
        )

        # Verify only item1's moves are returned
        assert len(item1_moves) == 1
        assert item1_moves[0].parent_item_id == parent_item1.id
        assert item1_moves[0].notes == "Move item 1"

    def test_query_by_location(self, test_db_session):
        """Test querying move history by location (from or to)."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"inventory": ["read", "write"]},
        )

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            active=True,
            role_id=role.id,
            role=role,
        )

        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        location_a = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        location_b = Location(
            id=uuid4(),
            name="Warehouse B",
            description="Secondary warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        location_c = Location(
            id=uuid4(),
            name="Warehouse C",
            description="Third warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        parent_item = ParentItem(
            id=uuid4(),
            name="Test Item",
            description="Test item for location queries",
            item_type_id=item_type.id,
            current_location_id=location_a.id,
            created_by=user.id,
            item_type=item_type,
            current_location=location_a,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [
                role,
                user,
                location_type,
                location_a,
                location_b,
                location_c,
                item_type,
                parent_item,
            ]
        )
        test_db_session.commit()

        # Create move history records
        move1 = MoveHistory(  # A -> B
            parent_item_id=parent_item.id,
            from_location_id=location_a.id,
            to_location_id=location_b.id,
            moved_at=datetime.now(timezone.utc) - timedelta(hours=2),
            moved_by=user.id,
            notes="Move A to B",
        )

        move2 = MoveHistory(  # B -> C
            parent_item_id=parent_item.id,
            from_location_id=location_b.id,
            to_location_id=location_c.id,
            moved_at=datetime.now(timezone.utc) - timedelta(hours=1),
            moved_by=user.id,
            notes="Move B to C",
        )

        test_db_session.add_all([move1, move2])
        test_db_session.commit()

        # Query moves involving location_b (either from or to)
        location_b_moves = (
            test_db_session.query(MoveHistory)
            .filter(
                (MoveHistory.from_location_id == location_b.id)
                | (MoveHistory.to_location_id == location_b.id)
            )
            .all()
        )

        # Verify both moves involving location_b are returned
        assert len(location_b_moves) == 2
        move_notes = [move.notes for move in location_b_moves]
        assert "Move A to B" in move_notes
        assert "Move B to C" in move_notes


class TestMoveHistoryFiltering:
    """Test move history filtering functionality."""

    def test_chronological_ordering(self, test_db_session):
        """Test that move history is returned in chronological order."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"inventory": ["read", "write"]},
        )

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            active=True,
            role_id=role.id,
            role=role,
        )

        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        location1 = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        location2 = Location(
            id=uuid4(),
            name="Warehouse B",
            description="Secondary warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        parent_item = ParentItem(
            id=uuid4(),
            name="Test Item",
            description="Test item for chronological ordering",
            item_type_id=item_type.id,
            current_location_id=location1.id,
            created_by=user.id,
            item_type=item_type,
            current_location=location1,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [
                role,
                user,
                location_type,
                location1,
                location2,
                item_type,
                parent_item,
            ]
        )
        test_db_session.commit()

        # Create move history records with different timestamps
        base_time = datetime.now(timezone.utc)

        move1 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location1.id,
            to_location_id=location2.id,
            moved_at=base_time - timedelta(hours=3),
            moved_by=user.id,
            notes="Oldest move",
        )

        move2 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location2.id,
            to_location_id=location1.id,
            moved_at=base_time - timedelta(hours=1),
            moved_by=user.id,
            notes="Newest move",
        )

        move3 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location1.id,
            to_location_id=location2.id,
            moved_at=base_time - timedelta(hours=2),
            moved_by=user.id,
            notes="Middle move",
        )

        test_db_session.add_all([move1, move2, move3])
        test_db_session.commit()

        # Query moves ordered by timestamp (most recent first)
        ordered_moves = (
            test_db_session.query(MoveHistory)
            .filter(MoveHistory.parent_item_id == parent_item.id)
            .order_by(MoveHistory.moved_at.desc())
            .all()
        )

        # Verify chronological ordering
        assert len(ordered_moves) == 3
        assert ordered_moves[0].notes == "Newest move"
        assert ordered_moves[1].notes == "Middle move"
        assert ordered_moves[2].notes == "Oldest move"

        # Verify timestamps are in descending order
        for i in range(len(ordered_moves) - 1):
            assert ordered_moves[i].moved_at >= ordered_moves[i + 1].moved_at

    def test_date_range_filtering(self, test_db_session):
        """Test filtering move history by date range."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"inventory": ["read", "write"]},
        )

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            active=True,
            role_id=role.id,
            role=role,
        )

        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        location1 = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        location2 = Location(
            id=uuid4(),
            name="Warehouse B",
            description="Secondary warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        parent_item = ParentItem(
            id=uuid4(),
            name="Test Item",
            description="Test item for date filtering",
            item_type_id=item_type.id,
            current_location_id=location1.id,
            created_by=user.id,
            item_type=item_type,
            current_location=location1,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [
                role,
                user,
                location_type,
                location1,
                location2,
                item_type,
                parent_item,
            ]
        )
        test_db_session.commit()

        # Create move history records across different time periods
        base_time = datetime.now(timezone.utc)

        # Moves outside the filter range
        old_move = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location1.id,
            to_location_id=location2.id,
            moved_at=base_time - timedelta(days=10),
            moved_by=user.id,
            notes="Old move",
        )

        future_move = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location2.id,
            to_location_id=location1.id,
            moved_at=base_time + timedelta(days=10),
            moved_by=user.id,
            notes="Future move",
        )

        # Moves within the filter range
        recent_move1 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location1.id,
            to_location_id=location2.id,
            moved_at=base_time - timedelta(hours=2),
            moved_by=user.id,
            notes="Recent move 1",
        )

        recent_move2 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location2.id,
            to_location_id=location1.id,
            moved_at=base_time - timedelta(hours=1),
            moved_by=user.id,
            notes="Recent move 2",
        )

        test_db_session.add_all([old_move, future_move, recent_move1, recent_move2])
        test_db_session.commit()

        # Define filter range (last 3 hours)
        start_date = base_time - timedelta(hours=3)
        end_date = base_time

        # Query with date range filter
        filtered_moves = (
            test_db_session.query(MoveHistory)
            .filter(
                MoveHistory.parent_item_id == parent_item.id,
                MoveHistory.moved_at >= start_date,
                MoveHistory.moved_at <= end_date,
            )
            .order_by(MoveHistory.moved_at.desc())
            .all()
        )

        # Verify only moves within the date range are returned
        assert len(filtered_moves) == 2
        move_notes = [move.notes for move in filtered_moves]
        assert "Recent move 1" in move_notes
        assert "Recent move 2" in move_notes
        assert "Old move" not in move_notes
        assert "Future move" not in move_notes

        # Verify chronological ordering within filtered results
        assert filtered_moves[0].moved_at >= filtered_moves[1].moved_at


class TestAssignmentHistoryIntegration:
    """Test assignment history functionality integration."""

    def test_assignment_history_creation(self, test_db_session):
        """Test that assignment history records are created correctly."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"inventory": ["read", "write"]},
        )

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            active=True,
            role_id=role.id,
            role=role,
        )

        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        location = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        parent_item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        child_item_type = ItemType(
            id=uuid4(),
            name="Component",
            description="Component items",
            category=ItemCategory.CHILD,
        )

        parent_item1 = ParentItem(
            id=uuid4(),
            name="Parent Item 1",
            description="First parent item",
            item_type_id=parent_item_type.id,
            current_location_id=location.id,
            created_by=user.id,
            item_type=parent_item_type,
            current_location=location,
            creator=user,
        )

        parent_item2 = ParentItem(
            id=uuid4(),
            name="Parent Item 2",
            description="Second parent item",
            item_type_id=parent_item_type.id,
            current_location_id=location.id,
            created_by=user.id,
            item_type=parent_item_type,
            current_location=location,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [
                role,
                user,
                location_type,
                location,
                parent_item_type,
                child_item_type,
                parent_item1,
                parent_item2,
            ]
        )
        test_db_session.commit()

        # Create a child item for the assignment history
        child_item = ChildItem(
            id=uuid4(),
            name="Test Child Item",
            description="Child item for assignment test",
            item_type_id=child_item_type.id,
            parent_item_id=parent_item1.id,
            created_by=user.id,
            item_type=child_item_type,
            parent_item=parent_item1,
            creator=user,
        )
        test_db_session.add(child_item)
        test_db_session.commit()

        # Create assignment history record
        assignment_time = datetime.now(timezone.utc)
        assignment_history = AssignmentHistory(
            child_item_id=child_item.id,  # Use actual child item ID
            from_parent_item_id=parent_item1.id,
            to_parent_item_id=parent_item2.id,
            assigned_at=assignment_time,
            assigned_by=user.id,
            notes="Test reassignment",
        )

        test_db_session.add(assignment_history)
        test_db_session.commit()
        test_db_session.refresh(assignment_history)

        # Verify assignment history record
        assert assignment_history.id is not None
        assert assignment_history.child_item_id == child_item.id
        assert assignment_history.from_parent_item_id == parent_item1.id
        assert assignment_history.to_parent_item_id == parent_item2.id
        assert assignment_history.assigned_by == user.id
        assert assignment_history.notes == "Test reassignment"
        # Handle timezone-aware vs timezone-naive datetime comparison
        if assignment_history.assigned_at.tzinfo is None:
            assert (
                assignment_history.assigned_at.replace(tzinfo=timezone.utc)
                == assignment_time
            )
        else:
            assert assignment_history.assigned_at == assignment_time

    def test_assignment_history_querying(self, test_db_session):
        """Test querying assignment history by various criteria."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"inventory": ["read", "write"]},
        )

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            active=True,
            role_id=role.id,
            role=role,
        )

        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        location = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        parent_item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        child_item_type = ItemType(
            id=uuid4(),
            name="Component",
            description="Component items",
            category=ItemCategory.CHILD,
        )

        parent_item1 = ParentItem(
            id=uuid4(),
            name="Parent Item 1",
            description="First parent item",
            item_type_id=parent_item_type.id,
            current_location_id=location.id,
            created_by=user.id,
            item_type=parent_item_type,
            current_location=location,
            creator=user,
        )

        parent_item2 = ParentItem(
            id=uuid4(),
            name="Parent Item 2",
            description="Second parent item",
            item_type_id=parent_item_type.id,
            current_location_id=location.id,
            created_by=user.id,
            item_type=parent_item_type,
            current_location=location,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [
                role,
                user,
                location_type,
                location,
                parent_item_type,
                child_item_type,
                parent_item1,
                parent_item2,
            ]
        )
        test_db_session.commit()

        # Create a child item for the assignment history
        child_item = ChildItem(
            id=uuid4(),
            name="Test Child Item",
            description="Child item for assignment test",
            item_type_id=child_item_type.id,
            parent_item_id=parent_item1.id,
            created_by=user.id,
            item_type=child_item_type,
            parent_item=parent_item1,
            creator=user,
        )
        test_db_session.add(child_item)
        test_db_session.commit()

        # Create assignment history records
        assignment1 = AssignmentHistory(
            child_item_id=child_item.id,
            from_parent_item_id=None,  # Initial assignment
            to_parent_item_id=parent_item1.id,
            assigned_at=datetime.now(timezone.utc) - timedelta(hours=2),
            assigned_by=user.id,
            notes="Initial assignment",
        )

        assignment2 = AssignmentHistory(
            child_item_id=child_item.id,
            from_parent_item_id=parent_item1.id,
            to_parent_item_id=parent_item2.id,
            assigned_at=datetime.now(timezone.utc) - timedelta(hours=1),
            assigned_by=user.id,
            notes="Reassignment",
        )

        test_db_session.add_all([assignment1, assignment2])
        test_db_session.commit()

        # Query assignment history by child item
        child_assignments = (
            test_db_session.query(AssignmentHistory)
            .filter(AssignmentHistory.child_item_id == child_item.id)
            .order_by(AssignmentHistory.assigned_at.desc())
            .all()
        )

        # Verify assignment history
        assert len(child_assignments) == 2
        assert child_assignments[0].notes == "Reassignment"
        assert child_assignments[1].notes == "Initial assignment"

        # Query by parent item (to)
        parent2_assignments = (
            test_db_session.query(AssignmentHistory)
            .filter(AssignmentHistory.to_parent_item_id == parent_item2.id)
            .all()
        )

        assert len(parent2_assignments) == 1
        assert parent2_assignments[0].notes == "Reassignment"
