"""Main gateway router for request routing to microservices."""

import os
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from shared.logging.config import get_logger

from ..dependencies import get_service_client

logger = get_logger(__name__)

router = APIRouter()

# Get environment (default to dev)
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Service endpoints mapping (environment-aware)
SERVICE_ENDPOINTS = {
    "inventory": f"http://inventory-service.{ENVIRONMENT}.inventory.local:8003",
    "location": f"http://location-service.{ENVIRONMENT}.inventory.local:8002",
    "user": f"http://user-service.{ENVIRONMENT}.inventory.local:8001",
    "reporting": f"http://reporting-service.{ENVIRONMENT}.inventory.local:8004",
}


async def route_request(
    request: Request,
    service_name: str,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
) -> JSONResponse:
    """Route request to appropriate microservice."""

    if service_name not in SERVICE_ENDPOINTS:
        logger.error(f"Unknown service: {service_name}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SERVICE_NOT_FOUND",
                    "message": f"Service '{service_name}' not found",
                    "timestamp": time.time(),
                    "request_id": id(request),
                }
            },
        )

    service_url = SERVICE_ENDPOINTS[service_name]
    target_url = f"{service_url}/api/v1{path}"

    # Prepare headers (forward authorization and other relevant headers)
    headers = {}
    if "authorization" in request.headers:
        headers["authorization"] = request.headers["authorization"]
    if "content-type" in request.headers:
        headers["content-type"] = request.headers["content-type"]

    # Add user context headers if available
    if hasattr(request.state, "user_id") and request.state.user_id is not None:
        headers["X-User-ID"] = str(request.state.user_id)
    if hasattr(request.state, "user_role") and request.state.user_role is not None:
        headers["X-User-Role"] = str(request.state.user_role)

    try:
        # Get request body if present
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()

        # Forward request to microservice
        logger.info(
            "Routing request to microservice",
            service=service_name,
            target_url=target_url,
            method=request.method,
            user_id=getattr(request.state, "user_id", None),
        )

        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=dict(request.query_params),
            timeout=30.0,
            follow_redirects=True,
        )

        # Log response
        logger.info(
            "Microservice response received",
            service=service_name,
            status_code=response.status_code,
            user_id=getattr(request.state, "user_id", None),
        )

        # Return response
        return JSONResponse(
            content=response.json() if response.content else {},
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    except httpx.TimeoutException:
        logger.error(
            "Service timeout",
            service=service_name,
            target_url=target_url,
            user_id=getattr(request.state, "user_id", None),
        )
        raise HTTPException(
            status_code=504,
            detail={
                "error": {
                    "code": "SERVICE_TIMEOUT",
                    "message": f"Service '{service_name}' timeout",
                    "timestamp": time.time(),
                    "request_id": id(request),
                }
            },
        )

    except httpx.ConnectError:
        logger.error(
            "Service unavailable",
            service=service_name,
            target_url=target_url,
            user_id=getattr(request.state, "user_id", None),
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": f"Service '{service_name}' is unavailable",
                    "timestamp": time.time(),
                    "request_id": id(request),
                }
            },
        )

    except Exception as e:
        logger.error(
            "Service routing error",
            service=service_name,
            error=str(e),
            user_id=getattr(request.state, "user_id", None),
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error occurred",
                    "timestamp": time.time(),
                    "request_id": id(request),
                }
            },
        )


# Authentication routes (direct to user service)
@router.post("/auth/login")
async def login(
    request: Request, client: httpx.AsyncClient = Depends(get_service_client)
):
    """Route login request to user service."""
    return await route_request(request, "user", "/auth/login", client)


@router.get("/auth/me")
async def get_current_user_info(
    request: Request, client: httpx.AsyncClient = Depends(get_service_client)
):
    """Route get current user request to user service."""
    return await route_request(request, "user", "/auth/me", client)


@router.post("/auth/register")
async def register(
    request: Request, client: httpx.AsyncClient = Depends(get_service_client)
):
    """Route register request to user service."""
    return await route_request(request, "user", "/auth/register", client)


@router.post("/auth/logout")
async def logout(
    request: Request, client: httpx.AsyncClient = Depends(get_service_client)
):
    """Route logout request to user service."""
    return await route_request(request, "user", "/auth/logout", client)


# User management routes
@router.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def users_routes(
    request: Request,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
):
    """Route user management requests to user service."""
    return await route_request(request, "user", f"/users/{path}", client)


@router.api_route("/roles/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def roles_routes(
    request: Request,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
):
    """Route role management requests to user service."""
    return await route_request(request, "user", f"/roles/{path}", client)


# Admin routes
@router.api_route("/admin/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def admin_routes(
    request: Request,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
):
    """Route admin requests to user service."""
    return await route_request(request, "user", f"/admin/{path}", client)


# Inventory management routes
@router.api_route("/items/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def items_routes(
    request: Request,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
):
    """Route item management requests to inventory service."""
    return await route_request(request, "inventory", f"/items/{path}", client)


# Location management routes
@router.api_route("/locations/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def locations_routes(
    request: Request,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
):
    """Route location management requests to location service."""
    # Handle backward compatibility for old paths
    if path.startswith("types"):
        # /api/v1/locations/types/* -> /api/v1/location-types/*
        new_path = path.replace("types", "", 1)  # Remove "types"
        route_path = f"/location-types{new_path}" if new_path else "/location-types"
    elif path.startswith("locations"):
        # /api/v1/locations/locations/* -> /api/v1/locations/*
        new_path = path.replace("locations", "", 1)  # Remove first "locations"
        route_path = f"/locations{new_path}" if new_path else "/locations"
    else:
        # Handle empty path (e.g., /api/v1/locations -> /locations)
        route_path = f"/locations/{path}" if path else "/locations"
    
    return await route_request(request, "location", route_path, client)


@router.api_route(
    "/location-types/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def location_types_routes(
    request: Request,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
):
):
    """Route location type management requests to location service."""
    # Handle empty path (e.g., /api/v1/location-types -> /location-types)
    route_path = f"/location-types/{path}" if path else "/location-types"
    return await route_request(request, "location", route_path, client)


@router.api_route("/movements/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def movements_routes(
    request: Request,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
):
    """Route movement requests to location service."""
    route_path = f"/movements/{path}" if path else "/movements"
    return await route_request(request, "location", route_path, client)


# Reporting routes
@router.api_route("/reports/{path:path}", methods=["GET", "POST"])
async def reports_routes(
    request: Request,
    path: str,
    client: httpx.AsyncClient = Depends(get_service_client),
):
    """Route reporting requests to reporting service."""
    return await route_request(request, "reporting", f"/reports/{path}", client)
