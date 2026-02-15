"""Run database migrations for staging environment."""
import subprocess
import os

# Set the database URL for staging
os.environ['DATABASE_URL'] = 'postgresql://inventory_user:InventoryDB2025!@staging-inventory-db.c47e2qi82sp6.us-east-1.rds.amazonaws.com:5432/inventory_management'

# Run alembic upgrade
print("Running database migrations...")
result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)
print(f"Exit code: {result.returncode}")
