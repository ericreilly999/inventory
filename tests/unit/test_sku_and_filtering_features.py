"""Tests for SKU field and item type filtering features."""

from uuid import uuid4

from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType


class TestSKUFieldRename:
    """Test that SKU field works correctly for parent and child items."""

    def test_parent_item_sku_field(self, test_db_session):
        """Test parent item uses sku field instead of name."""
        # Create dependencies
        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Warehouse type"
        )
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            id=uuid4(),
            name="Main Warehouse",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        item_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment type",
            category=ItemCategory.PARENT,
        )
        test_db_session.add(item_type)
        test_db_session.flush()

        # Create parent item with SKU
        parent_item = ParentItem(
            id=uuid4(),
            sku="PARENT-001",
            description="Test parent item",
            item_type_id=item_type.id,
            current_location_id=location.id,
        )
        test_db_session.add(parent_item)
        test_db_session.commit()

        # Verify SKU field
        assert parent_item.sku == "PARENT-001"
        assert hasattr(parent_item, "sku")
        assert not hasattr(parent_item, "name")

    def test_child_item_sku_field(self, test_db_session):
        """Test child item uses sku field instead of name."""
        # Create dependencies
        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Warehouse type"
        )
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            id=uuid4(),
            name="Main Warehouse",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        parent_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment type",
            category=ItemCategory.PARENT,
        )
        child_type = ItemType(
            id=uuid4(),
            name="Component",
            description="Component type",
            category=ItemCategory.CHILD,
        )
        test_db_session.add_all([parent_type, child_type])
        test_db_session.flush()

        parent_item = ParentItem(
            id=uuid4(),
            sku="PARENT-001",
            description="Test parent item",
            item_type_id=parent_type.id,
            current_location_id=location.id,
        )
        test_db_session.add(parent_item)
        test_db_session.flush()

        # Create child item with SKU
        child_item = ChildItem(
            id=uuid4(),
            sku="CHILD-001",
            description="Test child item",
            item_type_id=child_type.id,
            parent_item_id=parent_item.id,
        )
        test_db_session.add(child_item)
        test_db_session.commit()

        # Verify SKU field
        assert child_item.sku == "CHILD-001"
        assert hasattr(child_item, "sku")
        assert not hasattr(child_item, "name")


class TestItemTypeFiltering:
    """Test item type filtering by category."""

    def test_filter_parent_item_types(self, test_db_session):
        """Test filtering item types to show only parent types."""
        # Create parent and child item types
        parent_type1 = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment type",
            category=ItemCategory.PARENT,
        )
        parent_type2 = ItemType(
            id=uuid4(),
            name="Furniture",
            description="Furniture type",
            category=ItemCategory.PARENT,
        )
        child_type1 = ItemType(
            id=uuid4(),
            name="Component",
            description="Component type",
            category=ItemCategory.CHILD,
        )
        child_type2 = ItemType(
            id=uuid4(),
            name="Accessory",
            description="Accessory type",
            category=ItemCategory.CHILD,
        )
        test_db_session.add_all([parent_type1, parent_type2, child_type1, child_type2])
        test_db_session.commit()

        # Query for parent types only
        parent_types = (
            test_db_session.query(ItemType)
            .filter(ItemType.category == ItemCategory.PARENT)
            .all()
        )

        assert len(parent_types) == 2
        assert all(t.category == ItemCategory.PARENT for t in parent_types)
        assert {t.name for t in parent_types} == {"Equipment", "Furniture"}

    def test_filter_child_item_types(self, test_db_session):
        """Test filtering item types to show only child types."""
        # Create parent and child item types
        parent_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment type",
            category=ItemCategory.PARENT,
        )
        child_type1 = ItemType(
            id=uuid4(),
            name="Component",
            description="Component type",
            category=ItemCategory.CHILD,
        )
        child_type2 = ItemType(
            id=uuid4(),
            name="Accessory",
            description="Accessory type",
            category=ItemCategory.CHILD,
        )
        test_db_session.add_all([parent_type, child_type1, child_type2])
        test_db_session.commit()

        # Query for child types only
        child_types = (
            test_db_session.query(ItemType)
            .filter(ItemType.category == ItemCategory.CHILD)
            .all()
        )

        assert len(child_types) == 2
        assert all(t.category == ItemCategory.CHILD for t in child_types)
        assert {t.name for t in child_types} == {"Component", "Accessory"}


