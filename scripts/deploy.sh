#!/bin/bash

# Deployment script for Inventory Management System
# This script handles deployment to different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
AWS_REGION="us-east-1"
IMAGE_TAG="latest"
DRY_RUN=false
SKIP_TESTS=false
SKIP_BUILD=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "Deployment Script for Inventory Management System"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Target environment (dev|staging|prod) [default: dev]"
    echo "  -r, --region REGION      AWS region [default: us-east-1]"
    echo "  -t, --tag TAG           Docker image tag [default: latest]"
    echo "  -d, --dry-run           Show what would be deployed without actually deploying"
    echo "  --skip-tests            Skip running tests before deployment"
    echo "  --skip-build            Skip building Docker images"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e dev                           # Deploy to development"
    echo "  $0 -e prod -t v1.2.3               # Deploy specific version to production"
    echo "  $0 -e staging --dry-run             # Preview staging deployment"
}

# Function to validate environment
validate_environment() {
    case $ENVIRONMENT in
        dev|staging|prod)
            print_status "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT"
            print_error "Valid environments: dev, staging, prod"
            exit 1
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if required tools are installed
    local required_tools=("docker" "aws" "terraform" "jq")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Function to run tests
run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        print_warning "Skipping tests as requested"
        return 0
    fi
    
    print_status "Running tests..."
    
    # Start test services
    docker-compose -f docker-compose.test.yml up -d postgres redis
    
    # Wait for services to be ready
    sleep 10
    
    # Run tests
    if poetry run pytest tests/ --tb=short; then
        print_success "All tests passed"
    else
        print_error "Tests failed"
        docker-compose -f docker-compose.test.yml down
        exit 1
    fi
    
    # Clean up test services
    docker-compose -f docker-compose.test.yml down
}

# Function to build Docker images
build_images() {
    if [ "$SKIP_BUILD" = true ]; then
        print_warning "Skipping image build as requested"
        return 0
    fi
    
    print_status "Building Docker images..."
    
    local services=("api_gateway" "inventory" "location" "user" "reporting" "ui")
    
    for service in "${services[@]}"; do
        print_status "Building $service image..."
        
        if [ "$DRY_RUN" = false ]; then
            docker build -t "inventory-management-$service:$IMAGE_TAG" \
                -f "services/$service/Dockerfile" .
        else
            print_status "DRY RUN: Would build inventory-management-$service:$IMAGE_TAG"
        fi
    done
    
    print_success "All images built successfully"
}

# Function to push images to ECR
push_images() {
    print_status "Pushing images to ECR..."
    
    # Get ECR login token
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin \
        "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com"
    
    local services=("api_gateway" "inventory" "location" "user" "reporting" "ui")
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local ecr_registry="$account_id.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    for service in "${services[@]}"; do
        local local_tag="inventory-management-$service:$IMAGE_TAG"
        local remote_tag="$ecr_registry/inventory-management-$service:$IMAGE_TAG"
        
        print_status "Pushing $service image..."
        
        if [ "$DRY_RUN" = false ]; then
            docker tag "$local_tag" "$remote_tag"
            docker push "$remote_tag"
        else
            print_status "DRY RUN: Would push $remote_tag"
        fi
    done
    
    print_success "All images pushed successfully"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure with Terraform..."
    
    local terraform_dir="terraform/environments/$ENVIRONMENT"
    
    if [ ! -d "$terraform_dir" ]; then
        print_error "Terraform configuration not found for environment: $ENVIRONMENT"
        exit 1
    fi
    
    cd "$terraform_dir"
    
    # Initialize Terraform
    if [ "$DRY_RUN" = false ]; then
        terraform init
    else
        print_status "DRY RUN: Would run terraform init"
    fi
    
    # Plan deployment
    print_status "Creating Terraform plan..."
    
    if [ "$DRY_RUN" = false ]; then
        terraform plan \
            -var="environment=$ENVIRONMENT" \
            -var="aws_region=$AWS_REGION" \
            -var="image_tag=$IMAGE_TAG" \
            -out=tfplan
    else
        print_status "DRY RUN: Would create Terraform plan"
    fi
    
    # Apply deployment
    if [ "$DRY_RUN" = false ]; then
        print_status "Applying Terraform plan..."
        terraform apply -auto-approve tfplan
        print_success "Infrastructure deployed successfully"
    else
        print_status "DRY RUN: Would apply Terraform plan"
    fi
    
    cd - > /dev/null
}

