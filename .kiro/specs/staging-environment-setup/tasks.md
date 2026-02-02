# Staging Environment Setup - Tasks

## Task List

- [x] 1. Scale Down Dev Environment
  - [x] 1.1 Update dev Terraform configuration for task counts
  - [x] 1.2 Apply Terraform changes to dev environment
  - [x] 1.3 Verify dev services remain healthy after scale-down
  - [x] 1.4 Monitor dev environment for 1 hour

- [x] 2. Create ECR Repositories in us-east-1
  - [x] 2.1 Create ECR repositories for all services in us-east-1
  - [x] 2.2 Configure repository policies and lifecycle rules
  - [x] 2.3 Verify repositories accessible from GitHub Actions

- [x] 3. Create Staging Terraform Configuration
  - [x] 3.1 Create staging directory structure
  - [x] 3.2 Create staging main.tf with all modules
  - [x] 3.3 Create staging variables.tf
  - [x] 3.4 Create staging terraform.tfvars with staging-specific values
  - [x] 3.5 Create staging outputs.tf for ALB URL and other outputs
  - [x] 3.6 Initialize Terraform backend for staging

- [ ] 4. Deploy Staging Infrastructure
  - [ ] 4.1 Run terraform init for staging
  - [ ] 4.2 Run terraform plan and review changes
  - [ ] 4.3 Run terraform apply to create staging infrastructure
  - [ ] 4.4 Verify all resources created successfully
  - [ ] 4.5 Document staging ALB URL and database endpoint

- [x] 5. Implement Tag-Based Deployment Workflow
  - [x] 5.1 Create new GitHub Actions workflow file (deploy-staging.yml)
  - [x] 5.2 Configure workflow trigger for tag pattern v*.*.*
  - [x] 5.3 Add test execution step
  - [x] 5.4 Add Docker build step with version tagging
  - [x] 5.5 Add ECR push step for us-east-1
  - [x] 5.6 Add database migration step
  - [x] 5.7 Add service deployment step
  - [x] 5.8 Add health check verification step
  - [x] 5.9 Add deployment status notification

- [x] 6. Update Seed Scripts for Multi-Environment Support
  - [x] 6.1 Modify setup_default_roles.py to accept environment parameter
  - [x] 6.2 Modify reseed_complete_inventory.py to accept environment parameter
  - [x] 6.3 Modify generate_movements.py to accept environment parameter
  - [x] 6.4 Test scripts against dev environment
  - [x] 6.5 Create environment configuration mapping

- [x] 7. Create Manual Seed Workflow
  - [x] 7.1 Create seed-staging-data.yml workflow file
  - [x] 7.2 Configure workflow_dispatch trigger with environment input
  - [x] 7.3 Add steps to run all three seed scripts
  - [x] 7.4 Add verification step to check data seeded
  - [x] 7.5 Test workflow with dev environment

- [ ] 8. Test Tag-Based Deployment
  - [ ] 8.1 Create and push test tag (v0.1.0)
  - [ ] 8.2 Monitor GitHub Actions workflow execution
  - [ ] 8.3 Verify images built and pushed to us-east-1 ECR
  - [ ] 8.4 Verify services deployed to staging
  - [ ] 8.5 Verify all health checks passing
  - [ ] 8.6 Fix any issues and retry

- [ ] 9. Seed Staging Environment
  - [ ] 9.1 Trigger manual seed workflow for staging
  - [ ] 9.2 Monitor seed script execution
  - [ ] 9.3 Verify roles created in staging database
  - [ ] 9.4 Verify inventory items created
  - [ ] 9.5 Verify movement history created
  - [ ] 9.6 Test UI access to seeded data

- [ ] 10. Verify Staging Environment
  - [ ] 10.1 Test ALB URL accessibility
  - [ ] 10.2 Test UI loads and renders correctly
  - [ ] 10.3 Test login with admin credentials
  - [ ] 10.4 Test inventory listing and filtering
  - [ ] 10.5 Test location management
  - [ ] 10.6 Test movement creation
  - [ ] 10.7 Test user management
  - [ ] 10.8 Test role management
  - [ ] 10.9 Verify all 2 tasks running per service
  - [ ] 10.10 Verify auto-scaling disabled

