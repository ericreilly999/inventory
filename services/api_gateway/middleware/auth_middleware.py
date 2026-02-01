"""Authentication middleware for API Gateway."""

import time
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.auth.utils import verify_token
from shared.logging.config import get_logger

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and comprehensive request logging."""

    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/user/auth/login",
        "/api/user/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/user/admin/seed-database",
        "/api/user/admin/seed-status",
        "/api/user/admin/debug/config",
        "/api/user/admin/run-migrations",
        "/api/user/admin/test-password",
        "/api/user/admin/cleanup-admin",
        "/api/v1/admin/seed-database",
        "/api/v1/admin/seed-status",
        "/api/v1/admin/debug/config",
        "/api/v1/admin/run-migrations",
        "/api/v1/admin/test-password",
        "/api/v1/admin/cleanup-admin",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication and logging."""
        start_time = time.time()

        # Extract request information
        method = request.method
        url = str(request.url)
        path = request.url.path
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        # Log incoming request
        logger.info(
            "API Gateway request received",
            method=method,
            url=url,
            path=path,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        # Check if endpoint requires authentication
        if path not in self.PUBLIC_ENDPOINTS and not path.startswith("/api/user/auth/") and not path.startswith("/api/v1/auth/"):
            # Extract and verify JWT token
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                logger.warning(
                    "Authentication failed - missing or invalid authorization header",
                    path=path,
                    client_ip=client_ip,
                )
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": {
                            "code": "AUTHENTICATION_REQUIRED",
                            "message": "Valid authentication token required",
                            "timestamp": time.time(),
                            "request_id": id(request),
                        }
                    },
                )

            token = authorization.split(" ")[1]
            payload = verify_token(token)

            if not payload:
                logger.warning(
                    "Authentication failed - invalid token",
                    path=path,
                    client_ip=client_ip,
                )
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": "Invalid or expired authentication token",
                            "timestamp": time.time(),
                            "request_id": id(request),
                        }
                    },
                )

            # Add user context to request state
            request.state.user_id = payload.get("sub")
            request.state.user_role = payload.get("role")

            logger.info(
                "Authentication successful",
                user_id=request.state.user_id,
                user_role=request.state.user_role,
                path=path,
            )

        # Process request
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time

            # Log successful response
            logger.info(
                "API Gateway request completed",
                method=method,
                path=path,
                status_code=response.status_code,
                processing_time_ms=round(processing_time * 1000, 2),
                user_id=getattr(request.state, "user_id", None),
            )

            return response

        except Exception as e:
            processing_time = time.time() - start_time

            # Log error
            logger.error(
                "API Gateway request failed",
                method=method,
                path=path,
                error=str(e),
                processing_time_ms=round(processing_time * 1000, 2),
                user_id=getattr(request.state, "user_id", None),
            )

            # Re-raise the exception
            raise