# Function to update ECS services
update_ecs_services() {
    print_status "Updating ECS services..."
    
    local cluster_name="inventory-management-$ENVIRONMENT"
    local services=("api-gateway" "inventory-service" "location-service" "user-service" "reporting-service" "ui-service")
    
    for service in "${services[@]}"; do
        local service_name="inventory-management-$ENVIRONMENT-$service"
        
        print_status "Updating ECS service: $service_name"
        
        if [ "$DRY_RUN" = false ]; then
            aws ecs update-service \
                --cluster "$cluster_name" \
                --service "$service_name" \
                --force-new-deployment \
                --region "$AWS_REGION" > /dev/null
        else
            print_status "DRY RUN: Would update ECS service $service_name"
        fi
    done
    
    if [ "$DRY_RUN" = false ]; then
        print_status "Waiting for services to stabilize..."
        
        for service in "${services[@]}"; do
            local service_name="inventory-management-$ENVIRONMENT-$service"
            
            print_status "Waiting for $service_name to stabilize..."
            aws ecs wait services-stable \
                --cluster "$cluster_name" \
                --services "$service_name" \
                --region "$AWS_REGION"
        done
        
        print_success "All services updated successfully"
    else
        print_status "DRY RUN: Would wait for services to stabilize"
    fi
}

# Function to run health checks
run_health_checks() {
    if [ "$DRY_RUN" = true ]; then
        print_status "DRY RUN: Would run health checks"
        return 0
    fi
    
    print_status "Running post-deployment health checks..."
    
    # Get load balancer URL
    local lb_dns=$(aws elbv2 describe-load-balancers \
        --names "inventory-management-$ENVIRONMENT-alb" \
        --region "$AWS_REGION" \
        --query 'LoadBalancers[0].DNSName' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$lb_dns" ] || [ "$lb_dns" = "None" ]; then
        print_warning "Load balancer not found, skipping health checks"
        return 0
    fi
    
    local health_url="http://$lb_dns/health"
    local max_attempts=30
    local attempt=1
    
    print_status "Checking health endpoint: $health_url"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            print_success "Health check passed"
            return 0
        fi
        
        print_status "Health check attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    print_error "Health checks failed after $max_attempts attempts"
    exit 1
}

# Function to create deployment summary
create_deployment_summary() {
    print_status "Creating deployment summary..."
    
    local summary_file="deployment-summary-$ENVIRONMENT-$(date +%Y%m%d-%H%M%S).json"
    
    cat > "$summary_file" << EOF
{
  "deployment": {
    "environment": "$ENVIRONMENT",
    "region": "$AWS_REGION",
    "image_tag": "$IMAGE_TAG",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "dry_run": $DRY_RUN,
    "skip_tests": $SKIP_TESTS,
    "skip_build": $SKIP_BUILD,
    "deployed_by": "$(whoami)",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
  }
}
EOF
    
    print_success "Deployment summary saved to: $summary_file"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main deployment flow
main() {
    print_status "Starting deployment process..."
    
    validate_environment
    check_prerequisites
    
    if [ "$DRY_RUN" = true ]; then
        print_warning "DRY RUN MODE - No actual changes will be made"
    fi
    
    run_tests
    build_images
    push_images
    deploy_infrastructure
    update_ecs_services
    run_health_checks
    create_deployment_summary
    
    print_success "Deployment completed successfully!"
    
    if [ "$DRY_RUN" = false ]; then
        print_status "Environment: $ENVIRONMENT"
        print_status "Region: $AWS_REGION"
        print_status "Image Tag: $IMAGE_TAG"
    fi
}

# Run main function
main