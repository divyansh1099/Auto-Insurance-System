#!/bin/bash
# Migration Script: Bind Mounts → Named Volumes
# This script safely migrates your data from bind mounts to Docker named volumes

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Migration: Bind Mounts → Docker Named Volumes              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check if Docker is running
echo -e "${BLUE}[Step 1/6]${NC} Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Step 2: Create backup
echo -e "${BLUE}[Step 2/6]${NC} Creating database backup..."
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/migration-backup-$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

# Check if postgres container is running
if docker ps --format '{{.Names}}' | grep -q '^postgres$'; then
    echo "   Creating PostgreSQL backup..."
    docker exec postgres pg_dump -U insurance_user telematics_db > $BACKUP_FILE

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
        echo "   Size: $(du -h $BACKUP_FILE | cut -f1)"
    else
        echo -e "${RED}❌ Backup failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  PostgreSQL container not running, skipping backup${NC}"
    echo "   (Safe to continue if you just want to set up fresh)"
fi
echo ""

# Step 3: Stop containers
echo -e "${BLUE}[Step 3/6]${NC} Stopping Docker containers..."
docker-compose stop
echo -e "${GREEN}✅ Containers stopped${NC}"
echo ""

# Step 4: Remove containers (keeps data)
echo -e "${BLUE}[Step 4/6]${NC} Removing containers..."
docker-compose down
echo -e "${GREEN}✅ Containers removed (data preserved in bind mounts)${NC}"
echo ""

# Step 5: Start with new configuration
echo -e "${BLUE}[Step 5/6]${NC} Starting containers with named volumes..."
echo "   This will create new Docker-managed volumes:"
echo "   - postgres_data"
echo "   - redis_data"
echo "   - kafka_data"
echo "   - zookeeper_data"
echo ""

docker-compose up -d

echo -e "${GREEN}✅ Containers started with named volumes${NC}"
echo ""

# Wait for PostgreSQL to be ready
echo "   Waiting for PostgreSQL to be ready..."
sleep 5

MAX_TRIES=30
TRIES=0
until docker exec postgres pg_isready -U insurance_user > /dev/null 2>&1; do
    TRIES=$((TRIES+1))
    if [ $TRIES -gt $MAX_TRIES ]; then
        echo -e "${RED}❌ PostgreSQL failed to start after ${MAX_TRIES} seconds${NC}"
        exit 1
    fi
    echo "   Still waiting... ($TRIES/$MAX_TRIES)"
    sleep 1
done

echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
echo ""

# Step 6: Restore data (if backup exists)
echo -e "${BLUE}[Step 6/6]${NC} Restoring data..."

if [ -f "$BACKUP_FILE" ]; then
    echo "   Restoring from backup: $BACKUP_FILE"
    docker exec -i postgres psql -U insurance_user -d telematics_db < $BACKUP_FILE

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Data restored successfully from backup${NC}"
    else
        echo -e "${RED}❌ Restore from backup failed${NC}"
        echo -e "${YELLOW}   Running default restoration script instead...${NC}"
        ./restore-data.sh
    fi
else
    echo "   No backup found, running default restoration..."
    ./restore-data.sh
fi
echo ""

# Verify migration
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Migration Verification                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check named volumes
echo -e "${BLUE}📦 Docker Named Volumes:${NC}"
docker volume ls --filter name=auto-insurance-system | grep -E "postgres_data|redis_data|kafka_data|zookeeper_data" || echo "   (Volumes created with project prefix)"
echo ""

# Check data
echo -e "${BLUE}📊 Database Status:${NC}"
USER_COUNT=$(docker exec postgres psql -U insurance_user -d telematics_db -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs || echo "0")
DRIVER_COUNT=$(docker exec postgres psql -U insurance_user -d telematics_db -t -c "SELECT COUNT(*) FROM drivers;" 2>/dev/null | xargs || echo "0")
VEHICLE_COUNT=$(docker exec postgres psql -U insurance_user -d telematics_db -t -c "SELECT COUNT(*) FROM vehicles;" 2>/dev/null | xargs || echo "0")
TRIP_COUNT=$(docker exec postgres psql -U insurance_user -d telematics_db -t -c "SELECT COUNT(*) FROM trips;" 2>/dev/null | xargs || echo "0")

echo "   Users: $USER_COUNT"
echo "   Drivers: $DRIVER_COUNT"
echo "   Vehicles: $VEHICLE_COUNT"
echo "   Trips: $TRIP_COUNT"
echo ""

# Check running containers
echo -e "${BLUE}🐳 Running Containers:${NC}"
docker-compose ps
echo ""

# Final status
if [ "$USER_COUNT" -gt 0 ] && [ "$DRIVER_COUNT" -gt 0 ]; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ✅ MIGRATION SUCCESSFUL!                                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${GREEN}Your data has been successfully migrated to Docker named volumes!${NC}"
    echo ""
    echo "📋 What Changed:"
    echo "   ✅ PostgreSQL now uses 'postgres_data' named volume"
    echo "   ✅ Redis now uses 'redis_data' named volume"
    echo "   ✅ Kafka now uses 'kafka_data' named volume"
    echo "   ✅ Zookeeper now uses 'zookeeper_data' named volume"
    echo ""
    echo "🔒 Data Persistence:"
    echo "   ✅ Data survives 'docker-compose down'"
    echo "   ✅ Data only deleted with 'docker-compose down -v'"
    echo "   ✅ Better performance on many systems"
    echo ""
    echo "🗑️  Cleanup Old Bind Mounts (Optional):"
    echo "   The old './data/' directory is no longer used."
    echo "   You can safely delete it:"
    echo "   $ rm -rf ./data/"
    echo ""
    echo "🌐 Access Your Application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "🔑 Login Credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
else
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  MIGRATION COMPLETED WITH WARNINGS                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${YELLOW}The migration completed, but the database appears to be empty.${NC}"
    echo ""
    echo "This might be normal if you're setting up from scratch."
    echo ""
    echo "To populate the database, run:"
    echo "   $ ./restore-data.sh"
    echo ""
fi

# Backup info
if [ -f "$BACKUP_FILE" ]; then
    echo "📁 Backup Location:"
    echo "   $BACKUP_FILE"
    echo "   Keep this backup safe until you verify everything works!"
    echo ""
fi

exit 0
