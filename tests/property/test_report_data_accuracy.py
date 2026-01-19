"""Property tests for report data accuracy.

Feature: inventory-management, Property 6: Report Data Accuracy
Validates: Requirements 3.1, 3.3
"""

import uuid
from datetime import datetime, timezone
from hypothesis import given, strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.models import (
    Base, User, Role, Location, LocationType, 
    ParentItem, ChildItem, ItemType, ItemCategory
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
        permissions={}
    )
    session.add(role)
    
    # Create user
    user = User(
        id=uuid.uuid4(),
        username="test_user",
        email="test@example.com",
        password_hash="hashed_password",
        active=True,
        role_id=role.id
    )
    session.add(user)
    
    # Create location types
    warehouse_type = LocationType(
        id=uuid.uuid4(),
        name="warehouse",
        description="Warehouse location"
    )
    delivery_type = LocationType(
        id=uuid.uuid4(),
        name="delivery_site",
        description="Delivery site location"
    )
    session.add_all([warehouse_type, delivery_type])
    
    # Create parent item type
    parent_item_type = ItemType(
        id=uuid.uuid4(),
        name="parent_item_type",
        description="Parent item type",
        category=ItemCategory.PARENT
    )
    
    # Create child item type
    child_item_type = ItemType(
        id=uuid.uuid4(),
        name="child_item_type",
        description="Child item type",
        category=ItemCategory.CHILD
    )
    session.add_all([parent_item_type, child_item_type])
    
    session.commit()
    return user, warehouse_type, delivery_type, parent_item_type, child_item_type


