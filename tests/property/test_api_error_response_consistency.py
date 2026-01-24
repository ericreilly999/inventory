"""Property-based tests for API error response consistency.

Feature: inventory-management, Property 15: API Error Response Consistency
Validates: Requirements 7.4
"""

from unittest.mock import patch

from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from services.api_gateway.main import app
from shared.auth.utils import create_access_token


# Generators for test data
@st.composite
def error_scenario_data(draw):
    """Generate error scenario data."""
    error_type = draw(
        st.sampled_from(
            [
                "authentication_error",
                "service_unavailable",
                "service_timeout",
                "invalid_service",
                "rate_limit_exceeded",
            ]
        )
    )

    endpoint = draw(
        st.sampled_from(
            [
                "/api/v1/items/parent",
                "/api/v1/locations",
                "/api/v1/users",
                "/api/v1/reports",
            ]
        )
    )

    return {"error_type": error_type, "endpoint": endpoint}


@st.composite
def valid_user_data(draw):
    """Generate valid user data for authentication."""
    user_id = draw(st.uuids())
    username = draw(
        st.text(
            min_size=3,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )
    role = draw(st.sampled_from(["admin", "manager", "user"]))
    return {"user_id": str(user_id), "username": username, "role": role}


class TestAPIErrorResponseConsistencyProperties:
    """Property-based tests for API error response consistency."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @given(error_data=error_scenario_data())
    @settings(max_examples=10)
    def test_api_error_response_consistency_property(self, error_data):
        """
        Property 15: API Error Response Consistency

        For any failed API request, appropriate HTTP status codes and
        descriptive error messages should be returned.

        **Validates: Requirements 7.4**
        """
        endpoint = error_data["endpoint"]
        error_type = error_data["error_type"]

        if error_type == "authentication_error":
            # Test authentication error response consistency
            response = self.client.get(endpoint)

            # Should return 401 status code
            assert response.status_code == 401

            # Should have consistent error structure
            error_data = response.json()
            assert "error" in error_data
            assert "code" in error_data["error"]
            assert "message" in error_data["error"]
            assert "timestamp" in error_data["error"]
            assert "request_id" in error_data["error"]

            # Should have appropriate error code
            assert error_data["error"]["code"] == "AUTHENTICATION_REQUIRED"

            # Should have descriptive message
            assert len(error_data["error"]["message"]) > 0
            assert isinstance(error_data["error"]["message"], str)

            # Should have valid timestamp
            assert isinstance(error_data["error"]["timestamp"], (int, float))
            assert error_data["error"]["timestamp"] > 0

            # Should have request ID
            assert isinstance(error_data["error"]["request_id"], int)

        elif error_type == "service_unavailable":
            # Mock service unavailable scenario
            with patch("httpx.AsyncClient.request") as mock_request:
                mock_request.side_effect = Exception("Connection refused")

                # Create valid token for authentication
                token_payload = {
                    "sub": "test-user",
                    "username": "test",
                    "role": "user",
                }
                valid_token = create_access_token(token_payload)
                headers = {"Authorization": f"Bearer {valid_token}"}

                response = self.client.get(endpoint, headers=headers)

                # Should return 500 status code for internal server error
                assert response.status_code == 500

                # Should have consistent error structure
                error_data = response.json()
                assert "error" in error_data
                assert "code" in error_data["error"]
                assert "message" in error_data["error"]
                assert "timestamp" in error_data["error"]
                assert "request_id" in error_data["error"]

                # Should have appropriate error code
                assert error_data["error"]["code"] == "INTERNAL_SERVER_ERROR"

        elif error_type == "invalid_service":
            # Test invalid service endpoint
            invalid_endpoint = "/api/v1/invalid_service/test"

            # Create valid token for authentication
            token_payload = {
                "sub": "test-user",
                "username": "test",
                "role": "user",
            }
            valid_token = create_access_token(token_payload)
            headers = {"Authorization": f"Bearer {valid_token}"}

            response = self.client.get(invalid_endpoint, headers=headers)

            # Should return 404 status code
            assert response.status_code == 404

            # Should have consistent error structure
            error_data = response.json()
            assert "error" in error_data
            assert "code" in error_data["error"]
            assert "message" in error_data["error"]
            assert "timestamp" in error_data["error"]
            assert "request_id" in error_data["error"]

            # Should have appropriate error code
            assert error_data["error"]["code"] == "SERVICE_NOT_FOUND"

    @given(user_data=valid_user_data())
    @settings(max_examples=10)
    def test_rate_limit_error_consistency(self, user_data):
        """
        Property: Rate limit errors should have consistent format

        For any rate limit exceeded scenario, the error response should follow the standard format.
        """
        # Create valid token
        token_payload = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "role": user_data["role"],
        }
        valid_token = create_access_token(token_payload)
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Mock rate limit middleware to trigger rate limit
        with patch(
            "services.api_gateway.middleware.rate_limit_middleware.RateLimitMiddleware._is_rate_limited"
        ) as mock_rate_limit:
            mock_rate_limit.return_value = True

            response = self.client.get("/api/v1/items/parent", headers=headers)

            # Should return 429 status code
            assert response.status_code == 429

            # Should have consistent error structure
            error_data = response.json()
            assert "error" in error_data
            assert "code" in error_data["error"]
            assert "message" in error_data["error"]
            assert "timestamp" in error_data["error"]
            assert "request_id" in error_data["error"]

            # Should have appropriate error code
            assert error_data["error"]["code"] == "RATE_LIMIT_EXCEEDED"

            # Should have descriptive message about rate limiting
            assert "rate limit" in error_data["error"]["message"].lower()

    @given(user_data=valid_user_data())
    @settings(max_examples=10)
    def test_service_timeout_error_consistency(self, user_data):
        """
        Property: Service timeout errors should have consistent format

        For any service timeout scenario, the error response should follow the standard format.
        """
        # Create valid token
        token_payload = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "role": user_data["role"],
        }
        valid_token = create_access_token(token_payload)
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Mock service timeout scenario
        import httpx

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Request timeout")

            response = self.client.get("/api/v1/items/parent", headers=headers)

            # Should return 504 status code
            assert response.status_code == 504

            # Should have consistent error structure
            error_data = response.json()
            assert "error" in error_data
            assert "code" in error_data["error"]
            assert "message" in error_data["error"]
            assert "timestamp" in error_data["error"]
            assert "request_id" in error_data["error"]

            # Should have appropriate error code
            assert error_data["error"]["code"] == "SERVICE_TIMEOUT"

            # Should have descriptive message about timeout
            assert "timeout" in error_data["error"]["message"].lower()

    @given(user_data=valid_user_data())
    @settings(max_examples=10)
    def test_service_unavailable_error_consistency(self, user_data):
        """
        Property: Service unavailable errors should have consistent format

        For any service unavailable scenario, the error response should follow the standard format.
        """
        # Create valid token
        token_payload = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "role": user_data["role"],
        }
        valid_token = create_access_token(token_payload)
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Mock service unavailable scenario
        import httpx

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_request.side_effect = httpx.ConnectError("Connection failed")

            response = self.client.get("/api/v1/items/parent", headers=headers)

            # Should return 503 status code
            assert response.status_code == 503

            # Should have consistent error structure
            error_data = response.json()
            assert "error" in error_data
            assert "code" in error_data["error"]
            assert "message" in error_data["error"]
            assert "timestamp" in error_data["error"]
            assert "request_id" in error_data["error"]

            # Should have appropriate error code
            assert error_data["error"]["code"] == "SERVICE_UNAVAILABLE"

            # Should have descriptive message about unavailability
            assert "unavailable" in error_data["error"]["message"].lower()

    def test_error_response_structure_consistency(self):
        """
        Property: All error responses should have the same structure

        For any error response, the structure should be consistent across all error types.
        """
        # Test different error scenarios and verify structure consistency
        error_responses = []

        # Authentication error
        response = self.client.get("/api/v1/items/parent")
        error_responses.append(response.json())

        # Invalid endpoint error
        token_payload = {
            "sub": "test-user",
            "username": "test",
            "role": "user",
        }
        valid_token = create_access_token(token_payload)
        headers = {"Authorization": f"Bearer {valid_token}"}

        response = self.client.get("/api/v1/nonexistent", headers=headers)
        error_responses.append(response.json())

        # Verify all error responses have the same structure
        required_fields = ["error"]
        required_error_fields = ["code", "message", "timestamp", "request_id"]

        for error_response in error_responses:
            # Check top-level structure
            for field in required_fields:
                assert field in error_response, f"Missing field: {field}"

            # Check error object structure
            error_obj = error_response["error"]
            for field in required_error_fields:
                assert field in error_obj, f"Missing error field: {field}"

            # Check field types
            assert isinstance(error_obj["code"], str)
            assert isinstance(error_obj["message"], str)
            assert isinstance(error_obj["timestamp"], (int, float))
            assert isinstance(error_obj["request_id"], int)

            # Check field constraints
            assert len(error_obj["code"]) > 0
            assert len(error_obj["message"]) > 0
            assert error_obj["timestamp"] > 0

    @given(
        invalid_token=st.text(min_size=1, max_size=100),
        endpoint=st.sampled_from(
            ["/api/v1/items/parent", "/api/v1/locations", "/api/v1/users"]
        ),
    )
    @settings(max_examples=10)
    def test_invalid_token_error_consistency(self, invalid_token, endpoint):
        """
        Property: Invalid token errors should have consistent format

        For any invalid token scenario, the error response should follow the standard format.
        """
        # Ensure we have a clearly invalid token
        if invalid_token.startswith("Bearer "):
            invalid_token = invalid_token[7:]  # Remove Bearer prefix if present

        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = self.client.get(endpoint, headers=headers)

        # Should return 401 status code
        assert response.status_code == 401

        # Should have consistent error structure
        error_data = response.json()
        assert "error" in error_data
        assert "code" in error_data["error"]
        assert "message" in error_data["error"]
        assert "timestamp" in error_data["error"]
        assert "request_id" in error_data["error"]

        # Should have appropriate error code
        assert error_data["error"]["code"] == "INVALID_TOKEN"

        # Should have descriptive message about invalid token
        assert "token" in error_data["error"]["message"].lower()
        assert (
            "invalid" in error_data["error"]["message"].lower()
            or "expired" in error_data["error"]["message"].lower()
        )
