# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Inventory Management System.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and consists of multiple workflows that handle different aspects of the development lifecycle:

- **Continuous Integration (CI)**: Automated testing, code quality checks, and security scanning
- **Continuous Deployment (CD)**: Automated deployment to different environments
- **Quality Assurance**: Code quality metrics, test coverage, and performance testing
- **Security**: Vulnerability scanning, dependency checks, and compliance validation
- **Dependency Management**: Automated dependency updates and maintenance

## Workflows

### 1. Continuous Integration (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**
- **test-python-services**: Runs unit tests, integration tests, and property-based tests for Python services
- **test-ui-service**: Runs tests for the React UI service
- **security-scan**: Performs security vulnerability scanning
- **docker-build-test**: Tests Docker image builds for all services
- **terraform-validate**: Validates Terraform infrastructure code

**Prerequisites:**
- PostgreSQL and Redis test databases
- Python 3.11 and Node.js 18
- Poetry for Python dependency management

### 2. Continuous Deployment (`cd.yml`)

**Triggers:**
- Push to `main` branch (automatic deployment to dev)
- Manual workflow dispatch for staging/production deployments

**Jobs:**
- **build-and-push**: Builds and pushes Docker images to Amazon ECR
- **deploy-dev**: Deploys to development environment
- **deploy-staging**: Deploys to staging environment (manual trigger)
- **deploy-prod**: Deploys to production environment (manual trigger)
- **notify**: Sends deployment status notifications

**Environment Requirements:**
- AWS credentials configured as GitHub secrets
- ECR repositories created for each service
- Terraform state backend configured

### 3. Quality Assurance (`quality.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**
- **code-quality**: Runs linting, formatting, and type checking
- **test-coverage**: Measures test coverage and uploads to Codecov
- **performance-test**: Runs performance benchmarks
- **documentation-check**: Validates documentation quality
- **quality-gate**: Evaluates overall quality metrics

**Quality Standards:**
- Minimum 80% test coverage
- All linting checks must pass
- Type checking must pass without errors
- Performance benchmarks must meet thresholds

### 4. Security Scanning (`security.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch
- Daily scheduled scans at 2 AM UTC

**Jobs:**
- **dependency-scan**: Scans Python and Node.js dependencies for vulnerabilities
- **container-scan**: Scans Docker images for security issues
- **infrastructure-scan**: Scans Terraform code for security misconfigurations
- **secrets-scan**: Scans for exposed secrets in code
- **license-check**: Validates license compliance
- **security-summary**: Generates comprehensive security report

**Security Tools:**
- Safety (Python dependency scanning)
- Bandit (Python security linting)
- Trivy (Container vulnerability scanning)
- Grype (Additional container scanning)
- Checkov (Infrastructure security scanning)
- TFSec (Terraform security scanning)
- TruffleHog (Secrets detection)

### 5. Dependency Updates (`dependency-update.yml`)

**Triggers:**
- Weekly schedule (Mondays at 9 AM UTC)
- Manual workflow dispatch

**Jobs:**
- **update-python-deps**: Updates Python dependencies using Poetry
- **update-nodejs-deps**: Updates Node.js dependencies using npm
- **update-github-actions**: Updates GitHub Actions using Renovate
- **update-docker-images**: Updates Docker base images

**Automation:**
- Creates pull requests for dependency updates
- Groups related updates together
- Includes security vulnerability fixes

## Environment Configuration

### Development Environment

- **Automatic Deployment**: Triggered on every push to `main`
- **Infrastructure**: Single-instance services for cost optimization
- **Monitoring**: Basic CloudWatch logging
- **Database**: Single-AZ RDS instance

### Staging Environment

- **Manual Deployment**: Triggered via workflow dispatch
- **Infrastructure**: Production-like setup with reduced capacity
- **Monitoring**: Full monitoring and alerting
- **Database**: Multi-AZ RDS instance

### Production Environment

- **Manual Deployment**: Requires staging deployment success
- **Infrastructure**: High-availability setup with auto-scaling
- **Monitoring**: Comprehensive monitoring, alerting, and logging
- **Database**: Multi-AZ RDS with read replicas

## Required Secrets

Configure the following secrets in your GitHub repository:

### AWS Configuration
```
AWS_ACCESS_KEY_ID          # AWS access key for deployment
AWS_SECRET_ACCESS_KEY      # AWS secret key for deployment
ECR_REGISTRY              # ECR registry URL
```

### Application Configuration
```
JWT_SECRET_KEY            # JWT signing key for production
DATABASE_URL              # Production database connection string
REDIS_URL                 # Production Redis connection string
```

### Monitoring and Notifications
```
CODECOV_TOKEN             # Codecov integration token
SLACK_WEBHOOK_URL         # Slack notifications (optional)
```

## Local Development

### Running Tests Locally

```bash
# Install dependencies
poetry install

# Start test services
docker-compose -f docker-compose.test.yml up -d postgres redis

# Run all tests
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ --cov=services --cov=shared --cov-report=html

# Clean up
docker-compose -f docker-compose.test.yml down
```

### Building Docker Images

```bash
# Build all images
docker-compose build

# Build specific service
docker build -t inventory-management-api-gateway -f services/api_gateway/Dockerfile .
```

### Manual Deployment

```bash
# Deploy to development
./scripts/deploy.sh -e dev

# Deploy specific version to staging
./scripts/deploy.sh -e staging -t v1.2.3

# Dry run deployment
./scripts/deploy.sh -e prod --dry-run
```

## Monitoring and Observability

### Metrics and Logging

- **CloudWatch Logs**: Structured JSON logging for all services
- **CloudWatch Metrics**: Custom metrics for business logic
- **Application Performance**: Response time and error rate monitoring
- **Infrastructure Metrics**: CPU, memory, and network utilization

### Alerting

- **High Error Rates**: Alert when error rate exceeds 5%
- **High Response Times**: Alert when P95 response time exceeds 1 second
- **Service Health**: Alert when health checks fail
- **Infrastructure Issues**: Alert on resource exhaustion

### Dashboards

- **Service Overview**: High-level service health and performance
- **Business Metrics**: Inventory operations and user activity
- **Infrastructure**: Resource utilization and costs
- **Security**: Security events and compliance status

## Troubleshooting

### Common Issues

1. **Test Failures**
   - Check database connectivity
   - Verify environment variables
   - Review test logs for specific failures

2. **Deployment Failures**
   - Verify AWS credentials and permissions
   - Check Terraform state consistency
   - Review ECS service logs

3. **Security Scan Failures**
   - Update vulnerable dependencies
   - Fix security misconfigurations
   - Remove exposed secrets

4. **Quality Gate Failures**
   - Improve test coverage
   - Fix linting and formatting issues
   - Address performance regressions

### Getting Help

- Check GitHub Actions logs for detailed error messages
- Review CloudWatch logs for runtime issues
- Consult the troubleshooting section in the main README
- Contact the development team for assistance

## Best Practices

### Code Quality

- Write comprehensive tests for all new features
- Maintain high test coverage (>80%)
- Follow coding standards and style guides
- Use type hints and documentation

### Security

- Regularly update dependencies
- Scan for vulnerabilities before deployment
- Use secrets management for sensitive data
- Follow security best practices

### Deployment

- Test changes in development environment first
- Use feature flags for gradual rollouts
- Monitor deployments closely
- Have rollback procedures ready

### Monitoring

- Set up appropriate alerts and thresholds
- Monitor business metrics, not just technical metrics
- Use structured logging for better observability
- Regularly review and update monitoring setup