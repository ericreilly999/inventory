# Staging Environment Setup - Design Document

## Overview
This design document outlines the technical approach for creating a staging environment in us-east-1, scaling down the dev environment, and implementing tag-based deployments with semantic versioning.

## Architecture

### Environment Comparison

| Component | Dev (us-west-2) | Staging (us-east-1) |
|-----------|-----------------|---------------------|
| API Gateway | 1 task (512 CPU, 1024 MB) | 2 tasks (512 CPU, 1024 MB) |
| Inventory Service | 1 task (512 CPU, 1024 MB) | 2 tasks (512 CPU, 1024 MB) |
| Location Service | 1 task (512 CPU, 1024 MB) | 2 tasks (512 CPU, 1024 MB) |
| User Service | 1 task (256 CPU, 512 MB) | 2 tasks (256 CPU, 512 MB) |
| Reporting Service | 1 task (256 CPU, 512 MB) | 2 tasks (256 CPU, 512 MB) |
| UI Service | 1 task (256 CPU, 512 MB) | 2 tasks (256 CPU, 512 MB) |
| Database | db.t3.micro | db.t3.small |
| Redis | cache.t3.micro (1 node) | cache.t3.micro (1 node) |
| Auto-scaling | Enabled | Disabled |

### Infrastructure Components

#### 1. Networking
- **VPC**: Separate VPC per environment
  - Dev: 10.0.0.0/16 (us-west-2)
  - Staging: 10.1.0.0/16 (us-east-1)
- **Subnets**: 
  - 2 public subnets (for ALB)
  - 2 private subnets (for ECS tasks)
  - 2 database subnets (for RDS)
- **NAT Gateway**: One per AZ for private subnet internet access
- **Internet Gateway**: For public subnet access

#### 2. Security
- **Security Groups**:
  - ALB: Allow HTTP/HTTPS from internet
  - ECS: Allow traffic from ALB and internal services
  - RDS: Allow PostgreSQL from ECS security group
  - ElastiCache: Allow Redis from ECS security group
- **IAM Roles**:
  - ECS Task Execution Role (pull images, write logs)
  - ECS Task Role (application permissions)

#### 3. Database
- **RDS PostgreSQL**:
  - Dev: db.t3.micro (1 vCPU, 1 GB RAM)
  - Staging: db.t3.small (2 vCPU, 2 GB RAM)
  - Storage: 20 GB GP3
  - Multi-AZ: No (cost optimization)
  - Backup retention: 7 days
  - Automated backups: Enabled
- **Connection Pooling**: 
  - Dev: 5 min / 10 max connections
  - Staging: 10 min / 20 max connections

#### 4. Caching
- **ElastiCache Redis**:
  - Node type: cache.t3.micro
  - Nodes: 1 (single node)
  - Engine version: 7.x
  - Encryption at rest: Enabled
  - Encryption in transit: Enabled

#### 5. Load Balancing
- **Application Load Balancer**:
  - Scheme: Internet-facing
  - Listeners: HTTP (80)
  - Target Groups:
    - API Gateway (port 8000)
    - UI Service (port 80)
  - Health checks: /health endpoint
  - Deregistration delay: 30 seconds

#### 6. Container Orchestration
- **ECS Cluster**: Fargate launch type
- **Service Discovery**: AWS Cloud Map for internal service communication
- **Task Definitions**: One per service with specific CPU/memory
- **Auto-scaling**: Disabled for staging (manual verification required)

## Terraform Structure

### Directory Layout
```
terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── outputs.tf
│   └── staging/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── outputs.tf
├── modules/
│   ├── networking/
│   ├── security/
│   ├── rds/
│   ├── elasticache/
│   ├── alb/
│   ├── ecs-cluster/
│   ├── ecs-service/
│   └── migration-task/
└── shared/
    └── backend.tf
```

### State Management
- **Backend**: S3 with DynamoDB locking
- **State Files**:
  - Dev: `s3://inventory-terraform-state/dev/terraform.tfstate`
  - Staging: `s3://inventory-terraform-state/staging/terraform.tfstate`
