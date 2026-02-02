# Staging Environment Setup - Requirements

## Overview
Create a staging environment in us-east-1 for demo purposes with the same data as dev, scale down dev to 1 task per service, and implement tag-based deployment to staging.

## User Stories

### 1. As a DevOps Engineer, I want to scale down the dev environment to reduce costs
**Acceptance Criteria**:
- Dev environment API Gateway scaled to 1 task (currently 3)
- Dev environment Inventory Service scaled to 1 task (currently 2)
- Dev environment Location Service scaled to 1 task (currently 2)
- Dev environment User Service remains at 1 task
- Dev environment Reporting Service remains at 1 task
- Dev environment UI Service remains at 1 task
- Changes applied via Terraform
- Services remain functional after scaling

### 2. As a Product Manager, I want a staging environment in us-east-1 for demos
**Acceptance Criteria**:
- Staging environment created in us-east-1 region
- All services deployed with 2 tasks each for high availability
- Database instance created (db.t3.micro or similar)
- Redis instance created for caching
- Load balancer configured with health checks
- All services accessible via staging ALB URL
- Environment tagged as "staging" in AWS

### 3. As a Developer, I want staging to have the same demo data as dev
**Acceptance Criteria**:
- Staging database seeded with same data structure as dev:
  - 7 parent item types (Sports Tower, MedEd 1688, MedEd 1788, Clinical 1788, RISE Tower, 1788 Roll Stand, 1688 Roll Stand)
  - 10 of each parent item type (70 total)
  - Child items assigned to parent items
  - 5 hospitals (Hospital A-E)
  - Warehouse and quarantine locations
  - Movement history (125+ movements)
  - 6 roles (admin, Warehouse Manager, Inventory Clerk, Viewer, Location Manager, User Manager)
  - Admin user with credentials
- Seeding automated as part of deployment or via manual trigger
- Seed scripts idempotent (can run multiple times safely)

### 4. As a DevOps Engineer, I want tag-based deployments to staging
**Acceptance Criteria**:
- GitHub Actions workflow triggers on tag push
- Tags follow semantic versioning (v1.0.0, v1.1.0, etc.)
- Tag deployment workflow:
  - Runs all tests (unit, integration, property-based)
  - Builds Docker images with tag version
  - Pushes images to ECR with tag
  - Deploys to staging environment
  - Runs database migrations
  - Optionally runs seed scripts
- Deployment status reported in GitHub
- Failed deployments do not affect staging
- Rollback capability via previous tags

### 5. As a Developer, I want clear separation between dev and staging
**Acceptance Criteria**:
- Separate Terraform workspaces or state files for dev and staging
- Separate AWS resources (VPC, subnets, security groups, etc.)
- Separate databases (no shared data)
- Separate ECR image tags (dev vs staging)
- Environment variables clearly distinguish environments
- Logging and monitoring separated by environment

### 6. As a DevOps Engineer, I want to manage staging infrastructure via Terraform
**Acceptance Criteria**:
- Terraform configuration for staging environment
- Variables for environment-specific settings (region, task count, etc.)
- Reusable modules for common infrastructure
- State stored in S3 with locking
- Plan/apply workflow documented
- Destroy capability for cost management

## Technical Requirements

### Infrastructure
- **Region**: us-east-1 (staging), us-west-2 (dev)
- **Task Counts**:
  - Dev: 1 task per service
  - Staging: 2 tasks per service
- **Database**: db.t3.micro (or similar) per environment
- **Redis**: Single node per environment
- **Load Balancer**: Application Load Balancer per environment
- **Container Resources**:
  - API Gateway: 512 CPU, 1024 MB memory
  - Services: 256 CPU, 512 MB memory
  - UI: 256 CPU, 512 MB memory

### CI/CD Pipeline
- **Dev Deployment**: Triggered on push to main branch
- **Staging Deployment**: Triggered on tag push (v*.*.*)
- **Test Requirements**: All tests must pass before deployment
- **Image Tagging**:
  - Dev: `latest` and commit SHA
  - Staging: semantic version tag (v1.0.0)
- **Deployment Order**:
  1. Run tests
  2. Build images
  3. Push to ECR
  4. Run migrations
  5. Deploy services
  6. Run health checks
  7. (Optional) Run seed scripts

### Data Seeding
- **Seed Scripts**:
  - `scripts/setup_default_roles.py` - Create roles
  - `scripts/reseed_complete_inventory.py` - Create inventory data
  - `scripts/generate_movements.py` - Create movement history
- **Execution**:
  - Manual trigger via GitHub Actions workflow
  - Or automated as part of initial staging setup
- **Idempotency**: Scripts check for existing data before creating

### Security
- **Secrets Management**: AWS Secrets Manager or GitHub Secrets
- **Database Credentials**: Unique per environment
- **JWT Secret**: Unique per environment
- **Network Security**: Security groups restrict access
- **HTTPS**: SSL/TLS for all external traffic

## Non-Functional Requirements

### Performance
- Staging should handle demo load (10-20 concurrent users)
- Response times < 500ms for API calls
- UI load time < 3 seconds

### Availability
- Staging: 99% uptime (demo environment)
- Dev: Best effort (development environment)

### Cost
- Dev scaled down to reduce costs (~50% reduction)
- Staging optimized for demos (2 tasks for reliability)
- Total monthly cost target: < $200 for both environments

### Monitoring
- CloudWatch logs for all services
- Health check endpoints monitored
- Alerts for critical failures (staging only)

## Out of Scope
- Production environment setup
- Custom domain names (using ALB URLs)
- Advanced monitoring/alerting (Datadog, New Relic)
- Database replication between environments
- Blue/green deployments
- Canary deployments
- Auto-scaling based on load

## Dependencies
- Existing dev environment in us-west-2
- Terraform state in S3
- GitHub Actions workflows
- AWS account with appropriate permissions
- ECR repositories for Docker images

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Staging deployment fails | Demo unavailable | Keep dev environment as backup |
| Data seeding fails | Empty staging DB | Manual seed script execution |
| Tag deployment breaks main | Dev affected | Separate workflows for dev and staging |
| Cost overrun | Budget exceeded | Monitor costs, scale down when not in use |
| Region-specific issues | Staging unavailable | Document region differences |

## Success Criteria
- [ ] Dev environment scaled to 1 task per service
- [ ] Staging environment created in us-east-1
- [ ] Staging has 2 tasks per service
- [ ] Tag-based deployment workflow functional
- [ ] Staging seeded with demo data
- [ ] All services accessible and functional in staging
- [ ] Documentation updated with staging URLs and procedures
- [ ] Cost reduction achieved in dev environment
