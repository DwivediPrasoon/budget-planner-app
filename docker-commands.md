# Docker Commands for Local Development

This document contains all the necessary Docker commands to run the Budget Planner application locally with PostgreSQL database.

## Prerequisites

Make sure you have Docker and Docker Compose installed on your system.

## Quick Start

### 1. Start the PostgreSQL Database

```bash
# Start the database container
docker-compose up -d postgres

# Check if the container is running
docker-compose ps

# View logs
docker-compose logs postgres
```

### 2. Set up Environment Variables

```bash
# Copy the example environment file
cp env.local.example .env

# Edit the .env file if needed
nano .env
```

### 3. Run the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run the Flask application
python app_postgres.py
```

## Database Management Commands

### Start Database
```bash
docker-compose up -d postgres
```

### Stop Database
```bash
docker-compose down
```

### Restart Database
```bash
docker-compose restart postgres
```

### View Database Logs
```bash
docker-compose logs postgres
```

### Access Database Shell
```bash
# Connect to PostgreSQL shell
docker-compose exec postgres psql -U postgres -d budget_planner

# Or connect from host machine (if you have psql installed)
psql -h localhost -p 5432 -U postgres -d budget_planner
```

### Reset Database (Delete all data)
```bash
# Stop and remove containers with volumes
docker-compose down -v

# Start fresh
docker-compose up -d postgres
```

## Database Connection Details

- **Host**: localhost
- **Port**: 5432
- **Database**: budget_planner
- **Username**: postgres
- **Password**: postgres123

## Troubleshooting

### Check Database Health
```bash
# Check if database is ready
docker-compose exec postgres pg_isready -U postgres -d budget_planner
```

### View Container Status
```bash
docker-compose ps
```

### Check Database Connection
```bash
# Test connection from host
docker-compose exec postgres psql -U postgres -d budget_planner -c "SELECT version();"
```

### Reset Everything
```bash
# Stop all containers and remove volumes
docker-compose down -v

# Remove all images (optional)
docker system prune -a

# Start fresh
docker-compose up -d postgres
```

## Development Workflow

1. **Start database**: `docker-compose up -d postgres`
2. **Wait for database to be ready**: Check logs with `docker-compose logs postgres`
3. **Run application**: `source venv/bin/activate && python app_postgres.py`
4. **Access application**: Open http://localhost:5000 in your browser
5. **Stop when done**: `docker-compose down`

## Environment Variables

The application uses these environment variables for database connection:

- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: budget_planner)
- `DB_USER`: Database username (default: postgres)
- `DB_PASSWORD`: Database password (default: postgres123)

## Notes

- The database data is persisted in a Docker volume named `postgres_data`
- The database will be automatically initialized when the container starts for the first time
- The Flask application will create all necessary tables when it starts
- You can access the database using any PostgreSQL client with the connection details above 