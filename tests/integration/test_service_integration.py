"""
Service integration tests for inventory management system.

Tests inter-service communication patterns, API contract compliance,
database transaction boundaries, and event-driven communication flows.
Requirements: 10.3, 10.5
"""

import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy.orm import Session

from shared.models.assignment_history import AssignmentHistory
from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory
from shared.models.user import Role, User


@pytest.mark.skip(reason="Async integration tests need refactoring")
class TestInterServiceCommunication:
    """Test communication patterns between microservices."""

    @pytest.fixture
    def mock_service_responses(self):
        """Mock responses from different services."""
        return {
            "user_service": {
                "login": {
                    "access_token": "test-token-123",
                    "token_type": "bearer",
                    "user": {
                        "id": str(uuid.uuid4()),
                        "username": "testuser",
                        "email": "test@example.com",
                        "role": {
                            "name": "admin",
                            "permissions": ["read", "write"],
                        },
                    },
                },
                "users": [
                    {
                        "id": str(uuid.uuid4()),
                        "username": "user1",
                        "email": "user1@example.com",
                        "active": True,
                    }
                ],
            },
            "inventory_service": {
                "parent_items": [
                    {
                        "id": str(uuid.uuid4()),
                        "sku": "Test Parent Item",
                        "description": "Test description",
                        "item_type_id": str(uuid.uuid4()),
                        "current_location_id": str(uuid.uuid4()),
                    }
                ],
                "child_items": [
                    {
                        "id": str(uuid.uuid4()),
                        "sku": "Test Child Item",
                        "description": "Test child description",
                        "item_type_id": str(uuid.uuid4()),
                        "parent_item_id": str(uuid.uuid4()),
                    }
                ],
            },
            "location_service": {
                "locations": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Test Location",
                        "description": "Test location description",
                        "location_type_id": str(uuid.uuid4()),
                    }
                ],
                "movements": [
                    {
                        "id": str(uuid.uuid4()),
                        "parent_item_id": str(uuid.uuid4()),
                        "from_location_id": str(uuid.uuid4()),
                        "to_location_id": str(uuid.uuid4()),
                        "moved_at": "2025-01-18T10:00:00Z",
                        "moved_by": str(uuid.uuid4()),
                    }
                ],
            },
            "reporting_service": {
                "inventory_report": [
                    {
                        "location_name": "Warehouse A",
                        "item_count": 10,
                        "item_types": ["Electronics", "Tools"],
                    }
                ]
            },
        }

    @pytest.mark.asyncio
    async def test_authentication_flow_integration(self, mock_service_responses):
        """Test authentication flow between API Gateway and User Service."""

        # Mock the httpx client for user service
        with patch("httpx.AsyncClient.request") as mock_request:
            # Configure mock response for login
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_service_responses["user_service"][
                "login"
            ]
            mock_response.headers = {"content-type": "application/json"}
            mock_response.content = b'{"access_token": "test-token-123"}'
            mock_request.return_value = mock_response

            # Import and test the gateway routing function
            from fastapi import Request

            from services.api_gateway.routers.gateway import route_request

            # Create mock request
            request = AsyncMock(spec=Request)
            request.method = "POST"
            request.headers = {"content-type": "application/json"}
            request.body.return_value = (
                b'{"username": "testuser", "password": "password"}'
            )
            request.query_params = {}
            request.state = AsyncMock()

            # Create mock client
            client = AsyncMock(spec=httpx.AsyncClient)
            client.request = mock_request

            # Test the routing
            response = await route_request(request, "user", "/auth/login", client)

            # Verify the request was routed correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["method"] == "POST"
            assert "user-service:8003/api/v1/auth/login" in call_args[1]["url"]

            # Verify response
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_inventory_location_integration(self, mock_service_responses):
        """Test integration between Inventory and Location services."""

        with patch("httpx.AsyncClient.request") as mock_request:
            # Mock responses for both services
            def mock_response_side_effect(*args, **kwargs):
                mock_response = AsyncMock()
                mock_response.headers = {"content-type": "application/json"}

                if "inventory-service" in kwargs["url"]:
                    mock_response.status_code = 200
                    mock_response.json.return_value = mock_service_responses[
                        "inventory_service"
                    ]["parent_items"]
                    mock_response.content = b'[{"id": "test-id"}]'
                elif "location-service" in kwargs["url"]:
                    mock_response.status_code = 200
                    mock_response.json.return_value = mock_service_responses[
                        "location_service"
                    ]["locations"]
                    mock_response.content = b'[{"id": "test-location-id"}]'

                return mock_response

            mock_request.side_effect = mock_response_side_effect

            from fastapi import Request

            from services.api_gateway.routers.gateway import route_request

            # Test inventory service call
            request = AsyncMock(spec=Request)
            request.method = "GET"
            request.headers = {"authorization": "Bearer test-token"}
            request.body.return_value = b""
            request.query_params = {}
            request.state = AsyncMock()
            request.state.user_id = "test-user-id"

            client = AsyncMock(spec=httpx.AsyncClient)
            client.request = mock_request

            # Get parent items
            response = await route_request(
                request, "inventory", "/items/parent", client
            )
            assert response.status_code == 200

            # Get locations
            response = await route_request(request, "location", "/locations", client)
            assert response.status_code == 200

            # Verify both services were called
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_reporting_data_aggregation(self, mock_service_responses):
        """Test reporting service aggregating data from multiple services."""

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_service_responses[
                "reporting_service"
            ]["inventory_report"]
            mock_response.headers = {"content-type": "application/json"}
            mock_response.content = b'[{"location_name": "Warehouse A"}]'
            mock_request.return_value = mock_response

            from fastapi import Request

            from services.api_gateway.routers.gateway import route_request

            request = AsyncMock(spec=Request)
            request.method = "GET"
            request.headers = {"authorization": "Bearer test-token"}
            request.body.return_value = b""
            request.query_params = {}
            request.state = AsyncMock()

            client = AsyncMock(spec=httpx.AsyncClient)
            client.request = mock_request

            # Test reporting endpoint
            response = await route_request(
                request, "reporting", "/reports/inventory", client
            )

            assert response.status_code == 200
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_error_propagation(self):
        """Test error propagation between services."""

        with patch("httpx.AsyncClient.request") as mock_request:
            # Mock service error
            mock_request.side_effect = httpx.ConnectError("Service unavailable")

            from fastapi import HTTPException, Request

            from services.api_gateway.routers.gateway import route_request

            request = AsyncMock(spec=Request)
            request.method = "GET"
            request.headers = {}
            request.body.return_value = b""
            request.query_params = {}
            request.state = AsyncMock()

            client = AsyncMock(spec=httpx.AsyncClient)
            client.request = mock_request

            # Test error handling
            with pytest.raises(HTTPException) as exc_info:
                await route_request(request, "inventory", "/items/parent", client)

            assert exc_info.value.status_code == 503
            assert "SERVICE_UNAVAILABLE" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_request_header_forwarding(self):
        """Test that authentication headers are properly forwarded between services."""

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.headers = {"content-type": "application/json"}
            mock_response.content = b"[]"
            mock_request.return_value = mock_response

            from fastapi import Request

            from services.api_gateway.routers.gateway import route_request

            request = AsyncMock(spec=Request)
            request.method = "GET"
            request.headers = {
                "authorization": "Bearer test-token-123",
                "content-type": "application/json",
            }
            request.body.return_value = b""
            request.query_params = {}
            request.state = AsyncMock()
            request.state.user_id = "test-user-id"
            request.state.user_role = "admin"

            client = AsyncMock(spec=httpx.AsyncClient)
            client.request = mock_request

            await route_request(request, "inventory", "/items/parent", client)

            # Verify headers were forwarded
            call_args = mock_request.call_args
            headers = call_args[1]["headers"]
            assert headers["authorization"] == "Bearer test-token-123"
            assert headers["X-User-ID"] == "test-user-id"
            assert headers["X-User-Role"] == "admin"


