# Terraform Apply Rollback Note

## What Happened

When we applied Terraform changes to fix the health check issues, several services were rolled back to task definition revision 4:
- api-gateway: revision 17 → 4
- user-service: revision 17 → 4  
- reporting-service: revision 17 → 4

## Why This Happened

Terraform manages infrastructure state separately from the CD pipeline:
1. Terraform state had the original task definition configurations (revision 4)
2. CD pipeline had been deploying newer revisions (17, 18, etc.) with updated Docker images
3. When Terraform applied, it "corrected" the services back to what was in its state
4. Terraform doesn't track the CD pipeline's deployments

## Impact

These services are now running old code from revision 4, not the latest code with all our fixes.

## Solution

Trigger the CD pipeline to redeploy all services with the latest code. This commit will trigger the pipeline.

## Prevention

Going forward, we have two options:

### Option 1: Let CD Pipeline Manage Task Definitions (Recommended)
- Remove task definition management from Terraform
- Let the CD pipeline create and update task definitions
- Terraform only manages the ECS service configuration (not task definitions)

### Option 2: Keep Terraform and CD Pipeline in Sync
- Update Terraform state after each CD deployment
- More complex and error-prone

We should implement Option 1 to avoid this issue in the future.
