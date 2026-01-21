# Location Types 422 Error - Root Cause and Fix

## Problem
GET `/api/v1/locations/types` was returning 422 Unprocessable Entity errors consistently.

## Root Cause

**FastAPI Route Matching Order Issue**

The routers were included in this order:
```python
app.include_router(locations.router, prefix="/api/v1/locations")
app.include_router(location_types.router, prefix="/api/v1/locations/types")
```

When a request came for `/api/v1/locations/types`, FastAPI tried to match it against routes in order:
1. First checked `locations.router` routes with prefix `/api/v1/locations`
2. Found route `/{location_id}` which creates pattern `/api/v1/locations/{location_id}`
3. Matched `/api/v1/locations/types` against this pattern
4. Tried to parse "types" as a UUID for the `location_id` parameter
5. Failed validation with error: "Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], found `t` at 1"

The actual error from logs:
```json
{
  "path": "/api/v1/locations/types",
  "method": "GET",
  "errors": [{
    "type": "uuid_parsing",
    "loc": ["path", "location_id"],
    "msg": "Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], found `t` at 1",
    "input": "types"
  }]
}
```

## Solution

**Include more specific routes BEFORE generic parameterized routes:**

```python
# ORDER MATTERS! More specific routes must come first
app.include_router(location_types.router, prefix="/api/v1/locations/types")
app.include_router(locations.router, prefix="/api/v1/locations")
```

This is a fundamental FastAPI routing principle: when you have overlapping route patterns, the more specific route must be registered first. Otherwise, the generic parameterized route will match first and cause validation errors.

## Files Changed

### services/location/main.py
- Swapped order of router includes
- Added comment explaining the importance of order

## Why Previous Fixes Didn't Work

1. **Permission system fixes** - Were correct but not the issue
2. **JWT token format fixes** - Were correct but not the issue  
3. **Route prefix changes** - Were correct but not the issue
4. **Type annotation fixes** - Were correct but not the issue
5. **Dependencies parameter pattern** - Was correct but not the issue

All these fixes were valid improvements, but the actual problem was route matching order happening before any of our code executed.

## Deployment

**Commit:** f2af408
**Status:** Pushed to main, CD pipeline triggered
**Expected Result:** Location types endpoint should return 200 OK with data

## Testing

After deployment completes:
1. Navigate to Location Types page
2. Should see list of location types without 422 errors
3. Check CloudWatch logs - should see 200 OK responses
4. No need to log out/in - this wasn't a JWT issue

## Lessons Learned

1. **FastAPI Route Order is Critical:**
   - More specific routes must be registered before generic ones
   - `/api/v1/locations/types` must come before `/api/v1/locations/{location_id}`
   - This applies to any framework with pattern-based routing

2. **Debug Logging is Essential:**
   - The custom validation error handler we added revealed the actual error
   - Without seeing the full validation error, we were guessing at the cause
   - Always log validation errors with full context

3. **422 Errors Can Have Multiple Causes:**
   - Request validation (query params, body)
   - Path parameter validation (our case)
   - Dependency injection validation
   - Each requires different debugging approaches
