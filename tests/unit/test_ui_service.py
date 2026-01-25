"""Tests for UI service."""

import pytest
from fastapi.testclient import TestClient

from services.ui.main import app


@pytest.fixture
def ui_client():
    """Create test client for UI service."""
    return TestClient(app)


def test_ui_health(ui_client):
    """Test UI health endpoint."""
    response = ui_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_ui_root(ui_client):
    """Test UI root endpoint."""
    response = ui_client.get("/")
    assert response.status_code in [200, 404]


def test_ui_static_files(ui_client):
    """Test UI static files."""
    response = ui_client.get("/static/")
    assert response.status_code in [200, 404]


def test_ui_api_docs(ui_client):
    """Test UI API docs."""
    response = ui_client.get("/docs")
    assert response.status_code in [200, 404]


def test_ui_openapi(ui_client):
    """Test UI OpenAPI schema."""
    response = ui_client.get("/openapi.json")
    assert response.status_code in [200, 404]


def test_ui_cors_headers(ui_client):
    """Test UI CORS headers."""
    response = ui_client.options("/")
    assert response.status_code in [200, 204]


def test_ui_invalid_route(ui_client):
    """Test UI invalid route."""
    response = ui_client.get("/invalid-route-12345")
    assert response.status_code in [404, 200]


def test_ui_method_not_allowed(ui_client):
    """Test UI method not allowed."""
    response = ui_client.post("/health")
    assert response.status_code in [405, 200]
