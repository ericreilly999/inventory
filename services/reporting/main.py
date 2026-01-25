"""Reporting Service FastAPI application."""

from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.logging.config import configure_logging

from .middleware import auth_middleware
from .routers import reports

# Setup logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title="Reporting Service",
    description="Reporting and analytics service for inventory management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(auth_middleware.AuthMiddleware)

# Include routers
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "reporting-service"}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "Reporting Service API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
