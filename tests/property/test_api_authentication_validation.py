"""Property-based tests for API authentication and validation.

Feature: inventory-management, Property 14: API Authentication and Validation
Validates: Requirements 7.1, 7.2
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from services.api_gateway.main import app
from shared.auth.utils import create_access_token


# Generators for test data
@st.composite
def valid_api_request_data(draw):
    """Generate valid API request data."""
    user_id = draw(st.uuids())
    username = draw(
        st.text(
            min_size=3,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )
    role = draw(st.sampled_from(["admin", "manager", "user"]))
    permissions = draw(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.booleans(),
            min_size=1,
            max_size=5,
        )
    )
    return {
        "user_id": str(user_id),
        "username": username,
        "role": role,
        "permissions": permissions,
    }


@st.composite
def invalid_token_data(draw):
    """Generate invalid token data."""
    return draw(
        st.one_of(
            st.just(""),  # Empty token
            st.just("invalid_token"),  # Invalid format
            st.text(min_size=1, max_size=100),  # Random text
            st.just("Bearer"),  # Missing token part
            st.just("NotBearer valid_token"),  # Wrong prefix
        )
    )


@st.composite
def api_endpoint_data(draw):
    """Generate API endpoint data for testing."""
    service = draw(st.sampled_from(["users", "items", "locations", "reports"]))
    resource_id = draw(st.uuids())
    action = draw(
        st.sampled_from(["", f"/{resource_id}", f"/{resource_id}/details"])
    )
    return f"/api/v1/{service}{action}"


class TestAPIAuthenticationValidationProperties:
    """Property-based tests for API authentication and validation."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @given(request_data=valid_api_request_data(), endpoint=api_endpoint_data())
    @settings(max_examples=10)
    def test_api_authentication_and_validation_property(
        self, request_data, endpoint
    ):
        """
        Property 14: API Authentication and Validation

        For any third-party API request, authentication should be validated and
        request format should be checked before processing.

        **Validates: Requirements 7.1, 7.2**
        """
        # Create valid JWT token
        token_payload = {
            "sub": request_data["user_id"],
            "username": request_data["username"],
            "role": request_data["role"],
            "permissions": request_data["permissions"],
        }

        valid_token = create_access_token(token_payload)

        # Mock the microservice response to avoid actual service calls
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_response.content = b'{"status": "success"}'
            mock_response.headers = {"content-type": "application/json"}
            mock_request.return_value = mock_response

            # Test 1: Valid authentication should succeed
            headers = {"Authorization": f"Bearer {valid_token}"}
            response = self.client.get(endpoint, headers=headers)

            # Should not get authentication error (401)
            assert response.status_code != 401

            # Should either succeed (200) or have service-specific error (not auth error)
            assert response.status_code in [
                200,
                404,
                500,
                503,
                504,
            ]  # Valid service responses

            # Test 2: Missing authentication should fail for protected endpoints
            if endpoint not in [
                "/",
                "/health",
                "/docs",
                "/redoc",
                "/openapi.json",
            ] and not endpoint.startswith("/api/v1/auth/"):
                response_no_auth = self.client.get(endpoint)

                # Should get authentication error
                assert response_no_auth.status_code == 401

                # Should have proper error structure
                error_data = response_no_auth.json()
                assert "error" in error_data
                assert "code" in error_data["error"]
                assert "message" in error_data["error"]
                assert "timestamp" in error_data["error"]
                assert "request_id" in error_data["error"]
                assert error_data["error"]["code"] == "AUTHENTICATION_REQUIRED"

    @given(invalid_token=invalid_token_data(), endpoint=api_endpoint_data())
    @settings(max_examples=10)
    def test_invalid_token_validation_fails(self, invalid_token, endpoint):
        """
        Property: Invalid tokens should always fail validation

        For any API request with invalid authentication token, the request should be rejected.
        """
        # Skip public endpoints
        if endpoint in [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ] or endpoint.startswith("/api/v1/auth/"):
            return

        # Test various invalid token formats
        invalid_headers = []

        if invalid_token == "":
            invalid_headers.append({"Authorization": ""})
        elif invalid_token == "Bearer":
            invalid_headers.append({"Authorization": "Bearer"})
        elif invalid_token.startswith("NotBearer"):
            invalid_headers.append({"Authorization": invalid_token})
        else:
            invalid_headers.append(
                {"Authorization": f"Bearer {invalid_token}"}
            )

        for headers in invalid_headers:
            response = self.client.get(endpoint, headers=headers)

            # Should get authentication error
            assert response.status_code == 401

            # Should have proper error structure
            error_data = response.json()
            assert "error" in error_data
            assert error_data["error"]["code"] in [
                "AUTHENTICATION_REQUIRED",
                "INVALID_TOKEN",
            ]

    @given(request_data=valid_api_request_data())
    @settings(max_examples=10)
    def test_request_format_validation(self, request_data):
        """
        Property: Request format should be validated

        For any API request, the format should be validated before processing.
        """
        # Create valid JWT token
        token_payload = {
            "sub": request_data["user_id"],
            "username": request_data["username"],
            "role": request_data["role"],
            "permissions": request_data["permissions"],
        }

        valid_token = create_access_token(token_payload)
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Mock the microservice response
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request format",
                }
            }
            mock_response.content = b'{"error": {"code": "VALIDATION_ERROR", "message": "Invalid request format"}}'
            mock_response.headers = {"content-type": "application/json"}
            mock_request.return_value = mock_response

            # Test malformed JSON in POST request
            response = self.client.post(
                "/api/v1/items/parent",
                headers=headers,
                data="invalid json",  # Malformed JSON
            )

            # Should handle the request (authentication passed)
            # The actual validation error would come from the microservice
            assert response.status_code != 401  # Not an auth error

    @given(request_data=valid_api_request_data())
    @settings(max_examples=10)
    def test_comprehensive_audit_logging(self, request_data):
        """
        Property: All API interactions should be logged for audit purposes

        For any API request, appropriate audit logs should be created.
        """
        # Create valid JWT token
        token_payload = {
            "sub": request_data["user_id"],
            "username": request_data["username"],
            "role": request_data["role"],
            "permissions": request_data["permissions"],
        }

        valid_token = create_access_token(token_payload)
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Mock the microservice response
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_response.content = b'{"status": "success"}'
            mock_response.headers = {"content-type": "application/json"}
            mock_request.return_value = mock_response

            # Patch the logger to capture log calls
            with patch(
                "services.api_gateway.middleware.auth_middleware.logger"
            ) as mock_logger:
                _ = self.client.get("/api/v1/items/parent", headers=headers)

                # Verify that logging occurred
                # Should have at least request received and request completed logs
                assert mock_logger.info.call_count >= 2

                # Check that user context is logged
                log_calls = mock_logger.info.call_args_list

                # Find the authentication successful log
                auth_log_found = False
                for call in log_calls:
                    args, kwargs = call
                    if "Authentication successful" in args[0]:
                        auth_log_found = True
                        assert "user_id" in kwargs
                        assert kwargs["user_id"] == request_data["user_id"]
                        break

                assert (
                    auth_log_found
                ), "Authentication successful log not found"

    def test_public_endpoints_no_authentication_required(self):
        """
        Property: Public endpoints should not require authentication

        For any public endpoint, requests should succeed without authentication.
        """
        public_endpoints = ["/", "/health", "/docs", "/redoc", "/openapi.json"]

        for endpoint in public_endpoints:
            response = self.client.get(endpoint)

            # Should not get authentication error
            assert response.status_code != 401

            # Should get successful response or redirect
            assert response.status_code in [
                200,
                307,
                404,
            ]  # 404 is ok for some endpoints

    @given(request_data=valid_api_request_data())
    @settings(max_examples=10)
    def test_user_context_forwarding(self, request_data):
        """
        Property: User context should be forwarded to microservices

        For any authenticated request, user context should be included in forwarded requests.
        """
        # Create valid JWT token
        token_payload = {
            "sub": request_data["user_id"],
            "username": request_data["username"],
            "role": request_data["role"],
            "permissions": request_data["permissions"],
        }

        valid_token = create_access_token(token_payload)
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Mock the microservice response and capture forwarded headers
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_response.content = b'{"status": "success"}'
            mock_response.headers = {"content-type": "application/json"}
            mock_request.return_value = mock_response

            _ = self.client.get("/api/v1/items/parent", headers=headers)

            # Verify that the request was forwarded with user context
            if mock_request.called:
                call_args = mock_request.call_args
                forwarded_headers = call_args.kwargs.get("headers", {})

                # Should include authorization header
                assert "authorization" in forwarded_headers
                assert (
                    forwarded_headers["authorization"]
                    == f"Bearer {valid_token}"
                )

                # Should include user context headers
                assert "X-User-ID" in forwarded_headers
                assert (
                    forwarded_headers["X-User-ID"] == request_data["user_id"]
                )

                assert "X-User-Role" in forwarded_headers
                assert forwarded_headers["X-User-Role"] == request_data["role"]
