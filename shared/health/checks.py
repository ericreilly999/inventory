"""Health check utilities for microservices."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text

from shared.database.config import SessionLocal
from shared.database.redis_config import get_redis
from shared.logging.config import get_logger

logger = get_logger(__name__)


class HealthCheck:
    """Health check utility class."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: List[callable] = []

    def add_check(self, check_func: callable) -> None:
        """Add a health check function."""
        self.checks.append(check_func)

    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {
            "service": self.service_name,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }

        for check in self.checks:
            try:
                check_name = check.__name__
                check_result = (
                    await check()
                    if asyncio.iscoroutinefunction(check)
                    else check()
                )
                results["checks"][check_name] = {
                    "status": "healthy" if check_result else "unhealthy",
                    "details": (
                        check_result if isinstance(check_result, dict) else {}
                    ),
                }

                if not check_result:
                    results["status"] = "unhealthy"

            except Exception as e:
                logger.error(
                    f"Health check {check.__name__} failed", error=str(e)
                )
                results["checks"][check.__name__] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                results["status"] = "unhealthy"

        return results


def check_database() -> bool:
    """Check database connectivity."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.debug("Database health check passed")
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


def check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        redis_client = get_redis()
        redis_client.ping()
        logger.debug("Redis health check passed")
        return True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False


def check_basic() -> Dict[str, Any]:
    """Basic service health check."""
    return {"status": "healthy", "uptime": "running", "version": "1.0.0"}
