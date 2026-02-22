#!/bin/bash
# Reset dev database to clean state

set -e

echo "=========================================="
echo "Dev Database Reset Script"
echo "=========================================="

# Database connection details
DB_HOST="dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com"
DB_NAME="inventory_management"
DB_USER="inventory_admin"

echo ""
echo "This script will:"
echo "1. Connect to the dev database"
echo "2. Drop all tables"
echo "3. Run migrations from scratch"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Step 1: Dropping all tables..."
echo "-------------------------------"

# SQL to drop all tables
PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Drop all tables
DROP TABLE IF EXISTS assignment_history CASCADE;
DROP TABLE IF EXISTS move_history CASCADE;
DROP TABLE IF EXISTS child_items CASCADE;
DROP TABLE IF EXISTS parent_items CASCADE;
DROP TABLE IF EXISTS item_types CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS location_types CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Drop enum types
DROP TYPE IF EXISTS itemcategory CASCADE;

\echo 'All tables dropped successfully'
EOF

if [ $? -eq 0 ]; then
    echo "✓ Tables dropped successfully"
else
    echo "✗ Failed to drop tables"
    exit 1
fi

echo ""
echo "Step 2: Running migrations via API..."
echo "--------------------------------------"

# Login to get token
TOKEN=$(curl -s -X POST "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "✗ Failed to login - admin user may not exist yet"
    echo "  This is expected after dropping tables"
    echo ""
    echo "Manual steps required:"
    echo "1. Restart the user service to recreate admin user"
    echo "2. Run migrations via API"
    exit 1
fi

# Run migrations
MIGRATION_RESULT=$(curl -s -X POST "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/api/v1/admin/run-migrations" \
    -H "Authorization: Bearer $TOKEN")

echo "$MIGRATION_RESULT"

if echo "$MIGRATION_RESULT" | grep -q "success"; then
    echo "✓ Migrations completed successfully"
else
    echo "✗ Migration failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ Dev database reset complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify API is working: curl http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/api/v1/location-types"
echo "2. Test location deletion: python scripts/test_dev_location_deletion.py"