- [x] 11. Documentation and Handoff
  - [x] 11.1 Document staging ALB URL
  - [x] 11.2 Document staging database credentials
  - [x] 11.3 Document tag-based deployment process
  - [x] 11.4 Document manual seed workflow process
  - [x] 11.5 Document rollback procedures
  - [x] 11.6 Create deployment runbook
  - [x] 11.7 Update README with staging information

- [ ] 12. Cost Monitoring Setup
  - [ ] 12.1 Set up AWS Cost Explorer tags for staging
  - [ ] 12.2 Create cost alert for staging environment
  - [ ] 12.3 Verify dev cost reduction after scale-down
  - [ ] 12.4 Document monthly cost estimates

## Task Details

### 1.1 Update dev Terraform configuration for task counts
**Description**: Modify the dev environment Terraform configuration to scale down services from current counts to 1 task each.

**Files to modify**:
- `terraform/environments/dev/main.tf`

**Changes**:
- API Gateway: `desired_count = 1` (currently 3)
- Inventory Service: `desired_count = 1` (currently 2)
- Location Service: `desired_count = 1` (currently 2)
- Other services: Keep at 1

**Acceptance Criteria**:
- Terraform configuration updated
- No syntax errors
- Plan shows expected changes

---

### 1.2 Apply Terraform changes to dev environment
**Description**: Apply the Terraform changes to scale down the dev environment.

**Commands**:
```bash
cd terraform/environments/dev
terraform plan -out=tfplan
terraform apply tfplan
```

**Acceptance Criteria**:
- Terraform apply succeeds
- Services scaled down to 1 task each
- No errors during apply

---

### 1.3 Verify dev services remain healthy after scale-down
**Description**: Verify all dev services remain healthy and functional after scaling down.

**Verification Steps**:
- Check ECS service status in AWS console
- Verify all services have 1 running task
- Test health endpoints for all services
- Test UI functionality
- Test API endpoints

**Acceptance Criteria**:
- All services running with 1 task
- All health checks passing
- UI accessible and functional
- API endpoints responding correctly

---

### 2.1 Create ECR repositories for all services in us-east-1
**Description**: Create ECR repositories in us-east-1 region for all services.

**Repositories to create**:
- `inventory-management/api-gateway`
- `inventory-management/user-service`
- `inventory-management/inventory-service`
- `inventory-management/location-service`
- `inventory-management/reporting-service`
- `inventory-management/ui-service`

**Commands**:
```bash
aws ecr create-repository \
  --repository-name inventory-management/api-gateway \
  --region us-east-1

# Repeat for all services
```

**Acceptance Criteria**:
- All 6 repositories created in us-east-1
- Repositories visible in AWS console
- Repository URIs documented

---

### 2.2 Configure repository policies and lifecycle rules
**Description**: Configure ECR repository policies and lifecycle rules for image management.

**Lifecycle Policy**:
- Keep last 10 tagged images
- Remove untagged images after 7 days

**Acceptance Criteria**:
- Lifecycle policies applied to all repositories
- Policies verified in AWS console

---

### 3.1 Create staging directory structure
**Description**: Create the staging environment directory structure in Terraform.

**Directory to create**:
```
terraform/environments/staging/
├── main.tf
├── variables.tf
├── terraform.tfvars
├── outputs.tf
└── backend.tf
```

**Acceptance Criteria**:
- Directory structure created
- Files created with basic structure

---

### 3.2 Create staging main.tf with all modules
**Description**: Create the main Terraform configuration for staging, similar to dev but with staging-specific parameters.

**Key Differences from Dev**:
- Region: us-east-1
- VPC CIDR: 10.1.0.0/16
- All services: `desired_count = 2`
- All services: `enable_auto_scaling = false`
- Database: db.t3.small

**Acceptance Criteria**:
- main.tf created with all modules
- All services configured with 2 tasks
- Auto-scaling disabled
- Database upgraded to t3.small

---

### 3.3 Create staging variables.tf
**Description**: Create variables file for staging environment.

