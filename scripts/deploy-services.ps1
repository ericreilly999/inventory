# Deploy Services Script
# This script builds, pushes, and deploys services to ECS with proper image digests

param(
    [Parameter(Mandatory=$false)]
    [string[]]$Services = @("location", "inventory", "user", "reporting", "api_gateway"),
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-west-2",
    
    [Parameter(Mandatory=$false)]
    [string]$Cluster = "dev-inventory-cluster",
    
    [Parameter(Mandatory=$false)]
    [string]$ECRRegistry = "290993374431.dkr.ecr.us-west-2.amazonaws.com"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Inventory Management Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Login to ECR
Write-Host "[1/4] Logging in to Amazon ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECRRegistry
if ($LASTEXITCODE -ne 0) {
    Write-Host "ECR login failed (credential storage error is OK)" -ForegroundColor Yellow
}

$deployedServices = @()

foreach ($service in $Services) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Processing service: $service" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    # Determine service name and dockerfile path
    $serviceName = if ($service -eq "api_gateway") { "api-gateway" } else { "$service-service" }
    $dockerfilePath = "services/$service/Dockerfile"
    $repoName = "inventory-management/$serviceName"
    $ecsServiceName = "dev-$serviceName"
    
    # Build Docker image
    Write-Host "[2/4] Building Docker image for $service..." -ForegroundColor Yellow
    docker build -t "$repoName:latest" -f $dockerfilePath . 2>&1 | Select-String -Pattern "Step|FINISHED|ERROR|exporting"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed for $service" -ForegroundColor Red
        continue
    }
    
    # Tag and push image
    Write-Host "[3/4] Pushing Docker image to ECR..." -ForegroundColor Yellow
    $imageTag = "$ECRRegistry/$repoName`:latest"
    docker tag "$repoName:latest" $imageTag
    docker push $imageTag 2>&1 | Select-String -Pattern "Pushed|digest|latest|ERROR"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Push failed for $service" -ForegroundColor Red
        continue
    }
    
    # Get image digest
    Write-Host "Getting image digest..." -ForegroundColor Yellow
    $imageDigest = aws ecr describe-images `
        --repository-name $repoName `
        --region $Region `
        --image-ids imageTag=latest `
        --query "imageDetails[0].imageDigest" `
        --output text
    
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($imageDigest)) {
        Write-Host "Failed to get image digest for $service" -ForegroundColor Red
        continue
    }
    
    Write-Host "Image digest: $imageDigest" -ForegroundColor Cyan
    
    # Stop old task to force pull new image
    Write-Host "[4/4] Deploying to ECS..." -ForegroundColor Yellow
    Write-Host "Stopping old task to force image pull..." -ForegroundColor Yellow
    
    $taskArn = aws ecs list-tasks `
        --cluster $Cluster `
        --service-name $ecsServiceName `
        --region $Region `
        --query "taskArns[0]" `
        --output text
    
    if (-not [string]::IsNullOrEmpty($taskArn) -and $taskArn -ne "None") {
        aws ecs stop-task `
            --cluster $Cluster `
            --task $taskArn `
            --region $Region `
            --query "task.taskArn" `
            --output text | Out-Null
        
        Write-Host "Old task stopped. Waiting for new task to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
    
    # Force new deployment
    Write-Host "Forcing new deployment..." -ForegroundColor Yellow
    aws ecs update-service `
        --cluster $Cluster `
        --service $ecsServiceName `
        --force-new-deployment `
        --region $Region `
        --query "service.serviceName" `
        --output text | Out-Null
    
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
    
    $serviceInfo = aws ecs describe-services `
        --cluster $Cluster `
        --services $ecsServiceName `
        --region $Region `
        --query "services[0].{Running:runningCount,Desired:desiredCount}" `
        --output json | ConvertFrom-Json
    
    if ($serviceInfo.Running -eq $serviceInfo.Desired) {
        Write-Host "  ✓ $service : $($serviceInfo.Running)/$($serviceInfo.Desired) tasks running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $service : $($serviceInfo.Running)/$($serviceInfo.Desired) tasks running" -ForegroundColor Yellow
    }
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
