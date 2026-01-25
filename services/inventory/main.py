"""Inventory Service FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.logging.config import configure_logging

from .middleware import auth_middleware
from .routers import child_items, item_types, movements, parent_items

# Setup logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title="Inventory Service",
    description=(
        "Inventory management service for parent items, " "child items, and movements"
    ),
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
app.include_router(
    parent_items.router, prefix="/api/v1/items/parent", tags=["parent-items"]
)
app.include_router(
    child_items.router, prefix="/api/v1/items/child", tags=["child-items"]
)
app.include_router(item_types.router, prefix="/api/v1/items/types", tags=["item-types"])
app.include_router(movements.router, prefix="/api/v1/movements", tags=["movements"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "inventory-service"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Inventory Service API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
