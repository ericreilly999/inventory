# Dev Environment Cost Optimization

## Overview
This document outlines the automated cost optimization strategies for the development environment, including automatic shutdown, database management, and NAT Gateway optimization.

## Automated Environment Control

### GitHub Actions Workflows

#### 1. Dev Environment Control (`.github/workflows/dev-environment-control.yml`)
**Features:**
- Manual start/stop/status control
- Automatic shutdown schedule:
  - Weekdays: 8 PM EST (1 AM UTC)
  - Weekends: 6 PM EST (11 PM UTC)
- Manages both ECS services and RDS database

**Usage:**
```bash
# Via GitHub Actions UI
1. Go to Actions tab
2. Select "Dev Environment Control"
3. Click "Run workflow"
4. Choose action: start, stop, or status

# Via GitHub CLI
gh workflow run dev-environment-control.yml -f action=stop
gh workflow run dev-environment-control.yml -f action=start
gh workflow run dev-environment-control.yml -f action=status
```

#### 2. Start Dev Environment (`.github/workflows/dev-start.yml`)
**Features:**
- Quick start workflow
- Starts RDS database first, then ECS services
- Waits for database to be available before starting services

**Usage:**
```bash
# Via GitHub Actions UI
1. Go to Actions tab
2. Select "Start Dev Environment"
3. Click "Run workflow"

# Via GitHub CLI
gh workflow run dev-start.yml
```

### What Gets Stopped/Started

#### Stopped Resources:
1. **ECS Services** (6 services):
   - dev-inventory-api-gateway
   - dev-inventory-inventory
   - dev-inventory-location
   - dev-inventory-reporting
   - dev-inventory-user
   - dev-inventory-ui

2. **RDS Database**:
   - dev-inventory-db (PostgreSQL 15)

#### Resources That Remain Running:
- VPC and networking infrastructure
- NAT Gateway (see optimization below)
- Application Load Balancer
- CloudWatch Logs
- Secrets Manager
- ElastiCache (Redis) - consider stopping if not needed

## Cost Breakdown

### Monthly Costs (Approximate)

#### When Running 24/7:
| Resource | Cost/Month | Notes |
|----------|------------|-------|
| ECS Tasks (6 services) | $40-50 | Fargate pricing |
| RDS db.t3.micro | $30-40 | Includes storage |
| NAT Gateway | $32 | Hourly charge |
| NAT Gateway Data | $20-30 | Data processing |
| ALB | $16 | Always running |
| ElastiCache | $15-20 | Redis instance |
| **Total** | **$153-188** | |

#### When Stopped (Non-Business Hours):
| Resource | Cost/Month | Notes |
|----------|------------|-------|
| ECS Tasks | $0 | Scaled to 0 |
| RDS Database | $0 | Stopped |
| NAT Gateway | $32 | Still charged hourly |
| NAT Gateway Data | $2-5 | Minimal traffic |
| ALB | $16 | Always running |
| ElastiCache | $15-20 | Still running |
| **Total** | **$65-73** | |

### Savings Calculation

**Scenario: Stop dev environment outside business hours**
- Business hours: 9 AM - 8 PM EST (11 hours/day)
- Non-business hours: 13 hours/day + weekends
- Stopped time: ~65% of the month

**Monthly Savings:**
- ECS Tasks: $40-50 × 0.65 = $26-33 saved
- RDS Database: $30-40 × 0.65 = $20-26 saved
- NAT Gateway Data: $20-30 × 0.65 = $13-20 saved
- **Total Savings: $59-79/month (38-42% reduction)**

## NAT Gateway Cost Optimization

### Current Setup
The dev environment uses a NAT Gateway for private subnet internet access. This costs:
- **Hourly charge**: $0.045/hour = ~$32/month (always charged)
- **Data processing**: $0.045/GB = $20-30/month (depends on usage)

### Problem
NAT Gateway hourly charges apply even when the environment is stopped, wasting ~$32/month.

### Solution Options

#### Option 1: VPC Endpoints (Recommended)
Replace NAT Gateway with VPC Endpoints for AWS services.

**Benefits:**
- Eliminates NAT Gateway hourly charges ($32/month saved)
- Reduces data transfer costs
- Better security (traffic stays in AWS network)
- Lower latency

**Required VPC Endpoints:**
```hcl
# terraform/modules/networking/vpc_endpoints.tf
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id
}

resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}
```

**Cost:**
- Interface endpoints: $0.01/hour × 4 endpoints = $29/month
- Gateway endpoints (S3): Free
- **Net savings: $3/month + data transfer savings**

**Implementation Steps:**
1. Create VPC endpoints in Terraform
2. Update security groups to allow VPC endpoint traffic
3. Test services can pull images and access AWS services
4. Remove NAT Gateway from dev environment
5. Update route tables

#### Option 2: Conditional NAT Gateway
Only create NAT Gateway when environment is running.

**Benefits:**
- Eliminates hourly charges when stopped
- Full internet access when running

**Drawbacks:**
- Requires Terraform apply to start/stop
- Slower startup time (NAT Gateway creation takes 2-3 minutes)
- More complex automation

**Implementation:**
```hcl
# terraform/environments/dev/variables.tf
variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for dev environment"
  type        = bool
  default     = false
}

# terraform/modules/networking/main.tf
resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? length(var.availability_zones) : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = merge(var.tags, {
    Name = "${var.environment}-nat-gateway-${count.index + 1}"
  })
}
```

#### Option 3: Hybrid Approach
Use VPC Endpoints for AWS services + small NAT Gateway for external APIs.

