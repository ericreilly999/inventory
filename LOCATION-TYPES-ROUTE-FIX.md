# Location Types Route Fix

## Problem
Getting 422 Unprocessable Entity error when accessing `/api/v1/locations/types`

## Root Cause
**Route mismatch between UI and backend service**

- **UI calls**: `/api/v1/locations/types`
- **API Gateway forwards to**: `http://location-service:8002/api/v1/locations/types`
- **Location service was registered at**: `/api/v1/location-types` ❌

The location service router was using a hyphen (`location-types`) instead of a slash path (`locations/types`).

## Solution
Changed the location service router prefix from `/api/v1/location-types` to `/api/v1/locations/types`

### File Changed
`services/location/main.py`

**Before:**
```python
app.include_router(location_types.router, prefix="/api/v1/location-types", tags=["location-types"])
```

**After:**
```python
app.include_router(location_types.router, prefix="/api/v1/locations/types", tags=["location-types"])
```

## Why This Happened
The location service was originally designed with a different URL structure (`/location-types`) but the UI and API gateway were expecting a nested structure (`/locations/types`). This is a common REST API design pattern where sub-resources are nested under their parent resource.

## Testing
After deployment, these endpoints should work:
- `GET /api/v1/locations/types` - List all location types
- `POST /api/v1/locations/types` - Create a location type
- `GET /api/v1/locations/types/{id}` - Get a specific location type
- `PUT /api/v1/locations/types/{id}` - Update a location type
- `DELETE /api/v1/locations/types/{id}` - Delete a location type

## Deployment
```bash
git add services/location/main.py LOCATION-TYPES-ROUTE-FIX.md
git commit -m "Fix location types route - change from /location-types to /locations/types"
git push origin main
```

The CD pipeline will automatically deploy the fix.

## Related Issues
This was NOT a JWT or permissions issue - it was purely a routing mismatch. The 422 error was FastAPI's way of saying "I don't have a route handler for this path".