- **Workspaces**: Not used (separate directories instead)

### Module Reusability
All modules are environment-agnostic and accept environment-specific parameters:
- `environment`: Environment name (dev, staging)
- `aws_region`: AWS region
- `desired_count`: Number of tasks per service
- `db_instance_class`: RDS instance size
- `enable_auto_scaling`: Auto-scaling toggle

## CI/CD Pipeline Design

### Workflow Triggers

#### 1. Dev Deployment (Existing)
- **Trigger**: Push to `main` branch
- **Image Tags**: `latest` and `<commit-sha>`
- **Target**: Dev environment (us-west-2)

#### 2. Staging Deployment (New)
- **Trigger**: Git tag push matching `v*.*.*` pattern
- **Image Tags**: `<tag-version>` (e.g., `v1.0.0`)
- **Target**: Staging environment (us-east-1)
- **Semantic Versioning**: MAJOR.MINOR.PATCH format

### Deployment Workflow

```yaml
name: Deploy to Staging

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  1. Run Tests (unit, integration, property-based)
  2. Build Docker Images (tag with version)
  3. Push to ECR (us-east-1 registry)
  4. Run Database Migrations
  5. Deploy Services (update task definitions)
  6. Wait for Stability
  7. Run Health Checks
  8. Trigger Manual Seed (optional)
```

### Image Tagging Strategy

| Environment | Tag Format | Example |
|-------------|------------|---------|
| Dev | `latest`, `<sha>` | `latest`, `a1b2c3d` |
| Staging | `v<version>` | `v1.0.0`, `v1.1.0` |

### ECR Repositories
- **Region-specific**: Separate ECR repositories per region
  - Dev: `290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/*`
  - Staging: `290993374431.dkr.ecr.us-east-1.amazonaws.com/inventory-management/*`
- **Repositories**:
  - `inventory-management/api-gateway`
  - `inventory-management/user-service`
  - `inventory-management/inventory-service`
  - `inventory-management/location-service`
  - `inventory-management/reporting-service`
  - `inventory-management/ui-service`

### Deployment Steps Detail

#### Step 1: Run Tests
```bash
pytest tests/unit -v
pytest tests/integration -v
pytest tests/property -v --hypothesis-seed=random
```
- All tests must pass before proceeding
- Property-based tests run with random seed for coverage

#### Step 2: Build Images
```bash
docker build -t $ECR_REGISTRY/inventory-management/api-gateway:$TAG \
  -f services/api_gateway/Dockerfile .
# Repeat for all services
```
- Multi-stage builds for optimization
- Layer caching enabled via GitHub Actions cache

#### Step 3: Push to ECR
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY
docker push $ECR_REGISTRY/inventory-management/api-gateway:$TAG
```
- Authenticate with ECR
- Push all service images with version tag

#### Step 4: Run Migrations
```bash
# Via ECS task or admin endpoint
curl -X POST https://$STAGING_ALB/api/v1/user/admin/run-migrations \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```
- Alembic migrations applied to staging database
- Idempotent (safe to run multiple times)

#### Step 5: Deploy Services
```bash
# Update task definitions with new image tags
aws ecs update-service \
  --cluster staging-inventory-cluster \
  --service staging-api-gateway \
  --task-definition staging-api-gateway:$NEW_REVISION \
  --force-new-deployment
```
- Update all 6 services sequentially
- Force new deployment to pull latest images

#### Step 6: Wait for Stability
```bash
aws ecs wait services-stable \
  --cluster staging-inventory-cluster \
  --services staging-api-gateway \
  --max-attempts 30 \
  --delay 10
```
- Wait up to 5 minutes per service
- Verify all tasks are running and healthy

#### Step 7: Health Checks
```bash
curl -f https://$STAGING_ALB/health || exit 1
curl -f https://$STAGING_ALB/api/v1/user/health || exit 1
# Check all service health endpoints
```
- Verify all services respond to health checks
- Fail deployment if any service is unhealthy

#### Step 8: Manual Seed Trigger (Optional)
- GitHub Actions workflow dispatch
- Runs seed scripts against staging database
- Triggered manually after deployment verification

