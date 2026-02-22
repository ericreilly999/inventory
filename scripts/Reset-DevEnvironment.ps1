# Reset Dev Environment by restarting services
# This will force ECS to recreate containers and run migrations fresh

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "=" * 70
Write-Host "Dev Environment Reset"
Write-Host "=" * 70
Write-Host ""

if (-not $Force) {
    Write-Host "This script will:"
    Write-Host "1. Stop all ECS tasks in dev cluster"
    Write-Host "2. Force new deployment (pulls latest images)"
    Write-Host "3. Services will restart and run migrations"
    Write-Host ""
    $confirm = Read-Host "Continue? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Aborted."
        exit 1
    }
}

$region = "us-west-2"
$cluster = "dev-inventory-cluster"
$services = @(
    "dev-api-gateway",
    "dev-inventory-service",
    "dev-location-service",
    "dev-user-service",
    "dev-reporting-service",
    "dev-ui-service"
)

Write-Host ""
Write-Host "Step 1: Stopping all running tasks..."
Write-Host "---------------------------------------"

foreach ($service in $services) {
    Write-Host "Stopping tasks for: $service"
    
    # Get running tasks
    $tasks = aws ecs list-tasks `
        --cluster $cluster `
        --service-name $service `
        --region $region `
        --query "taskArns" `
        --output json | ConvertFrom-Json
    
    if ($tasks.Count -gt 0) {
        foreach ($task in $tasks) {
            Write-Host "  Stopping task: $($task.Split('/')[-1])"
            aws ecs stop-task `
                --cluster $cluster `
                --task $task `
                --region $region `
                --no-cli-pager | Out-Null
        }
        Write-Host "  [OK] Tasks stopped"
    } else {
        Write-Host "  No running tasks"
    }
}

Write-Host ""
Write-Host "Step 2: Forcing new deployment..."
Write-Host "-----------------------------------"

foreach ($service in $services) {
    Write-Host "Updating service: $service"
    
    aws ecs update-service `
        --cluster $cluster `
        --service $service `
        --force-new-deployment `
        --region $region `
        --no-cli-pager | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Deployment triggered"
    } else {
        Write-Host "  [FAIL] Failed to update service"
    }
}

Write-Host ""
Write-Host "Step 3: Waiting for services to stabilize..."
Write-Host "----------------------------------------------"
Write-Host "(This may take 5-10 minutes)"
Write-Host ""

foreach ($service in $services) {
    Write-Host "Waiting for: $service"
    
    aws ecs wait services-stable `
        --cluster $cluster `
        --services $service `
        --region $region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Service stable"
    } else {
        Write-Host "  [WARN] Service may not be stable yet"
    }
}

Write-Host ""
Write-Host "Step 4: Verifying deployment..."
Write-Host "---------------------------------"

Start-Sleep -Seconds 10

# Test API
try {
    $response = Invoke-WebRequest `
        -Uri "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/api/v1/auth/login" `
        -Method POST `
        -Body '{"username":"admin","password":"admin"}' `
        -ContentType "application/json" `
        -UseBasicParsing `
        -TimeoutSec 10
    
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] API is responding"
        
        $token = ($response.Content | ConvertFrom-Json).access_token
        
        # Test location types endpoint
        $locTypesResponse = Invoke-WebRequest `
            -Uri "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/api/v1/location-types" `
            -Headers @{Authorization = "Bearer $token"} `
            -UseBasicParsing `
            -TimeoutSec 10
        
        if ($locTypesResponse.StatusCode -eq 200) {
            $locTypes = $locTypesResponse.Content | ConvertFrom-Json
            Write-Host "Location Types endpoint working ($($locTypes.Count) types)"
        }
    }
} catch {
    Write-Host "API verification failed: $_"
    Write-Host "  Services may still be starting up"
}

Write-Host ""
Write-Host "=" * 70
Write-Host "[SUCCESS] Dev environment reset complete!"
Write-Host "=" * 70
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Wait a few minutes for all services to fully start"
Write-Host "2. Run migrations: python scripts/run_dev_migration.py"
Write-Host "3. Test location deletion: python scripts/test_dev_location_deletion.py"
