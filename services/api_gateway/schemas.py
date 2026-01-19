"""Schemas for API Gateway service."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float
    request_id: int


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: ErrorDetail


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str


class RootResponse(BaseModel):
    """Root endpoint response schema."""
    message: str
    version: str