@given(
    location_configs=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),  # location name
            st.sampled_from([0, 1]),  # location type index (warehouse or delivery)
            st.integers(min_value=0, max_value=5),  # parent items count
            st.integers(min_value=0, max_value=3)   # child items per parent
        ),
        min_size=1,
        max_size=4
    )
)
def test_report_data_accuracy_property(location_configs):
    """
    Property 6: Report Data Accuracy
    
    For any generated inventory report, the data should accurately reflect 
    current inventory status, location assignments, and item counts by type.
    
    **Validates: Requirements 3.1, 3.3**
    """
    setup_test_database()
    
    try:
        session = SessionLocal()
        
        # Create test data
        user, warehouse_type, delivery_type, parent_item_type, child_item_type = create_test_data(session)
        location_types = [warehouse_type, delivery_type]
        
        # Create locations and items based on the generated configuration
        locations = []
        expected_totals = {
            'total_locations': 0,
            'total_parent_items': 0,
            'total_child_items': 0,
            'by_location': {},
            'by_item_type': {
                'parent': {'parent_count': 0, 'child_count': 0},
                'child': {'parent_count': 0, 'child_count': 0}
            }
        }
        
        for loc_name, loc_type_idx, parent_count, child_per_parent in location_configs:
            # Create location
            location = Location(
                id=uuid.uuid4(),
                name=f"Location_{loc_name}",
                description=f"Test location {loc_name}",
                location_type_id=location_types[loc_type_idx].id
            )
            session.add(location)
            session.commit()
            locations.append(location)
            
            # Track expected counts
            expected_totals['total_locations'] += 1
            expected_totals['by_location'][location.id] = {
                'parent_items_count': parent_count,
                'child_items_count': parent_count * child_per_parent,
                'location_name': location.name,
                'location_type': location_types[loc_type_idx].name
            }
            
            # Create parent items at this location
            for i in range(parent_count):
                parent_item = ParentItem(
                    id=uuid.uuid4(),
                    name=f"Parent_{loc_name}_{i}",
                    description=f"Test parent item {i} at {loc_name}",
                    item_type_id=parent_item_type.id,
                    current_location_id=location.id,
                    created_by=user.id
                )
                session.add(parent_item)
                session.commit()
                
                expected_totals['total_parent_items'] += 1
                expected_totals['by_item_type']['parent']['parent_count'] += 1
                
                # Create child items for this parent
                for j in range(child_per_parent):
                    child_item = ChildItem(
                        id=uuid.uuid4(),
                        name=f"Child_{loc_name}_{i}_{j}",
                        description=f"Test child item {j} for parent {i}",
                        item_type_id=child_item_type.id,
                        parent_item_id=parent_item.id,
                        created_by=user.id
                    )
                    session.add(child_item)
                    
                    expected_totals['total_child_items'] += 1
                    expected_totals['by_item_type']['child']['child_count'] += 1
            
            session.commit()
        
        # Generate inventory status report data (simulating the report logic)
        # Requirement 3.1: Current inventory status by location
        actual_location_data = {}
        for location in locations:
            # Count parent items at this location
            parent_items_count = session.query(ParentItem).filter(
                ParentItem.current_location_id == location.id
            ).count()
            
            # Count child items (through their parent items)
            child_items_count = session.query(ChildItem).join(ParentItem).filter(
                ParentItem.current_location_id == location.id
            ).count()
            
            actual_location_data[location.id] = {
                'parent_items_count': parent_items_count,
                'child_items_count': child_items_count,
                'location_name': location.name,
                'location_type': location.location_type.name
            }
        
        # Verify inventory status report accuracy (Requirement 3.1)
        for location_id, expected_data in expected_totals['by_location'].items():
            actual_data = actual_location_data[location_id]
            
            # Verify parent items count matches
            assert actual_data['parent_items_count'] == expected_data['parent_items_count'], \
                f"Parent items count mismatch at location {expected_data['location_name']}: " \
                f"expected {expected_data['parent_items_count']}, got {actual_data['parent_items_count']}"
            
            # Verify child items count matches
            assert actual_data['child_items_count'] == expected_data['child_items_count'], \
                f"Child items count mismatch at location {expected_data['location_name']}: " \
                f"expected {expected_data['child_items_count']}, got {actual_data['child_items_count']}"
            
            # Verify location metadata matches
            assert actual_data['location_name'] == expected_data['location_name']
            assert actual_data['location_type'] == expected_data['location_type']
        
        # Generate inventory count report data (simulating the report logic)
        # Requirement 3.3: Inventory counts by item type
        actual_parent_type_count = session.query(ParentItem).filter(
            ParentItem.item_type_id == parent_item_type.id
        ).count()
        
        actual_child_type_count = session.query(ChildItem).filter(
            ChildItem.item_type_id == child_item_type.id
        ).count()
        
        # Verify inventory count report accuracy (Requirement 3.3)
        assert actual_parent_type_count == expected_totals['by_item_type']['parent']['parent_count'], \
            f"Parent item type count mismatch: " \
            f"expected {expected_totals['by_item_type']['parent']['parent_count']}, got {actual_parent_type_count}"
        
        assert actual_child_type_count == expected_totals['by_item_type']['child']['child_count'], \
            f"Child item type count mismatch: " \
            f"expected {expected_totals['by_item_type']['child']['child_count']}, got {actual_child_type_count}"
        
        # Verify total counts consistency
        total_actual_parents = sum(data['parent_items_count'] for data in actual_location_data.values())
        total_actual_children = sum(data['child_items_count'] for data in actual_location_data.values())
        
        assert total_actual_parents == expected_totals['total_parent_items'], \
            f"Total parent items mismatch: expected {expected_totals['total_parent_items']}, got {total_actual_parents}"
        
        assert total_actual_children == expected_totals['total_child_items'], \
            f"Total child items mismatch: expected {expected_totals['total_child_items']}, got {total_actual_children}"
        
        # Verify location count
        assert len(actual_location_data) == expected_totals['total_locations'], \
            f"Total locations mismatch: expected {expected_totals['total_locations']}, got {len(actual_location_data)}"
        
        session.close()
        
    finally:
        teardown_test_database()


if __name__ == "__main__":
    # Run a simple test to verify the property works
    test_report_data_accuracy_property([
        ("Warehouse1", 0, 2, 1),  # warehouse with 2 parents, 1 child each
        ("Delivery1", 1, 1, 2)    # delivery site with 1 parent, 2 children
    ])
    print("Property test passed!")