**Variables to define**:
- aws_region (default: us-east-1)
- environment (default: staging)
- vpc_cidr (default: 10.1.0.0/16)
- db_instance_class (default: db.t3.small)
- All image variables

**Acceptance Criteria**:
- variables.tf created
- All required variables defined
- Defaults set appropriately

---

### 3.4 Create staging terraform.tfvars with staging-specific values
**Description**: Create tfvars file with staging-specific configuration values.

**Values to set**:
```hcl
aws_region  = "us-east-1"
environment = "staging"
vpc_cidr    = "10.1.0.0/16"
db_instance_class = "db.t3.small"
# ECR image URLs for us-east-1
```

**Acceptance Criteria**:
- terraform.tfvars created
- All values set correctly
- ECR URLs point to us-east-1

---

### 3.6 Initialize Terraform backend for staging
**Description**: Initialize Terraform backend for staging environment with S3 state storage.

**Backend Configuration**:
```hcl
terraform {
  backend "s3" {
    bucket         = "inventory-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

**Commands**:
```bash
cd terraform/environments/staging
terraform init
```

**Acceptance Criteria**:
- Backend initialized successfully
- State file created in S3
- Lock table configured

---

### 4.3 Run terraform apply to create staging infrastructure
**Description**: Apply Terraform configuration to create all staging infrastructure.

**Commands**:
```bash
cd terraform/environments/staging
terraform apply
```

**Resources Created**:
- VPC and networking (subnets, NAT, IGW)
- Security groups
- RDS database (db.t3.small)
- ElastiCache Redis
- Application Load Balancer
- ECS cluster
- 6 ECS services (2 tasks each)

**Acceptance Criteria**:
- Terraform apply succeeds
- All resources created
- No errors during creation
- Resources visible in AWS console

---

### 5.1 Create new GitHub Actions workflow file (deploy-staging.yml)
**Description**: Create a new GitHub Actions workflow for tag-based staging deployments.

**File**: `.github/workflows/deploy-staging.yml`

**Workflow Structure**:
```yaml
name: Deploy to Staging

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  test:
    # Run all tests
  
  build-and-push:
    # Build and push images with version tag
  
  deploy-staging:
    # Deploy to staging environment
  
  verify:
    # Verify deployment
```

**Acceptance Criteria**:
- Workflow file created
- Trigger configured for version tags
- Basic job structure defined

---

### 5.4 Add Docker build step with version tagging
**Description**: Add Docker build step that tags images with the git tag version.

**Implementation**:
```yaml
- name: Extract version from tag
  id: version
  run: echo "version=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    tags: ${{ env.ECR_REGISTRY }}/inventory-management/${{ matrix.service }}:${{ steps.version.outputs.version }}
```

**Acceptance Criteria**:
- Version extracted from git tag
- Images tagged with version
- Images pushed to us-east-1 ECR

---

### 5.7 Add service deployment step
**Description**: Add step to update ECS services with new task definitions.

**Implementation**:
```yaml
- name: Update ECS services
  run: |
    services=("api-gateway" "user-service" "inventory-service" "location-service" "reporting-service" "ui-service")
    for service in "${services[@]}"; do
      # Get current task definition
      # Update image tag
      # Register new task definition
      # Update service
    done
```

**Acceptance Criteria**:
- All services updated with new images
- Services force new deployment
- No errors during update

---

### 6.1 Modify setup_default_roles.py to accept environment parameter
**Description**: Update the roles setup script to accept an environment parameter and use the appropriate API URL.

**Changes**:
```python
import os

ENVIRONMENTS = {
    "dev": "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com",
    "staging": "http://staging-inventory-alb-XXXXXXXX.us-east-1.elb.amazonaws.com"
}

