# Deployment Guide

## Overview

This guide covers deploying the Inventory Management System to AWS ECS.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Docker installed and running
- PowerShell (for Windows) or Bash (for Linux/Mac)
- Access to ECR repository: `290993374431.dkr.ecr.us-west-2.amazonaws.com`

## Deployment Methods

### Method 1: Automated Deployment Script (Recommended)

Use the PowerShell deployment script for reliable, repeatable deployments:

```powershell
# Deploy all services
.\scripts\deploy-services.ps1

# Deploy specific services only
.\scripts\deploy-services.ps1 -Services @("location", "user")

# Deploy to different region/cluster
.\scripts\deploy-services.ps1 -Region us-west-2 -Cluster dev-inventory-cluster
```

The script will:
1. Login to ECR
2. Build Docker images for each service
3. Push images to ECR with proper tags
4. Stop old ECS tasks to force image pull
5. Deploy new tasks with updated images
6. Wait and verify deployment health

### Method 2: GitHub Actions CI/CD

Push code to the `main` branch to trigger automatic deployment:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

The GitHub Actions workflow will:
1. Build and push Docker images with commit SHA tags
2. Deploy to dev environment automatically
3. Wait for services to stabilize
4. Run health checks

### Method 3: Manual Deployment

For manual control over the deployment process:

```powershell
# 1. Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 290993374431.dkr.ecr.us-west-2.amazonaws.com

# 2. Build image
docker build -t inventory-management/location-service:latest -f services/location/Dockerfile .

# 3. Tag image
docker tag inventory-management/location-service:latest 290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/location-service:latest

# 4. Push image
docker push 290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/location-service:latest

# 5. Stop old task (forces new image pull)
$taskArn = aws ecs list-tasks --cluster dev-inventory-cluster --service-name dev-location-service --region us-west-2 --query "taskArns[0]" --output text
aws ecs stop-task --cluster dev-inventory-cluster --task $taskArn --region us-west-2

# 6. Force new deployment
aws ecs update-service --cluster dev-inventory-cluster --service dev-location-service --force-new-deployment --region us-west-2
```

## Service Architecture

### Services and Ports

| Service | Port | ECS Service Name | ECR Repository |
|---------|------|------------------|----------------|
| API Gateway | 8000 | dev-api-gateway | inventory-management/api-gateway |
| User Service | 8001 | dev-user-service | inventory-management/user-service |
| Location Service | 8002 | dev-location-service | inventory-management/location-service |
| Inventory Service | 8003 | dev-inventory-service | inventory-management/inventory-service |
| Reporting Service | 8004 | dev-reporting-service | inventory-management/reporting-service |

### Infrastructure

- **Region**: us-west-2
- **ECS Cluster**: dev-inventory-cluster
- **Load Balancer**: dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com
- **Database**: dev-inventory-db.c54y4qiae8o2.us-west-2.rds.amazonaws.com

## Troubleshooting

### Issue: Services not pulling new images

**Problem**: ECS caches Docker images with `latest` tag

**Solution**: Stop the old task before deploying
```powershell
$taskArn = aws ecs list-tasks --cluster dev-inventory-cluster --service-name dev-location-service --region us-west-2 --query "taskArns[0]" --output text
aws ecs stop-task --cluster dev-inventory-cluster --task $taskArn --region us-west-2
```

### Issue: Unhealthy containers

**Problem**: Container health checks failing

**Solution**: Check CloudWatch logs
```powershell
# View recent logs
aws logs tail /ecs/dev-inventory --region us-west-2 --since 5m --follow

# Filter for specific service
aws logs tail /ecs/dev-inventory --region us-west-2 --since 5m --filter-pattern "location-service"
```

### Issue: 403 Forbidden errors after deployment

**Problem**: Old JWT tokens have incorrect permission format

**Solution**: Log out and log back in to get new JWT token with correct format

### Issue: Deployment stuck

**Problem**: ECS service not stabilizing

**Solution**: Check service events
```powershell
aws ecs describe-services --cluster dev-inventory-cluster --services dev-location-service --region us-west-2 --query "services[0].events[0:5]"
```

## Post-Deployment Checklist

After deploying, verify:

- [ ] All services show 1/1 tasks running
- [ ] Health checks passing (200 OK)
- [ ] No errors in CloudWatch logs
- [ ] API endpoints responding correctly
- [ ] Users can log in successfully
- [ ] Dashboard loads without errors

## Monitoring

### Check Service Health

```powershell
aws ecs describe-services --cluster dev-inventory-cluster --services dev-location-service dev-inventory-service dev-user-service dev-reporting-service dev-api-gateway --region us-west-2 --query "services[*].{Name:serviceName,Running:runningCount,Desired:desiredCount}" --output table
```

### View Logs

```powershell
# Tail logs in real-time
aws logs tail /ecs/dev-inventory --region us-west-2 --follow

# View last 100 log entries
aws logs tail /ecs/dev-inventory --region us-west-2 --since 10m

# Filter for errors
aws logs filter-log-events --log-group-name "/ecs/dev-inventory" --region us-west-2 --filter-pattern "ERROR" --max-items 20
```

### Check Task Status

```powershell
# List running tasks
aws ecs list-tasks --cluster dev-inventory-cluster --region us-west-2

# Get task details
aws ecs describe-tasks --cluster dev-inventory-cluster --tasks <task-arn> --region us-west-2
```

## Rollback

If deployment fails, rollback to previous version:

```powershell
# Get previous task definition
aws ecs describe-services --cluster dev-inventory-cluster --services dev-location-service --region us-west-2 --query "services[0].deployments[1].taskDefinition"

# Update service to use previous task definition
aws ecs update-service --cluster dev-inventory-cluster --service dev-location-service --task-definition <previous-task-def> --region us-west-2
```

## Best Practices

1. **Always test locally first** before deploying to AWS
2. **Use the deployment script** for consistent deployments
3. **Monitor logs** during and after deployment
4. **Stop old tasks** to ensure new images are pulled
5. **Wait for stabilization** before testing (60 seconds minimum)
6. **Log out/in after deployment** to get new JWT tokens
7. **Check all services** not just the ones you deployed
8. **Keep deployment logs** for troubleshooting

## Common Deployment Scenarios

### Scenario 1: Fix a bug in one service

```powershell
# Deploy only the affected service
.\scripts\deploy-services.ps1 -Services @("location")
```

### Scenario 2: Deploy all services after major changes

```powershell
# Deploy all services
.\scripts\deploy-services.ps1

# Wait for stabilization
Start-Sleep -Seconds 60

# Verify health
aws ecs describe-services --cluster dev-inventory-cluster --services dev-location-service dev-inventory-service dev-user-service dev-reporting-service dev-api-gateway --region us-west-2 --query "services[*].{Name:serviceName,Running:runningCount,Desired:desiredCount}" --output table
```

### Scenario 3: Emergency rollback

```powershell
# Stop all new tasks
$services = @("dev-location-service", "dev-inventory-service", "dev-user-service", "dev-reporting-service", "dev-api-gateway")
foreach ($service in $services) {
    $taskArn = aws ecs list-tasks --cluster dev-inventory-cluster --service-name $service --region us-west-2 --query "taskArns[0]" --output text
    if ($taskArn) {
        aws ecs stop-task --cluster dev-inventory-cluster --task $taskArn --region us-west-2
    }
}

# ECS will automatically start tasks with the previous image
```

## Support

For deployment issues:
1. Check CloudWatch logs first
2. Verify service health in ECS console
3. Review this deployment guide
4. Check the troubleshooting section above