## Data Seeding Strategy

### Seed Scripts Execution Order
1. **Setup Roles**: `scripts/setup_default_roles.py`
   - Creates 6 default roles with permissions
   - Idempotent (checks for existing roles)
   
2. **Seed Inventory**: `scripts/reseed_complete_inventory.py`
   - Creates 70 parent items (10 of each type)
   - Creates child items for each parent
   - Distributes items across locations
   - Creates initial movement history
   
3. **Generate Movements**: `scripts/generate_movements.py`
   - Moves items 0-4 times randomly
   - Creates realistic movement history
   - Total ~125+ movements

### Manual Trigger Workflow
```yaml
name: Seed Staging Data

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to seed'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging

jobs:
  seed-data:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Configure AWS credentials
      - Get staging ALB URL from Terraform outputs
      - Run setup_default_roles.py
      - Run reseed_complete_inventory.py
      - Run generate_movements.py
      - Verify data seeded successfully
```

### Seed Script Modifications
Update scripts to accept environment parameter:
```python
# Environment-specific configuration
ENVIRONMENTS = {
    "dev": "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com",
    "staging": "http://staging-inventory-alb-XXXXXXXX.us-east-1.elb.amazonaws.com"
}

API_BASE_URL = ENVIRONMENTS.get(os.environ.get("ENVIRONMENT", "dev"))
```

## Scaling Down Dev Environment

### Changes Required
Update `terraform/environments/dev/main.tf`:

```hcl
# API Gateway Service - Scale from 3 to 1
module "api_gateway_service" {
  # ... existing config ...
  desired_count = 1  # Changed from 3
}

# Inventory Service - Scale from 2 to 1
module "inventory_service" {
  # ... existing config ...
  desired_count = 1  # Changed from 2
}

# Location Service - Scale from 2 to 1
module "location_service" {
  # ... existing config ...
  desired_count = 1  # Changed from 2
}

# Other services remain at 1
```

### Deployment Process
1. Update Terraform configuration
2. Run `terraform plan` to verify changes
3. Run `terraform apply` to scale down
4. Monitor service health during scale-down
5. Verify all services remain functional

### Expected Cost Savings
- API Gateway: 3 tasks → 1 task (~66% reduction)
- Inventory Service: 2 tasks → 1 task (~50% reduction)
- Location Service: 2 tasks → 1 task (~50% reduction)
- **Total**: ~40-50% reduction in ECS task costs for dev

## Staging Environment Configuration

### Terraform Variables (`terraform/environments/staging/terraform.tfvars`)
```hcl
# Staging environment configuration
aws_region  = "us-east-1"
environment = "staging"
vpc_cidr    = "10.1.0.0/16"

# Database configuration
db_instance_class    = "db.t3.small"  # Upgraded from micro
db_allocated_storage = 20
db_name              = "inventory_management"
db_username          = "inventory_user"

# Cache configuration
cache_node_type = "cache.t3.micro"
cache_num_nodes = 1

# Container images (us-east-1 ECR)
api_gateway_image       = "290993374431.dkr.ecr.us-east-1.amazonaws.com/inventory-management/api-gateway:v1.0.0"
user_service_image      = "290993374431.dkr.ecr.us-east-1.amazonaws.com/inventory-management/user-service:v1.0.0"
inventory_service_image = "290993374431.dkr.ecr.us-east-1.amazonaws.com/inventory-management/inventory-service:v1.0.0"
location_service_image  = "290993374431.dkr.ecr.us-east-1.amazonaws.com/inventory-management/location-service:v1.0.0"
reporting_service_image = "290993374431.dkr.ecr.us-east-1.amazonaws.com/inventory-management/reporting-service:v1.0.0"
ui_service_image        = "290993374431.dkr.ecr.us-east-1.amazonaws.com/inventory-management/ui-service:v1.0.0"
```

### Service Configuration
All services configured with `desired_count = 2` and `enable_auto_scaling = false`:

```hcl
module "api_gateway_service" {
  source = "../../modules/ecs-service"
  
  # ... existing config ...
  desired_count        = 2
  enable_auto_scaling  = false
  
  # ... rest of config ...
}
```

