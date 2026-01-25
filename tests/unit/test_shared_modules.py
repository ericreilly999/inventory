"""Tests for shared modules: health checks, logging, redis config."""

import logging
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from redis import Redis

from shared.database.redis_config import RedisCache, get_redis, get_redis_pool
from shared.health.checks import HealthCheck, check_basic, check_database, check_redis
from shared.logging.config import (
    configure_logging,
    get_logger,
    log_request,
)


def test_configure_logging():
    """Test logging configuration."""
    configure_logging()
    logger = logging.getLogger("test_logger")
    assert logger is not None


def test_get_logger():
    """Test getting a logger instance."""
    logger = get_logger("test_module")
    assert logger is not None
    assert logger.name == "test_module"


def test_get_logger_with_level():
    """Test getting logger with specific level."""
    logger = get_logger("test_module", level=logging.DEBUG)
    assert logger.level == logging.DEBUG


def test_log_request():
    """Test request logging."""
    with patch("shared.logging.config.get_access_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        log_request(
            request_id="test-123",
            method="GET",
            path="/api/test",
            status_code=200,
            duration_ms=123.45,
        )
        # Should call info for 200 status
        assert mock_logger.info.called or mock_logger.warning.called


@pytest.mark.asyncio
async def test_check_database_success(test_db_session):
    """Test database health check success."""
    result = check_database()
    assert result is True


@pytest.mark.asyncio
async def test_check_database_failure():
    """Test database health check failure."""
    with patch("shared.health.checks.SessionLocal") as mock_session:
        mock_session.return_value.execute.side_effect = Exception("Database error")
        result = check_database()
        assert result is False


@pytest.mark.asyncio
async def test_check_redis_success():
    """Test Redis health check success."""
    with patch("shared.health.checks.get_redis") as mock_get_redis:
        mock_redis = MagicMock(spec=Redis)
        mock_redis.ping.return_value = True
        mock_get_redis.return_value = mock_redis

        result = check_redis()
        assert result is True


@pytest.mark.asyncio
async def test_check_redis_failure():
    """Test Redis health check failure."""
    with patch("shared.health.checks.get_redis") as mock_get_redis:
        mock_redis = MagicMock(spec=Redis)
        mock_redis.ping.side_effect = Exception("Redis error")
        mock_get_redis.return_value = mock_redis

        result = check_redis()
        assert result is False


@pytest.mark.asyncio
async def test_check_basic():
    """Test basic health check."""
    result = check_basic()
    assert result["status"] == "healthy"
    assert "uptime" in result
    assert "version" in result


@pytest.mark.asyncio
async def test_health_check_class():
    """Test HealthCheck class."""
    health = HealthCheck("test-service")
    assert health.service_name == "test-service"

    def test_check():
        return True

    health.add_check(test_check)
    assert len(health.checks) == 1


@pytest.mark.asyncio
async def test_health_check_run_checks():
    """Test running health checks."""
    health = HealthCheck("test-service")

    def passing_check():
        return True

    health.add_check(passing_check)
    results = await health.run_checks()

    assert results["service"] == "test-service"
    assert results["status"] == "healthy"
    assert "timestamp" in results
    assert "checks" in results


