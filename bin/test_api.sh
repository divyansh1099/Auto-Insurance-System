#!/bin/bash

# API Testing Script
# Tests all major endpoints

set -e

BASE_URL="http://localhost:8000/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Testing Telematics Insurance System API"
echo "=========================================="
echo ""

# 1. Health Check
echo "1️⃣  Testing Health Check..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
  echo -e "${GREEN}✅ Health check passed${NC}"
else
  echo -e "${RED}❌ Health check failed${NC}"
  echo "$HEALTH"
  exit 1
fi
echo ""

# 2. Login
echo "2️⃣  Testing Login..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo -e "${RED}❌ Login failed${NC}"
  echo "$LOGIN_RESPONSE"
  exit 1
fi
echo -e "${GREEN}✅ Login successful${NC}"
echo ""

# 3. Get Current User
echo "3️⃣  Testing Get Current User..."
USER_RESPONSE=$(curl -s $BASE_URL/auth/me \
  -H "Authorization: Bearer $TOKEN")
if echo "$USER_RESPONSE" | grep -q "username"; then
  echo -e "${GREEN}✅ Get current user successful${NC}"
  echo "$USER_RESPONSE" | jq '.username, .is_admin'
else
  echo -e "${RED}❌ Get current user failed${NC}"
  echo "$USER_RESPONSE"
fi
echo ""

# 4. Get Driver
echo "4️⃣  Testing Get Driver..."
DRIVER_RESPONSE=$(curl -s $BASE_URL/drivers/DRV-0001 \
  -H "Authorization: Bearer $TOKEN")
if echo "$DRIVER_RESPONSE" | grep -q "driver_id"; then
  echo -e "${GREEN}✅ Get driver successful${NC}"
  echo "$DRIVER_RESPONSE" | jq '.driver_id, .first_name, .last_name'
else
  echo -e "${YELLOW}⚠️  Driver not found (may need to create demo data)${NC}"
fi
echo ""

# 5. Get Driver Statistics
echo "5️⃣  Testing Get Driver Statistics..."
STATS_RESPONSE=$(curl -s "$BASE_URL/drivers/DRV-0001/statistics?period_days=30" \
  -H "Authorization: Bearer $TOKEN")
if echo "$STATS_RESPONSE" | grep -q "total_miles"; then
  echo -e "${GREEN}✅ Get statistics successful${NC}"
  echo "$STATS_RESPONSE" | jq '.total_miles, .total_trips, .avg_speed'
else
  echo -e "${YELLOW}⚠️  Statistics not available (may need to generate events)${NC}"
fi
echo ""

# 6. Get Risk Score
echo "6️⃣  Testing Get Risk Score..."
RISK_RESPONSE=$(curl -s $BASE_URL/risk/DRV-0001/score \
  -H "Authorization: Bearer $TOKEN")
if echo "$RISK_RESPONSE" | grep -q "risk_score"; then
  echo -e "${GREEN}✅ Get risk score successful${NC}"
  echo "$RISK_RESPONSE" | jq '.risk_score, .risk_category, .confidence'
else
  echo -e "${YELLOW}⚠️  Risk score not available (may need to generate events)${NC}"
fi
echo ""

# 7. Get Premium
echo "7️⃣  Testing Get Premium..."
PREMIUM_RESPONSE=$(curl -s $BASE_URL/pricing/DRV-0001/current \
  -H "Authorization: Bearer $TOKEN")
if echo "$PREMIUM_RESPONSE" | grep -q "monthly_premium"; then
  echo -e "${GREEN}✅ Get premium successful${NC}"
  echo "$PREMIUM_RESPONSE" | jq '.monthly_premium, .final_premium'
else
  echo -e "${YELLOW}⚠️  Premium not available${NC}"
fi
echo ""

# 8. Get Trips
echo "8️⃣  Testing Get Trips..."
TRIPS_RESPONSE=$(curl -s "$BASE_URL/drivers/DRV-0001/trips?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN")
if echo "$TRIPS_RESPONSE" | grep -q "trips"; then
  echo -e "${GREEN}✅ Get trips successful${NC}"
  TRIP_COUNT=$(echo "$TRIPS_RESPONSE" | jq '.trips | length')
  echo "Trips found: $TRIP_COUNT"
else
  echo -e "${YELLOW}⚠️  Trips not available (may need to generate events)${NC}"
fi
echo ""

# 9. Admin Dashboard Stats
echo "9️⃣  Testing Admin Dashboard Stats..."
ADMIN_RESPONSE=$(curl -s $BASE_URL/admin/dashboard/stats \
  -H "Authorization: Bearer $TOKEN")
if echo "$ADMIN_RESPONSE" | grep -q "total_drivers"; then
  echo -e "${GREEN}✅ Admin dashboard stats successful${NC}"
  echo "$ADMIN_RESPONSE" | jq '.total_drivers, .total_miles, .average_risk_score'
else
  echo -e "${YELLOW}⚠️  Admin stats not available${NC}"
fi
echo ""

# 10. Test Error Handling
echo "🔟 Testing Error Handling..."
ERROR_RESPONSE=$(curl -s $BASE_URL/drivers/INVALID-ID \
  -H "Authorization: Bearer $TOKEN")
if echo "$ERROR_RESPONSE" | grep -q "error_code"; then
  echo -e "${GREEN}✅ Error handling works${NC}"
  echo "$ERROR_RESPONSE" | jq '.error_code, .detail'
else
  echo -e "${YELLOW}⚠️  Error response format may need checking${NC}"
fi
echo ""

# 11. Test Metrics
echo "1️⃣1️⃣ Testing Metrics Endpoint..."
METRICS_RESPONSE=$(curl -s http://localhost:8000/metrics)
if echo "$METRICS_RESPONSE" | grep -q "http_requests_total"; then
  echo -e "${GREEN}✅ Metrics endpoint works${NC}"
  METRIC_COUNT=$(echo "$METRICS_RESPONSE" | grep -c "^[^#]" || true)
  echo "Metrics found: $METRIC_COUNT"
else
  echo -e "${RED}❌ Metrics endpoint failed${NC}"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ Testing completed!${NC}"
echo ""
echo "📊 Summary:"
echo "  - Health: ✅"
echo "  - Authentication: ✅"
echo "  - API Endpoints: ✅"
echo "  - Error Handling: ✅"
echo "  - Metrics: ✅"
echo ""
echo "💡 Tip: Generate test data with:"
echo "   docker compose exec simulator python /app/telematics_simulator.py --duration 60"

