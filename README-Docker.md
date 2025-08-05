# Docker Setup for Budget Planner

This guide will help you set up the Budget Planner application locally using Docker for the PostgreSQL database.

## Quick Start

### 1. Prerequisites

- Docker Desktop installed and running
- Docker Compose (usually comes with Docker Desktop)
- Python 3.7+ and virtual environment

### 2. Start the Database

```bash
# Using the convenience script
./db.sh start

# Or using docker-compose directly
docker-compose up -d postgres
```

### 3. Set up Environment Variables

```bash
# Copy the example environment file
cp env.local.example .env

# The default values should work, but you can edit if needed
nano .env
```

### 4. Run the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run the Flask application
python app_postgres.py
```

### 5. Access the Application

Open your browser and go to: http://localhost:5000

## Database Management

### Using the Convenience Script

The `db.sh` script provides easy commands for database management:

```bash
./db.sh start      # Start the database
./db.sh stop       # Stop the database
./db.sh restart    # Restart the database
./db.sh status     # Check database status
./db.sh connect    # Connect to database shell
./db.sh logs       # View database logs
./db.sh reset      # Reset database (delete all data)
./db.sh help       # Show all available commands
```

### Using Docker Compose Directly

```bash
# Start database
docker-compose up -d postgres

# Stop database
docker-compose down

# View logs
docker-compose logs postgres

# Connect to database shell
docker-compose exec postgres psql -U postgres -d budget_planner
```

## Database Connection Details

- **Host**: localhost
- **Port**: 5432
- **Database**: budget_planner
- **Username**: postgres
- **Password**: postgres123

## Development Workflow

1. **Start the day**: `./db.sh start`
2. **Run application**: `source venv/bin/activate && python app_postgres.py`
3. **End the day**: `./db.sh stop`

## Troubleshooting

### Database Won't Start

```bash
# Check Docker status
docker info

# Check if port 5432 is available
lsof -i :5432

# View detailed logs
./db.sh logs
```

### Connection Issues

```bash
# Check if database is ready
./db.sh status

# Test connection
docker-compose exec postgres pg_isready -U postgres -d budget_planner
```

### Reset Everything

```bash
# Stop and remove everything
docker-compose down -v

# Start fresh
./db.sh start
```

## Files Created

- `docker-compose.yml` - Docker Compose configuration
- `init.sql` - Database initialization script
- `env.local.example` - Example environment variables
- `db.sh` - Database management script
- `docker-commands.md` - Detailed Docker commands reference

## Notes

- Database data is persisted in a Docker volume
- The database will be automatically initialized on first start
- The Flask application creates all necessary tables
- You can use any PostgreSQL client to connect to the database 