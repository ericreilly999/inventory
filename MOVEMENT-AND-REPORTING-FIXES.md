# Movement and Reporting Service Fixes

## Date: January 24, 2026

## Issues Fixed

### 1. Movement Endpoint TokenData Error (500 Internal Server Error)

**Problem:**
- When moving parent items, the endpoint was failing with: `'TokenData' object has no attribute 'id'`
- Error occurred in `/api/v1/movements/move` endpoint

**Root Cause:**
- The `require_location_write` dependency returns a `TokenData` object, not a `User` object
- Code was trying to access `current_user.id` but `TokenData` has `user_id` instead

**Solution:**
- Changed parameter name from `current_user: User` to `token_data` (no type hint needed)
- Updated all references from `current_user.id` to `token_data.user_id`
- Fixed in: `services/location/routers/movements.py`

**Changes:**
```python
# Before
async def move_item(
    move_request: ItemMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_location_write)
):
    # ... code using current_user.id

# After
async def move_item(
    move_request: ItemMoveRequest,
    db: Session = Depends(get_db),
    token_data = Depends(require_location_write)
):
    # ... code using token_data.user_id
```

### 2. Reporting Service Inventory Counts Missing Location Filter

**Problem:**
- UI was sending `location_ids` parameter but API wasn't accepting it
- Only `location_type_ids` was supported, causing filtering issues

**Solution:**
- Added `location_ids` parameter to `/api/v1/reports/inventory/counts` endpoint
- Added location filtering logic to the query
- Fixed in: `services/reporting/routers/reports.py`

**Changes:**
```python
# Added parameter
location_ids: Optional[List[UUID]] = Query(None, description="Filter by specific locations")

# Added filtering logic
if location_ids:
    location_type_query = location_type_query.filter(
        Location.id.in_(location_ids)
    )
```

## Testing

### Movement Endpoint
1. Navigate to Inventory page
2. Select a parent item
3. Click "Move Item"
4. Select destination location
5. Add notes (optional)
6. Click "Move"
7. Verify success message appears
8. Verify item appears in new location

### Reporting Service
1. Navigate to Reports page
2. Select "Inventory Reports" tab
3. Choose a specific location from dropdown
4. Choose an item type (optional)
5. Click "Generate Report"
6. Verify report displays with filtered data
7. Verify charts update correctly
8. Verify table shows only items from selected location

## Deployment

Changes deployed via CI/CD pipeline:
- Commit: 1649822
- Services affected: location-service, reporting-service
- Docker images tagged with commit SHA
- ECS services will auto-deploy new task definitions

## Files Modified

1. `services/location/routers/movements.py`
   - Fixed TokenData.id error
   - Changed parameter from `current_user: User` to `token_data`
   - Updated references to use `token_data.user_id`

2. `services/reporting/routers/reports.py`
   - Added `location_ids` parameter to inventory counts endpoint
   - Added location filtering to query logic
   - Updated error logging to include new parameter

## Related Issues

- Previous fix: Parent item creation 400 error (item type category validation)
- Previous fix: Child item creation error (AssignmentHistory missing created_at)
- Previous fix: Location service 422 errors (route matching order)

## Notes

- The `TokenData` vs `User` pattern is consistent across all services
- Permission dependencies return `TokenData` objects with user_id, username, role_id, and permissions
- If you need the full `User` object, use `get_current_user()` dependency instead
- The reporting service now supports filtering by both location_ids and location_type_ids
