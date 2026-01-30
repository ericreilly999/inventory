# How to Run the Database Migration

## Problem

The application code expects a `sku` column but the database still has `name` columns. This causes all API endpoints to return 500 errors because the services crash when querying the database.

## Solution

Run the migration SQL manually against the RDS database.

## Option 1: Via AWS Systems Manager Session Manager (Recommended)

If you have an EC2 bastion host or can use Session Manager:

```bash
# Connect to database via psql
psql "postgresql://inventory_user:InventoryDB2025!@dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com:5432/inventory_management"

# Run the migration SQL
\i manual_migration.sql

# Or run commands directly:
ALTER TABLE parent_items RENAME COLUMN name TO sku;
ALTER TABLE child_items RENAME COLUMN name TO sku;
UPDATE alembic_version SET version_num = '49871d03964c';
```

## Option 2: Via AWS RDS Query Editor

1. Go to AWS Console → RDS → Query Editor
2. Connect to `dev-inventory-db`
3. Use credentials from Secrets Manager: `dev/inventory-management/database`
4. Run these SQL commands:

```sql
ALTER TABLE parent_items RENAME COLUMN name TO sku;
ALTER TABLE child_items RENAME COLUMN name TO sku;
UPDATE alembic_version SET version_num = '49871d03964c';
```

## Option 3: Temporarily Enable Public Access (Not Recommended)

1. Modify RDS instance to allow public access
2. Update security group to allow your IP
3. Run migration from local machine:
   ```bash
   python run_migration_direct.py
   ```
4. Disable public access and remove security group rule

## Option 4: Via EC2 Bastion Host

If you have a bastion host in the VPC:

```bash
# SSH to bastion
ssh -i your-key.pem ec2-user@bastion-ip

# Install psql if needed
sudo yum install postgresql -y

# Connect and run migration
psql "postgresql://inventory_user:InventoryDB2025!@dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com:5432/inventory_management"

# Run SQL
ALTER TABLE parent_items RENAME COLUMN name TO sku;
ALTER TABLE child_items RENAME COLUMN name TO sku;
UPDATE alembic_version SET version_num = '49871d03964c';
```

## Verification

After running the migration, verify it worked:

```sql
-- Check columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'parent_items' AND column_name = 'sku';

-- Check alembic version
SELECT * FROM alembic_version;
-- Should show: 49871d03964c

-- Check data
SELECT id, sku, description FROM parent_items LIMIT 5;
SELECT id, sku, description FROM child_items LIMIT 5;
```

Then test the application:
```bash
curl http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/api/inventory/parent-items
```

You should see items with `sku` values instead of null.

## Why This Happened

1. We created the migration file and updated all code to use `sku`
2. We deployed the code changes
3. But the migration never ran because:
   - The ECS migration task definition doesn't exist yet (needs Terraform apply)
   - The admin endpoint can't run migrations because the services crash on startup (they can't query the database with the wrong column name)
   - We can't run it from local machine because RDS is in a private subnet

## Future Prevention

Once this migration is complete, we'll:
1. Apply the Terraform to create the migration task definition
2. Re-enable the migration step in the CD pipeline
3. Future migrations will run automatically before deployment
