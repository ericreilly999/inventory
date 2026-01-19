#!/bin/bash

# Docker Utilities for Inventory Management System
# This script provides utilities for managing Docker containers

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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to create log directories
create_log_dirs() {
    print_status "Creating log directories..."
    mkdir -p logs/{api-gateway,inventory-service,location-service,user-service,reporting-service,ui-service}
    print_success "Log directories created"
}

# Function to build all images
build_images() {
    print_status "Building Docker images..."
    docker-compose build --no-cache
    print_success "All images built successfully"
}

# Function to start services
start_services() {
    local env=${1:-development}
    print_status "Starting services in $env environment..."
    
    create_log_dirs
    
    if [ "$env" = "production" ]; then
        docker-compose -f docker-compose.prod.yml up -d
    else
        docker-compose up -d
    fi
    
    print_success "Services started successfully"
}

# Function to stop services
stop_services() {
    local env=${1:-development}
    print_status "Stopping services..."
    
    if [ "$env" = "production" ]; then
        docker-compose -f docker-compose.prod.yml down
    else
        docker-compose down
    fi
    
    print_success "Services stopped successfully"
}

# Function to restart services
restart_services() {
    local env=${1:-development}
    print_status "Restarting services..."
    stop_services "$env"
    start_services "$env"
}

# Function to show service status
show_status() {
    print_status "Service status:"
    docker-compose ps
}

# Function to show logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Function to run health checks
health_check() {
    print_status "Running health checks..."
    
    services=("api-gateway" "inventory-service" "location-service" "user-service" "reporting-service" "ui-service")
    ports=(8000 8001 8002 8003 8004 8005)
    
    for i in "${!services[@]}"; do
        service="${services[$i]}"
        port="${ports[$i]}"
        
        print_status "Checking $service on port $port..."
        
        # Wait for service to be ready
        timeout=60
        counter=0
        
        while [ $counter -lt $timeout ]; do
            if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
                print_success "$service is healthy"
                break
            fi
            
            counter=$((counter + 1))
            sleep 1
        done
        
        if [ $counter -eq $timeout ]; then
            print_error "$service health check failed after $timeout seconds"
        fi
    done
}

# Function to clean up Docker resources
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Docker Utilities for Inventory Management System"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build                 Build all Docker images"
    echo "  start [env]          Start services (env: development|production, default: development)"
    echo "  stop [env]           Stop services (env: development|production, default: development)"
    echo "  restart [env]        Restart services (env: development|production, default: development)"
    echo "  status               Show service status"
    echo "  logs [service]       Show logs (all services if no service specified)"
    echo "  health               Run health checks on all services"
    echo "  cleanup              Clean up Docker resources (containers, images, volumes, networks)"
    echo "  help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start services in development mode"
    echo "  $0 start production         # Start services in production mode"
    echo "  $0 logs api-gateway         # Show logs for api-gateway service"
    echo "  $0 health                   # Run health checks"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build_images
            ;;
        start)
            start_services "${2:-development}"
            ;;
        stop)
            stop_services "${2:-development}"
            ;;
        restart)
            restart_services "${2:-development}"
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        health)
            health_check
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"