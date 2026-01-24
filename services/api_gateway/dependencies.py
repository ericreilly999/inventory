"""Dependencies for API Gateway service."""

from typing import AsyncGenerator

import httpx

from shared.logging.config import get_logger

logger = get_logger(__name__)


async def get_service_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Get HTTP client for microservice communication."""
    async with httpx.AsyncClient() as client:
        yield client
