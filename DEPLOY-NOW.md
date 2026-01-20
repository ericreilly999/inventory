# Deploy Now - Manual Commands

The PowerShell scripts have syntax issues. Use these direct commands instead:

## Get Commit SHA

```powershell
$SHA = (git rev-parse --short HEAD).Trim()
Write-Host "Deploying with SHA: $SHA"
```

## Deploy Location Service

```powershell
# Build and push
docker build -t location-service:$SHA -f services/location/Dockerfile .
docker tag location-service:$SHA 290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/location-service:$SHA
docker push 290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/location-service:$SHA

# Get current task definition and update image
$taskDef = aws ecs describe-task-definition --task-definition dev-location-service --region us-west-2 --query "taskDefinition" --output json | ConvertFrom-Json
$taskDef.containerDefinitions[0].image = "290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/location-service:$SHA"
$taskDef.PSObject.Properties.Remove('taskDefinitionArn')
$taskDef.PSObject.Properties.Remove('revision')
$taskDef.PSObject.Properties.Remove('status')
$taskDef.PSObject.Properties.Remove('requiresAttributes')
$taskDef.PSObject.Properties.Remove('compatibilities')
$taskDef.PSObject.Properties.Remove('registeredAt')
$taskDef.PSObject.Properties.Remove('registeredBy')

# Save and register
$taskDef | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 task-def-location.json
$newTask = aws ecs register-task-definition --cli-input-json file://task-def-location.json --region us-west-2 --output json | ConvertFrom-Json
$newRev = $newTask.taskDefinition.revision

# Update service
aws ecs update-service --cluster dev-inventory-cluster --service dev-location-service --task-definition "dev-location-service:$newRev" --force-new-deployment --region us-west-2
```

## Deploy User Service

```powershell
# Build and push
docker build -t user-service:$SHA -f services/user/Dockerfile .
docker tag user-service:$SHA 290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/user-service:$SHA
docker push 290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/user-service:$SHA

# Get current task definition and update image
$taskDef = aws ecs describe-task-definition --task-definition dev-user-service --region us-west-2 --query "taskDefinition" --output json | ConvertFrom-Json
$taskDef.containerDefinitions[0].image = "290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/user-service:$SHA"
$taskDef.PSObject.Properties.Remove('taskDefinitionArn')
$taskDef.PSObject.Properties.Remove('revision')
$taskDef.PSObject.Properties.Remove('status')
$taskDef.PSObject.Properties.Remove('requiresAttributes')
$taskDef.PSObject.Properties.Remove('compatibilities')
$taskDef.PSObject.Properties.Remove('registeredAt')
$taskDef.PSObject.Properties.Remove('registeredBy')

# Save and register
$taskDef | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 task-def-user.json
$newTask = aws ecs register-task-definition --cli-input-json file://task-def-user.json --region us-west-2 --output json | ConvertFrom-Json
$newRev = $newTask.taskDefinition.revision

# Update service
aws ecs update-service --cluster dev-inventory-cluster --service dev-user-service --task-definition "dev-user-service:$newRev" --force-new-deployment --region us-west-2
```

## Verify Deployment

```powershell
# Wait a bit
Start-Sleep -Seconds 60

# Check services
aws ecs describe-services --cluster dev-inventory-cluster --services dev-location-service dev-user-service --region us-west-2 --query "services[*].{Name:serviceName,TaskDef:taskDefinition,Running:runningCount,Desired:desiredCount}" --output table
```

## After Deployment

1. Log out of the application
2. Log back in to get new JWT token
3. Test these pages:
   - Dashboard (should show chart)
   - Location Types (no 422 error)
   - Users (no 403 error)
   - Roles (no 403 error)

## For Future Deployments

Once you merge the CD workflow fixes to main, GitHub Actions will handle this automatically with proper image tagging.
