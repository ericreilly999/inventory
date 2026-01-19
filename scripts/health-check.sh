#!/bin/bash

# Health Check Script for Inventory Management System
# Checks the health of all microservices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Service configuration
declare -A services=(
    ["api-gateway"]="8000"
    ["inventory-service"]="8001"
    ["location-service"]="8002"
    ["user-service"]="8003"
    ["reporting-service"]="8004"
    ["ui-service"]="8005"
)

# Function to check service health
check_service_health() {
    local service_name=$1
    local port=$2
    local timeout=${3:-60}
    
    print_status "Checking $service_name on port $port..."
    
    local counter=0
    while [ $counter -lt $timeout ]; do
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "$service_name is healthy"
            return 0
        fi
        
        counter=$((counter + 1))
        sleep 1
    done
    
    print_error "$service_name health check failed after $timeout seconds"
    return 1
}

# Function to check database connectivity
check_database() {
    print_status "Checking database connectivity..."
    
    if docker-compose exec -T postgres pg_isready -U inventory_user -d inventory_management > /dev/null 2>&1; then
        print_success "PostgreSQL database is healthy"
    else
        print_error "PostgreSQL database is not responding"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    print_status "Checking Redis connectivity..."
    
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is healthy"
    else
        print_error "Redis is not responding"
        return 1
    fi
}

# Function to run comprehensive health checks
run_health_checks() {
    local failed_services=()
    
    print_status "Starting comprehensive health checks..."
    echo ""
    
    # Check database services first
    if ! check_database; then
        failed_services+=("postgres")
    fi
    
    if ! check_redis; then
        failed_services+=("redis")
    fi
    
    echo ""
    
    # Check microservices
    for service in "${!services[@]}"; do
        if ! check_service_health "$service" "${services[$service]}"; then
            failed_services+=("$service")
        fi
    done
    
    echo ""
    
    # Summary
    if [ ${#failed_services[@]} -eq 0 ]; then
        print_success "All services are healthy!"
        return 0
    else
        print_error "The following services failed health checks:"
        for service in "${failed_services[@]}"; do
            echo "  - $service"
        done
        return 1
    fi
}

# Function to show service status
show_service_status() {
    print_status "Current service status:"
    docker-compose ps
}

# Function to show help
show_help() {
    echo "Health Check Script for Inventory Management System"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -s, --status   Show service status"
    echo "  -q, --quiet    Run in quiet mode (less verbose output)"
    echo ""
    echo "Examples:"
    echo "  $0             # Run full health checks"
    echo "  $0 --status    # Show service status"
}

# Parse command line arguments
QUIET=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--status)
            show_service_status
            exit 0
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
if [ "$QUIET" = true ]; then
    # Redirect output to suppress verbose messages
    run_health_checks > /dev/null 2>&1
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "All services healthy"
    else
        echo "Some services failed health checks"
    fi
    
    exit $exit_code
else
    run_health_checks
fi