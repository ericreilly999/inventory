"""Property tests for child item assignment uniqueness.

Feature: inventory-management, Property 10: Child Item Assignment Uniqueness
Validates: Requirements 9.2
"""

import uuid
from datetime import datetime
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
    
    # Create location type
    location_type = LocationType(
        id=uuid.uuid4(),
        name="warehouse",
        description="Warehouse location"
    )
    session.add(location_type)
    
    # Create location
    location = Location(
        id=uuid.uuid4(),
        name="Test Location",
        description="Test location",
        location_type_id=location_type.id
    )
    session.add(location)
    
    # Create parent item type
    parent_item_type = ItemType(
        id=uuid.uuid4(),
        name="parent_item_type",
        description="Parent item type",
        category=ItemCategory.PARENT
    )
    session.add(parent_item_type)
    
    # Create child item type
    child_item_type = ItemType(
        id=uuid.uuid4(),
        name="child_item_type",
        description="Child item type",
        category=ItemCategory.CHILD
    )
    session.add(child_item_type)
    
    session.commit()
    return user, location, parent_item_type, child_item_type


@given(
    parent_count=st.integers(min_value=2, max_value=4),
    child_count=st.integers(min_value=1, max_value=5)
)
def test_child_item_assignment_uniqueness_property(parent_count, child_count):
    """
    Property 10: Child Item Assignment Uniqueness
    
    For any child item, it should be assigned to at most one parent item 
    at any given time.
    
    **Validates: Requirements 9.2**
    """
    setup_test_database()
    
    try:
        session = SessionLocal()
        
        # Create test data
        user, location, parent_item_type, child_item_type = create_test_data(session)
        
        # Create multiple parent items
        parent_items = []
        for i in range(parent_count):
            parent_item = ParentItem(
                id=uuid.uuid4(),
                name=f"Parent_{i}",
                description=f"Test parent item {i}",
                item_type_id=parent_item_type.id,
                current_location_id=location.id,
                created_by=user.id
            )
            session.add(parent_item)
            parent_items.append(parent_item)
        
        session.commit()
        
        # Create child items and assign them to parent items
        child_items = []
        for i in range(child_count):
            # Assign each child to the first parent initially
            child_item = ChildItem(
                id=uuid.uuid4(),
                name=f"Child_{i}",
                description=f"Test child item {i}",
                item_type_id=child_item_type.id,
                parent_item_id=parent_items[0].id,
                created_by=user.id
            )
            session.add(child_item)
            child_items.append(child_item)
        
        session.commit()
        
        # Property verification: Each child item is assigned to exactly one parent
        for child_item in child_items:
            session.refresh(child_item)
            
            # Requirement 9.2: Child item should be assigned to exactly one parent
            assert child_item.parent_item_id is not None
            assert child_item.parent_item_id == parent_items[0].id
            
            # Verify the relationship is bidirectional
            assert child_item.parent_item is not None
            assert child_item.parent_item.id == parent_items[0].id
        
        # Test reassignment: Move each child to different parents
        for i, child_item in enumerate(child_items):
            # Choose a different parent for reassignment
            new_parent_index = (i + 1) % len(parent_items)
            new_parent = parent_items[new_parent_index]
            old_parent_id = child_item.parent_item_id
            
            # Reassign child to new parent
            child_item.parent_item_id = new_parent.id
            session.commit()
            session.refresh(child_item)
            
            # Property verification: Child is now assigned to new parent only
            assert child_item.parent_item_id == new_parent.id
            assert child_item.parent_item_id != old_parent_id
            
            # Verify the relationship is correct
            assert child_item.parent_item.id == new_parent.id
        
        # Verify uniqueness: No child should be assigned to multiple parents
        all_child_items = session.query(ChildItem).all()
        
        for child_item in all_child_items:
            # Each child should have exactly one parent_item_id
            assert child_item.parent_item_id is not None
            
            # Count how many times this child appears in parent relationships
            parent_count_for_child = 0
            for parent_item in parent_items:
                session.refresh(parent_item)
                if child_item in parent_item.child_items:
                    parent_count_for_child += 1
            
            # Property verification: Child appears in exactly one parent's child list
            assert parent_count_for_child == 1
        
        # Test constraint: Attempt to create duplicate assignment should fail
        # (This simulates what should happen with proper database constraints)
        test_child = child_items[0]
        original_parent_id = test_child.parent_item_id
        
        # Simulate the constraint check that should happen in the service layer
        for other_parent in parent_items:
            if other_parent.id != original_parent_id:
                # This represents the validation that should prevent multiple assignments
                # In a real system, this would be enforced by database constraints
                # or application-level validation
                
                # Verify child is not already assigned to this other parent
                other_parent_child_ids = [c.id for c in other_parent.child_items]
                assert test_child.id not in other_parent_child_ids
        
        # Final verification: All children are uniquely assigned
        child_parent_assignments = {}
        for child_item in all_child_items:
            child_id = child_item.id
            parent_id = child_item.parent_item_id
            
            # Each child should appear only once in our tracking
            assert child_id not in child_parent_assignments
            child_parent_assignments[child_id] = parent_id
        
        # Verify we have the expected number of unique assignments
        assert len(child_parent_assignments) == child_count
        
        session.close()
        
    finally:
        teardown_test_database()


if __name__ == "__main__":
    # Run a simple test to verify the property works
    test_child_item_assignment_uniqueness_property(2, 3)
    print("Property test passed!")