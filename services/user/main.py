"""User Service FastAPI application."""

from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.logging.config import configure_logging

from .middleware import auth_middleware
from .routers import admin, auth, roles, users

# Setup logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title="User Service",
    description="User authentication and management service",
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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "user-service"}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "User Service API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
