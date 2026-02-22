"""Location Service FastAPI application."""

from typing import Callable, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config.settings import settings
from shared.logging.config import configure_logging, get_logger

from .middleware import auth_middleware
from .routers import location_types, locations, movements

# Setup logging
configure_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Location Service",
    description="Location and movement management service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=True,  # Enable debug mode
)


# Add custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Log and return detailed validation errors."""
    logger.error(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
        body=exc.body,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": str(exc.body) if exc.body else None,
            "path": request.url.path,
        },
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


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """Log all incoming requests with details."""
    logger.info(
        f"Location Service - {request.method} {request.url.path}",
        method=request.method,
        path=request.url.path,
        query_params=dict(request.query_params),
        headers={
            k: v
            for k, v in request.headers.items()
            if k.lower() not in ["authorization", "cookie"]
        },
    )
    response = await call_next(request)
    logger.info(
        f"Location Service - Response {response.status_code}",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    return response


# Include routers
app.include_router(locations.router, prefix="/api/v1/locations", tags=["locations"])
app.include_router(
    location_types.router,
    prefix="/api/v1/location-types",
    tags=["location-types"],
)
app.include_router(movements.router, prefix="/api/v1/movements", tags=["movements"])


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "location-service"}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "Location Service API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
