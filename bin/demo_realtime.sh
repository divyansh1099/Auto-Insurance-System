#!/bin/bash

# Real-Time System Demo Script
# This script demonstrates the near real-time processing system

set -e

echo "🚀 Real-Time Telematics System Demo"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if services are running
echo -e "${BLUE}📋 Checking services...${NC}"
if ! docker ps | grep -q "backend"; then
    echo -e "${RED}❌ Backend service is not running${NC}"
    echo "Starting services..."
    docker-compose up -d
    echo "Waiting for services to be ready..."
    sleep 10
fi

# Get driver ID (use first available or DRV-0001)
DRIVER_ID=${1:-DRV-0001}
echo -e "${GREEN}✓ Using driver: $DRIVER_ID${NC}"
echo ""

# Check if user is logged in (optional)
echo -e "${BLUE}📝 Note: Make sure you're logged in at http://localhost:3000/login${NC}"
echo -e "${BLUE}   Username: demo${NC}"
echo -e "${BLUE}   Password: demo123${NC}"
echo ""

# Step 1: Generate initial data
echo -e "${YELLOW}Step 1: Generating initial telematics data...${NC}"
python3 src/backend/scripts/generate_telematics_data.py \
  --driver-id "$DRIVER_ID" \
  --events 20 \
  --lat 37.7749 \
  --lon -122.4194 || {
    echo -e "${RED}Error: Make sure Python script is executable and dependencies are installed${NC}"
    exit 1
}

echo -e "${GREEN}✓ Generated 20 initial events${NC}"
echo ""

# Step 2: Check events in database
echo -e "${YELLOW}Step 2: Verifying events in database...${NC}"
EVENT_COUNT=$(docker exec backend python3 -c "
from app.models.database import SessionLocal, TelematicsEvent
db = SessionLocal()
count = db.query(TelematicsEvent).filter(TelematicsEvent.driver_id == '$DRIVER_ID').count()
print(count)
" 2>/dev/null || echo "0")

echo -e "${GREEN}✓ Found $EVENT_COUNT events for driver $DRIVER_ID${NC}"
echo ""

# Step 3: Generate a trip with realistic behavior
echo -e "${YELLOW}Step 3: Generating a realistic trip (20 minutes)...${NC}"
echo "This will create events with varying speeds and behaviors..."
python3 src/backend/scripts/generate_telematics_data.py \
  --driver-id "$DRIVER_ID" \
  --trip \
  --trip-duration 20 \
  --lat 37.7749 \
  --lon -122.4194 || {
    echo -e "${RED}Error generating trip${NC}"
    exit 1
}

echo -e "${GREEN}✓ Trip generated${NC}"
echo ""

# Step 4: Check Kafka consumer
echo -e "${YELLOW}Step 4: Checking Kafka consumer status...${NC}"
if docker logs backend 2>&1 | grep -q "kafka_consumer_started"; then
    echo -e "${GREEN}✓ Kafka consumer is running${NC}"
else
    echo -e "${YELLOW}⚠ Kafka consumer may not be running${NC}"
fi
echo ""

# Step 5: Check real-time analysis
echo -e "${YELLOW}Step 5: Checking real-time analysis...${NC}"
sleep 2

# Try to get analysis via API
ANALYSIS=$(curl -s http://localhost:8000/api/v1/realtime/analysis/$DRIVER_ID \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"demo","password":"demo123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)" 2>/dev/null || echo "")

if [ ! -z "$ANALYSIS" ]; then
    echo -e "${GREEN}✓ Real-time analysis available${NC}"
    echo "$ANALYSIS" | python3 -m json.tool 2>/dev/null | head -20 || echo "$ANALYSIS"
else
    echo -e "${YELLOW}⚠ Real-time analysis not available yet (may need more events)${NC}"
fi
echo ""

# Step 6: Instructions for viewing
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📱 Next Steps:${NC}"
echo ""
echo "1. Open Live Dashboard:"
echo -e "   ${GREEN}http://localhost:3000/live${NC}"
echo ""
echo "2. Or navigate to 'Live Driving' in the sidebar"
echo ""
echo "3. Generate more data to see real-time updates:"
echo -e "   ${YELLOW}python3 src/backend/scripts/generate_telematics_data.py \\${NC}"
echo -e "   ${YELLOW}  --driver-id $DRIVER_ID \\${NC}"
echo -e "   ${YELLOW}  --duration 60 \\${NC}"
echo -e "   ${YELLOW}  --interval 10${NC}"
echo ""
echo "4. Watch for:"
echo "   • Safety Score updates"
echo "   • Risk Score changes"
echo "   • Safety alert popups"
echo "   • Dynamic pricing updates"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Step 7: Continuous data generation (optional)
read -p "Generate continuous data for 60 seconds? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Generating events every 10 seconds for 60 seconds...${NC}"
    echo "Open http://localhost:3000/live in your browser to see updates!"
    echo ""
    python3 src/backend/scripts/generate_telematics_data.py \
      --driver-id "$DRIVER_ID" \
      --duration 60 \
      --interval 10 \
      --lat 37.7749 \
      --lon -122.4194 &
    
    echo -e "${GREEN}✓ Data generation started in background${NC}"
    echo "Check the Live Dashboard to see real-time updates!"
fi

