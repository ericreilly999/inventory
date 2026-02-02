"""Logging configuration for the inventory management system."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from shared.config.settings import settings


def setup_file_logging() -> None:
    """Set up file-based logging for Docker containers."""
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)

    # Application log file
    app_log_file = log_dir / "application.log"

    # Error log file
    error_log_file = log_dir / "error.log"

    # Access log file
    access_log_file = log_dir / "access.log"

    # Configure file handlers
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    access_handler = logging.handlers.RotatingFileHandler(
        access_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    # Set log levels
    app_handler.setLevel(logging.INFO)
    error_handler.setLevel(logging.ERROR)
    access_handler.setLevel(logging.INFO)

    # Create formatters
    service_name = os.getenv("SERVICE_NAME", "unknown")
    environment = os.getenv("ENVIRONMENT", "development")
    json_format = (
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": "%(message)s", '
        f'"service": "{service_name}", "environment": "{environment}"}}'
    )
    json_formatter = logging.Formatter(json_format)

    app_handler.setFormatter(json_formatter)
    error_handler.setFormatter(json_formatter)
    access_handler.setFormatter(json_formatter)

    # Add handlers to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(app_handler)

    # Add error handler for error-level logs
    error_logger = logging.getLogger("error")
    error_logger.addHandler(error_handler)

    # Add access handler for access logs
    access_logger = logging.getLogger("access")
    access_logger.addHandler(access_handler)


def configure_logging() -> None:
    """Configure structured logging for the application."""

    # NOTE: Always log to stdout for CloudWatch compatibility
    # File logging is disabled to ensure logs are captured by CloudWatch
    # if os.getenv("ENVIRONMENT") in ["production", "staging"]:
    #     setup_file_logging()

    # Configure structlog processors based on environment
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add service and environment context
    def add_service_context(logger, method_name, event_dict):
        event_dict["service"] = os.getenv("SERVICE_NAME", "unknown")
        event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
        event_dict["container_id"] = os.getenv("HOSTNAME", "unknown")
        return event_dict

    processors.append(add_service_context)

    # Choose renderer based on environment
    if (
        os.getenv("ENVIRONMENT") in ["production", "staging"]
        or settings.logging.format == "json"
    ):
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging - ALWAYS to stdout for CloudWatch
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.logging.level.upper()),
        force=True,  # Force reconfiguration
    )

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)

    # Configure CloudWatch-friendly logging for AWS environments
    if os.getenv("AWS_DEFAULT_REGION"):
        configure_cloudwatch_logging()


def configure_cloudwatch_logging() -> None:
    """Configure logging for CloudWatch integration."""
    # CloudWatch expects structured JSON logs
    # This is handled by the JSON renderer in structlog

    # Set up CloudWatch-specific log groups
    service_name = os.getenv("SERVICE_NAME", "unknown")
    environment = os.getenv("ENVIRONMENT", "development")

    # Create logger for CloudWatch metrics
    cloudwatch_logger = logging.getLogger("cloudwatch")
    cloudwatch_logger.setLevel(logging.INFO)

    # Log startup information for CloudWatch
    startup_logger = get_logger("startup")
    startup_logger.info(
        "Service starting",
        service=service_name,
        environment=environment,
        log_group=f"/ecs/inventory-management/{service_name}",
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


def get_access_logger() -> structlog.stdlib.BoundLogger:
    """Get a logger for access logs."""
    return structlog.get_logger("access")


def get_error_logger() -> structlog.stdlib.BoundLogger:
    """Get a logger for error logs."""
    return structlog.get_logger("error")


def add_request_context(
    request_id: str,
    user_id: str = None,
    service_name: str = None,
    method: str = None,
    path: str = None,
    status_code: int = None,
    duration_ms: float = None,
) -> Dict[str, Any]:
    """Add request context to log entries."""
    context = {
        "request_id": request_id,
        "service": service_name or os.getenv("SERVICE_NAME", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }

    if user_id:
        context["user_id"] = user_id

    if method:
        context["method"] = method

    if path:
        context["path"] = path

    if status_code:
        context["status_code"] = status_code

    if duration_ms:
        context["duration_ms"] = duration_ms

    return context


def log_request(
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str = None,
) -> None:
    """Log HTTP request information."""
    logger = get_access_logger()

    context = add_request_context(
        request_id=request_id,
        user_id=user_id,
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
    )

    if status_code >= 400:
        logger.warning("HTTP request completed with error", **context)
    else:
        logger.info("HTTP request completed", **context)


def log_error(
    error: Exception,
    request_id: str = None,
    user_id: str = None,
    additional_context: Dict[str, Any] = None,
) -> None:
    """Log error information."""
    logger = get_error_logger()

    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "service": os.getenv("SERVICE_NAME", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }

    if request_id:
        context["request_id"] = request_id

    if user_id:
        context["user_id"] = user_id

    if additional_context:
        context.update(additional_context)

    logger.error("Application error occurred", exc_info=error, **context)