## Security Considerations

### Secrets Management
- **Database Password**: Stored in AWS Secrets Manager
- **JWT Secret**: Unique per environment, stored in Secrets Manager
- **Redis Auth Token**: Generated and stored in Secrets Manager
- **GitHub Secrets**: AWS credentials for deployment

### Network Security
- **Private Subnets**: All ECS tasks run in private subnets
- **Security Groups**: Least-privilege access rules
- **No Public IPs**: Tasks access internet via NAT Gateway
- **ALB Only**: Public access only through load balancer

### Access Control
- **IAM Roles**: Separate roles per environment
- **Resource Tags**: All resources tagged with environment
- **CloudWatch Logs**: Separate log groups per environment
- **Encryption**: At-rest and in-transit encryption enabled

## Monitoring and Observability

### CloudWatch Logs
- **Log Groups**: `/ecs/staging-inventory-<service>`
- **Retention**: 7 days (cost optimization)
- **Log Streams**: One per task

### CloudWatch Metrics
- **ECS Metrics**: CPU, memory, task count
- **ALB Metrics**: Request count, latency, error rate
- **RDS Metrics**: Connections, CPU, storage
- **Custom Metrics**: Application-level metrics

### Health Checks
- **ECS Health Checks**: Container-level health via Docker
- **ALB Health Checks**: HTTP health endpoint checks
- **Frequency**: Every 30 seconds
- **Thresholds**: 3 consecutive failures = unhealthy

### Alerting (Future)
- Critical failures in staging
- Database connection issues
- High error rates
- Service unavailability

## Rollback Strategy

### Tag-Based Rollback
1. Identify last known good version tag (e.g., `v1.0.0`)
2. Push rollback tag or re-push existing tag
3. Deployment workflow runs with previous version
4. Services updated to previous task definitions
5. Verify rollback successful

### Manual Rollback
```bash
# Update service to previous task definition
aws ecs update-service \
  --cluster staging-inventory-cluster \
  --service staging-api-gateway \
  --task-definition staging-api-gateway:$PREVIOUS_REVISION
```

### Database Rollback
- Alembic downgrade migrations if needed
- Restore from RDS snapshot (last resort)
- Test rollback procedures in dev first

## Testing Strategy

### Pre-Deployment Testing
- All unit tests must pass
- All integration tests must pass
- All property-based tests must pass
- No linting errors
- No type errors

### Post-Deployment Verification
1. **Health Checks**: All services respond to /health
2. **Smoke Tests**: Basic API calls succeed
3. **UI Access**: Frontend loads and renders
4. **Database**: Migrations applied successfully
5. **Authentication**: Login flow works
6. **Data Seeding**: Seed scripts complete successfully

### Staging Verification Checklist
- [ ] All services running with 2 tasks each
- [ ] ALB health checks passing
- [ ] Database accessible from services
- [ ] Redis accessible from services
- [ ] UI loads in browser
- [ ] Login with admin credentials works
- [ ] API endpoints respond correctly
- [ ] Inventory data visible in UI
- [ ] Movement history visible
- [ ] Roles and permissions working

## Cost Estimation

### Monthly Cost Breakdown (Staging)

| Resource | Configuration | Estimated Cost |
|----------|--------------|----------------|
| ECS Tasks (6 services × 2 tasks) | 12 tasks @ 0.5 vCPU, 1 GB | $35 |
| RDS (db.t3.small) | 2 vCPU, 2 GB RAM | $30 |
| ElastiCache (cache.t3.micro) | 1 node | $12 |
| ALB | 1 load balancer | $20 |
| NAT Gateway | 2 AZs | $65 |
| Data Transfer | Minimal | $5 |
| CloudWatch Logs | 7-day retention | $5 |
| **Total Staging** | | **~$172/month** |

### Dev Environment (After Scale-Down)