API_BASE_URL = ENVIRONMENTS.get(os.environ.get("ENVIRONMENT", "dev"))
```

**Acceptance Criteria**:
- Script accepts ENVIRONMENT env var
- Script uses correct API URL per environment
- Script works with both dev and staging

---

### 6.2 Modify reseed_complete_inventory.py to accept environment parameter
**Description**: Update the inventory seeding script to accept an environment parameter.

**Changes**: Same pattern as 6.1

**Acceptance Criteria**:
- Script accepts ENVIRONMENT env var
- Script uses correct API URL per environment
- Script works with both dev and staging

---

### 6.3 Modify generate_movements.py to accept environment parameter
**Description**: Update the movements generation script to accept an environment parameter.

**Changes**: Same pattern as 6.1

**Acceptance Criteria**:
- Script accepts ENVIRONMENT env var
- Script uses correct API URL per environment
- Script works with both dev and staging

---

### 7.1 Create seed-staging-data.yml workflow file
**Description**: Create a GitHub Actions workflow for manually seeding staging data.

**File**: `.github/workflows/seed-staging-data.yml`

**Workflow Structure**:
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
      - Checkout
      - Setup Python
      - Install dependencies
      - Run setup_default_roles.py
      - Run reseed_complete_inventory.py
      - Run generate_movements.py
```

**Acceptance Criteria**:
- Workflow file created
- Manual trigger configured
- Environment parameter accepted

---

### 7.3 Add steps to run all three seed scripts
**Description**: Add steps to run all seed scripts in order.

**Implementation**:
```yaml
- name: Setup roles
  run: python scripts/setup_default_roles.py
  env:
    ENVIRONMENT: ${{ inputs.environment }}

- name: Seed inventory
  run: python scripts/reseed_complete_inventory.py
  env:
    ENVIRONMENT: ${{ inputs.environment }}

- name: Generate movements
  run: python scripts/generate_movements.py
  env:
    ENVIRONMENT: ${{ inputs.environment }}
```

**Acceptance Criteria**:
- All three scripts run in order
- Environment variable passed correctly
- Scripts complete successfully

---

### 8.1 Create and push test tag (v0.1.0)
**Description**: Create and push a test tag to trigger the staging deployment workflow.

**Commands**:
```bash
git tag v0.1.0
git push origin v0.1.0
```

**Acceptance Criteria**:
- Tag created locally
- Tag pushed to GitHub
- Workflow triggered automatically

---

### 8.2 Monitor GitHub Actions workflow execution
**Description**: Monitor the staging deployment workflow execution and verify each step completes successfully.

**Steps to Monitor**:
- Test execution
- Image builds
- ECR pushes
- Service deployments
- Health checks

**Acceptance Criteria**:
- Workflow completes successfully
- All steps pass
- No errors in logs

---

### 9.1 Trigger manual seed workflow for staging
**Description**: Manually trigger the seed workflow to populate staging with demo data.

**Steps**:
1. Go to GitHub Actions
2. Select "Seed Staging Data" workflow
3. Click "Run workflow"
4. Select "staging" environment
5. Click "Run workflow"

**Acceptance Criteria**:
- Workflow triggered successfully
- Workflow starts executing

---

### 9.3 Verify roles created in staging database
**Description**: Verify that all default roles were created in the staging database.

**Verification**:
- Login to staging UI
- Navigate to Roles page
- Verify 6 roles exist (admin + 5 default roles)

**Acceptance Criteria**:
- All 6 roles visible
- Permissions configured correctly

---

### 9.4 Verify inventory items created
**Description**: Verify that all inventory items were created in staging.

**Verification**:
- Navigate to Inventory page
- Verify 70 parent items exist
- Verify items distributed across locations
- Verify child items assigned to parents

**Acceptance Criteria**:
- 70 parent items visible
- Items have correct SKUs (simple numbers)
- Child items have serial number SKUs
- Items distributed across warehouses, hospitals, quarantine

---

### 10.1 Test ALB URL accessibility
**Description**: Verify the staging ALB URL is accessible from the internet.

**Test**:
```bash
curl -I http://staging-inventory-alb-XXXXXXXX.us-east-1.elb.amazonaws.com
```

**Acceptance Criteria**:
- ALB responds with HTTP 200
- No connection errors
- Response time < 1 second

---

### 10.3 Test login with admin credentials
**Description**: Test logging in to staging with admin credentials.

**Test Steps**:
1. Navigate to staging UI
2. Enter username: admin
3. Enter password: admin
4. Click login

**Acceptance Criteria**:
- Login succeeds
- Dashboard loads
- User menu shows admin user

---

### 10.9 Verify all 2 tasks running per service
**Description**: Verify that all services are running with exactly 2 tasks.

