# Location Service Type Mismatch Fixes

## Problem
Multiple endpoints in the location service had type mismatches in their dependency injection that would cause 422 errors.

## Root Cause
The `require_location_read()` dependency function returns `TokenData`, but the route handlers were expecting `User` objects:

```python
_: User = Depends(require_location_read)  # ❌ Wrong - require_location_read returns TokenData
```

This causes FastAPI to fail validation because it can't convert `TokenData` to `User`.

## Solution
Changed all occurrences to use `token_data` instead of `_: User`:

```python
token_data = Depends(require_location_read)  # ✅ Correct
```

## Files Fixed

### 1. services/location/main.py
- Fixed route prefix from `/api/v1/location-types` to `/api/v1/locations/types`

### 2. services/location/routers/locations.py
Fixed 4 functions:
- `list_locations()` - GET /
- `list_locations_with_item_counts()` - GET /with-items
- `get_location()` - GET /{location_id}
- `get_location_items()` - GET /{location_id}/items

### 3. services/location/routers/movements.py
Fixed 3 functions:
- `get_move_history()` - GET /
- `get_item_move_history()` - GET /items/{item_id}
- `get_recent_moves()` - GET /recent

### 4. services/location/routers/location_types.py
Already fixed in previous commit:
- `list_location_types()` - GET /
- `get_location_type()` - GET /{location_type_id}

## Impact
These fixes ensure that all location service endpoints work correctly with the JWT token authentication system. The endpoints will now:
- Accept valid JWT tokens
- Properly validate permissions
- Return data instead of 422 errors

## Testing
After deployment, test these endpoints:
- GET /api/v1/locations - List locations
- GET /api/v1/locations/types - List location types
- GET /api/v1/locations/{id} - Get specific location
- GET /api/v1/movements - Get movement history

All should return 200 OK with data instead of 422 errors.

## Deployment
```bash
git add services/location/
git commit -m "Fix all location service type mismatches and route prefix"
git push origin main
```

The CD pipeline will automatically deploy the fixes.