| Resource | Configuration | Estimated Cost |
|----------|--------------|----------------|
| ECS Tasks (6 services × 1 task) | 6 tasks | $18 |
| RDS (db.t3.micro) | 1 vCPU, 1 GB RAM | $15 |
| ElastiCache (cache.t3.micro) | 1 node | $12 |
| ALB | 1 load balancer | $20 |
| NAT Gateway | 2 AZs | $65 |
| Data Transfer | Minimal | $5 |
| CloudWatch Logs | 7-day retention | $5 |
| **Total Dev** | | **~$140/month** |

### Combined Total
- **Dev + Staging**: ~$312/month (within budget)
- **Savings from Dev Scale-Down**: ~$20/month

## Implementation Phases

### Phase 1: Scale Down Dev (Low Risk)
1. Update dev Terraform configuration
2. Apply changes to scale down tasks
3. Verify dev environment stability
4. Monitor for 24 hours

### Phase 2: Create Staging Infrastructure (Medium Risk)
1. Create staging Terraform configuration
2. Initialize Terraform backend for staging
3. Create ECR repositories in us-east-1
4. Apply Terraform to create infrastructure
5. Verify all resources created successfully

### Phase 3: Implement Tag-Based Deployment (Medium Risk)
1. Create new GitHub Actions workflow
2. Configure workflow triggers for tags
3. Update image build process for versioning
4. Test workflow with test tag
5. Verify deployment to staging

### Phase 4: Seed Staging Data (Low Risk)
1. Update seed scripts for environment parameter
2. Create manual trigger workflow
3. Run seed scripts against staging
4. Verify data in staging database
5. Test UI with seeded data

### Phase 5: Documentation and Handoff (Low Risk)
1. Document staging URLs and credentials
2. Create runbook for deployments
3. Document rollback procedures
4. Train team on tag-based deployments

## Success Metrics

### Technical Metrics
- Staging deployment time: < 15 minutes
- All services healthy after deployment
- Zero downtime during dev scale-down
- Seed scripts complete in < 10 minutes

### Business Metrics
- Staging environment available for demos
- Cost reduction achieved in dev
- Tag-based deployment workflow functional
- Team can deploy to staging independently

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Dev scale-down causes instability | High | Low | Monitor closely, can scale back up quickly |
| Staging deployment fails | Medium | Medium | Keep dev as backup, test thoroughly |
| Cross-region issues | Medium | Low | Test ECR replication, verify region config |
| Seed scripts fail in staging | Low | Low | Scripts are idempotent, can retry |
| Cost overrun | Medium | Low | Monitor costs weekly, scale down if needed |
| Tag deployment breaks main | High | Low | Separate workflows, no shared state |

## Open Questions (Resolved)
1. ✅ Should we run seed scripts automatically or manually? **Manual trigger post-deployment**
2. ✅ What semantic versioning scheme? **v*.*.*  (MAJOR.MINOR.PATCH)**
3. ✅ Database size for staging? **db.t3.small (one size up from micro)**
4. ✅ Auto-scaling in staging? **Disabled, wait for verification**

## Dependencies

### External Dependencies
- AWS account with appropriate permissions
- GitHub repository with Actions enabled
- Terraform >= 1.0
- Docker and Docker Buildx
- AWS CLI v2

### Internal Dependencies
- Existing dev environment (reference)
- Seed scripts (working in dev)
- Docker images (buildable)
- Terraform modules (tested)

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Scale Down Dev | 1 hour | None |
| Phase 2: Create Staging Infra | 4 hours | Phase 1 complete |
| Phase 3: Tag-Based Deployment | 3 hours | Phase 2 complete |
| Phase 4: Seed Staging Data | 2 hours | Phase 3 complete |
| Phase 5: Documentation | 2 hours | Phase 4 complete |
| **Total** | **12 hours** | Sequential execution |

## Conclusion

This design provides a comprehensive approach to creating a staging environment with tag-based deployments while optimizing dev costs. The solution leverages existing Terraform modules, maintains environment separation, and provides a clear path for demo deployments via semantic versioning tags.

Key benefits:
- Cost-optimized dev environment (~40% reduction)
- Production-like staging for demos (2 tasks per service)
- Automated tag-based deployments
- Manual data seeding for control
- Clear rollback strategy
- Comprehensive monitoring and health checks
