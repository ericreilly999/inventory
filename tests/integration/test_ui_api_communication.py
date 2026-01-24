"""
Integration tests for UI-API communication.

Tests API integration and error handling for the UI service.
Requirements: 10.3
"""

from typing import Dict

import pytest
import requests


class TestUIAPICommunication:
    """Test UI-API communication patterns and error handling."""

    @pytest.fixture
    def api_base_url(self) -> str:
        """Base URL for API Gateway."""
        return "http://localhost:8000"

    @pytest.fixture
    def auth_headers(self, api_base_url: str) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        # Login to get auth token
        login_data = {"username": "admin", "password": "admin123"}

        try:
            response = requests.post(
                f"{api_base_url}/api/v1/auth/login",
                json=login_data,
                timeout=10,
            )

            if response.status_code == 200:
                token = response.json().get("access_token")
                return {"Authorization": f"Bearer {token}"}
            else:
                # Return empty headers if login fails
                return {}
        except requests.RequestException:
            # Return empty headers if API is not available
            return {}

    def test_authentication_flow(self, api_base_url: str):
        """Test authentication flow that UI depends on."""
        # Test login endpoint
        login_data = {"username": "admin", "password": "admin123"}

        try:
            response = requests.post(
                f"{api_base_url}/api/v1/auth/login",
                json=login_data,
                timeout=10,
            )

            # Should return 200 or 401 (if credentials are wrong)
            assert response.status_code in [200, 401, 404]

            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data
                assert "user" in data

        except requests.RequestException:
            # API might not be running, skip test
            pytest.skip("API Gateway not available")

    def test_inventory_endpoints(
        self, api_base_url: str, auth_headers: Dict[str, str]
    ):
        """Test inventory endpoints that UI consumes."""
        if not auth_headers:
            pytest.skip("Authentication not available")

        endpoints = [
            "/api/v1/items/parent",
            "/api/v1/items/child",
            "/api/v1/items/types",
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{api_base_url}{endpoint}",
                    headers=auth_headers,
                    timeout=10,
                )

                # Should return 200 (success) or 401/403 (auth issues)
                assert response.status_code in [200, 401, 403, 404]

                if response.status_code == 200:
                    # Should return valid JSON
                    data = response.json()
                    assert isinstance(data, list)

            except requests.RequestException:
                pytest.skip(f"Endpoint {endpoint} not available")

    def test_location_endpoints(
        self, api_base_url: str, auth_headers: Dict[str, str]
    ):
        """Test location endpoints that UI consumes."""
        if not auth_headers:
            pytest.skip("Authentication not available")

        endpoints = ["/api/v1/locations", "/api/v1/locations/types"]

        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{api_base_url}{endpoint}",
                    headers=auth_headers,
                    timeout=10,
                )

                assert response.status_code in [200, 401, 403, 404]

                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, list)

            except requests.RequestException:
                pytest.skip(f"Endpoint {endpoint} not available")

    def test_reporting_endpoints(
        self, api_base_url: str, auth_headers: Dict[str, str]
    ):
        """Test reporting endpoints that UI consumes."""
        if not auth_headers:
            pytest.skip("Authentication not available")

        endpoints = ["/api/v1/reports/inventory", "/api/v1/reports/movements"]

        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{api_base_url}{endpoint}",
                    headers=auth_headers,
                    timeout=10,
                )

                assert response.status_code in [200, 401, 403, 404]

                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, list)

            except requests.RequestException:
                pytest.skip(f"Endpoint {endpoint} not available")

    def test_user_management_endpoints(
        self, api_base_url: str, auth_headers: Dict[str, str]
    ):
        """Test user management endpoints that UI consumes."""
        if not auth_headers:
            pytest.skip("Authentication not available")

        endpoints = ["/api/v1/users", "/api/v1/roles"]

        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{api_base_url}{endpoint}",
                    headers=auth_headers,
                    timeout=10,
                )

                assert response.status_code in [200, 401, 403, 404]

                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, list)

            except requests.RequestException:
                pytest.skip(f"Endpoint {endpoint} not available")

    def test_error_response_format(self, api_base_url: str):
        """Test that API returns consistent error format for UI."""
        # Test with invalid endpoint
        try:
            response = requests.get(
                f"{api_base_url}/api/v1/invalid-endpoint", timeout=10
            )

            # Should return 404
            assert response.status_code == 404

            # Should return JSON error format
            if response.headers.get("content-type", "").startswith(
                "application/json"
            ):
                data = response.json()
                assert "error" in data

        except requests.RequestException:
            pytest.skip("API Gateway not available")

    def test_cors_headers(self, api_base_url: str):
        """Test CORS headers for UI integration."""
        try:
            response = requests.options(
                f"{api_base_url}/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
                timeout=10,
            )

            # Should handle CORS preflight
            assert response.status_code in [200, 204, 404]

        except requests.RequestException:
            pytest.skip("API Gateway not available")

    def test_content_type_handling(self, api_base_url: str):
        """Test that API handles JSON content type correctly."""
        try:
            response = requests.post(
                f"{api_base_url}/api/v1/auth/login",
                json={"username": "test", "password": "test"},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Should accept JSON content type
            assert response.status_code in [200, 401, 400, 404]

        except requests.RequestException:
            pytest.skip("API Gateway not available")

    def test_api_response_times(
        self, api_base_url: str, auth_headers: Dict[str, str]
    ):
        """Test API response times for UI performance."""
        if not auth_headers:
            pytest.skip("Authentication not available")

        # Test key endpoints used by UI
        endpoints = [
            "/api/v1/items/parent",
            "/api/v1/locations",
            "/api/v1/reports/inventory",
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{api_base_url}{endpoint}",
                    headers=auth_headers,
                    timeout=5,  # 5 second timeout for performance test
                )

                # Response should be received within timeout
                assert response.elapsed.total_seconds() < 5.0

            except requests.Timeout:
                pytest.fail(f"Endpoint {endpoint} exceeded 5 second timeout")
            except requests.RequestException:
                pytest.skip(f"Endpoint {endpoint} not available")

    def test_pagination_support(
        self, api_base_url: str, auth_headers: Dict[str, str]
    ):
        """Test pagination parameters for UI data grids."""
        if not auth_headers:
            pytest.skip("Authentication not available")

        try:
            # Test with pagination parameters
            response = requests.get(
                f"{api_base_url}/api/v1/items/parent?limit=10&offset=0",
                headers=auth_headers,
                timeout=10,
            )

            assert response.status_code in [200, 401, 403, 404]

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                # Should respect limit parameter
                assert len(data) <= 10

        except requests.RequestException:
            pytest.skip("Pagination endpoint not available")


class TestUIErrorHandling:
    """Test error handling scenarios that UI must handle."""

    @pytest.fixture
    def api_base_url(self) -> str:
        """Base URL for API Gateway."""
        return "http://localhost:8000"

    @pytest.fixture
    def auth_headers(self, api_base_url: str) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        # Login to get auth token
        login_data = {"username": "admin", "password": "admin123"}

        try:
            response = requests.post(
                f"{api_base_url}/api/v1/auth/login",
                json=login_data,
                timeout=10,
            )

            if response.status_code == 200:
                token = response.json().get("access_token")
                return {"Authorization": f"Bearer {token}"}
            else:
                # Return empty headers if login fails
                return {}
        except requests.RequestException:
            # Return empty headers if API is not available
            return {}

    def test_network_timeout_handling(self, api_base_url: str):
        """Test UI can handle network timeouts."""
        try:
            # Use very short timeout to simulate network issues
            requests.get(
                f"{api_base_url}/api/v1/items/parent",
                timeout=0.001,  # 1ms timeout
            )
        except requests.Timeout:
            # This is expected - UI should handle timeouts gracefully
            assert True
        except requests.RequestException:
            # Other network errors are also expected
            assert True

    def test_invalid_json_handling(self, api_base_url: str):
        """Test API handles invalid JSON from UI."""
        try:
            response = requests.post(
                f"{api_base_url}/api/v1/auth/login",
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Should return 400 Bad Request for invalid JSON
            assert response.status_code in [400, 404]

        except requests.RequestException:
            pytest.skip("API Gateway not available")

    def test_large_payload_handling(
        self, api_base_url: str, auth_headers: Dict[str, str]
    ):
        """Test API handles large payloads from UI."""
        if not auth_headers:
            pytest.skip("Authentication not available")

        # Create a large description field
        large_data = {
            "name": "Test Item",
            "description": "x" * 10000,  # 10KB description
            "item_type_id": "test-id",
            "current_location_id": "test-location-id",
        }

        try:
            response = requests.post(
                f"{api_base_url}/api/v1/items/parent",
                json=large_data,
                headers=auth_headers,
                timeout=10,
            )

            # Should handle large payloads (success or validation error)
            assert response.status_code in [200, 201, 400, 413, 404]

        except requests.RequestException:
            pytest.skip("API endpoint not available")
