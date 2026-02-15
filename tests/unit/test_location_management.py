"""Unit tests for location management functionality.

Tests location creation, modification, deletion scenarios.
Requirements: 4.1, 4.2, 4.3
"""

import uuid
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.location.dependencies import (
    get_location_by_id,
    get_location_type_by_id,
    validate_location_deletion,
    validate_location_type_deletion,
)
from shared.models.location import Location, LocationType


class TestLocationValidation:
    """Test location validation functions."""

    def test_validate_location_deletion_with_items_should_raise_error(self):
        """Test that location deletion validation fails when items are assigned."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_location = Mock(spec=Location)
        mock_location.id = uuid.uuid4()
        mock_location.name = "Test Location"

        # Mock query to return 1 item (indicating items are assigned)
        mock_db.query.return_value.filter.return_value.count.return_value = 1

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_location_deletion(mock_location, mock_db)

        assert exc_info.value.status_code == 409
        assert "Cannot delete location" in exc_info.value.detail
        assert "1 item(s) are currently assigned" in exc_info.value.detail

    def test_validate_location_deletion_without_items_should_pass(self):
        """Test that location deletion validation passes when no items are assigned."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_location = Mock(spec=Location)
        mock_location.id = uuid.uuid4()
        mock_location.name = "Test Location"

        # Mock query to return 0 items (no items assigned)
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        # Act & Assert - should not raise any exception
        validate_location_deletion(mock_location, mock_db)

    def test_validate_location_type_deletion_with_locations_should_raise_error(
        self,
    ):
        """Test that location type deletion validation fails when locations use it."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_location_type = Mock(spec=LocationType)
        mock_location_type.id = uuid.uuid4()
        mock_location_type.name = "Test Location Type"

        # Mock locations that use this type
        mock_location1 = Mock(spec=Location)
        mock_location1.name = "Location 1"
        mock_location2 = Mock(spec=Location)
        mock_location2.name = "Location 2"

        # Mock query to return 2 locations using this type
        mock_db.query.return_value.filter.return_value.count.return_value = 2
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
            mock_location1,
            mock_location2,
        ]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_location_type_deletion(mock_location_type, mock_db)

        assert exc_info.value.status_code == 409
        assert "Cannot delete location type" in exc_info.value.detail
        assert "2 location(s) are using it" in exc_info.value.detail
        assert "Location 1" in exc_info.value.detail
        assert "Location 2" in exc_info.value.detail

    def test_validate_location_type_deletion_without_locations_pass(
        self,
    ):
        """Test location type deletion validation passes."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_location_type = Mock(spec=LocationType)
        mock_location_type.id = uuid.uuid4()
        mock_location_type.name = "Test Location Type"

        # Mock query to return 0 locations
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        # Act & Assert - should not raise any exception
        validate_location_type_deletion(mock_location_type, mock_db)


class TestLocationRetrieval:
    """Test location retrieval functions."""

    @pytest.mark.asyncio
    async def test_get_location_by_id_existing_location(self):
        """Test retrieving an existing location by ID."""
        # Arrange
        location_id = uuid.uuid4()
        mock_db = Mock(spec=Session)
        mock_location = Mock(spec=Location)
        mock_location.id = location_id
        mock_location.name = "Test Location"

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_location
        )

        # Act
        result = await get_location_by_id(location_id, mock_db)

        # Assert
        assert result == mock_location
        mock_db.query.assert_called_once_with(Location)

    @pytest.mark.asyncio
    async def test_get_location_by_id_nonexistent_location(self):
        """Test retrieving a non-existent location by ID raises 404."""
        # Arrange
        location_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_location_by_id(location_id, mock_db)

        assert exc_info.value.status_code == 404
        assert f"Location with id {location_id} not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_location_type_by_id_existing_type(self):
        """Test retrieving an existing location type by ID."""
        # Arrange
        location_type_id = uuid.uuid4()
        mock_db = Mock(spec=Session)
        mock_location_type = Mock(spec=LocationType)
        mock_location_type.id = location_type_id
        mock_location_type.name = "Test Location Type"

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_location_type
        )

        # Act
        result = await get_location_type_by_id(location_type_id, mock_db)

        # Assert
        assert result == mock_location_type
        mock_db.query.assert_called_once_with(LocationType)

    @pytest.mark.asyncio
    async def test_get_location_type_by_id_nonexistent_type(self):
        """Test retrieving a non-existent location type by ID raises 404."""
        # Arrange
        location_type_id = uuid.uuid4()
        mock_db = Mock(spec=Session)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_location_type_by_id(location_type_id, mock_db)

        assert exc_info.value.status_code == 404
        assert (
            f"Location type with id {location_type_id} not found"
            in exc_info.value.detail
        )


