# Location Types 422 Error - Root Cause and Fix

## Problem
GET `/api/v1/locations/types` was returning 422 Unprocessable Entity errors consistently.

## Investigation Process

### Initial Hypotheses (Ruled Out)
1. ✅ Permission system issues - Already fixed with wildcard permission support
2. ✅ JWT token format - Already fixed with array-to-dict conversion
3. ✅ Route prefix mismatch - Already fixed (changed to `/api/v1/locations/types`)
4. ✅ Type annotation issues - Already fixed (changed `_: User` to `token_data`)

### Debug Logging Findings
- Enabled debug mode and custom validation error handler in `services/location/main.py`
- Logs showed:
  - "Location Service - GET /api/v1/locations/types" ✅ Request received
  - "422 Unprocessable Entity" ❌ Error occurred
  - **NO "Validation error" log message** ⚠️ Custom handler never triggered!

This indicated the 422 was happening BEFORE reaching our route handler or exception handler.

## Root Cause

**FastAPI was trying to validate `token_data = Depends(require_location_read)` as a function parameter!**

When you use `Depends()` as a function parameter with a variable name like:
```python
async def list_location_types(
    token_data = Depends(require_location_read)  # ❌ WRONG
):
```

FastAPI tries to:
1. Inject the dependency result into the parameter
2. Validate the parameter type
3. Include it in the OpenAPI schema

Since `require_location_read` returns a `TokenData` object but there's no type annotation, FastAPI's validation was failing with 422 before even calling the route handler.

## Solution

Use `dependencies` parameter in the route decorator instead:
```python
@router.get("/", dependencies=[Depends(require_location_read)])  # ✅ CORRECT
async def list_location_types(
    # No token_data parameter needed
):
```

This tells FastAPI:
- Execute the dependency for validation/authorization
- Don't inject the result as a parameter
- Don't include it in OpenAPI schema

## Files Changed

### services/location/routers/location_types.py
- Changed `list_location_types()` to use `dependencies=[Depends(require_location_read)]`
- Changed `get_location_type()` to use `dependencies=[Depends(require_location_read)]`
- Removed `token_data` parameters

### services/location/routers/locations.py
- Changed `list_locations()` to use `dependencies=[Depends(require_location_read)]`
- Changed `list_locations_with_item_counts()` to use `dependencies=[Depends(require_location_read)]`
- Changed `get_location()` to use `dependencies=[Depends(require_location_read)]`
- Changed `get_location_items()` to use `dependencies=[Depends(require_location_read)]`
- Removed `token_data` parameters

### services/location/routers/movements.py
- Changed `get_move_history()` to use `dependencies=[Depends(require_location_read)]`
- Changed `get_item_move_history()` to use `dependencies=[Depends(require_location_read)]`
- Changed `get_recent_moves()` to use `dependencies=[Depends(require_location_read)]`
- Removed `token_data` parameters

## Pattern Consistency

This fix aligns the location service with the pattern already used in:
- ✅ Inventory service (`services/inventory/routers/*.py`)
- ✅ User service (`services/user/routers/*.py`)
- ✅ Reporting service (if applicable)

All services now consistently use `dependencies=[Depends(require_xxx)]` for authorization checks.

## Deployment

**Commit:** e9d0ad7
**Status:** Pushed to main, CD pipeline triggered
**Expected Result:** Location types endpoint should return 200 OK with data

## Testing

After deployment completes:
1. Log out and log back in to get fresh JWT token
2. Navigate to Location Types page
3. Should see list of location types without 422 errors
4. Check CloudWatch logs - should see 200 OK responses

## Lessons Learned

1. **FastAPI Dependency Patterns:**
   - Use `dependencies=[Depends(xxx)]` for authorization/validation only
   - Use `param = Depends(xxx)` only when you need the dependency result in your function

2. **Debugging 422 Errors:**
   - If custom exception handlers don't trigger, the error is happening in FastAPI's validation layer
   - Check for parameter type mismatches or missing type annotations
   - Compare with working examples in other services

3. **Consistency Matters:**
   - Following established patterns prevents subtle bugs
   - Code review should catch pattern deviations
