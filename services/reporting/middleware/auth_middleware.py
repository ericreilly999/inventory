"""Authentication middleware for Reporting Service."""

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API requests."""

    # Paths that don't require authentication
    EXEMPT_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through authentication middleware."""

        # Skip authentication for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(
                f"Missing or invalid Authorization header for " f"{request.url.path}"
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "MISSING_AUTHORIZATION",
                        "message": "Authorization header required",
                        "details": {"header": "Authorization: Bearer <token>"},
                    }
                },
            )

        # Continue with request processing
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                        "details": {},
                    }
                },
            )
