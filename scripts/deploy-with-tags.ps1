# Deploy Services Script with Tagged Images
# This script builds, tags with commit SHA, pushes, and deploys services to ECS

param(
    [Parameter(Mandatory=$false)]
    [string[]]$Services = @("location", "user"),
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-west-2",
    
    [Parameter(Mandatory=$false)]
    [string]$Cluster = "dev-inventory-cluster",
    
    [Parameter(Mandatory=$false)]
    [string]$ECRRegistry = "290993374431.dkr.ecr.us-west-2.amazonaws.com"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tagged Image Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get current commit SHA
$commitSHA = (git rev-parse --short HEAD).Trim()
Write-Host "Commit SHA: $commitSHA" -ForegroundColor Cyan
Write-Host ""

# Login to ECR
Write-Host "[1/5] Logging in to Amazon ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECRRegistry
if ($LASTEXITCODE -ne 0) {
    Write-Host "ECR login failed" -ForegroundColor Red
    exit 1
}

$deployedServices = @()

foreach ($service in $Services) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Processing service: $service" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    # Determine service name
    $serviceName = if ($service -eq "api_gateway") { "api-gateway" } else { "$service-service" }
    $dockerfilePath = "services/$service/Dockerfile"
    $repoName = "inventory-management/$serviceName"
    $ecsServiceName = "dev-$serviceName"
    
    # Build Docker image
    Write-Host "[2/5] Building Docker image for $service..." -ForegroundColor Yellow
    $imageWithTag = "${repoName}:${commitSHA}"
    docker build -t $imageWithTag -f $dockerfilePath .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed for $service" -ForegroundColor Red
        continue
    }
    
    # Tag and push image with commit SHA
    Write-Host "[3/5] Pushing Docker image to ECR with tag $commitSHA..." -ForegroundColor Yellow
    $imageTagSHA = "${ECRRegistry}/${repoName}:${commitSHA}"
    $imageTagLatest = "${ECRRegistry}/${repoName}:latest"
    
    docker tag $imageWithTag $imageTagSHA
    docker tag $imageWithTag $imageTagLatest
    
    docker push $imageTagSHA
    docker push $imageTagLatest
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Push failed for $service" -ForegroundColor Red
        continue
    }
    
    Write-Host "Pushed: $imageTagSHA" -ForegroundColor Cyan
    Write-Host "Pushed: $imageTagLatest" -ForegroundColor Cyan
    
    # Get current task definition
    Write-Host "[4/5] Creating new task definition..." -ForegroundColor Yellow
    $taskDefJson = aws ecs describe-task-definition `
        --task-definition $ecsServiceName `
        --region $Region `
        --query "taskDefinition" `
        --output json
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to get task definition for $service" -ForegroundColor Red
        continue
    }
    
    # Parse and update task definition
    $taskDef = $taskDefJson | ConvertFrom-Json
    $taskDef.containerDefinitions[0].image = $imageTagSHA
    
    # Remove fields that can't be in register-task-definition
    $taskDef.PSObject.Properties.Remove('taskDefinitionArn')
    $taskDef.PSObject.Properties.Remove('revision')
    $taskDef.PSObject.Properties.Remove('status')
    $taskDef.PSObject.Properties.Remove('requiresAttributes')
    $taskDef.PSObject.Properties.Remove('compatibilities')
    $taskDef.PSObject.Properties.Remove('registeredAt')
    $taskDef.PSObject.Properties.Remove('registeredBy')
    
    # Save to temp file
    $tempFile = [System.IO.Path]::GetTempFileName()
    $taskDef | ConvertTo-Json -Depth 10 | Set-Content $tempFile
    
    # Register new task definition
    $newTaskDefJson = aws ecs register-task-definition `
        --cli-input-json "file://$tempFile" `
        --region $Region `
        --output json
    
    Remove-Item $tempFile
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to register new task definition for $service" -ForegroundColor Red
        continue
    }
    
    $newTaskDef = $newTaskDefJson | ConvertFrom-Json
    $newRevision = $newTaskDef.taskDefinition.revision
    Write-Host "New task definition: $ecsServiceName`:$newRevision" -ForegroundColor Cyan
    
    # Update service with new task definition
    Write-Host "[5/5] Updating ECS service..." -ForegroundColor Yellow
    $taskDefWithRevision = "${ecsServiceName}:${newRevision}"
    aws ecs update-service `
        --cluster $Cluster `
        --service $ecsServiceName `
        --task-definition $taskDefWithRevision `
        --force-new-deployment `
        --region $Region `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Deployment initiated for $service" -ForegroundColor Green
        $deployedServices += $service
    } else {
        Write-Host "✗ Deployment failed for $service" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Commit SHA: $commitSHA" -ForegroundColor Cyan
Write-Host "Successfully deployed services:" -ForegroundColor Green
foreach ($service in $deployedServices) {
    Write-Host "  ✓ $service" -ForegroundColor Green
}

Write-Host ""
Write-Host "Waiting for services to stabilize (60 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

Write-Host ""
Write-Host "Checking service health..." -ForegroundColor Yellow
foreach ($service in $deployedServices) {
    $serviceName = if ($service -eq "api_gateway") { "api-gateway" } else { "$service-service" }
    $ecsServiceName = "dev-$serviceName"
    
    $serviceInfoJson = aws ecs describe-services `
        --cluster $Cluster `
        --services $ecsServiceName `
        --region $Region `
        --query "services[0].{TaskDef:taskDefinition,Running:runningCount,Desired:desiredCount}" `
        --output json
    
    $serviceInfo = $serviceInfoJson | ConvertFrom-Json
    
    Write-Host "  Service: $service" -ForegroundColor White
    Write-Host "    Task Definition: $($serviceInfo.TaskDef)" -ForegroundColor Gray
    Write-Host "    Running: $($serviceInfo.Running)/$($serviceInfo.Desired)" -ForegroundColor $(if ($serviceInfo.Running -eq $serviceInfo.Desired) { "Green" } else { "Yellow" })
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Check CloudWatch logs for any errors" -ForegroundColor White
Write-Host "2. Test the application endpoints" -ForegroundColor White
Write-Host "3. Log out and log back in to get new JWT tokens" -ForegroundColor White
