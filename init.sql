-- Budget Planner Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Create the database if it doesn't exist (this is handled by POSTGRES_DB env var)
-- The database 'budget_planner' will be created automatically

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE budget_planner TO postgres;

-- Connect to the budget_planner database
\c budget_planner;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Note: The actual tables will be created by the Flask application
-- when it initializes the database using the init_db() function 