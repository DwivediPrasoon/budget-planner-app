#!/bin/bash

# Budget Planner Database Management Script

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

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
}

# Function to start database
start_db() {
    print_status "Starting PostgreSQL database..."
    docker-compose up -d postgres
    
    print_status "Waiting for database to be ready..."
    sleep 5
    
    # Check if database is ready
    if docker-compose exec postgres pg_isready -U postgres -d budget_planner > /dev/null 2>&1; then
        print_success "Database is ready!"
        print_status "Database connection details:"
        echo "  Host: localhost"
        echo "  Port: 5432"
        echo "  Database: budget_planner"
        echo "  Username: postgres"
        echo "  Password: postgres123"
    else
        print_warning "Database might still be starting up. Please wait a moment and check with: docker-compose logs postgres"
    fi
}

# Function to stop database
stop_db() {
    print_status "Stopping PostgreSQL database..."
    docker-compose down
    print_success "Database stopped!"
}

# Function to restart database
restart_db() {
    print_status "Restarting PostgreSQL database..."
    docker-compose restart postgres
    print_success "Database restarted!"
}

# Function to show database status
status_db() {
    print_status "Database status:"
    docker-compose ps postgres
    
    echo ""
    print_status "Recent logs:"
    docker-compose logs --tail=10 postgres
}

# Function to reset database
reset_db() {
    print_warning "This will delete all data in the database. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Resetting database..."
        docker-compose down -v
        docker-compose up -d postgres
        print_success "Database reset complete!"
    else
        print_status "Database reset cancelled."
    fi
}

# Function to connect to database shell
connect_db() {
    print_status "Connecting to database shell..."
    docker-compose exec postgres psql -U postgres -d budget_planner
}

# Function to show logs
logs_db() {
    print_status "Showing database logs..."
    docker-compose logs -f postgres
}

# Function to show help
show_help() {
    echo "Budget Planner Database Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the PostgreSQL database"
    echo "  stop      Stop the PostgreSQL database"
    echo "  restart   Restart the PostgreSQL database"
    echo "  status    Show database status and recent logs"
    echo "  reset     Reset database (delete all data)"
    echo "  connect   Connect to database shell"
    echo "  logs      Show database logs (follow mode)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start the database"
    echo "  $0 status   # Check database status"
    echo "  $0 connect  # Connect to database shell"
}

# Main script logic
main() {
    check_docker
    check_docker_compose
    
    case "${1:-help}" in
        start)
            start_db
            ;;
        stop)
            stop_db
            ;;
        restart)
            restart_db
            ;;
        status)
            status_db
            ;;
        reset)
            reset_db
            ;;
        connect)
            connect_db
            ;;
        logs)
            logs_db
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 