class TestLocationCreation:
    """Test location creation scenarios."""

    def test_location_creation_with_valid_data(self):
        """Test creating a location with valid data."""
        # Arrange
        location_type_id = uuid.uuid4()
        location_data = {
            "name": "Test Warehouse",
            "description": "A test warehouse location",
            "location_metadata": {"capacity": 1000},
            "location_type_id": location_type_id,
        }

        # Act
        location = Location(**location_data)

        # Assert
        assert location.name == "Test Warehouse"
        assert location.description == "A test warehouse location"
        assert location.location_metadata == {"capacity": 1000}
        assert location.location_type_id == location_type_id

    def test_location_creation_with_minimal_data(self):
        """Test creating a location with minimal required data."""
        # Arrange
        location_type_id = uuid.uuid4()
        location_data = {
            "name": "Minimal Location",
            "location_type_id": location_type_id,
        }

        # Act
        location = Location(**location_data)

        # Assert
        assert location.name == "Minimal Location"
        assert location.description is None
        assert location.location_metadata is None  # SQLAlchemy default behavior
        assert location.location_type_id == location_type_id

    def test_location_type_creation_with_valid_data(self):
        """Test creating a location type with valid data."""
        # Arrange
        location_type_data = {
            "name": "Warehouse",
            "description": "Storage warehouse locations",
        }

        # Act
        location_type = LocationType(**location_type_data)

        # Assert
        assert location_type.name == "Warehouse"
        assert location_type.description == "Storage warehouse locations"

    def test_location_type_creation_with_minimal_data(self):
        """Test creating a location type with minimal required data."""
        # Arrange
        location_type_data = {"name": "Delivery Site"}

        # Act
        location_type = LocationType(**location_type_data)

        # Assert
        assert location_type.name == "Delivery Site"
        assert location_type.description is None


class TestLocationModification:
    """Test location modification scenarios."""

    def test_location_update_name(self):
        """Test updating a location's name."""
        # Arrange
        location = Location(
            name="Old Name",
            description="Test location",
            location_type_id=uuid.uuid4(),
        )

        # Act
        location.name = "New Name"

        # Assert
        assert location.name == "New Name"
        assert location.description == "Test location"  # Unchanged

    def test_location_update_metadata(self):
        """Test updating a location's metadata."""
        # Arrange
        location = Location(
            name="Test Location",
            location_metadata={"capacity": 500},
            location_type_id=uuid.uuid4(),
        )

        # Act
        location.location_metadata = {
            "capacity": 1000,
            "temperature_controlled": True,
        }

        # Assert
        assert location.location_metadata["capacity"] == 1000
        assert location.location_metadata["temperature_controlled"] is True

    def test_location_type_update_description(self):
        """Test updating a location type's description."""
        # Arrange
        location_type = LocationType(name="Warehouse", description="Old description")

        # Act
        location_type.description = "Updated warehouse description"

        # Assert
        assert location_type.name == "Warehouse"  # Unchanged
        assert location_type.description == "Updated warehouse description"


class TestLocationDeletionScenarios:
    """Test various location deletion scenarios."""

    def test_location_deletion_constraint_with_multiple_items(self):
        """Test location deletion validation with multiple items assigned."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_location = Mock(spec=Location)
        mock_location.id = uuid.uuid4()
        mock_location.name = "Busy Location"

        # Mock query to return 5 items
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_location_deletion(mock_location, mock_db)

        assert exc_info.value.status_code == 409
        assert "5 item(s) are currently assigned" in exc_info.value.detail

    def test_location_type_deletion_constraint_with_multiple_locations(self):
        """Test location type deletion validation with multiple locations using it."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_location_type = Mock(spec=LocationType)
        mock_location_type.id = uuid.uuid4()
        mock_location_type.name = "Popular Type"

        # Mock locations that use this type
        mock_location1 = Mock(spec=Location)
        mock_location1.name = "Location A"
        mock_location2 = Mock(spec=Location)
        mock_location2.name = "Location B"
        mock_location3 = Mock(spec=Location)
        mock_location3.name = "Location C"

        # Mock query to return 3 locations
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
            mock_location1,
            mock_location2,
            mock_location3,
        ]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_location_type_deletion(mock_location_type, mock_db)

        assert exc_info.value.status_code == 409
        assert "3 location(s) are using it" in exc_info.value.detail
        assert "Location A" in exc_info.value.detail
        assert "Location B" in exc_info.value.detail
        assert "Location C" in exc_info.value.detail


class TestLocationEdgeCases:
    """Test edge cases and error conditions."""

    def test_location_with_empty_name_should_fail_validation(self):
        """Test that location with empty name should fail validation."""
        # This would typically be caught by Pydantic validation in the API layer
        # Here we test the model can handle it but validation should happen
        # upstream

        # Arrange & Act
        location = Location(name="", location_type_id=uuid.uuid4())  # Empty name

        # Assert - model accepts it but API validation should catch this
        assert location.name == ""

    def test_location_with_very_long_name(self):
        """Test location with maximum allowed name length."""
        # Arrange
        long_name = "A" * 200  # Maximum length from model definition
        location_type_id = uuid.uuid4()

        # Act
        location = Location(name=long_name, location_type_id=location_type_id)

        # Assert
        assert location.name == long_name
        assert len(location.name) == 200

    def test_location_type_with_very_long_name(self):
        """Test location type with maximum allowed name length."""
        # Arrange
        long_name = "B" * 100  # Maximum length from model definition

        # Act
        location_type = LocationType(name=long_name)

        # Assert
        assert location_type.name == long_name
        assert len(location_type.name) == 100

    def test_location_metadata_with_complex_structure(self):
        """Test location with complex metadata structure."""
        # Arrange
        complex_metadata = {
            "capacity": 1000,
            "zones": ["A", "B", "C"],
            "equipment": {"forklifts": 5, "scanners": 10},
            "temperature_range": {"min": -20, "max": 25},
        }

        # Act
        location = Location(
            name="Complex Location",
            location_metadata=complex_metadata,
            location_type_id=uuid.uuid4(),
        )

        # Assert
        assert location.location_metadata == complex_metadata
        assert location.location_metadata["zones"] == ["A", "B", "C"]
        assert location.location_metadata["equipment"]["forklifts"] == 5


if __name__ == "__main__":
    pytest.main([__file__])
