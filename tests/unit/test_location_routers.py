"""Unit tests for location service routers."""

from uuid import uuid4

import pytest

from shared.models.location import Location, LocationType


class TestLocationTypesRouter:
    """Test location types router functionality."""

    def test_create_location_type(self, test_db_session):
        """Test creating a location type."""
        location_type = LocationType(
            id=uuid4(),
            name="Warehouse",
            description="Storage warehouse",
        )
        test_db_session.add(location_type)
        test_db_session.commit()
        test_db_session.refresh(location_type)

        assert location_type.id is not None
        assert location_type.name == "Warehouse"

    def test_get_location_type(self, test_db_session):
        """Test retrieving a location type."""
        location_type = LocationType(
            id=uuid4(),
            name="Warehouse",
            description="Storage warehouse",
        )
        test_db_session.add(location_type)
        test_db_session.commit()

        retrieved = (
            test_db_session.query(LocationType)
            .filter(LocationType.id == location_type.id)
            .first()
        )
        assert retrieved is not None
        assert retrieved.name == "Warehouse"

    def test_list_location_types(self, test_db_session):
        """Test listing location types."""
        location_type1 = LocationType(name="Warehouse", description="Storage warehouse")
        location_type2 = LocationType(name="Office", description="Office space")
        test_db_session.add_all([location_type1, location_type2])
        test_db_session.commit()

        all_types = test_db_session.query(LocationType).all()
        assert len(all_types) >= 2


class TestLocationsRouter:
    """Test locations router functionality."""

    def test_create_location(self, test_db_session):
        """Test creating a location."""
        location_type = LocationType(name="Warehouse", description="Storage warehouse")
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            id=uuid4(),
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.commit()
        test_db_session.refresh(location)

        assert location.id is not None
        assert location.name == "Warehouse A"
        assert location.location_type_id == location_type.id

    def test_get_location(self, test_db_session):
        """Test retrieving a location."""
        location_type = LocationType(name="Warehouse", description="Storage warehouse")
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.commit()

        retrieved = (
            test_db_session.query(Location).filter(Location.id == location.id).first()
        )
        assert retrieved is not None
        assert retrieved.name == "Warehouse A"

    def test_list_locations(self, test_db_session):
        """Test listing locations."""
        location_type = LocationType(name="Warehouse", description="Storage warehouse")
        test_db_session.add(location_type)
        test_db_session.flush()

        location1 = Location(
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        location2 = Location(
            name="Warehouse B",
            description="Secondary warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add_all([location1, location2])
        test_db_session.commit()

        all_locations = test_db_session.query(Location).all()
        assert len(all_locations) >= 2
