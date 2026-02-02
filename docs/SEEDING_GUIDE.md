# Data Seeding Guide

## Overview
This guide explains how to seed demo data into the dev and staging environments.

## Seed Scripts

### 1. setup_default_roles.py
Creates 6 default roles with granular permissions:
- **admin**: Full system access (created during initial setup)
- **Warehouse Manager**: Full inventory and location management
- **Inventory Clerk**: Read/write inventory, read-only locations
- **Viewer**: Read-only access to all services
- **Location Manager**: Full location management, read-only inventory
- **User Manager**: Manage users but not roles

### 2. reseed_complete_inventory.py
Creates complete inventory dataset:
- **70 parent items**: 10 of each type (Sports Tower, MedEd 1688, MedEd 1788, Clinical 1788, RISE Tower, 1788 Roll Stand, 1688 Roll Stand)
- **Child items**: Assigned to each parent based on configuration
- **Locations**: 5 hospitals (Hospital A-E), warehouses, quarantine
- **Distribution**: Items distributed across locations
- **SKU Format**: 
  - Parent items: Simple numbers (1, 2, 3...)
  - Child items: Serial numbers (e.g., 2204FE3842)

### 3. generate_movements.py
Creates movement history:
- **Random movements**: Each item moved 0-4 times
- **Total movements**: ~125+ movement records
- **Realistic history**: Items moved between warehouses, hospitals, and quarantine

## Seeding via GitHub Actions (Recommended)

### Prerequisites
1. Environment deployed and healthy
2. Admin credentials configured
3. API accessible

### Steps

1. **Navigate to GitHub Actions**
   - Go to your repository
   - Click "Actions" tab
   - Find "Seed Staging Data" workflow

2. **Run Workflow**
   - Click "Run workflow" button
   - Select environment:
     - `staging`: Seed staging environment
     - `dev`: Seed dev environment
   - Click "Run workflow"

3. **Monitor Progress**
   - Watch workflow execution
   - Check each step completes successfully
   - Review logs for any errors

4. **Verify Data**
   - Login to environment UI
   - Check Roles page (should show 6 roles)
   - Check Inventory page (should show 70 items)
   - Check movement history

### Expected Output

```
=========================================
SETTING UP DEFAULT ROLES - STAGING ENVIRONMENT
=========================================
✓ Created role: Warehouse Manager
✓ Created role: Inventory Clerk
✓ Created role: Viewer
✓ Created role: Location Manager
✓ Created role: User Manager

=========================================
COMPLETE INVENTORY RESEEDING - STAGING ENVIRONMENT
=========================================
[1/6] Clearing existing inventory...
[2/6] Setting up item types...
[3/6] Setting up locations...
[4/6] Creating inventory...
[5/6] Moving items to hospitals...
[6/6] Creating additional movement history...

Total parent items created: 70
Total movements created: 125

=========================================
GENERATING MOVEMENT HISTORY - STAGING ENVIRONMENT
=========================================
Total parent items: 70
Items moved: 50
Items not moved: 20
Total movements created: 125
```

## Manual Seeding (Alternative)

If you need to run scripts manually:

### Prerequisites
```bash
pip install requests
```

### Set Environment Variable
```bash
# For staging
export ENVIRONMENT=staging

# For dev
export ENVIRONMENT=dev
```

### Run Scripts in Order

```bash
# 1. Setup roles
python scripts/setup_default_roles.py

# 2. Seed inventory
python scripts/reseed_complete_inventory.py

# 3. Generate movements
python scripts/generate_movements.py
```

## Idempotency

All seed scripts are designed to be idempotent:

- **setup_default_roles.py**: Checks for existing roles before creating
- **reseed_complete_inventory.py**: Deletes existing items before creating new ones
- **generate_movements.py**: Creates new movements (doesn't delete existing)

You can safely run the scripts multiple times.

## Troubleshooting

### Script Fails to Connect

**Symptoms**: Connection refused or timeout errors

**Solutions**:
1. Verify environment URL is correct
2. Check ALB is accessible
3. Verify security groups allow traffic
4. Check services are running

### Authentication Fails

**Symptoms**: 401 Unauthorized errors

**Solutions**:
1. Verify admin credentials (username: admin, password: admin)
2. Check user service is running
3. Verify database has admin user
4. Check JWT secret is configured

### Rate Limiting Errors

**Symptoms**: 429 Too Many Requests

**Solutions**:
1. Scripts include delays between requests
2. Increase delays if needed
3. Check API Gateway rate limits
4. Run scripts during off-peak hours

### Data Creation Fails

**Symptoms**: Items or movements not created

**Solutions**:
1. Check database connectivity
2. Verify database migrations are current
3. Check CloudWatch logs for errors
4. Verify item types exist
5. Check location types exist

### Partial Data Created

**Symptoms**: Some items created, others failed

**Solutions**:
1. Review script logs for specific errors
2. Check which step failed
3. Fix the issue
4. Re-run the script (idempotent)

## Customizing Seed Data

### Modify Item Counts

Edit `reseed_complete_inventory.py`:

```python
# Change from 10 to desired count
for i in range(10):  # <-- Change this number
    # Create items...
```

### Modify Movement Count

Edit `generate_movements.py`:

```python
# Change movement range
num_moves = random.randint(0, 4)  # <-- Change max value
```

### Add New Item Types

Edit `reseed_complete_inventory.py`:

```python
# Add new parent type
new_tower = get_or_create_item_type("New Tower", "parent")

# Add to configs
configs = [
    # ... existing configs ...
    {
        'type': new_tower,
        'children': [
            {'type': some_child_type},
            # ... more children ...
        ]
    }
]
```

### Add New Locations

Edit `reseed_complete_inventory.py`:

```python
# Add more hospitals
for name in ["Hospital A", "Hospital B", "Hospital C", "Hospital D", "Hospital E", "Hospital F"]:
    # ... create location ...
```

## Environment-Specific Configuration

The scripts automatically detect the environment from the `ENVIRONMENT` variable:

```python
ENVIRONMENTS = {
    "dev": "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com",
    "staging": "http://staging-inventory-alb.us-east-1.elb.amazonaws.com"
}

API_BASE_URL = ENVIRONMENTS.get(os.environ.get("ENVIRONMENT", "dev"))
```

To add a new environment:
1. Add entry to `ENVIRONMENTS` dict in each script
2. Update GitHub Actions workflow to include new environment option

## Best Practices

### Before Seeding

1. ✅ Verify environment is healthy
2. ✅ Check database is accessible
3. ✅ Confirm admin credentials work
4. ✅ Review existing data (will be deleted)

### During Seeding

1. ✅ Monitor script output
2. ✅ Watch for errors
3. ✅ Check CloudWatch logs
4. ✅ Be patient (takes 10-15 minutes)

### After Seeding

1. ✅ Verify data in UI
2. ✅ Test inventory listing
3. ✅ Test movement history
4. ✅ Test role permissions
5. ✅ Document seed date/version

## Seed Data Summary

After successful seeding, you should have:

| Data Type | Count | Details |
|-----------|-------|---------|
| Roles | 6 | admin + 5 default roles |
| Parent Items | 70 | 10 of each type |
| Child Items | ~200-300 | Varies by configuration |
| Locations | 10+ | 5 hospitals + warehouses + quarantine |
| Movements | 125+ | Random movement history |

## Related Documentation

- [Staging Deployment Guide](./STAGING_DEPLOYMENT.md)
- [Database Migrations](./DATABASE_MIGRATIONS.md)
- [API Documentation](./API.md)
