"""API Gateway Service FastAPI application."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config.settings import settings
from shared.logging.config import configure_logging

from .middleware import auth_middleware, rate_limit_middleware
from .routers import gateway

# Setup logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title="API Gateway",
    description="Central API Gateway for Inventory Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Add exception handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException and return consistent error format."""
    # If detail is already a dict with error structure, return it directly
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )
    # Otherwise wrap it in standard format
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
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
