# Staging Environment Deployment Guide

## Overview
This document describes how to deploy to the staging environment using semantic versioning tags.

## Environments

### Dev Environment
- **Region**: us-west-2
- **URL**: http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com
- **Deployment**: Automatic on push to `main` branch
- **Task Count**: 1 task per service
- **Database**: db.t3.micro

### Staging Environment
- **Region**: us-east-1
- **URL**: Will be available after first deployment (check Terraform outputs)
- **Deployment**: Manual via semantic version tags
- **Task Count**: 2 tasks per service
- **Database**: db.t3.small
- **Auto-scaling**: Disabled

## Deploying to Staging

### Prerequisites
1. All changes merged to `main` branch
2. All tests passing in CI
3. Code reviewed and approved

### Deployment Process

#### 1. Create a Semantic Version Tag

Tags must follow the format `v*.*.*` (e.g., `v1.0.0`, `v1.1.0`, `v2.0.0`)

**Semantic Versioning Guidelines**:
- **MAJOR** version (v**X**.0.0): Breaking changes, incompatible API changes
- **MINOR** version (v1.**X**.0): New features, backwards-compatible
- **PATCH** version (v1.0.**X**): Bug fixes, backwards-compatible

**Example**:
```bash
# Create a tag for version 1.0.0
git tag v1.0.0

# Push the tag to GitHub
git push origin v1.0.0
```

#### 2. Monitor Deployment

The tag push will automatically trigger the "Deploy to Staging" workflow:

1. Go to GitHub Actions: https://github.com/YOUR_ORG/YOUR_REPO/actions
2. Find the "Deploy to Staging" workflow run
3. Monitor the progress through these stages:
   - **Test**: Runs unit, integration, and property-based tests
   - **Build and Push**: Builds Docker images with version tag
   - **Deploy Staging**: Updates ECS services with new images
   - **Notify**: Reports deployment status

#### 3. Verify Deployment

After the workflow completes successfully:

1. Check ECS services in AWS Console (us-east-1):
   - All services should show 2/2 tasks running
   - Task definitions should reference the new version tag

2. Test the staging URL:
   ```bash
   curl http://STAGING_ALB_URL/health
   ```

3. Test the UI:
   - Open staging URL in browser
   - Login with admin credentials
   - Verify functionality

#### 4. Seed Data (Optional)

If this is the first deployment or you need fresh demo data:

1. Go to GitHub Actions
2. Select "Seed Staging Data" workflow
3. Click "Run workflow"
4. Select "staging" environment
5. Click "Run workflow"
6. Monitor the seeding process

The seed workflow will:
- Create 6 default roles
- Create 70 parent items (10 of each type)
- Create child items for each parent
- Generate 125+ movement history records

## Rollback Procedures

### Option 1: Tag-Based Rollback (Recommended)

Deploy a previous version by pushing its tag again:

```bash
# Identify the last known good version
git tag -l

# Push the previous version tag
git push origin v1.0.0 --force
```

This will trigger a new deployment with the previous version.

### Option 2: Manual Rollback via AWS Console

1. Go to ECS Console (us-east-1)
2. Select the staging cluster
3. For each service:
   - Click "Update"
   - Select previous task definition revision
   - Click "Update Service"
4. Wait for services to stabilize

### Option 3: Manual Rollback via AWS CLI

```bash
# List task definition revisions
aws ecs list-task-definitions \
  --family-prefix staging-api-gateway \
  --region us-east-1

# Update service to previous revision
aws ecs update-service \
  --cluster staging-inventory-cluster \
  --service staging-api-gateway \
  --task-definition staging-api-gateway:PREVIOUS_REVISION \
  --region us-east-1
```

## Database Migrations

Database migrations are run automatically during deployment via the admin endpoint:
```
POST /api/v1/user/admin/run-migrations
```

If migrations fail, you can run them manually:

1. SSH into an ECS task or use ECS Exec
2. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```

### Rolling Back Migrations

If you need to rollback database changes:

```bash
# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade REVISION_ID
```

## Troubleshooting

### Deployment Fails at Build Stage

**Symptoms**: Docker build fails or images can't be pushed to ECR

**Solutions**:
1. Check Docker build logs in GitHub Actions
2. Verify ECR repositories exist in us-east-1
3. Check AWS credentials are valid
4. Verify Dockerfile syntax

### Deployment Fails at Deploy Stage

**Symptoms**: ECS services don't update or tasks fail to start

**Solutions**:
1. Check ECS service events in AWS Console
2. Verify task definition is valid
3. Check CloudWatch logs for container errors
4. Verify security groups allow traffic
5. Check task execution role permissions

### Services Unhealthy After Deployment

**Symptoms**: Health checks failing, tasks restarting

**Solutions**:
1. Check CloudWatch logs for errors
2. Verify database connectivity
3. Check Redis connectivity
4. Verify environment variables are correct
5. Check security group rules

### Seed Scripts Fail

**Symptoms**: Seed workflow fails or data not created

**Solutions**:
1. Check seed script logs in GitHub Actions
2. Verify staging ALB URL is correct in scripts
3. Test API endpoints manually
4. Check database connectivity
5. Verify admin credentials work

## Best Practices

### Before Deploying

1. ✅ Test changes thoroughly in dev environment
2. ✅ Run all tests locally
3. ✅ Review code changes
4. ✅ Update version number appropriately
5. ✅ Document breaking changes

### During Deployment

1. ✅ Monitor GitHub Actions workflow
2. ✅ Watch ECS service updates in AWS Console
3. ✅ Check CloudWatch logs for errors
4. ✅ Be ready to rollback if issues occur

### After Deployment

1. ✅ Verify all services healthy
2. ✅ Test critical functionality
3. ✅ Check for errors in logs
4. ✅ Update documentation if needed
5. ✅ Notify team of deployment

## Version History

Track your staging deployments:

| Version | Date | Changes | Deployed By |
|---------|------|---------|-------------|
| v1.0.0 | TBD | Initial staging deployment | - |

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review GitHub Actions workflow logs
3. Check AWS ECS service events
4. Contact DevOps team

## Related Documentation

- [Terraform Configuration](../terraform/environments/staging/)
- [GitHub Actions Workflows](../.github/workflows/)
- [Database Migrations](./DATABASE_MIGRATIONS.md)
- [General Deployment Guide](./DEPLOYMENT.md)