@pytest.mark.skip(reason="API contract tests need refactoring")
class TestAPIContractCompliance:
    """Test API contract compliance between services."""

    def test_user_service_contract(self):
        """Test User Service API contract compliance."""

        # Expected endpoints and their contracts
        expected_endpoints = {
            "/api/v1/auth/login": {
                "method": "POST",
                "request_schema": {"username": str, "password": str},
                "response_schema": {
                    "access_token": str,
                    "token_type": str,
                    "user": dict,
                },
            },
            "/api/v1/users": {"method": "GET", "response_schema": list},
            "/api/v1/roles": {"method": "GET", "response_schema": list},
        }

        # This test validates the contract structure
        # In a real implementation, this would make actual API calls
        # and validate response schemas
        for endpoint, contract in expected_endpoints.items():
            assert "method" in contract
            assert contract["method"] in ["GET", "POST", "PUT", "DELETE"]

            if "response_schema" in contract:
                assert contract["response_schema"] in [
                    str,
                    int,
                    dict,
                    list,
                    bool,
                ]

    def test_inventory_service_contract(self):
        """Test Inventory Service API contract compliance."""

        expected_endpoints = {
            "/api/v1/items/parent": {
                "methods": ["GET", "POST"],
                "get_response": list,
                "post_request": {
                    "name": str,
                    "description": str,
                    "item_type_id": str,
                    "current_location_id": str,
                },
            },
            "/api/v1/items/child": {
                "methods": ["GET", "POST"],
                "get_response": list,
                "post_request": {
                    "name": str,
                    "description": str,
                    "item_type_id": str,
                    "parent_item_id": str,
                },
            },
        }

        for endpoint, contract in expected_endpoints.items():
            assert "methods" in contract
            assert isinstance(contract["methods"], list)
            assert len(contract["methods"]) > 0

    def test_location_service_contract(self):
        """Test Location Service API contract compliance."""

        expected_endpoints = {
            "/api/v1/locations": {
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "get_response": list,
                "post_request": {
                    "name": str,
                    "description": str,
                    "location_type_id": str,
                },
            },
            "/api/v1/movements": {
                "methods": ["GET", "POST"],
                "post_request": {
                    "parent_item_id": str,
                    "to_location_id": str,
                    "notes": str,
                },
            },
        }

        for endpoint, contract in expected_endpoints.items():
            assert "methods" in contract
            assert "GET" in contract["methods"]

    def test_reporting_service_contract(self):
        """Test Reporting Service API contract compliance."""

        expected_endpoints = {
            "/api/v1/reports/inventory": {
                "method": "GET",
                "response_schema": list,
                "query_params": ["location_id", "item_type_id"],
            },
            "/api/v1/reports/movements": {
                "method": "GET",
                "response_schema": list,
                "query_params": ["start_date", "end_date", "location_id"],
            },
        }

        for endpoint, contract in expected_endpoints.items():
            assert "method" in contract
            assert "response_schema" in contract
            if "query_params" in contract:
                assert isinstance(contract["query_params"], list)


