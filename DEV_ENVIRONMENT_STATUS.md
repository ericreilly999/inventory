# Dev Environment Status

## Current Issue

The dev environment database has duplicate SKU values that prevent migrations from running:

```
Error: (psycopg2.errors.UniqueViolation) could not create unique index "uq_parent_items_sku"
DETAIL:  Key (sku)=(2) is duplicated.
```

## Root Cause

Earlier testing created duplicate SKU values in the database. The migration `20260201181337_add_unique_constraint_to_sku_fields.py` attempts to add a unique constraint but fails due to existing duplicates.

## Attempted Fixes

1. ✗ Restarted ECS services - doesn't reset database
2. ✗ Tried rollback endpoint - not available
3. ✗ Tried SQL fix endpoint - not available
4. ✗ Direct database access - requires RDS credentials

## Solutions

### Option 1: Drop and Recreate Dev Database (Recommended for long-term)

Requires Terraform access:

```bash
# Navigate to dev terraform
cd terraform/environments/dev

# Destroy and recreate RDS instance
terraform destroy -target=module.rds
terraform apply -target=module.rds

# Redeploy services to run migrations
gh workflow run cd.yml
```

**Pros:**
- Clean slate
- Fixes all database issues
- Good for long-term dev environment health

**Cons:**
- Requires Terraform access
- Takes 10-15 minutes
- Loses all dev data

### Option 2: Manual Database Cleanup

Connect to RDS and fix duplicates:

```sql
-- Connect to dev database
psql -h dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com \
     -U inventory_admin \
     -d inventory_management

-- Fix duplicate SKUs in parent_items
WITH duplicates AS (
    SELECT id, sku, 
           ROW_NUMBER() OVER (PARTITION BY sku ORDER BY created_at) as rn
    FROM parent_items
    WHERE sku IS NOT NULL
)
UPDATE parent_items
SET sku = CONCAT(parent_items.sku, '-', duplicates.rn)
FROM duplicates
WHERE parent_items.id = duplicates.id
AND duplicates.rn > 1;

-- Fix duplicate SKUs in child_items
WITH duplicates AS (
    SELECT id, sku,
           ROW_NUMBER() OVER (PARTITION BY sku ORDER BY created_at) as rn
    FROM child_items
    WHERE sku IS NOT NULL
)
UPDATE child_items
SET sku = CONCAT(child_items.sku, '-', duplicates.rn)
FROM duplicates
WHERE child_items.id = duplicates.id
AND duplicates.rn > 1;

-- Run migrations via API after fixing
```

**Pros:**
- Preserves existing data
- Quick fix

**Cons:**
- Requires RDS credentials
- Manual SQL execution
- Data quality issues remain

### Option 3: Use Staging for Testing (Recommended for immediate testing)

Staging has a clean database with proper seed data.

```bash
# Deploy to staging
gh workflow run cd.yml -f environment=staging

# Test location deletion in staging
# URL: http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com
```

**Pros:**
- Clean database
- Proper seed data already loaded
- No dev environment issues
- Faster to get testing

**Cons:**
- Doesn't fix dev environment
- Uses staging resources

## Recommendation

**For immediate testing:** Use Option 3 (Staging)
- Staging is ready with clean data
- Can test location deletion feature immediately
- Dev can be fixed separately

**For long-term:** Use Option 1 (Drop/Recreate)
- Fixes dev environment properly
- Clean slate for future development
- Can be done after testing in staging

## Next Steps

1. Deploy and test in staging (immediate)
2. Schedule dev database recreation (when convenient)
3. Document proper dev environment maintenance procedures

## Files Created

- `scripts/Reset-DevEnvironment.ps1` - Restart ECS services
- `scripts/fix_dev_database.py` - Attempted automated fix
- `scripts/run_dev_migration.py` - Run migrations in dev
- `scripts/test_dev_location_deletion.py` - Test location deletion
- `scripts/rollback_and_reapply_migrations.py` - Attempted rollback

## Current Dev Environment State

- ✓ Services are running
- ✓ API is accessible
- ✓ Authentication works
- ✗ Migrations cannot complete (duplicate SKUs)
- ✗ Some endpoints return 404 (routing issues)
- ⚠ Database needs cleanup or recreation
