# Build and push all Docker images to ECR
$ErrorActionPreference = "Stop"

$ACCOUNT_ID = "290993374431"
$REGION = "us-west-2"
$ECR_REGISTRY = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

$services = @(
    "inventory",
    "location", 
    "user",
    "reporting",
    "ui"
)

Write-Host "Building and pushing Docker images to ECR..." -ForegroundColor Green

foreach ($service in $services) {
    Write-Host "Building $service..." -ForegroundColor Yellow
    
    # Build the image
    docker build -t "inventory-management/$service`:latest" -f "services/$service/Dockerfile" .
    
    # Tag for ECR
    docker tag "inventory-management/$service`:latest" "$ECR_REGISTRY/inventory-management/$service`:latest"
    
    # Push to ECR
    Write-Host "Pushing $service to ECR..." -ForegroundColor Yellow
    docker push "$ECR_REGISTRY/inventory-management/$service`:latest"
    
    Write-Host "✓ $service completed" -ForegroundColor Green
}

Write-Host "All images built and pushed successfully!" -ForegroundColor Green