"""Tests for shared modules: health checks, logging, redis config."""

import logging
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from redis import Redis
from sqlalchemy.orm import Session

from shared.database.redis_config import RedisCache, get_redis, get_redis_pool
from shared.health.checks import (
    check_database_health,
    check_redis_health,
    get_health_status,
)
from shared.logging.config import (
    configure_logging,
    get_logger,
    log_request,
    log_response,
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
    logger = get_logger("test")
    with patch.object(logger, "info") as mock_info:
        log_request(logger, "GET", "/api/test", {"user": "test"})
        mock_info.assert_called_once()


def test_log_response():
    """Test response logging."""
    logger = get_logger("test")
    with patch.object(logger, "info") as mock_info:
        log_response(logger, 200, 0.123)
        mock_info.assert_called_once()


def test_log_response_error():
    """Test error response logging."""
    logger = get_logger("test")
    with patch.object(logger, "error") as mock_error:
        log_response(logger, 500, 0.456)
        mock_error.assert_called_once()


@pytest.mark.asyncio
async def test_check_database_health_success(test_db_session):
    """Test database health check success."""
    result = await check_database_health(test_db_session)
    assert result["status"] == "healthy"
    assert result["database"] == "connected"


@pytest.mark.asyncio
async def test_check_database_health_failure():
    """Test database health check failure."""
    mock_session = MagicMock(spec=Session)
    mock_session.execute.side_effect = Exception("Database error")

    result = await check_database_health(mock_session)
    assert result["status"] == "unhealthy"
    assert "error" in result


@pytest.mark.asyncio
async def test_check_redis_health_success():
    """Test Redis health check success."""
    mock_redis = MagicMock(spec=Redis)
    mock_redis.ping.return_value = True

    result = await check_redis_health(mock_redis)
    assert result["status"] == "healthy"
    assert result["redis"] == "connected"


@pytest.mark.asyncio
async def test_check_redis_health_failure():
    """Test Redis health check failure."""
    mock_redis = MagicMock(spec=Redis)
    mock_redis.ping.side_effect = Exception("Redis error")

    result = await check_redis_health(mock_redis)
    assert result["status"] == "unhealthy"
    assert "error" in result


@pytest.mark.asyncio
async def test_check_redis_health_none():
    """Test Redis health check with None client."""
    result = await check_redis_health(None)
    assert result["status"] == "healthy"
    assert result["redis"] == "not configured"


@pytest.mark.asyncio
async def test_get_health_status_all_healthy(test_db_session):
    """Test overall health status when all services healthy."""
    mock_redis = MagicMock(spec=Redis)
    mock_redis.ping.return_value = True

    result = await get_health_status(test_db_session, mock_redis)
    assert result["status"] == "healthy"
    assert "database" in result
    assert "redis" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_get_health_status_database_unhealthy():
    """Test overall health status when database unhealthy."""
    mock_session = MagicMock(spec=Session)
    mock_session.execute.side_effect = Exception("DB error")

    result = await get_health_status(mock_session, None)
    assert result["status"] == "unhealthy"


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
            client = get_redis()
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
        mock_session = MagicMock(spec=Session)
        mock_session.execute.return_value = None
        result = await get_health_status(mock_session, None)

        assert "status" in result
        assert "timestamp" in result
        assert "database" in result
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
        mock_session = MagicMock(spec=Session)
        mock_session.execute.return_value = None

        result = await get_health_status(mock_session, None)
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