**Verification**:
- Check ECS console
- Verify each service shows 2/2 tasks running
- Verify tasks are healthy

**Services to Check**:
- staging-api-gateway
- staging-user-service
- staging-inventory-service
- staging-location-service
- staging-reporting-service
- staging-ui-service

**Acceptance Criteria**:
- All 6 services running
- Each service has 2 tasks
- All tasks healthy

---

### 10.10 Verify auto-scaling disabled
**Description**: Verify that auto-scaling is disabled for all staging services.

**Verification**:
- Check ECS service configuration
- Verify no auto-scaling policies attached
- Verify desired count is fixed at 2

**Acceptance Criteria**:
- No auto-scaling policies
- Desired count fixed at 2
- Services will not scale automatically

---

### 11.3 Document tag-based deployment process
**Description**: Document the process for deploying to staging using tags.

**Documentation to Create**:
```markdown
# Deploying to Staging

## Process
1. Ensure all changes are merged to main
2. Create a semantic version tag: `git tag v1.0.0`
3. Push the tag: `git push origin v1.0.0`
4. Monitor GitHub Actions workflow
5. Verify deployment in AWS console
6. Run manual seed workflow if needed
7. Verify staging environment

## Semantic Versioning
- MAJOR.MINOR.PATCH format
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

## Rollback
- Push previous version tag
- Or manually update ECS services
```

**Acceptance Criteria**:
- Documentation created
- Process clearly explained
- Examples provided

---

### 11.5 Document rollback procedures
**Description**: Document procedures for rolling back a failed staging deployment.

**Documentation to Create**:
```markdown
# Rollback Procedures

## Tag-Based Rollback
1. Identify last known good version
2. Push rollback tag: `git push origin v1.0.0`
3. Monitor deployment workflow
4. Verify rollback successful

## Manual Rollback
1. Identify previous task definition revision
2. Update service with previous revision
3. Force new deployment
4. Verify services healthy

## Database Rollback
1. Run Alembic downgrade if needed
2. Or restore from RDS snapshot
```

**Acceptance Criteria**:
- Rollback procedures documented
- Multiple rollback options provided
- Clear step-by-step instructions

---

### 12.1 Set up AWS Cost Explorer tags for staging
**Description**: Configure AWS Cost Explorer to track staging costs separately.

**Tags to Configure**:
- Environment: staging
- Product: inventory-management
- ManagedBy: terraform

**Acceptance Criteria**:
- Cost allocation tags enabled
- Staging costs visible in Cost Explorer
- Can filter by environment tag

---

### 12.3 Verify dev cost reduction after scale-down
**Description**: Verify that dev environment costs have decreased after scaling down.

**Verification**:
- Compare ECS task costs before/after
- Verify ~40-50% reduction in task costs
- Document actual savings

**Acceptance Criteria**:
- Cost reduction verified
- Savings documented
- Within expected range

---

## Estimated Timeline

| Task | Estimated Time |
|------|----------------|
| 1. Scale Down Dev | 1 hour |
| 2. Create ECR Repositories | 30 minutes |
| 3. Create Staging Terraform Config | 2 hours |
| 4. Deploy Staging Infrastructure | 1 hour |
| 5. Implement Tag-Based Deployment | 2 hours |
| 6. Update Seed Scripts | 1 hour |
| 7. Create Manual Seed Workflow | 1 hour |
| 8. Test Tag-Based Deployment | 1 hour |
| 9. Seed Staging Environment | 30 minutes |
| 10. Verify Staging Environment | 1 hour |
| 11. Documentation | 1 hour |
| 12. Cost Monitoring | 30 minutes |
| **Total** | **12 hours** |

## Dependencies

- Task 2 can run in parallel with Task 1
- Task 3 depends on Task 1 completion (for reference)
- Task 4 depends on Tasks 2 and 3
- Task 5 depends on Task 4
- Tasks 6 and 7 can run in parallel with Task 5
- Task 8 depends on Tasks 4, 5, 6, 7
- Task 9 depends on Task 8
- Task 10 depends on Task 9
- Tasks 11 and 12 can run in parallel after Task 10
