#!/bin/bash

# VPP Traffic Visualization Engine - Docker Deployment Script
# This script helps deploy the application using Docker and Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose is installed"
    
    # Check Docker daemon
    if ! docker ps &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Build Docker image
build_image() {
    print_header "Building Docker Image"
    
    if docker-compose build; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Start containers
start_containers() {
    print_header "Starting Containers"
    
    if docker-compose up -d; then
        print_success "Containers started successfully"
    else
        print_error "Failed to start containers"
        exit 1
    fi
}

# Wait for service to be ready
wait_for_service() {
    print_header "Waiting for Service to be Ready"
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:5000/api/health &> /dev/null; then
            print_success "Service is ready"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done
    
    print_error "Service failed to start within timeout"
    return 1
}

# Display service information
show_service_info() {
    print_header "Service Information"
    
    print_info "Backend API: http://localhost:5000"
    print_info "Frontend: http://localhost:80"
    print_info "WebSocket: ws://localhost:80/socket.io"
    
    echo ""
    print_info "Docker Compose Status:"
    docker-compose ps
    
    echo ""
    print_info "Useful Commands:"
    echo "  View logs:        docker-compose logs -f"
    echo "  Stop containers:  docker-compose down"
    echo "  Restart service:  docker-compose restart"
    echo "  Remove volumes:   docker-compose down -v"
}

# Main execution
main() {
    print_header "VPP Traffic Visualization Engine - Docker Deployment"
    
    # Parse command line arguments
    case "${1:-start}" in
        start)
            check_prerequisites
            build_image
            start_containers
            wait_for_service
            show_service_info
            ;;
        stop)
            print_header "Stopping Containers"
            docker-compose down
            print_success "Containers stopped"
            ;;
        restart)
            print_header "Restarting Containers"
            docker-compose restart
            print_success "Containers restarted"
            ;;
        logs)
            docker-compose logs -f
            ;;
        status)
            print_header "Container Status"
            docker-compose ps
            ;;
        clean)
            print_header "Cleaning Up"
            docker-compose down -v
            print_success "Cleanup complete"
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|logs|status|clean}"
            echo ""
            echo "Commands:"
            echo "  start   - Build and start containers (default)"
            echo "  stop    - Stop and remove containers"
            echo "  restart - Restart running containers"
            echo "  logs    - View container logs"
            echo "  status  - Show container status"
            echo "  clean   - Remove containers and volumes"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
