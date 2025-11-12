#!/bin/bash

# Quick test script for Phase 1 improvements
# Usage: ./bin/test_improvements.sh

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BOLD}${BLUE}=================================================${NC}"
echo -e "${BOLD}${BLUE}  Phase 1 Performance Improvements Quick Test${NC}"
echo -e "${BOLD}${BLUE}=================================================${NC}\n"

# Test 1: Check if services are running
echo -e "${BOLD}1. Checking services...${NC}"
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Docker services are running${NC}"
else
    echo -e "${RED}✗ Docker services not running${NC}"
    echo -e "${YELLOW}Run: docker compose up -d${NC}"
    exit 1
fi

# Test 2: Check API availability
echo -e "\n${BOLD}2. Testing API availability...${NC}"
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is accessible${NC}"
else
    echo -e "${RED}✗ API is not accessible${NC}"
    exit 1
fi

# Test 3: Check metrics endpoint
echo -e "\n${BOLD}3. Testing metrics endpoint...${NC}"
METRICS=$(curl -s http://localhost:8000/metrics)

if echo "$METRICS" | grep -q "cache_hits_total"; then
    echo -e "${GREEN}✓ New cache metrics available${NC}"
else
    echo -e "${YELLOW}⚠ Cache metrics not found (may need metrics collector enabled)${NC}"
fi

if echo "$METRICS" | grep -q "db_connection_pool_size"; then
    echo -e "${GREEN}✓ Database pool metrics available${NC}"
else
    echo -e "${YELLOW}⚠ DB pool metrics not found${NC}"
fi

if echo "$METRICS" | grep -q "kafka_consumer_lag"; then
    echo -e "${GREEN}✓ Kafka lag metrics available${NC}"
else
    echo -e "${YELLOW}⚠ Kafka lag metrics not found${NC}"
fi

if echo "$METRICS" | grep -q "active_drivers_total"; then
    echo -e "${GREEN}✓ Business metrics available${NC}"
else
    echo -e "${YELLOW}⚠ Business metrics not found (metrics collector may need to be started)${NC}"
fi

# Test 4: Check database indexes
echo -e "\n${BOLD}4. Checking database indexes...${NC}"
INDEX_COUNT=$(docker compose exec -T postgres psql -U insurance_user -d insurance_db -t -c "
    SELECT COUNT(*)
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$INDEX_COUNT" -gt 20 ]; then
    echo -e "${GREEN}✓ Database indexes created (${INDEX_COUNT} indexes)${NC}"
elif [ "$INDEX_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Some indexes created (${INDEX_COUNT} indexes, expected 25+)${NC}"
else
    echo -e "${RED}✗ No indexes found${NC}"
    echo -e "${YELLOW}Run: docker compose exec postgres psql -U insurance_user -d insurance_db -f /app/migrations/001_add_performance_indexes.sql${NC}"
fi

# Test 5: Test query performance
echo -e "\n${BOLD}5. Testing query performance...${NC}"
START=$(date +%s%N)
docker compose exec -T postgres psql -U insurance_user -d insurance_db -t -c "
    SELECT COUNT(*) FROM telematics_events LIMIT 1
" > /dev/null 2>&1 || true
END=$(date +%s%N)
DURATION_MS=$(( (END - START) / 1000000 ))

if [ $DURATION_MS -lt 100 ]; then
    echo -e "${GREEN}✓ Query performance: ${DURATION_MS}ms (EXCELLENT)${NC}"
elif [ $DURATION_MS -lt 500 ]; then
    echo -e "${GREEN}✓ Query performance: ${DURATION_MS}ms (GOOD)${NC}"
else
    echo -e "${YELLOW}⚠ Query performance: ${DURATION_MS}ms (could be better)${NC}"
fi

# Test 6: Check Redis
echo -e "\n${BOLD}6. Testing Redis connection...${NC}"
if docker compose exec -T redis redis-cli PING 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✓ Redis is responding${NC}"

    # Test SCAN command
    docker compose exec -T redis redis-cli SET test_scan_key "test" EX 60 > /dev/null 2>&1
    SCAN_RESULT=$(docker compose exec -T redis redis-cli SCAN 0 MATCH "test_*" COUNT 100 2>/dev/null || echo "FAIL")

    if echo "$SCAN_RESULT" | grep -q "test_scan_key"; then
        echo -e "${GREEN}✓ Redis SCAN working correctly${NC}"
        docker compose exec -T redis redis-cli DEL test_scan_key > /dev/null 2>&1
    fi
else
    echo -e "${RED}✗ Redis not accessible${NC}"
fi

# Test 7: API response time
echo -e "\n${BOLD}7. Testing API response times...${NC}"
echo -e "${BLUE}(Testing without authentication - 401 responses are OK)${NC}"

# Test /docs endpoint (should work)
START=$(date +%s%N)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")
END=$(date +%s%N)
DURATION_MS=$(( (END - START) / 1000000 ))

if [ "$STATUS" = "200" ]; then
    if [ $DURATION_MS -lt 200 ]; then
        echo -e "${GREEN}✓ API /docs: ${DURATION_MS}ms (Status: ${STATUS})${NC}"
    else
        echo -e "${YELLOW}⚠ API /docs: ${DURATION_MS}ms (Status: ${STATUS})${NC}"
    fi
else
    echo -e "${YELLOW}⚠ API /docs returned status: ${STATUS}${NC}"
fi

# Summary
echo -e "\n${BOLD}${BLUE}=================================================${NC}"
echo -e "${BOLD}${BLUE}  Test Summary${NC}"
echo -e "${BOLD}${BLUE}=================================================${NC}"

echo -e "\n${GREEN}✓${NC} = Working correctly"
echo -e "${YELLOW}⚠${NC} = Working but needs attention"
echo -e "${RED}✗${NC} = Not working"

echo -e "\n${BOLD}Next steps:${NC}"
echo -e "1. Check detailed test results above"
echo -e "2. For comprehensive testing, run: ${BLUE}python3 tests/test_performance_improvements.py${NC}"
echo -e "3. View metrics at: ${BLUE}http://localhost:8000/metrics${NC}"
echo -e "4. View API docs at: ${BLUE}http://localhost:8000/docs${NC}"

echo -e "\n${BOLD}If indexes are missing:${NC}"
echo -e "${BLUE}docker compose exec postgres psql -U insurance_user -d insurance_db -f /app/migrations/001_add_performance_indexes.sql${NC}"

echo -e "\n${BOLD}To enable metrics collector:${NC}"
echo -e "Add to src/backend/app/main.py startup event:"
echo -e "${BLUE}from app.services.metrics_collector import start_metrics_collector"
echo -e "asyncio.create_task(start_metrics_collector())${NC}"

echo ""
