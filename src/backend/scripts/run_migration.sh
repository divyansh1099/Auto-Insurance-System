#!/bin/bash

# Database Migration Runner
# Usage: ./run_migration.sh [migration_file.sql]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get migration file
MIGRATION_FILE=${1:-"migrations/001_add_missing_columns.sql"}

# Check if file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}Error: Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Running database migration: $MIGRATION_FILE${NC}"
echo ""

# Get database connection details from environment or use defaults
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-telematics_db}
DB_USER=${DB_USER:-insurance_user}
DB_PASSWORD=${DB_PASSWORD:-insurance_pass}

# Check if running in Docker
if docker compose ps postgres 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}Detected Docker Compose environment${NC}"
    echo "Running migration in Docker container..."
    
    # Copy migration file to container and execute
    docker compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" < "$MIGRATION_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migration completed successfully!${NC}"
    else
        echo -e "${RED}❌ Migration failed!${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Docker Compose not detected. Attempting direct connection...${NC}"
    
    # Try direct psql connection
    if command -v psql &> /dev/null; then
        export PGPASSWORD="$DB_PASSWORD"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Migration completed successfully!${NC}"
        else
            echo -e "${RED}❌ Migration failed!${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Error: psql not found. Please install PostgreSQL client or use Docker Compose.${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Migration verification:${NC}"
echo "You can verify the migration by checking the database schema."

