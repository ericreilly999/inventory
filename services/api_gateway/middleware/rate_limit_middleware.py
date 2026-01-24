"""Rate limiting middleware for API Gateway."""

import time
from typing import Callable, Dict

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.config.settings import settings
from shared.logging.config import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting."""

    def __init__(self, app):
        super().__init__(app)
        # In-memory rate limit storage (in production, use Redis)
        self.rate_limit_storage: Dict[str, Dict[str, float]] = {}
        self.requests_per_window = settings.api.rate_limit_requests
        self.window_seconds = settings.api.rate_limit_window

    def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Use user ID if authenticated, otherwise use IP address
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _is_rate_limited(self, client_key: str) -> bool:
        """Check if client is rate limited."""
        current_time = time.time()

        # Initialize client data if not exists
        if client_key not in self.rate_limit_storage:
            self.rate_limit_storage[client_key] = {
                "requests": 0,
                "window_start": current_time,
            }

        client_data = self.rate_limit_storage[client_key]

        # Reset window if expired
        if current_time - client_data["window_start"] >= self.window_seconds:
            client_data["requests"] = 0
            client_data["window_start"] = current_time

        # Check if limit exceeded
        if client_data["requests"] >= self.requests_per_window:
            return True

        # Increment request count
        client_data["requests"] += 1
        return False

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with rate limiting."""

        # Skip rate limiting for health checks
        if request.url.path in [
            "/health",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]:
            return await call_next(request)

        client_key = self._get_client_key(request)

        if self._is_rate_limited(client_key):
            logger.warning(
                "Rate limit exceeded",
                client_key=client_key,
                path=request.url.path,
                method=request.method,
            )

            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Maximum {
                            self.requests_per_window} requests per {
                            self.window_seconds} seconds.",
                        "timestamp": time.time(),
                        "request_id": id(request),
                    }},
            )

        return await call_next(request)
