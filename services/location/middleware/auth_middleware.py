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
        
        # Log the request
        logger.info(f"Location Service - {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Location Service error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "detail": str(e)}
            )