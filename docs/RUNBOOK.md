# Deployment Runbook

## Quick Reference

### Environment URLs
- **Dev**: http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com
- **Staging**: Check Terraform outputs after deployment

### Credentials
- **Username**: admin
- **Password**: admin

### AWS Regions
- **Dev**: us-west-2
- **Staging**: us-east-1

## Pre-Deployment Checklist

- [ ] All changes merged to `main` branch
- [ ] All tests passing in CI
- [ ] Code reviewed and approved
- [ ] Version number decided (semantic versioning)
- [ ] Breaking changes documented
- [ ] Team notified of upcoming deployment

## Deployment Steps

### For Dev Environment (Automatic)

1. **Merge to Main**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Push Changes**
   ```bash
   git push origin main
   ```

3. **Monitor Deployment**
   - Go to GitHub Actions
   - Watch "Continuous Deployment" workflow
   - Verify all steps complete successfully

4. **Verify Deployment**
   - Check dev URL is accessible
   - Test login
   - Verify changes deployed

### For Staging Environment (Tag-Based)

1. **Create Version Tag**
   ```bash
   # Determine version (MAJOR.MINOR.PATCH)
   git tag v1.0.0
   
   # Push tag
   git push origin v1.0.0
   ```

2. **Monitor Deployment**
   - Go to GitHub Actions
   - Watch "Deploy to Staging" workflow
   - Monitor these stages:
     - Test (unit, integration, property-based)
     - Build and Push (Docker images)
     - Deploy Staging (ECS services)
     - Notify (status report)

3. **Verify Deployment**
   - Check ECS Console (us-east-1)
   - Verify 2/2 tasks running per service
   - Test staging URL
   - Test login
   - Verify functionality

4. **Seed Data (If Needed)**
   - Go to GitHub Actions
   - Run "Seed Staging Data" workflow
   - Select "staging" environment
   - Monitor seeding progress
   - Verify data in UI

## Post-Deployment Verification

### Health Checks

```bash
# Dev environment
curl http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/health

# Staging environment
curl http://STAGING_ALB_URL/health
```

### Service Status

Check ECS Console:
- All services show desired task count
- All tasks are healthy
- No tasks stuck in pending/stopping

### Application Tests

1. **Login Test**
   - Navigate to environment URL
   - Login with admin credentials
   - Verify dashboard loads

2. **Inventory Test**
   - Navigate to Inventory page
   - Verify items load
   - Test filtering and search

3. **Movement Test**
   - Create a test movement
   - Verify movement recorded
   - Check movement history

4. **User Management Test**
   - Navigate to Users page
   - Create test user
   - Verify user created

5. **Role Management Test**
   - Navigate to Roles page
   - Verify roles exist
   - Test role permissions

### Logs Review

Check CloudWatch Logs for errors:
```bash
# List log groups
aws logs describe-log-groups \
  --log-group-name-prefix /ecs/staging-inventory \
  --region us-east-1

# Tail logs for a service
aws logs tail /ecs/staging-inventory-api-gateway \
  --follow \
  --region us-east-1
```

## Rollback Procedures

### Quick Rollback (Tag-Based)

```bash
# Identify last known good version
git tag -l

# Push previous version tag
git push origin v1.0.0 --force
```

### Manual Rollback (AWS Console)

1. Go to ECS Console (appropriate region)
2. Select cluster
3. For each service:
   - Click service name
   - Click "Update"
   - Select "Revision" dropdown
   - Choose previous revision
   - Click "Update Service"
4. Wait for services to stabilize

### Manual Rollback (AWS CLI)

```bash
# Update service to previous revision
aws ecs update-service \
  --cluster staging-inventory-cluster \
  --service staging-api-gateway \
  --task-definition staging-api-gateway:PREVIOUS_REVISION \
  --force-new-deployment \
  --region us-east-1
```

### Database Rollback

```bash
# Connect to database
psql -h DB_ENDPOINT -U inventory_user -d inventory_management

# Or use Alembic
alembic downgrade -1
```

## Common Issues and Solutions

### Issue: Deployment Stuck

**Symptoms**: Workflow running for > 30 minutes

**Solutions**:
1. Check GitHub Actions logs
2. Look for hanging steps
3. Cancel and retry
4. Check AWS service limits

### Issue: Tasks Won't Start

**Symptoms**: ECS tasks fail to start or immediately stop

**Solutions**:
1. Check CloudWatch logs for errors
2. Verify task definition is valid
3. Check security groups
4. Verify IAM roles
5. Check resource availability (CPU/memory)

### Issue: Health Checks Failing

**Symptoms**: Tasks start but fail health checks

**Solutions**:
1. Check application logs
2. Verify database connectivity
3. Check Redis connectivity
4. Verify environment variables
5. Test health endpoint manually

### Issue: Database Connection Errors

**Symptoms**: Services can't connect to database

**Solutions**:
1. Verify security groups allow traffic
2. Check database is running
3. Verify connection string
4. Check database credentials
5. Test connection from ECS task

### Issue: Seed Scripts Fail

**Symptoms**: Seeding workflow fails

**Solutions**:
1. Check script logs
2. Verify API is accessible
3. Test admin credentials
4. Check database state
5. Run scripts manually

## Emergency Contacts

### On-Call Rotation
- Check PagerDuty for current on-call engineer

### Escalation Path
1. DevOps Team Lead
2. Engineering Manager
3. CTO

## Monitoring and Alerts

### CloudWatch Dashboards
- ECS Service Metrics
- ALB Metrics
- RDS Metrics
- Application Metrics

### Key Metrics to Watch
- Task count (should match desired count)
- CPU utilization (< 70%)
- Memory utilization (< 80%)
- Request latency (< 500ms)
- Error rate (< 1%)

### Alert Thresholds
- Task count below desired: Immediate alert
- High CPU (> 80%): Warning
- High memory (> 90%): Warning
- High error rate (> 5%): Immediate alert
- Database connections exhausted: Immediate alert

## Maintenance Windows

### Scheduled Maintenance
- **Dev**: Anytime (no SLA)
- **Staging**: Weekdays 9 AM - 5 PM ET (demo environment)

### Emergency Maintenance
- Follow change management process
- Notify stakeholders
- Document changes
- Verify after completion

## Documentation Updates

After each deployment:
1. Update version history in STAGING_DEPLOYMENT.md
2. Document any issues encountered
3. Update runbook if new procedures discovered
4. Share learnings with team

## Related Documentation

- [Staging Deployment Guide](./STAGING_DEPLOYMENT.md)
- [Seeding Guide](./SEEDING_GUIDE.md)
- [Database Migrations](./DATABASE_MIGRATIONS.md)
- [Terraform Documentation](../terraform/README.md)
