"""Authentication middleware for Location Service."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for request logging and basic validation."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add authentication context."""
        
        # Skip auth for health check and docs endpoints
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Log the request with full details
        logger.info(
            f"Location Service - {request.method} {request.url.path}",
            extra={
                "query_params": dict(request.query_params),
                "path": request.url.path,
                "method": request.method
            }
        )
        
        try:
            response = await call_next(request)
            logger.info(
                f"Location Service - Response {response.status_code}",
                extra={
                    "path": request.url.path,
                    "status_code": response.status_code
                }
            )
            return response
        except Exception as e:
            logger.error(f"Location Service error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "detail": str(e)}
            )