**Benefits:**
- Reduced NAT Gateway data processing costs
- Still have internet access for external APIs
- Best of both worlds

**Cost:**
- NAT Gateway: $32/month (hourly)
- VPC Endpoints: $29/month
- **Total: $61/month** (vs $52/month with NAT only)

### Recommendation

**For Dev Environment: Option 1 (VPC Endpoints)**
- Eliminates $32/month fixed cost
- Services only need AWS API access (ECR, S3, CloudWatch, Secrets Manager)
- No external API calls required in dev
- One-time setup, permanent savings

**For Staging/Production: Option 3 (Hybrid)**
- Keep NAT Gateway for external API calls
- Use VPC Endpoints to reduce data transfer costs
- Better security and performance

## Additional Cost Optimizations

### 1. ElastiCache (Redis)
**Current:** Always running (~$15-20/month)

**Options:**
- Stop Redis when dev environment is stopped
- Use smaller instance type (cache.t3.micro)
- Share Redis instance across environments

**Implementation:**
```bash
# Add to stop workflow
aws elasticache modify-replication-group \
  --replication-group-id dev-inventory-cache \
  --automatic-failover-enabled false \
  --apply-immediately

# Note: ElastiCache doesn't support stop/start like RDS
# Consider deleting and recreating, or using smaller instance
```

### 2. RDS Storage
**Current:** gp3 storage with auto-scaling

**Optimization:**
- Use smaller allocated storage for dev
- Disable Performance Insights (saves $7/month)
- Reduce backup retention to 1 day

**Implementation:**
```hcl
# terraform/environments/dev/terraform.tfvars
db_allocated_storage = 20  # Minimum for gp3
performance_insights_enabled = false
backup_retention_period = 1
```

### 3. CloudWatch Logs
**Current:** Unlimited retention

**Optimization:**
- Set log retention to 7 days for dev
- Use log filtering to reduce ingestion

**Implementation:**
```hcl
# terraform/modules/ecs-cluster/main.tf
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.environment}-inventory"
  retention_in_days = var.environment == "dev" ? 7 : 30
}
```

### 4. ECS Task Sizing
**Current:** Various CPU/memory allocations

**Optimization:**
- Use smaller task sizes for dev
- Reduce desired count to 1 for all services

**Current Allocations:**
- API Gateway: 512 CPU, 1024 MB
- Inventory: 512 CPU, 1024 MB
- Location: 512 CPU, 1024 MB
- User: 256 CPU, 512 MB
- Reporting: 256 CPU, 512 MB
- UI: 256 CPU, 512 MB

**Optimized for Dev:**
- API Gateway: 256 CPU, 512 MB
- Inventory: 256 CPU, 512 MB
- Location: 256 CPU, 512 MB
- User: 256 CPU, 512 MB
- Reporting: 256 CPU, 512 MB
- UI: 256 CPU, 512 MB

**Savings:** ~$15-20/month

## Implementation Checklist

### Phase 1: Automated Stop/Start (✅ Complete)
- [x] Create dev-environment-control workflow
- [x] Add RDS stop/start logic
- [x] Add scheduled auto-stop
- [x] Create quick-start workflow
- [x] Test stop/start functionality

### Phase 2: NAT Gateway Optimization (Recommended Next)
- [ ] Create VPC endpoints Terraform module
- [ ] Add VPC endpoints to dev environment
- [ ] Test services with VPC endpoints
- [ ] Remove NAT Gateway from dev
- [ ] Update documentation

### Phase 3: Additional Optimizations (Optional)
- [ ] Reduce ECS task sizes for dev
- [ ] Optimize CloudWatch log retention
- [ ] Reduce RDS allocated storage
- [ ] Disable Performance Insights for dev
- [ ] Consider ElastiCache optimization

## Monitoring and Alerts

### Cost Monitoring
Set up AWS Cost Anomaly Detection:
```bash
aws ce create-anomaly-monitor \
  --monitor-name "dev-inventory-cost-monitor" \
  --monitor-type DIMENSIONAL \
  --monitor-dimension SERVICE
```

### Budget Alerts
Create budget for dev environment:
```bash
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget file://dev-budget.json
```

**dev-budget.json:**
```json
{
  "BudgetName": "dev-inventory-monthly",
  "BudgetLimit": {
    "Amount": "100",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

## Summary

### Current State
- Dev environment runs 24/7
- Monthly cost: ~$153-188
- No automatic shutdown

### With Automated Stop/Start
- Dev environment stops outside business hours
- Monthly cost: ~$94-109 (when stopped 65% of time)
- **Savings: $59-79/month (38-42%)**

### With VPC Endpoints (Recommended)
- Replace NAT Gateway with VPC Endpoints
- Monthly cost: ~$62-77 (with stop/start)
- **Additional savings: $32/month**
- **Total savings: $91-111/month (59%)**

### Fully Optimized
- VPC Endpoints + smaller instances + optimized settings
- Monthly cost: ~$45-60
- **Total savings: $108-128/month (70%)**

## Next Steps

1. **Immediate:** Use the automated stop/start workflows
2. **This Week:** Implement VPC Endpoints to eliminate NAT Gateway costs
3. **This Month:** Optimize instance sizes and settings for dev environment
4. **Ongoing:** Monitor costs and adjust as needed

## Support

For questions or issues:
- Check workflow runs in GitHub Actions
- Review CloudWatch logs for service health
- Check RDS console for database status
- Contact DevOps team for infrastructure changes
