# Staging Environment Setup - Implementation Summary

## ✅ Completed Tasks

### 1. Dev Environment Scale-Down
- ✅ Updated Terraform configuration to scale dev services to 1 task each
- ✅ Modified `terraform/environments/dev/main.tf`:
  - API Gateway: 3 → 1 task
  - Inventory Service: 2 → 1 task
  - Location Service: 2 → 1 task
- ✅ Expected cost savings: ~40-50% reduction in ECS task costs

### 2. Staging Terraform Configuration
- ✅ Created complete staging environment configuration in `terraform/environments/staging/`
- ✅ Files created:
  - `main.tf`: All services configured with 2 tasks, auto-scaling disabled
  - `variables.tf`: Environment-specific variables
  - `terraform.tfvars`: Staging values (us-east-1, db.t3.small)
  - `outputs.tf`: ALB URL and resource outputs
  - `backend.tf`: S3 state backend configuration

### 3. Tag-Based Deployment Workflow
- ✅ Created `.github/workflows/deploy-staging.yml`
- ✅ Workflow triggers on semantic version tags (v*.*.*)
- ✅ Deployment pipeline includes:
  - Test execution (unit, integration, property-based)
  - Docker image builds with version tags
  - ECR push to us-east-1
  - ECS service updates
  - Health check verification
  - Deployment status notification

### 4. Multi-Environment Seed Scripts
- ✅ Updated all seed scripts to support multiple environments:
  - `scripts/setup_default_roles.py`
  - `scripts/reseed_complete_inventory.py`
  - `scripts/generate_movements.py`
- ✅ Scripts now accept `ENVIRONMENT` variable (dev/staging)
- ✅ Environment-specific API URLs configured

### 5. Manual Seed Workflow
- ✅ Created `.github/workflows/seed-staging-data.yml`
- ✅ Manual trigger via workflow_dispatch
- ✅ Runs all three seed scripts in sequence
- ✅ Supports both dev and staging environments

### 6. Comprehensive Documentation
- ✅ Created `docs/STAGING_DEPLOYMENT.md`: Complete staging deployment guide
- ✅ Created `docs/SEEDING_GUIDE.md`: Data seeding instructions
- ✅ Created `docs/RUNBOOK.md`: Operational runbook with troubleshooting
- ✅ Updated `README.md`: Added staging environment information

## 📋 Next Steps (Manual Execution Required)

### Step 1: Apply Dev Scale-Down
```bash
cd terraform/environments/dev
terraform plan
terraform apply
```
**Expected**: Dev services will scale from 3/2 tasks to 1 task each

### Step 2: Create ECR Repositories in us-east-1
```bash
# Create repositories for all services
aws ecr create-repository --repository-name inventory-management/api-gateway --region us-east-1
aws ecr create-repository --repository-name inventory-management/user-service --region us-east-1
aws ecr create-repository --repository-name inventory-management/inventory-service --region us-east-1
aws ecr create-repository --repository-name inventory-management/location-service --region us-east-1
aws ecr create-repository --repository-name inventory-management/reporting-service --region us-east-1
aws ecr create-repository --repository-name inventory-management/ui-service --region us-east-1
```

### Step 3: Deploy Staging Infrastructure
```bash
cd terraform/environments/staging
terraform init
terraform plan
# Review the plan carefully
terraform apply
```
**Expected**: Creates complete staging environment in us-east-1

### Step 4: Update Seed Scripts with Staging URL
After staging deployment, get the ALB URL from Terraform outputs:
```bash
terraform output alb_url
```

Update the staging URL in seed scripts:
- `scripts/setup_default_roles.py`
- `scripts/reseed_complete_inventory.py`
- `scripts/generate_movements.py`

Replace placeholder with actual staging ALB URL.

### Step 5: Test Tag-Based Deployment
```bash
# Create and push a test tag
git add .
git commit -m "feat: staging environment setup complete"
git push origin main

# Create version tag
git tag v0.1.0
git push origin v0.1.0
```
**Expected**: Triggers staging deployment workflow

### Step 6: Seed Staging Data
1. Go to GitHub Actions
2. Select "Seed Staging Data" workflow
3. Click "Run workflow"
4. Select "staging" environment
5. Click "Run workflow"

**Expected**: Creates 70 items, 6 roles, 125+ movements

### Step 7: Verify Staging Environment
- [ ] Access staging ALB URL
- [ ] Login with admin credentials
- [ ] Verify 2 tasks running per service in ECS
- [ ] Test inventory functionality
- [ ] Test movement creation
- [ ] Test user management
- [ ] Test role management