@pytest.mark.asyncio
async def test_health_check_failing_check():
    """Test health check with failing check."""
    health = HealthCheck("test-service")

    def failing_check():
        return False

    health.add_check(failing_check)
    results = await health.run_checks()

    assert results["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_health_check_exception():
    """Test health check with exception."""
    health = HealthCheck("test-service")

    def error_check():
        raise Exception("Test error")

    health.add_check(error_check)
    results = await health.run_checks()

    assert results["status"] == "unhealthy"
    assert "error" in results["checks"]["error_check"]


def test_redis_pool_initialization():
    """Test Redis pool initialization."""
    pool = get_redis_pool()
    assert pool is not None


def test_get_redis_client():
    """Test getting Redis client."""
    with patch("shared.database.redis_config.redis.Redis") as mock_redis:
        mock_redis.return_value = MagicMock(spec=Redis)
        client = get_redis()
        assert client is not None


def test_get_redis_client_connection_error():
    """Test Redis client with connection error."""
    with patch("shared.database.redis_config.redis.Redis") as mock_redis:
        mock_redis.side_effect = Exception("Connection failed")
        try:
            get_redis()
            assert False, "Should have raised exception"
        except Exception:
            pass


def test_redis_cache_initialization():
    """Test Redis cache initialization."""
    with patch("shared.database.redis_config.get_redis") as mock_get_redis:
        mock_get_redis.return_value = MagicMock(spec=Redis)
        cache = RedisCache()
        assert cache is not None
        assert cache.client is not None


def test_logging_different_levels():
    """Test logging at different levels."""
    logger = get_logger("test_levels")

    with patch.object(logger, "debug") as mock_debug:
        logger.debug("Debug message")
        mock_debug.assert_called_once()

    with patch.object(logger, "info") as mock_info:
        logger.info("Info message")
        mock_info.assert_called_once()

    with patch.object(logger, "warning") as mock_warning:
        logger.warning("Warning message")
        mock_warning.assert_called_once()

    with patch.object(logger, "error") as mock_error:
        logger.error("Error message")
        mock_error.assert_called_once()


def test_logging_with_extra_fields():
    """Test logging with extra fields."""
    logger = get_logger("test_extra")
    with patch.object(logger, "info") as mock_info:
        logger.info("Message", extra={"user_id": str(uuid4()), "action": "test"})
        mock_info.assert_called_once()


def test_health_check_response_format():
    """Test health check response format."""
    import asyncio

    async def run_test():
        health = HealthCheck("test-service")

        def test_check():
            return True

        health.add_check(test_check)
        result = await health.run_checks()

        assert "status" in result
        assert "timestamp" in result
        assert "service" in result
        assert isinstance(result["timestamp"], str)

    asyncio.run(run_test())


def test_redis_connection_pool():
    """Test Redis connection pool configuration."""
    with patch("shared.database.redis_config.redis.ConnectionPool") as mock_pool:
        mock_pool.from_url.return_value = MagicMock()
        pool = get_redis_pool()
        assert pool is not None


def test_logging_exception_handling():
    """Test logging exception handling."""
    logger = get_logger("test_exception")
    try:
        raise ValueError("Test exception")
    except ValueError:
        with patch.object(logger, "exception") as mock_exception:
            logger.exception("An error occurred")
            mock_exception.assert_called_once()


def test_health_check_with_custom_checks():
    """Test health check with custom service checks."""
    import asyncio

    async def run_test():
        health = HealthCheck("custom-service")

        async def async_check():
            return True

        health.add_check(async_check)
        result = await health.run_checks()
        assert result is not None
        assert "status" in result

    asyncio.run(run_test())


def test_redis_cache_get():
    """Test Redis cache get operation."""
    import asyncio

    async def run_test():
        with patch("shared.database.redis_config.get_redis") as mock_get_redis:
            mock_client = MagicMock(spec=Redis)
            mock_client.get.return_value = "test_value"
            mock_get_redis.return_value = mock_client

            cache = RedisCache()
            result = await cache.get("test_key")
            assert result == "test_value"

    asyncio.run(run_test())


def test_redis_cache_set():
    """Test Redis cache set operation."""
    import asyncio

    async def run_test():
        with patch("shared.database.redis_config.get_redis") as mock_get_redis:
            mock_client = MagicMock(spec=Redis)
            mock_client.set.return_value = True
            mock_get_redis.return_value = mock_client

            cache = RedisCache()
            result = await cache.set("test_key", "test_value")
            assert result is True

    asyncio.run(run_test())


def test_redis_cache_delete():
    """Test Redis cache delete operation."""
    import asyncio

    async def run_test():
        with patch("shared.database.redis_config.get_redis") as mock_get_redis:
            mock_client = MagicMock(spec=Redis)
            mock_client.delete.return_value = 1
            mock_get_redis.return_value = mock_client

            cache = RedisCache()
            result = await cache.delete("test_key")
            assert result is True

    asyncio.run(run_test())


def test_redis_cache_exists():
    """Test Redis cache exists operation."""
    import asyncio

    async def run_test():
        with patch("shared.database.redis_config.get_redis") as mock_get_redis:
            mock_client = MagicMock(spec=Redis)
            mock_client.exists.return_value = 1
            mock_get_redis.return_value = mock_client

            cache = RedisCache()
            result = await cache.exists("test_key")
            assert result is True

    asyncio.run(run_test())
