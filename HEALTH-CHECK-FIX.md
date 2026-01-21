# Health Check Failures - Root Cause and Fix

## Problem

Both inventory and location services were constantly failing health checks and restarting, causing:
- Multiple running tasks (2 running when desired count is 1)
- Service instability
- Potential data inconsistencies

## Root Cause

**Port Configuration Mismatch in Terraform**

The Terraform configuration had the ports swapped:

| Service | Actual Port | Terraform Port | Status |
|---------|-------------|----------------|--------|
| Inventory | 8003 | 8002 | ❌ WRONG |
| Location | 8002 | 8003 | ❌ WRONG |

This caused:
1. ECS task definitions to be created with wrong port mappings
2. Health checks to check the wrong ports
3. Health checks to fail continuously
4. ECS to restart tasks thinking they were unhealthy
5. Multiple tasks running simultaneously

## Evidence

From ECS task definition for inventory-service:
```json
{
  "name": "inventory-service",
  "port": 8002,  // WRONG - should be 8003
  "healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:8002/health || exit 1"]
  }
}
```

From service status:
```json
{
  "name": "dev-inventory-service",
  "running": 2,  // Should be 1
  "desired": 1
}
```

## Solution

Fixed port mappings in `terraform/environments/dev/main.tf`:

**Inventory Service:**
```terraform
container_port = 8003  # Changed from 8002
```

**Location Service:**
```terraform
container_port = 8002  # Changed from 8003
```

## How to Apply the Fix

The Terraform changes need to be applied to update the task definitions:

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

This will:
1. Update the ECS task definitions with correct port mappings
2. Update health check commands to check correct ports
3. Trigger a new deployment with the corrected configuration
4. Stop the restart loop

## Verification

After applying Terraform changes:

1. Check service status:
```bash
aws ecs describe-services \
  --cluster dev-inventory-cluster \
  --services dev-inventory-service dev-location-service \
  --region us-west-2 \
  --query "services[*].{name:serviceName,running:runningCount,desired:desiredCount}"
```

Expected: `running` should equal `desired` (both should be 1)

2. Check task health:
```bash
aws ecs describe-tasks \
  --cluster dev-inventory-cluster \
  --tasks $(aws ecs list-tasks --cluster dev-inventory-cluster --service-name dev-inventory-service --region us-west-2 --query 'taskArns[0]' --output text) \
  --region us-west-2 \
  --query 'tasks[0].healthStatus'
```

Expected: `HEALTHY`

3. Check CloudWatch logs for health check success:
```bash
aws logs tail /ecs/dev-inventory --since 5m --filter-pattern "health" --region us-west-2
```

Expected: No health check failures

## Files Changed

- `terraform/environments/dev/main.tf` - Fixed port mappings

## Commit

**Commit:** 3c697f8

## Why This Happened

The ports were likely swapped during initial Terraform configuration. The services were defined with:
- Inventory on port 8003 (in code)
- Location on port 8002 (in code)

But Terraform was configured with the opposite mapping, possibly due to:
- Copy-paste error during initial setup
- Confusion about which service uses which port
- Changes to port assignments after Terraform was initially configured

## Prevention

To prevent this in the future:
1. Document port assignments clearly in README
2. Add validation in Terraform to check port consistency
3. Include port numbers in service names or comments
4. Test health checks immediately after infrastructure changes
