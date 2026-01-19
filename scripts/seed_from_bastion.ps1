# PowerShell script to seed the database from a Windows bastion host

# Database connection details
$DB_HOST = "dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com"
$DB_PORT = "5432"
$DB_NAME = "inventory_management"
$DB_USER = "inventory_user"
$DB_PASSWORD = "InventoryDB2025!"

Write-Host "Connecting to database and seeding admin user..." -ForegroundColor Green

# Check if psql is available
if (!(Get-Command psql -ErrorAction SilentlyContinue)) {
    Write-Host "PostgreSQL client (psql) not found. Please install PostgreSQL client tools." -ForegroundColor Red
    Write-Host "Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    exit 1
}

# Set password environment variable
$env:PGPASSWORD = $DB_PASSWORD

# Run the SQL script
try {
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f scripts/seed_admin_direct.sql
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database seeded successfully!" -ForegroundColor Green
        Write-Host "   You can now log in with:" -ForegroundColor Cyan
        Write-Host "   Username: admin" -ForegroundColor White
        Write-Host "   Password: secret" -ForegroundColor White
        Write-Host "   URL: http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/" -ForegroundColor White
    } else {
        Write-Host "❌ Failed to seed database" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error running psql: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Clear password environment variable
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}