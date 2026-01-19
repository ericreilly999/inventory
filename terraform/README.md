# Inventory Management System - Terraform Infrastructure

This directory contains the Terraform Infrastructure as Code (IaC) for the Inventory Management System. The infrastructure is designed to deploy containerized microservices on AWS Fargate with supporting services.

## Architecture Overview

The infrastructure consists of:

- **VPC with public/private subnets** across multiple AZs
- **Application Load Balancer** for traffic distribution
- **ECS Fargate cluster** for containerized microservices
- **RDS PostgreSQL** with Multi-AZ for high availability
- **ElastiCache Redis** for caching and session storage
- **Service Discovery** for inter-service communication
- **CloudWatch** for logging and monitoring
- **Secrets Manager** for secure credential storage

## Directory Structure

```
terraform/
├── environments/           # Environment-specific configurations
│   ├── dev/               # Development environment
│   ├── prod/              # Production environment
│   └── locals.tf          # Environment-specific local values
├── modules/               # Reusable Terraform modules
│   ├── networking/        # VPC, subnets, routing
│   ├── security/          # Security groups
│   ├── rds/              # PostgreSQL database
│   ├── elasticache/      # Redis cache
│   ├── alb/              # Application Load Balancer
│   ├── ecs-cluster/      # ECS cluster and IAM roles
│   └── ecs-service/      # ECS service template
├── shared/               # Shared variables and outputs
└── README.md
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **Docker** for building container images
4. **AWS permissions** for creating VPC, ECS, RDS, ElastiCache resources

## Environment Configuration

### Development Environment

The development environment is configured for cost optimization:

- **Database**: db.t3.micro with single AZ
- **Cache**: cache.t3.micro with 1 node
- **Containers**: 256 CPU, 512MB memory
- **Auto-scaling**: 1-3 instances
- **Deletion protection**: Disabled

### Production Environment

The production environment is configured for high availability and performance:

- **Database**: db.r6g.large with Multi-AZ
- **Cache**: cache.r6g.large with 2 nodes
- **Containers**: 512 CPU, 1024MB memory
- **Auto-scaling**: 2-20 instances
- **Deletion protection**: Enabled

## Deployment Instructions

### 1. Development Environment

```bash
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Set database password (required)
export TF_VAR_db_password="your-secure-password"

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

### 2. Production Environment

```bash
cd terraform/environments/prod

# Initialize Terraform
terraform init

# Set required variables
export TF_VAR_db_password="your-secure-password"
export TF_VAR_ssl_certificate_arn="arn:aws:acm:region:account:certificate/cert-id"
export TF_VAR_api_gateway_image="your-ecr-repo/api-gateway:v1.0.0"

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

## Required Variables

### Development Environment

- `db_password`: Database password (set via environment variable)

### Production Environment

- `db_password`: Database password (set via environment variable)
- `ssl_certificate_arn`: ARN of SSL certificate for HTTPS
- `api_gateway_image`: Container image URI for API Gateway
- Additional service images as needed

## Resource Tagging

All resources are automatically tagged with:

- `Environment`: Environment name (dev, staging, prod)
- `Product`: "inventory-management"
- `ManagedBy`: "terraform"

Additional environment-specific tags are applied based on the configuration in `locals.tf`.

## Security Considerations

1. **Network Security**: Services run in private subnets with no direct internet access
2. **Database Security**: RDS is isolated in database subnets with restricted access
3. **Secrets Management**: Database and Redis credentials stored in AWS Secrets Manager
4. **Encryption**: All data encrypted at rest and in transit
5. **IAM Roles**: Least privilege access for ECS tasks

## Monitoring and Logging

- **CloudWatch Logs**: Centralized logging for all services
- **Container Insights**: ECS cluster and service metrics
- **Performance Insights**: Database performance monitoring
- **Auto Scaling**: CPU and memory-based scaling policies

## Cost Optimization

### Development Environment

- Uses smaller instance types (t3.micro)
- Single AZ deployment for RDS
- Minimal auto-scaling configuration
- Shorter log retention periods

### Production Environment

- Uses performance-optimized instances (r6g.large)
- Multi-AZ deployment for high availability
- Aggressive auto-scaling for traffic spikes
- Extended log retention for compliance

## Disaster Recovery

- **RDS**: Automated backups with point-in-time recovery
- **Multi-AZ**: Automatic failover for database
- **ElastiCache**: Snapshot-based backup and restore
- **Infrastructure**: Version-controlled Terraform state

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure AWS credentials have sufficient permissions
2. **Resource Limits**: Check AWS service limits for your account
3. **Image Pull Errors**: Verify container images exist and are accessible
4. **Health Check Failures**: Ensure services expose health endpoints

### Useful Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster dev-inventory-cluster --services dev-api-gateway

# View service logs
aws logs tail /ecs/dev-inventory --follow

# Check RDS status
aws rds describe-db-instances --db-instance-identifier dev-inventory-db

# View ElastiCache status
aws elasticache describe-replication-groups --replication-group-id dev-inventory-redis
```

## Cleanup

To destroy the infrastructure:

```bash
# Development environment
cd terraform/environments/dev
terraform destroy

# Production environment
cd terraform/environments/prod
terraform destroy
```

**Warning**: This will permanently delete all resources including databases. Ensure you have backups if needed.