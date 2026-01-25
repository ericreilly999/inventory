"""Tests for configuration and utility modules."""

import os
from unittest.mock import patch

from shared.config.settings import Settings, settings
from shared.database.config import get_db
from shared.logging.config import (
    add_request_context,
    configure_logging,
    get_logger,
    log_error,
    log_request,
)


# Test Settings
def test_settings_defaults():
    """Test default settings values."""
    # Settings will use environment variables if set, so check actual values
    assert settings.environment in ["development", "test", "production"]
    assert isinstance(settings.debug, bool)
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]


def test_settings_database_property():
    """Test database settings property."""
    assert hasattr(settings, "database")
    assert hasattr(settings.database, "url")
    assert hasattr(settings.database, "pool_size")


def test_settings_redis_property():
    """Test redis settings property."""
    assert hasattr(settings, "redis")
    assert hasattr(settings.redis, "url")


def test_settings_auth_property():
    """Test auth settings property."""
    assert hasattr(settings, "auth")
    assert hasattr(settings.auth, "jwt_secret_key")
    assert hasattr(settings.auth, "jwt_algorithm")


def test_settings_logging_property():
    """Test logging settings property."""
    assert hasattr(settings, "logging")
    assert hasattr(settings.logging, "level")
    assert hasattr(settings.logging, "format")


def test_settings_monitoring_property():
    """Test monitoring settings property."""
    assert hasattr(settings, "monitoring")
    assert hasattr(settings.monitoring, "prometheus_port")


def test_settings_api_property():
    """Test API settings property."""
    assert hasattr(settings, "api")
    assert hasattr(settings.api, "title")
    assert hasattr(settings.api, "cors_origins")


# Test Database Config
def test_get_db_generator():
    """Test get_db returns a generator."""
    db_gen = get_db()
    assert hasattr(db_gen, "__next__")


def test_get_db_yields_session():
    """Test get_db yields a session."""
    db_gen = get_db()
    try:
        session = next(db_gen)
        assert session is not None
    except StopIteration:
        pass
    finally:
        try:
            db_gen.close()
        except Exception:
            pass


# Test Logging Config
def test_configure_logging():
    """Test logging configuration."""
    # Should not raise any errors
    configure_logging()


def test_get_logger():
    """Test getting a logger."""
    logger = get_logger("test_module")
    assert logger is not None


def test_add_request_context():
    """Test adding request context."""
    context = add_request_context(
        request_id="test-123",
        user_id="user-456",
        method="GET",
        path="/api/test",
        status_code=200,
        duration_ms=150.5,
    )

    assert context["request_id"] == "test-123"
    assert context["user_id"] == "user-456"
    assert context["method"] == "GET"
    assert context["path"] == "/api/test"
    assert context["status_code"] == 200
    assert context["duration_ms"] == 150.5


def test_add_request_context_minimal():
    """Test adding minimal request context."""
    context = add_request_context(request_id="test-123")

    assert context["request_id"] == "test-123"
    assert "service" in context
    assert "environment" in context


def test_log_request():
    """Test logging HTTP request."""
    # Should not raise errors
    log_request(
        request_id="test-123",
        method="POST",
        path="/api/items",
        status_code=201,
        duration_ms=250.0,
        user_id="user-789",
    )


def test_log_request_error_status():
    """Test logging HTTP request with error status."""
    # Should not raise errors
    log_request(
        request_id="test-456",
        method="GET",
        path="/api/items/999",
        status_code=404,
        duration_ms=50.0,
    )


def test_log_error():
    """Test logging errors."""
    error = ValueError("Test error message")

    # Should not raise errors
    log_error(
        error=error,
        request_id="test-789",
        user_id="user-123",
        additional_context={"action": "test_action"},
    )


def test_log_error_minimal():
    """Test logging error with minimal info."""
    error = RuntimeError("Minimal error")

    # Should not raise errors
    log_error(error=error)


# Test Environment Variables
@patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"})
def test_database_url_from_env():
    """Test reading database URL from environment."""
    test_settings = Settings()
    assert "postgresql" in test_settings.database_url


@patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
def test_log_level_from_env():
    """Test reading log level from environment."""
    test_settings = Settings()
    assert test_settings.log_level == "DEBUG"


@patch.dict(os.environ, {"ENVIRONMENT": "production"})
def test_environment_from_env():
    """Test reading environment from environment variable."""
    test_settings = Settings()
    assert test_settings.environment == "production"


# Test Settings Validation
def test_settings_jwt_expiration():
    """Test JWT expiration setting."""
    assert settings.jwt_expiration_hours > 0


def test_settings_database_pool_size():
    """Test database pool size setting."""
    assert settings.database_pool_size > 0


def test_settings_redis_timeout():
    """Test Redis timeout settings."""
    assert settings.redis_socket_timeout > 0
    assert settings.redis_socket_connect_timeout > 0


# Test Logging Levels
def test_logger_info():
    """Test logger info level."""
    logger = get_logger("test")
    # Should not raise errors
    logger.info("Test info message", extra_field="value")


def test_logger_error():
    """Test logger error level."""
    logger = get_logger("test")
    # Should not raise errors
    logger.error("Test error message", error_code=500)


def test_logger_warning():
    """Test logger warning level."""
    logger = get_logger("test")
    # Should not raise errors
    logger.warning("Test warning message")


def test_logger_debug():
    """Test logger debug level."""
    logger = get_logger("test")
    # Should not raise errors
    logger.debug("Test debug message")


# Test Configuration Edge Cases
def test_settings_cors_origins():
    """Test settings CORS origins."""
    # CORS origins should be a list
    assert isinstance(settings.cors_origins, list)


def test_settings_rate_limit():
    """Test rate limit settings."""
    assert settings.rate_limit_requests > 0
    assert settings.rate_limit_window > 0


# Test Database Connection
def test_database_engine_exists():
    """Test database engine is created."""
    from shared.database.config import engine

    assert engine is not None


def test_session_local_exists():
    """Test SessionLocal is created."""
    from shared.database.config import SessionLocal

    assert SessionLocal is not None


# Test Metadata
def test_database_metadata_exists():
    """Test database metadata exists."""
    from shared.database.config import metadata

    assert metadata is not None


def test_base_metadata_exists():
    """Test Base metadata exists."""
    from shared.models.base import Base

    assert Base.metadata is not None


# Test Model Imports
def test_all_models_imported():
    """Test all models are properly imported."""
    from shared.models.assignment_history import AssignmentHistory
    from shared.models.item import ChildItem, ItemType, ParentItem
    from shared.models.location import Location, LocationType
    from shared.models.move_history import MoveHistory
    from shared.models.user import Role, User

    assert AssignmentHistory is not None
    assert ChildItem is not None
    assert ItemType is not None
    assert ParentItem is not None
    assert Location is not None
    assert LocationType is not None
    assert MoveHistory is not None
    assert Role is not None
    assert User is not None