class TestReportSplitting:
    """Test that reports are split by parent and child item types."""

    def test_parent_item_type_counts(self, test_db_session):
        """Test counting parent items by type."""
        # Create location dependencies
        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Warehouse type"
        )
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            id=uuid4(),
            name="Main Warehouse",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        # Create parent item types
        equipment_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment type",
            category=ItemCategory.PARENT,
        )
        furniture_type = ItemType(
            id=uuid4(),
            name="Furniture",
            description="Furniture type",
            category=ItemCategory.PARENT,
        )
        test_db_session.add_all([equipment_type, furniture_type])
        test_db_session.flush()

        # Create parent items
        for i in range(3):
            parent_item = ParentItem(
                id=uuid4(),
                sku=f"EQUIP-{i:03d}",
                description=f"Equipment {i}",
                item_type_id=equipment_type.id,
                current_location_id=location.id,
            )
            test_db_session.add(parent_item)

        for i in range(2):
            parent_item = ParentItem(
                id=uuid4(),
                sku=f"FURN-{i:03d}",
                description=f"Furniture {i}",
                item_type_id=furniture_type.id,
                current_location_id=location.id,
            )
            test_db_session.add(parent_item)

        test_db_session.commit()

        # Count parent items by type
        from sqlalchemy import func

        counts = (
            test_db_session.query(
                ItemType.name, func.count(ParentItem.id).label("count")
            )
            .join(ParentItem, ParentItem.item_type_id == ItemType.id)
            .filter(ItemType.category == ItemCategory.PARENT)
            .group_by(ItemType.name)
            .all()
        )

        count_dict = {name: count for name, count in counts}
        assert count_dict["Equipment"] == 3
        assert count_dict["Furniture"] == 2

    def test_child_item_type_counts(self, test_db_session):
        """Test counting child items by type."""
        # Create location dependencies
        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Warehouse type"
        )
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            id=uuid4(),
            name="Main Warehouse",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        # Create item types
        parent_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment type",
            category=ItemCategory.PARENT,
        )
        component_type = ItemType(
            id=uuid4(),
            name="Component",
            description="Component type",
            category=ItemCategory.CHILD,
        )
        accessory_type = ItemType(
            id=uuid4(),
            name="Accessory",
            description="Accessory type",
            category=ItemCategory.CHILD,
        )
        test_db_session.add_all([parent_type, component_type, accessory_type])
        test_db_session.flush()

        # Create parent item
        parent_item = ParentItem(
            id=uuid4(),
            sku="PARENT-001",
            description="Test parent",
            item_type_id=parent_type.id,
            current_location_id=location.id,
        )
        test_db_session.add(parent_item)
        test_db_session.flush()

        # Create child items
        for i in range(4):
            child_item = ChildItem(
                id=uuid4(),
                sku=f"COMP-{i:03d}",
                description=f"Component {i}",
                item_type_id=component_type.id,
                parent_item_id=parent_item.id,
            )
            test_db_session.add(child_item)

        for i in range(2):
            child_item = ChildItem(
                id=uuid4(),
                sku=f"ACC-{i:03d}",
                description=f"Accessory {i}",
                item_type_id=accessory_type.id,
                parent_item_id=parent_item.id,
            )
            test_db_session.add(child_item)

        test_db_session.commit()

        # Count child items by type
        from sqlalchemy import func

        counts = (
            test_db_session.query(
                ItemType.name, func.count(ChildItem.id).label("count")
            )
            .join(ChildItem, ChildItem.item_type_id == ItemType.id)
            .filter(ItemType.category == ItemCategory.CHILD)
            .group_by(ItemType.name)
            .all()
        )

        count_dict = {name: count for name, count in counts}
        assert count_dict["Component"] == 4
        assert count_dict["Accessory"] == 2

    def test_separate_parent_and_child_counts(self, test_db_session):
        """Test that parent and child counts are separate."""
        # Create location dependencies
        location_type = LocationType(
            id=uuid4(), name="Warehouse", description="Warehouse type"
        )
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            id=uuid4(),
            name="Main Warehouse",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        # Create item types
        parent_type = ItemType(
            id=uuid4(),
            name="Equipment",
            description="Equipment type",
            category=ItemCategory.PARENT,
        )
        child_type = ItemType(
            id=uuid4(),
            name="Component",
            description="Component type",
            category=ItemCategory.CHILD,
        )
        test_db_session.add_all([parent_type, child_type])
        test_db_session.flush()

        # Create parent items
        parent_item = ParentItem(
            id=uuid4(),
            sku="PARENT-001",
            description="Test parent",
            item_type_id=parent_type.id,
            current_location_id=location.id,
        )
        test_db_session.add(parent_item)
        test_db_session.flush()

        # Create child items
        for i in range(3):
            child_item = ChildItem(
                id=uuid4(),
                sku=f"CHILD-{i:03d}",
                description=f"Child {i}",
                item_type_id=child_type.id,
                parent_item_id=parent_item.id,
            )
            test_db_session.add(child_item)

        test_db_session.commit()

        # Verify separate counts
        from sqlalchemy import func

        parent_count = (
            test_db_session.query(func.count(ParentItem.id))
            .join(ItemType, ParentItem.item_type_id == ItemType.id)
            .filter(ItemType.category == ItemCategory.PARENT)
            .scalar()
        )

        child_count = (
            test_db_session.query(func.count(ChildItem.id))
            .join(ItemType, ChildItem.item_type_id == ItemType.id)
            .filter(ItemType.category == ItemCategory.CHILD)
            .scalar()
        )

        assert parent_count == 1
        assert child_count == 3
