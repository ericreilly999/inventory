"""API Gateway Service FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.logging.config import configure_logging
from .routers import gateway
from .middleware import auth_middleware, rate_limit_middleware

# Setup logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title="API Gateway",
    description="Central API Gateway for Inventory Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(rate_limit_middleware.RateLimitMiddleware)

# Add authentication middleware
app.add_middleware(auth_middleware.AuthMiddleware)

# Include routers
app.include_router(gateway.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Inventory Management API Gateway", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)