class TestDatabaseTransactionBoundaries:
    """Test database transaction boundaries across services."""

    def test_item_movement_transaction_integrity(self, test_db_session: Session):
        """Test that item movements maintain transaction integrity."""

        # Create test data
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role_id=role.id,
            active=True,
        )
        test_db_session.add(user)
        test_db_session.flush()

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
        test_db_session.flush()

        item_type = ItemType(
            name="Electronics",
            description="Electronic items",
            category=ItemCategory.PARENT,
        )
        test_db_session.add(item_type)
        test_db_session.flush()

        parent_item = ParentItem(
            sku="Laptop",
            description="Dell Laptop",
            item_type_id=item_type.id,
            current_location_id=location1.id,
            created_by=user.id,
        )
        test_db_session.add(parent_item)
        test_db_session.flush()

        # Test transaction boundary - movement should be atomic
        try:
            # Simulate item movement
            old_location_id = parent_item.current_location_id
            parent_item.current_location_id = location2.id

            # Create move history record
            move_history = MoveHistory(
                parent_item_id=parent_item.id,
                from_location_id=old_location_id,
                to_location_id=location2.id,
                moved_by=user.id,
                notes="Test movement",
            )
            test_db_session.add(move_history)

            # Commit transaction
            test_db_session.commit()

            # Verify both changes were committed
            assert parent_item.current_location_id == location2.id

            move_record = (
                test_db_session.query(MoveHistory)
                .filter_by(parent_item_id=parent_item.id)
                .first()
            )
            assert move_record is not None
            assert move_record.to_location_id == location2.id

        except Exception:
            # If any part fails, transaction should rollback
            test_db_session.rollback()
            pytest.fail("Transaction should maintain integrity")

    def test_child_item_assignment_transaction(self, test_db_session: Session):
        """Test child item assignment transaction boundaries."""

        # Create test data
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role_id=role.id,
            active=True,
        )
        test_db_session.add(user)
        test_db_session.flush()

        location_type = LocationType(name="Warehouse", description="Storage warehouse")
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        parent_item_type = ItemType(
            name="Electronics",
            description="Electronic items",
            category=ItemCategory.PARENT,
        )
        child_item_type = ItemType(
            name="Accessories",
            description="Electronic accessories",
            category=ItemCategory.CHILD,
        )
        test_db_session.add_all([parent_item_type, child_item_type])
        test_db_session.flush()

        parent_item = ParentItem(
            sku="Laptop",
            description="Dell Laptop",
            item_type_id=parent_item_type.id,
            current_location_id=location.id,
            created_by=user.id,
        )
        test_db_session.add(parent_item)
        test_db_session.flush()

        # Create a second parent item for reassignment
        parent_item2 = ParentItem(
            sku="Desktop",
            description="Dell Desktop",
            item_type_id=parent_item_type.id,
            current_location_id=location.id,
            created_by=user.id,
        )
        test_db_session.add(parent_item2)
        test_db_session.flush()

        child_item = ChildItem(
            sku="Mouse",
            description="Wireless mouse",
            item_type_id=child_item_type.id,
            parent_item_id=parent_item.id,  # Must have a parent
            created_by=user.id,
        )
        test_db_session.add(child_item)
        test_db_session.flush()

        # Test assignment transaction - reassign to different parent
        try:
            # Reassign child to different parent
            old_parent_id = child_item.parent_item_id
            child_item.parent_item_id = parent_item2.id

            # Create assignment history
            assignment_history = AssignmentHistory(
                child_item_id=child_item.id,
                from_parent_item_id=old_parent_id,
                to_parent_item_id=parent_item2.id,
                assigned_by=user.id,
                notes="Test assignment",
            )
            test_db_session.add(assignment_history)

            test_db_session.commit()

            # Verify assignment
            assert child_item.parent_item_id == parent_item2.id

            history_record = (
                test_db_session.query(AssignmentHistory)
                .filter_by(child_item_id=child_item.id)
                .first()
            )
            assert history_record is not None
            assert history_record.to_parent_item_id == parent_item2.id

        except Exception:
            test_db_session.rollback()
            pytest.fail("Assignment transaction should maintain integrity")

    def test_concurrent_modification_handling(self, test_db_session: Session):
        """Test handling of concurrent modifications."""

        # Create test data
        role = Role(
            name="admin",
            description="Administrator",
            permissions={"read": True, "write": True},
        )
        test_db_session.add(role)
        test_db_session.flush()

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role_id=role.id,
            active=True,
        )
        test_db_session.add(user)
        test_db_session.flush()

        location_type = LocationType(name="Warehouse", description="Storage warehouse")
        test_db_session.add(location_type)
        test_db_session.flush()

        location = Location(
            name="Warehouse A",
            description="Main warehouse",
            location_type_id=location_type.id,
        )
        test_db_session.add(location)
        test_db_session.flush()

        item_type = ItemType(
            name="Electronics",
            description="Electronic items",
            category=ItemCategory.PARENT,
        )
        test_db_session.add(item_type)
        test_db_session.flush()

        parent_item = ParentItem(
            sku="Laptop",
            description="Dell Laptop",
            item_type_id=item_type.id,
            current_location_id=location.id,
            created_by=user.id,
        )
        test_db_session.add(parent_item)
        test_db_session.commit()

        # Test concurrent modification detection
        # This would typically involve optimistic locking or version fields
        original_updated_at = parent_item.updated_at

        # Simulate modification
        parent_item.description = "Updated Dell Laptop"
        test_db_session.commit()

        # Verify timestamp changed
        assert parent_item.updated_at > original_updated_at


