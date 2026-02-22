# Location Deletion Feature - Deployment Plan

## Current Status

### Changes Implemented
1. **Database Migration** (`382574989839_allow_location_deletion_with_history.py`):
   - Changes foreign key constraints on `move_history` table from `RESTRICT` to `SET NULL`
   - Allows locations to be deleted even when they appear in historical movement records
   - Historical records preserved with NULL location references

2. **Code Changes**:
   - Updated `shared/models/move_history.py` with `ondelete="SET NULL"`
   - Updated `services/location/dependencies.py` validation logic
   - Only checks for active inventory, not historical data
   - Improved error messages

3. **Tests**:
   - All unit tests passing (360 passed)
   - Property tests failing (pre-existing issues, not related to this feature)

### Dev Environment Issues
- Has duplicate SKU data from earlier testing
- Migration cannot run due to unique constraint violations
- API routing issues detected
- **Recommendation**: Skip dev, deploy directly to staging

### Staging Environment
- Clean database with proper seed data
- 100 parent items with child components
- 13 active locations (5 JDM warehouses, 5 quarantines, 3 client sites)
- Old locations exist for testing deletion
- **Ready for deployment and testing**

## Deployment Steps

### 1. Deploy to Staging
```bash
# Trigger staging deployment via GitHub Actions
gh workflow run cd.yml -f environment=staging
```

### 2. Run Migration in Staging
After deployment completes:
```bash
# Login to staging
curl -X POST http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Run migration (use token from login)
curl -X POST http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com/api/v1/admin/run-migrations \
  -H "Authorization: Bearer <TOKEN>"
```

### 3. Test Location Deletion
Test in staging UI:
1. Login: http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com
2. Navigate to Locations
3. Try to delete old location types (Office, Storage Room, etc.)
4. Try to delete old locations (Warehouse A, B, C, etc.)
5. Verify:
   - Locations with NO active items can be deleted
   - Locations WITH active items cannot be deleted (clear error message)
   - Historical movement records are preserved

## Expected Behavior

### Can Delete:
- Locations with 0 active items (even if they have historical movement data)
- Location types with 0 locations using them

### Cannot Delete:
- Locations with active items assigned
- Location types with locations still using them
- Clear error messages explaining why

### Error Messages:
- Location with items: "Cannot delete location 'X' - N item(s) are currently assigned to it. Move all items to another location first."
- Location type with locations: "Cannot delete location type 'X' - N location(s) are using it: [list]. Delete or reassign these locations first."

## Rollback Plan
If issues occur:
1. Revert migration: The migration has a `downgrade()` function that restores RESTRICT constraints
2. Redeploy previous version
3. Historical data remains intact

## Success Criteria
- ✓ Migration runs successfully in staging
- ✓ Old locations can be deleted (those with 0 active items)
- ✓ Old location types can be deleted (those with 0 locations)
- ✓ Locations with active items cannot be deleted
- ✓ Clear error messages displayed
- ✓ Historical movement records preserved with NULL references
