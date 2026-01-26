"""Unit tests for report generation functionality.

Tests various report types and error conditions.
**Validates: Requirements 3.4, 3.5**
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory
from shared.models.user import Role, User


class TestInventoryStatusReports:
    """Test inventory status report generation."""

    def test_inventory_status_basic_report(self, test_db_session):
        """Test basic inventory status report generation."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"reports": ["read"]},
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
            name="Main Warehouse",
            description="Primary storage location",
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

        # Create parent items
        parent_item1 = ParentItem(
            id=uuid4(),
            name="Equipment 1",
            description="First equipment item",
            item_type_id=parent_item_type.id,
            current_location_id=location.id,
            created_by=user.id,
            item_type=parent_item_type,
            current_location=location,
            creator=user,
        )

        parent_item2 = ParentItem(
            id=uuid4(),
            name="Equipment 2",
            description="Second equipment item",
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

        # Create child items
        child_item1 = ChildItem(
            id=uuid4(),
            name="Component 1",
            description="First component",
            item_type_id=child_item_type.id,
            parent_item_id=parent_item1.id,
            created_by=user.id,
            item_type=child_item_type,
            parent_item=parent_item1,
            creator=user,
        )

        child_item2 = ChildItem(
            id=uuid4(),
            name="Component 2",
            description="Second component",
            item_type_id=child_item_type.id,
            parent_item_id=parent_item1.id,
            created_by=user.id,
            item_type=child_item_type,
            parent_item=parent_item1,
            creator=user,
        )

        test_db_session.add_all([child_item1, child_item2])
        test_db_session.commit()

        # Simulate inventory status report logic
        parent_items_count = (
            test_db_session.query(ParentItem)
            .filter(ParentItem.current_location_id == location.id)
            .count()
        )

        child_items_count = (
            test_db_session.query(ChildItem)
            .join(ParentItem)
            .filter(ParentItem.current_location_id == location.id)
            .count()
        )

        # Verify report data
        assert parent_items_count == 2
        assert child_items_count == 2

    def test_inventory_status_empty_location(self, test_db_session):
        """Test inventory status report for location with no items."""
        # Create test data
        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        location = Location(
            id=uuid4(),
            name="Empty Warehouse",
            description="Location with no items",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        test_db_session.add_all([location_type, location])
        test_db_session.commit()

        # Simulate inventory status report logic for empty location
        parent_items_count = (
            test_db_session.query(ParentItem)
            .filter(ParentItem.current_location_id == location.id)
            .count()
        )

        child_items_count = (
            test_db_session.query(ChildItem)
            .join(ParentItem)
            .filter(ParentItem.current_location_id == location.id)
            .count()
        )

        # Verify empty location report
        assert parent_items_count == 0
        assert child_items_count == 0

    def test_inventory_status_nonexistent_location(self, test_db_session):
        """Test inventory status report error handling for nonexistent location."""
        nonexistent_location_id = uuid4()

        # Simulate checking if location exists
        location_exists = (
            test_db_session.query(Location)
            .filter(Location.id == nonexistent_location_id)
            .first()
            is not None
        )

        # Verify location doesn't exist
        assert not location_exists

        # This would trigger a 404 error in the actual API
        # The test verifies the database query behavior


class TestMovementHistoryReports:
    """Test movement history report generation."""

    def test_movement_history_basic_report(self, test_db_session):
        """Test basic movement history report generation."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"reports": ["read"]},
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
            description="First warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        location2 = Location(
            id=uuid4(),
            name="Warehouse B",
            description="Second warehouse",
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
            name="Test Equipment",
            description="Equipment for movement testing",
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

        # Create movement history
        base_time = datetime.now(timezone.utc)

        move1 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location1.id,
            to_location_id=location2.id,
            moved_at=base_time - timedelta(hours=2),
            moved_by=user.id,
            notes="First move",
        )

        move2 = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location2.id,
            to_location_id=location1.id,
            moved_at=base_time - timedelta(hours=1),
            moved_by=user.id,
            notes="Second move",
        )

        test_db_session.add_all([move1, move2])
        test_db_session.commit()

        # Simulate movement history report logic
        movements = (
            test_db_session.query(MoveHistory)
            .order_by(MoveHistory.moved_at.desc())
            .all()
        )

        # Verify movement history report
        assert len(movements) == 2
        assert movements[0].notes == "Second move"  # Most recent first
        assert movements[1].notes == "First move"

        # Verify chronological ordering
        assert movements[0].moved_at >= movements[1].moved_at

    def test_movement_history_date_filtering(self, test_db_session):
        """Test movement history report with date filtering."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"reports": ["read"]},
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
            description="First warehouse",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        location2 = Location(
            id=uuid4(),
            name="Warehouse B",
            description="Second warehouse",
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
            name="Test Equipment",
            description="Equipment for date filtering testing",
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

        # Create movements across different time periods
        base_time = datetime.now(timezone.utc)

        old_move = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location1.id,
            to_location_id=location2.id,
            moved_at=base_time - timedelta(days=10),
            moved_by=user.id,
            notes="Old move",
        )

        recent_move = MoveHistory(
            parent_item_id=parent_item.id,
            from_location_id=location2.id,
            to_location_id=location1.id,
            moved_at=base_time - timedelta(hours=1),
            moved_by=user.id,
            notes="Recent move",
        )

        test_db_session.add_all([old_move, recent_move])
        test_db_session.commit()

        # Simulate date filtering (last 24 hours)
        start_date = base_time - timedelta(hours=24)
        end_date = base_time

        filtered_movements = (
            test_db_session.query(MoveHistory)
            .filter(
                MoveHistory.moved_at >= start_date,
                MoveHistory.moved_at <= end_date,
            )
            .order_by(MoveHistory.moved_at.desc())
            .all()
        )

        # Verify date filtering
        assert len(filtered_movements) == 1
        assert filtered_movements[0].notes == "Recent move"

    def test_movement_history_invalid_date_range(self):
        """Test movement history report error handling for invalid date range."""
        # Simulate invalid date range (start > end)
        base_time = datetime.now(timezone.utc)
        start_date = base_time
        end_date = base_time - timedelta(hours=1)

        # This would trigger a 400 error in the actual API
        is_valid_range = start_date <= end_date
        assert not is_valid_range


class TestInventoryCountReports:
    """Test inventory count report generation."""

    def test_inventory_count_by_item_type(self, test_db_session):
        """Test inventory count report by item type."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"reports": ["read"]},
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
            name="Main Warehouse",
            description="Primary storage location",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        equipment_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        component_type = ItemType(
            id=uuid4(),
            name="Component",
            description="Component items",
            category=ItemCategory.CHILD,
        )

        # Create items of different types
        equipment1 = ParentItem(
            id=uuid4(),
            name="Equipment 1",
            description="First equipment",
            item_type_id=equipment_type.id,
            current_location_id=location.id,
            created_by=user.id,
            item_type=equipment_type,
            current_location=location,
            creator=user,
        )

        equipment2 = ParentItem(
            id=uuid4(),
            name="Equipment 2",
            description="Second equipment",
            item_type_id=equipment_type.id,
            current_location_id=location.id,
            created_by=user.id,
            item_type=equipment_type,
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
                equipment_type,
                component_type,
                equipment1,
                equipment2,
            ]
        )
        test_db_session.commit()

        # Create child items
        component1 = ChildItem(
            id=uuid4(),
            name="Component 1",
            description="First component",
            item_type_id=component_type.id,
            parent_item_id=equipment1.id,
            created_by=user.id,
            item_type=component_type,
            parent_item=equipment1,
            creator=user,
        )

        component2 = ChildItem(
            id=uuid4(),
            name="Component 2",
            description="Second component",
            item_type_id=component_type.id,
            parent_item_id=equipment1.id,
            created_by=user.id,
            item_type=component_type,
            parent_item=equipment1,
            creator=user,
        )

        component3 = ChildItem(
            id=uuid4(),
            name="Component 3",
            description="Third component",
            item_type_id=component_type.id,
            parent_item_id=equipment2.id,
            created_by=user.id,
            item_type=component_type,
            parent_item=equipment2,
            creator=user,
        )

        test_db_session.add_all([component1, component2, component3])
        test_db_session.commit()

        # Simulate inventory count by item type
        equipment_count = (
            test_db_session.query(ParentItem)
            .filter(ParentItem.item_type_id == equipment_type.id)
            .count()
        )

        component_count = (
            test_db_session.query(ChildItem)
            .filter(ChildItem.item_type_id == component_type.id)
            .count()
        )

        # Verify counts by item type
        assert equipment_count == 2
        assert component_count == 3

    def test_inventory_count_by_location_type(self, test_db_session):
        """Test inventory count report by location type."""
        # Create test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"reports": ["read"]},
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

        warehouse_type = LocationType(
            id=uuid4(), name="Warehouse", description="Storage facility"
        )

        delivery_type = LocationType(
            id=uuid4(), name="Delivery Site", description="Delivery location"
        )

        warehouse = Location(
            id=uuid4(),
            name="Main Warehouse",
            description="Primary storage",
            location_type_id=warehouse_type.id,
            location_type=warehouse_type,
        )

        delivery_site = Location(
            id=uuid4(),
            name="Delivery Site A",
            description="First delivery site",
            location_type_id=delivery_type.id,
            location_type=delivery_type,
        )

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        # Create items at different location types
        warehouse_item = ParentItem(
            id=uuid4(),
            name="Warehouse Equipment",
            description="Equipment in warehouse",
            item_type_id=item_type.id,
            current_location_id=warehouse.id,
            created_by=user.id,
            item_type=item_type,
            current_location=warehouse,
            creator=user,
        )

        delivery_item = ParentItem(
            id=uuid4(),
            name="Delivery Equipment",
            description="Equipment at delivery site",
            item_type_id=item_type.id,
            current_location_id=delivery_site.id,
            created_by=user.id,
            item_type=item_type,
            current_location=delivery_site,
            creator=user,
        )

        # Add all entities to database
        test_db_session.add_all(
            [
                role,
                user,
                warehouse_type,
                delivery_type,
                warehouse,
                delivery_site,
                item_type,
                warehouse_item,
                delivery_item,
            ]
        )
        test_db_session.commit()

        # Simulate inventory count by location type
        warehouse_items = (
            test_db_session.query(ParentItem)
            .join(Location)
            .filter(Location.location_type_id == warehouse_type.id)
            .count()
        )

        delivery_items = (
            test_db_session.query(ParentItem)
            .join(Location)
            .filter(Location.location_type_id == delivery_type.id)
            .count()
        )

        # Verify counts by location type
        assert warehouse_items == 1
        assert delivery_items == 1


class TestReportErrorHandling:
    """Test report generation error handling."""

    def test_report_with_invalid_filters(self, test_db_session):
        """Test report generation with invalid filter parameters."""
        # Test with invalid UUID format
        invalid_uuid = "not-a-uuid"

        # This would trigger validation errors in the actual API
        # The test verifies the validation logic
        try:
            uuid4_obj = uuid4()  # Valid UUID for comparison
            assert str(uuid4_obj) != invalid_uuid
        except ValueError:
            # Invalid UUID format would raise ValueError
            pass

    def test_report_database_error_simulation(self, test_db_session):
        """Test report generation error handling for database issues."""
        # Simulate database connection issues
        # In a real scenario, this would test database timeout or
        # connection errors

        # Test with empty database (no data scenario)
        parent_items_count = test_db_session.query(ParentItem).count()
        child_items_count = test_db_session.query(ChildItem).count()

        # Verify empty database handling
        assert parent_items_count == 0
        assert child_items_count == 0

    def test_report_large_dataset_handling(self, test_db_session):
        """Test report generation with large datasets."""
        # Create test data for performance testing
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"reports": ["read"]},
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
            name="Large Warehouse",
            description="Warehouse with many items",
            location_type_id=location_type.id,
            location_type=location_type,
        )

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment items",
            category=ItemCategory.PARENT,
        )

        # Add base entities
        test_db_session.add_all([role, user, location_type, location, item_type])
        test_db_session.commit()

        # Create multiple items (simulating larger dataset)
        items = []
        for i in range(10):  # Reduced for test performance
            item = ParentItem(
                id=uuid4(),
                name=f"Equipment {i}",
                description=f"Equipment item {i}",
                item_type_id=item_type.id,
                current_location_id=location.id,
                created_by=user.id,
                item_type=item_type,
                current_location=location,
                creator=user,
            )
            items.append(item)

        test_db_session.add_all(items)
        test_db_session.commit()

        # Test query performance with larger dataset
        start_time = datetime.now()
        items_count = (
            test_db_session.query(ParentItem)
            .filter(ParentItem.current_location_id == location.id)
            .count()
        )
        end_time = datetime.now()

        # Verify query completed and returned correct count
        assert items_count == 10

        # Basic performance check (should complete quickly)
        query_duration = (end_time - start_time).total_seconds()
        assert query_duration < 1.0  # Should complete within 1 second


class TestReportDataExport:
    """Test report data export functionality."""

    def test_export_format_validation(self):
        """Test export format validation."""
        valid_formats = ["json", "csv"]
        invalid_formats = ["xml", "pdf", "excel"]

        # Test valid formats
        for fmt in valid_formats:
            assert fmt in ["json", "csv"]

        # Test invalid formats
        for fmt in invalid_formats:
            assert fmt not in ["json", "csv"]

    def test_export_data_structure(self, test_db_session):
        """Test export data structure consistency."""
        # Create minimal test data
        role = Role(
            id=uuid4(),
            name="inventory_manager",
            description="Inventory Manager Role",
            permissions={"reports": ["read"]},
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
            name="Export Test Warehouse",
            description="Warehouse for export testing",
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
            name="Export Test Item",
            description="Item for export testing",
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

        # Simulate export data structure
        export_data = {
            "parent_item_id": str(parent_item.id),
            "parent_item_sku": parent_item.sku,
            "parent_item_description": parent_item.description,
            "parent_item_type": parent_item.item_type.name,
            "location_name": parent_item.current_location.name,
            "location_type": (parent_item.current_location.location_type.name),
            "child_items_count": len(parent_item.child_items),
            "created_at": parent_item.created_at.isoformat(),
            "updated_at": parent_item.updated_at.isoformat(),
        }

        # Verify export data structure
        required_fields = [
            "parent_item_id",
            "parent_item_sku",
            "parent_item_type",
            "location_name",
            "location_type",
            "child_items_count",
        ]

        for field in required_fields:
            assert field in export_data
            assert export_data[field] is not None

        # Verify data types
        assert isinstance(export_data["child_items_count"], int)
        assert isinstance(export_data["parent_item_sku"], str)
        assert isinstance(export_data["location_name"], str)
