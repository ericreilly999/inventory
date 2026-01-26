"""Property tests for constraint enforcement.

Feature: inventory-management, Property 9: Constraint Enforcement
Validates: Requirements 4.4, 4.5, 8.4
"""

import uuid

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.models import (
    Base,
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

    # Enable foreign key constraints in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal(), engine


def create_test_data(session):
    """Create minimal test data required for property tests."""
    # Create role
    role = Role(
        id=uuid.uuid4(),
        sku="test_role",
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
        id=uuid.uuid4(), sku="warehouse", description="Warehouse location"
    )
    session.add(location_type)

    # Create location
    location = Location(
        id=uuid.uuid4(),
        sku="Test Location",
        description="Test location",
        location_type_id=location_type.id,
    )
    session.add(location)

    # Create item types
    parent_item_type = ItemType(
        id=uuid.uuid4(),
        sku="parent_item_type",
        description="Parent item type",
        category=ItemCategory.PARENT,
    )
    child_item_type = ItemType(
        id=uuid.uuid4(),
        sku="child_item_type",
        description="Child item type",
        category=ItemCategory.CHILD,
    )
    session.add_all([parent_item_type, child_item_type])

    # Create parent item
    parent_item = ParentItem(
        id=uuid.uuid4(),
        sku="Test Parent Item",
        description="Test parent item",
        item_type_id=parent_item_type.id,
        current_location_id=location.id,
        created_by=user.id,
    )
    session.add(parent_item)

    session.commit()
    return (
        user,
        location,
        location_type,
        parent_item_type,
        child_item_type,
        parent_item,
    )


@given(
    location_name=st.text(min_size=1, max_size=50),
    location_type_name=st.text(min_size=1, max_size=50),
    item_type_name=st.text(min_size=1, max_size=50),
)
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_constraint_enforcement_property(
    location_name, location_type_name, item_type_name
):
    """
    Property 9: Constraint Enforcement

    For any deletion attempt of entities with dependent relationships (locations with items,
    item types in use), the deletion should be prevented and return an error.

    **Validates: Requirements 4.4, 4.5, 8.4**
    """
    session, engine = get_test_session()

    try:
        # Create test data
        (
            user,
            location,
            location_type,
            parent_item_type,
            child_item_type,
            parent_item,
        ) = create_test_data(session)

        # Test 1: Deleting location with assigned items should fail (Requirement 4.4)
        # The location has a parent item assigned to it
        try:
            session.delete(location)
            session.commit()
            # If we reach here, the constraint was not enforced
            assert (
                False
            ), "Expected IntegrityError when deleting location with assigned items"
        except IntegrityError:
            # This is expected - constraint enforced
            session.rollback()

        # Test 2: Deleting location type with locations using it should fail (Requirement 4.5)
        # The location_type is being used by the location
        try:
            session.delete(location_type)
            session.commit()
            # If we reach here, the constraint was not enforced
            assert False, "Expected IntegrityError when deleting location type in use"
        except IntegrityError:
            # This is expected - constraint enforced
            session.rollback()

        # Test 3: Deleting item type with items using it should fail (Requirement 8.4)
        # The parent_item_type is being used by the parent_item
        try:
            session.delete(parent_item_type)
            session.commit()
            # If we reach here, the constraint was not enforced
            assert False, "Expected IntegrityError when deleting item type in use"
        except IntegrityError:
            # This is expected - constraint enforced
            session.rollback()

        # Test 4: Create additional entities to test more constraint scenarios

        # Create another location type that's not in use
        unused_location_type = LocationType(
            id=uuid.uuid4(),
            sku=location_type_name + "_unused",
            description="Unused location type",
        )
        session.add(unused_location_type)
        session.commit()

        # Create another item type that's not in use
        unused_item_type = ItemType(
            id=uuid.uuid4(),
            sku=item_type_name + "_unused",
            description="Unused item type",
            category=ItemCategory.PARENT,
        )
        session.add(unused_item_type)
        session.commit()

        # Test 5: Deleting unused entities should succeed

        # Delete unused location type should work
        session.delete(unused_location_type)
        session.commit()

        # Verify it was deleted
        deleted_location_type = (
            session.query(LocationType)
            .filter_by(name=location_type_name + "_unused")
            .first()
        )
        assert deleted_location_type is None, "Unused location type should be deleted"

        # Delete unused item type should work
        session.delete(unused_item_type)
        session.commit()

        # Verify it was deleted
        deleted_item_type = (
            session.query(ItemType).filter_by(name=item_type_name + "_unused").first()
        )
        assert deleted_item_type is None, "Unused item type should be deleted"

        # Test 6: After removing dependencies, deletion should be allowed

        # Remove the parent item first
        session.delete(parent_item)
        session.commit()

        # Now deleting the location should work
        session.delete(location)
        session.commit()

        # Verify location was deleted
        deleted_location = session.query(Location).filter_by(id=location.id).first()
        assert (
            deleted_location is None
        ), "Location should be deleted after removing dependencies"

        # Now deleting the location type should work
        session.delete(location_type)
        session.commit()

        # Verify location type was deleted
        deleted_location_type = (
            session.query(LocationType).filter_by(id=location_type.id).first()
        )
        assert (
            deleted_location_type is None
        ), "Location type should be deleted after removing dependencies"

        session.close()

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@given(location_name=st.text(min_size=1, max_size=50))
@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_location_deletion_with_items_constraint(location_name):
    """
    Test specific constraint: locations with items cannot be deleted.

    **Validates: Requirement 4.4**
    """
    session, engine = get_test_session()

    try:
        # Create test data
        (
            user,
            location,
            location_type,
            parent_item_type,
            child_item_type,
            parent_item,
        ) = create_test_data(session)

        # Verify the parent item is at the location
        assert parent_item.current_location_id == location.id

        # Try to delete the location - should fail
        try:
            session.delete(location)
            session.commit()
            assert False, "Should not be able to delete location with items"
        except IntegrityError:
            session.rollback()

        # Verify location still exists
        existing_location = session.query(Location).filter_by(id=location.id).first()
        assert (
            existing_location is not None
        ), "Location should still exist after failed deletion"

        session.close()

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@given(item_type_name=st.text(min_size=1, max_size=50))
@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_item_type_deletion_with_items_constraint(item_type_name):
    """
    Test specific constraint: item types in use cannot be deleted.

    **Validates: Requirement 8.4**
    """
    session, engine = get_test_session()

    try:
        # Create test data
        (
            user,
            location,
            location_type,
            parent_item_type,
            child_item_type,
            parent_item,
        ) = create_test_data(session)

        # Verify the parent item uses the item type
        assert parent_item.item_type_id == parent_item_type.id

        # Try to delete the item type - should fail
        try:
            session.delete(parent_item_type)
            session.commit()
            assert False, "Should not be able to delete item type in use"
        except IntegrityError:
            session.rollback()

        # Verify item type still exists
        existing_item_type = (
            session.query(ItemType).filter_by(id=parent_item_type.id).first()
        )
        assert (
            existing_item_type is not None
        ), "Item type should still exist after failed deletion"

        session.close()

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


if __name__ == "__main__":
    # Run simple tests to verify the properties work
    test_constraint_enforcement_property(
        "TestLocation", "TestLocationType", "TestItemType"
    )
    test_location_deletion_with_items_constraint("TestLocation")
    test_item_type_deletion_with_items_constraint("TestItemType")
    print("Constraint enforcement property tests passed!")
