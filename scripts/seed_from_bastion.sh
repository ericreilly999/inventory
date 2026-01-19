#!/bin/bash
# Script to seed the database from a bastion host or EC2 instance with database access

# Database connection details
DB_HOST="dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com"
DB_PORT="5432"
DB_NAME="inventory_management"
DB_USER="inventory_user"
DB_PASSWORD="InventoryDB2025!"

echo "Connecting to database and seeding admin user..."

# Install psql if not available
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL client..."
    sudo yum update -y
    sudo yum install -y postgresql15
fi

# Run the SQL script
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f scripts/seed_admin_direct.sql

if [ $? -eq 0 ]; then
    echo "✅ Database seeded successfully!"
    echo "   You can now log in with:"
    echo "   Username: admin"
    echo "   Password: secret"
    echo "   URL: http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/"
else
    echo "❌ Failed to seed database"
    exit 1
fi