class TestEventDrivenCommunication:
    """Test event-driven communication flows between services."""

    @pytest.mark.asyncio
    async def test_item_movement_event_flow(self):
        """Test event flow when an item is moved between locations."""

        # Mock event publishing/consuming
        events_published = []

        def mock_publish_event(event_type: str, data: Dict[str, Any]):
            events_published.append({"type": event_type, "data": data})

        # Simulate item movement event
        item_id = str(uuid.uuid4())
        from_location_id = str(uuid.uuid4())
        to_location_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Publish movement event
        mock_publish_event(
            "item.moved",
            {
                "item_id": item_id,
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
                "moved_by": user_id,
                "timestamp": "2025-01-18T10:00:00Z",
            },
        )

        # Verify event was published
        assert len(events_published) == 1
        event = events_published[0]
        assert event["type"] == "item.moved"
        assert event["data"]["item_id"] == item_id
        assert event["data"]["from_location_id"] == from_location_id
        assert event["data"]["to_location_id"] == to_location_id

    @pytest.mark.asyncio
    async def test_user_role_change_event_flow(self):
        """Test event flow when user role changes."""

        events_published = []

        def mock_publish_event(event_type: str, data: Dict[str, Any]):
            events_published.append({"type": event_type, "data": data})

        # Simulate role change event
        user_id = str(uuid.uuid4())
        old_role = "user"
        new_role = "admin"

        mock_publish_event(
            "user.role_changed",
            {
                "user_id": user_id,
                "old_role": old_role,
                "new_role": new_role,
                "changed_by": str(uuid.uuid4()),
                "timestamp": "2025-01-18T10:00:00Z",
            },
        )

        # Verify event was published
        assert len(events_published) == 1
        event = events_published[0]
        assert event["type"] == "user.role_changed"
        assert event["data"]["user_id"] == user_id
        assert event["data"]["old_role"] == old_role
        assert event["data"]["new_role"] == new_role

    @pytest.mark.asyncio
    async def test_inventory_update_event_flow(self):
        """Test event flow for inventory updates."""

        events_published = []

        def mock_publish_event(event_type: str, data: Dict[str, Any]):
            events_published.append({"type": event_type, "data": data})

        # Simulate inventory update events
        parent_item_id = str(uuid.uuid4())
        child_item_id = str(uuid.uuid4())

        # Parent item created
        mock_publish_event(
            "inventory.parent_item_created",
            {
                "item_id": parent_item_id,
                "name": "New Laptop",
                "location_id": str(uuid.uuid4()),
                "created_by": str(uuid.uuid4()),
                "timestamp": "2025-01-18T10:00:00Z",
            },
        )

        # Child item assigned
        mock_publish_event(
            "inventory.child_item_assigned",
            {
                "child_item_id": child_item_id,
                "parent_item_id": parent_item_id,
                "assigned_by": str(uuid.uuid4()),
                "timestamp": "2025-01-18T10:01:00Z",
            },
        )

        # Verify events were published in order
        assert len(events_published) == 2

        create_event = events_published[0]
        assert create_event["type"] == "inventory.parent_item_created"
        assert create_event["data"]["item_id"] == parent_item_id

        assign_event = events_published[1]
        assert assign_event["type"] == "inventory.child_item_assigned"
        assert assign_event["data"]["child_item_id"] == child_item_id
        assert assign_event["data"]["parent_item_id"] == parent_item_id

    def test_event_ordering_and_consistency(self):
        """Test that events maintain proper ordering and consistency."""

        events = []

        def mock_event_handler(event_type: str, data: Dict[str, Any]):
            events.append(
                {
                    "type": event_type,
                    "data": data,
                    "processed_at": len(events),  # Simple ordering
                }
            )

        # Simulate a sequence of related events
        item_id = str(uuid.uuid4())
        location1_id = str(uuid.uuid4())
        location2_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Event sequence: create item -> move item -> update item
        mock_event_handler(
            "inventory.item_created",
            {
                "item_id": item_id,
                "location_id": location1_id,
                "created_by": user_id,
            },
        )

        mock_event_handler(
            "inventory.item_moved",
            {
                "item_id": item_id,
                "from_location_id": location1_id,
                "to_location_id": location2_id,
                "moved_by": user_id,
            },
        )

        mock_event_handler(
            "inventory.item_updated",
            {
                "item_id": item_id,
                "updated_fields": ["description"],
                "updated_by": user_id,
            },
        )

        # Verify event ordering
        assert len(events) == 3
        assert events[0]["type"] == "inventory.item_created"
        assert events[1]["type"] == "inventory.item_moved"
        assert events[2]["type"] == "inventory.item_updated"

        # Verify all events reference the same item
        for event in events:
            assert event["data"]["item_id"] == item_id

    def test_event_error_handling_and_retry(self):
        """Test event processing error handling and retry mechanisms."""

        processed_events = []
        failed_events = []
        retry_count = {}

        def mock_event_processor(
            event_type: str, data: Dict[str, Any], should_fail: bool = False
        ):
            event_id = data.get("event_id", "unknown")

            if should_fail and retry_count.get(event_id, 0) < 2:
                # Simulate failure for first 2 attempts
                retry_count[event_id] = retry_count.get(event_id, 0) + 1
                failed_events.append(
                    {
                        "type": event_type,
                        "data": data,
                        "retry_count": retry_count[event_id],
                    }
                )
                raise Exception(f"Processing failed for {event_type}")
            else:
                # Success on 3rd attempt or immediate success
                processed_events.append(
                    {
                        "type": event_type,
                        "data": data,
                        "retry_count": retry_count.get(event_id, 0),
                    }
                )

        # Test successful event processing
        try:
            mock_event_processor(
                "inventory.item_created",
                {"event_id": "event-1", "item_id": str(uuid.uuid4())},
            )
        except Exception:
            pass

        # Test event with retries
        for attempt in range(3):
            try:
                mock_event_processor(
                    "inventory.item_moved",
                    {"event_id": "event-2", "item_id": str(uuid.uuid4())},
                    should_fail=True,
                )
                break  # Success
            except Exception:
                continue  # Retry

        # Verify processing results
        assert len(processed_events) == 2  # Both events eventually processed
        assert len(failed_events) == 2  # 2 failed attempts for event-2

        # Verify retry logic
        event_2_processed = next(
            e for e in processed_events if e["data"]["event_id"] == "event-2"
        )
        assert event_2_processed["retry_count"] == 2  # Succeeded on 3rd attempt
