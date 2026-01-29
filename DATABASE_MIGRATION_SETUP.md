# Database Migration Setup

## Database Credentials Retrieved

From AWS Secrets Manager (`dev/inventory-management/database`):

```json
{
  "dbname": "inventory_management",
  "engine": "postgres",
  "host": "dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com",
  "port": 5432,
  "username": "inventory_user",
  "password": "InventoryDB2025!"
}
```

## DATABASE_URL Format

The DATABASE_URL should be set as a GitHub secret with the following value:

**IMPORTANT:** Use `inventory_management` as the database name (not `database`)

```
postgresql://inventory_user:InventoryDB2025!@dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com:5432/inventory_management
```

## Steps to Add GitHub Secret

1. Go to your GitHub repository: https://github.com/ericreilly999/inventory
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `DATABASE_URL`
5. Value: `postgresql://inventory_user:InventoryDB2025!@dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com:5432/inventory_management`
6. Click **Add secret**

## What Happens Next

Once the secret is added:

1. The next deployment will automatically run database migrations
2. The migration will rename the `name` column to `sku` in both `parent_items` and `child_items` tables
3. The application will work correctly with the new schema
4. All future deployments will run migrations automatically

## Manual Migration (Alternative)

If you prefer to run the migration manually instead of through CI/CD:

```bash
# Set the DATABASE_URL environment variable
export DATABASE_URL="postgresql://inventory_user:InventoryDB2025!@dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com:5432/inventory_management"

# Install alembic if not already installed
pip install alembic psycopg2-binary sqlalchemy

# Run the migration
alembic upgrade head
```

## Verification

After the migration runs, you can verify it worked by:

1. Checking the GitHub Actions logs for "Running Database Migrations"
2. Testing the inventory page - items should now show SKU values
3. Checking CloudWatch logs - no more "column sku does not exist" errors

## Migration Details

**Migration File:** `migrations/versions/rename_name_to_sku.py`

**What it does:**
- Renames `parent_items.name` → `parent_items.sku`
- Renames `child_items.name` → `child_items.sku`
- Preserves all existing data
- No data loss

**Revision ID:** `49871d03964c`
**Previous Revision:** `48871d03964b`

## Rollback (if needed)

If something goes wrong, you can rollback the migration:

```bash
export DATABASE_URL="postgresql://inventory_user:InventoryDB2025!@dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com:5432/inventory_management"
alembic downgrade -1
```

This will revert the column names back to `name`.