## 📊 Configuration Summary

### Dev Environment (us-west-2)
| Service | Tasks | CPU | Memory | Auto-scaling |
|---------|-------|-----|--------|--------------|
| API Gateway | 1 | 512 | 1024 | Enabled |
| User Service | 1 | 256 | 512 | Enabled |
| Inventory Service | 1 | 512 | 1024 | Enabled |
| Location Service | 1 | 512 | 1024 | Enabled |
| Reporting Service | 1 | 256 | 512 | Enabled |
| UI Service | 1 | 256 | 512 | Enabled |
| **Database** | db.t3.micro | | | |

### Staging Environment (us-east-1)
| Service | Tasks | CPU | Memory | Auto-scaling |
|---------|-------|-----|--------|--------------|
| API Gateway | 2 | 512 | 1024 | **Disabled** |
| User Service | 2 | 256 | 512 | **Disabled** |
| Inventory Service | 2 | 512 | 1024 | **Disabled** |
| Location Service | 2 | 512 | 1024 | **Disabled** |
| Reporting Service | 2 | 256 | 512 | **Disabled** |
| UI Service | 2 | 256 | 512 | **Disabled** |
| **Database** | db.t3.small | | | |

## 🔄 Deployment Workflows

### Dev Deployment (Automatic)
```
Push to main → CI tests → Build images → Deploy to dev (us-west-2)
```

### Staging Deployment (Tag-Based)
```
Push tag v*.*.* → Run tests → Build images → Push to ECR (us-east-1) → Deploy to staging
```

### Manual Seeding
```
GitHub Actions → Seed Staging Data → Select environment → Run scripts
```

## 📝 Files Created/Modified

### New Files
- `.github/workflows/deploy-staging.yml` - Staging deployment workflow
- `.github/workflows/seed-staging-data.yml` - Manual seed workflow
- `terraform/environments/staging/main.tf` - Staging infrastructure
- `terraform/environments/staging/variables.tf` - Staging variables
- `terraform/environments/staging/terraform.tfvars` - Staging values
- `terraform/environments/staging/outputs.tf` - Staging outputs
- `terraform/environments/staging/backend.tf` - State backend config
- `docs/STAGING_DEPLOYMENT.md` - Deployment guide
- `docs/SEEDING_GUIDE.md` - Seeding instructions
- `docs/RUNBOOK.md` - Operational runbook
- `STAGING_SETUP_SUMMARY.md` - This file

### Modified Files
- `terraform/environments/dev/main.tf` - Scaled down to 1 task per service
- `scripts/setup_default_roles.py` - Added environment support
- `scripts/reseed_complete_inventory.py` - Added environment support
- `scripts/generate_movements.py` - Added environment support
- `README.md` - Added staging environment documentation

## 💰 Cost Estimates

### Monthly Costs
- **Dev** (after scale-down): ~$140/month
- **Staging**: ~$172/month
- **Total**: ~$312/month

### Cost Breakdown (Staging)
- ECS Tasks (12 tasks): $35
- RDS (db.t3.small): $30
- ElastiCache: $12
- ALB: $20
- NAT Gateway: $65
- Data Transfer: $5
- CloudWatch Logs: $5

## 🎯 Success Criteria

- [x] Dev environment scaled to 1 task per service
- [x] Staging Terraform configuration created
- [x] Tag-based deployment workflow implemented
- [x] Seed scripts support multiple environments
- [x] Manual seed workflow created
- [x] Comprehensive documentation written
- [ ] ECR repositories created in us-east-1 (manual)
- [ ] Staging infrastructure deployed (manual)
- [ ] First tag deployment successful (manual)
- [ ] Staging seeded with demo data (manual)
- [ ] All services verified healthy (manual)

## 🔗 Quick Links

- [Staging Deployment Guide](docs/STAGING_DEPLOYMENT.md)
- [Seeding Guide](docs/SEEDING_GUIDE.md)
- [Deployment Runbook](docs/RUNBOOK.md)
- [Staging Terraform Config](terraform/environments/staging/)
- [Deploy Staging Workflow](.github/workflows/deploy-staging.yml)
- [Seed Data Workflow](.github/workflows/seed-staging-data.yml)

## 📞 Support

For issues or questions:
1. Check the documentation links above
2. Review CloudWatch logs in AWS Console
3. Check GitHub Actions workflow logs
4. Review this summary document

---

**Status**: Configuration complete, ready for manual deployment steps
**Date**: 2026-02-01
**Version**: v0.1.0 (initial staging setup)
