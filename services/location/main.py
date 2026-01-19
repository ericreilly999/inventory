"""Location Service FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.logging.config import configure_logging
from .routers import locations, location_types, movements
from .middleware import auth_middleware

# Setup logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title="Location Service",
    description="Location and movement management service",
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

# Add authentication middleware
app.add_middleware(auth_middleware.AuthMiddleware)

# Include routers
app.include_router(locations.router, prefix="/api/v1/locations", tags=["locations"])
app.include_router(location_types.router, prefix="/api/v1/location-types", tags=["location-types"])
app.include_router(movements.router, prefix="/api/v1/movements", tags=["movements"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "location-service"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Location Service API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)