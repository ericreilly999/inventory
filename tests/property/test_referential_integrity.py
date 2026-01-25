"""Property tests for referential integrity validation.

Feature: inventory-management, Property 8: Referential Integrity Validation
Validates: Requirements 4.1, 8.3, 9.1
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
    ChildItem,
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

    # Create location
    location = Location(
        id=uuid.uuid4(),
        name="Test Location",
        description="Test location",
        location_type_id=location_type.id,
    )
    session.add(location)

    # Create item types
    parent_item_type = ItemType(
        id=uuid.uuid4(),
        name="parent_item_type",
        description="Parent item type",
        category=ItemCategory.PARENT,
    )
    child_item_type = ItemType(
        id=uuid.uuid4(),
        name="child_item_type",
        description="Child item type",
        category=ItemCategory.CHILD,
    )
    session.add_all([parent_item_type, child_item_type])

    session.commit()
    return user, location, location_type, parent_item_type, child_item_type


@given(
    location_name=st.text(min_size=1, max_size=50),
    item_name=st.text(min_size=1, max_size=50),
)
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_referential_integrity_validation_property(location_name, item_name):
    """
    Property 8: Referential Integrity Validation

    For any creation operation (locations, items, assignments), all referenced
    entities must exist or the operation should fail with appropriate validation errors.

    **Validates: Requirements 4.1, 8.3, 9.1**
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
        ) = create_test_data(session)

        # Test 1: Creating location with non-existent location_type should fail
        non_existent_location_type_id = uuid.uuid4()
        invalid_location = Location(
            id=uuid.uuid4(),
            name=location_name,
            description="Invalid location",
            location_type_id=non_existent_location_type_id,
        )
        session.add(invalid_location)

        try:
            session.commit()
            # If we reach here, the constraint was not enforced
            assert False, "Expected IntegrityError for non-existent location_type_id"
        except IntegrityError:
            # This is expected - referential integrity enforced
            session.rollback()

        # Test 2: Creating parent item with non-existent location should fail
        non_existent_location_id = uuid.uuid4()
        invalid_parent_item = ParentItem(
            id=uuid.uuid4(),
            name=item_name,
            description="Invalid parent item",
            item_type_id=parent_item_type.id,
            current_location_id=non_existent_location_id,
            created_by=user.id,
        )
        session.add(invalid_parent_item)

        try:
            session.commit()
            # If we reach here, the constraint was not enforced
            assert False, "Expected IntegrityError for non-existent location_id"
        except IntegrityError:
            # This is expected - referential integrity enforced
            session.rollback()

        # Test 3: Creating parent item with non-existent item_type should fail
        non_existent_item_type_id = uuid.uuid4()
        invalid_parent_item_2 = ParentItem(
            id=uuid.uuid4(),
            name=item_name + "_2",
            description="Invalid parent item 2",
            item_type_id=non_existent_item_type_id,
            current_location_id=location.id,
            created_by=user.id,
        )
        session.add(invalid_parent_item_2)

        try:
            session.commit()
            # If we reach here, the constraint was not enforced
            assert False, "Expected IntegrityError for non-existent item_type_id"
        except IntegrityError:
            # This is expected - referential integrity enforced
            session.rollback()

        # Test 4: Creating child item with non-existent parent should fail
        non_existent_parent_id = uuid.uuid4()
        invalid_child_item = ChildItem(
            id=uuid.uuid4(),
            name=item_name + "_child",
            description="Invalid child item",
            item_type_id=child_item_type.id,
            parent_item_id=non_existent_parent_id,
            created_by=user.id,
        )
        session.add(invalid_child_item)

        try:
            session.commit()
            # If we reach here, the constraint was not enforced
            assert False, "Expected IntegrityError for non-existent parent_item_id"
        except IntegrityError:
            # This is expected - referential integrity enforced
            session.rollback()

        # Test 5: Valid operations should succeed
        # Create valid location
        valid_location = Location(
            id=uuid.uuid4(),
            name=location_name + "_valid",
            description="Valid location",
            location_type_id=location_type.id,
        )
        session.add(valid_location)
        session.commit()

        # Create valid parent item
        valid_parent_item = ParentItem(
            id=uuid.uuid4(),
            name=item_name + "_valid",
            description="Valid parent item",
            item_type_id=parent_item_type.id,
            current_location_id=valid_location.id,
            created_by=user.id,
        )
        session.add(valid_parent_item)
        session.commit()

        # Create valid child item
        valid_child_item = ChildItem(
            id=uuid.uuid4(),
            name=item_name + "_valid_child",
            description="Valid child item",
            item_type_id=child_item_type.id,
            parent_item_id=valid_parent_item.id,
            created_by=user.id,
        )
        session.add(valid_child_item)
        session.commit()

        # Verify all valid entities were created successfully
        assert (
            session.query(Location).filter_by(name=location_name + "_valid").first()
            is not None
        )
        assert (
            session.query(ParentItem).filter_by(name=item_name + "_valid").first()
            is not None
        )
        assert (
            session.query(ChildItem).filter_by(name=item_name + "_valid_child").first()
            is not None
        )

        session.close()

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


if __name__ == "__main__":
    # Run a simple test to verify the property works
    test_referential_integrity_validation_property("TestLocation", "TestItem")
    print("Referential integrity property test passed!")
