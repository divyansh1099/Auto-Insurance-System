#!/bin/bash

# Live Real-Time Demo
# Shows the system working with actual data generation

echo "🚀 Real-Time Telematics System - Live Demo"
echo "=========================================="
echo ""

# Check services
echo "📋 Checking services..."
if ! docker ps | grep -q "backend"; then
    echo "❌ Backend not running. Start with: docker-compose up -d"
    exit 1
fi
echo "✅ Services running"
echo ""

# Option 1: Use existing simulator
echo "📡 Option 1: Starting telematics simulator..."
echo "   This will generate realistic driving data"
echo ""

docker exec -d simulator sh -c "
NUM_DRIVERS=1 \
SIMULATION_DAYS=1 \
CONTINUOUS_MODE=false \
ENABLE_KAFKA=true \
python3 telematics_simulator.py
" 2>/dev/null

echo "✅ Simulator started"
echo "⏳ Waiting for events to be generated and processed..."
sleep 5

# Check events
echo ""
echo "📊 Checking events..."
EVENT_COUNT=$(docker exec backend python3 -c "
from app.models.database import SessionLocal, TelematicsEvent
db = SessionLocal()
count = db.query(TelematicsEvent).count()
print(count)
" 2>/dev/null || echo "0")

echo "✅ Found $EVENT_COUNT events in database"
echo ""

# Show recent events
echo "📋 Recent Events:"
docker exec backend python3 -c "
from app.models.database import SessionLocal, TelematicsEvent
from datetime import datetime, timedelta
db = SessionLocal()
recent = db.query(TelematicsEvent).filter(
    TelematicsEvent.timestamp >= datetime.utcnow() - timedelta(minutes=5)
).order_by(TelematicsEvent.timestamp.desc()).limit(5).all()
for e in recent:
    print(f'  • {e.driver_id} - {e.event_type} - {e.speed}mph - {e.timestamp.strftime(\"%H:%M:%S\")}')
" 2>/dev/null || echo "  (No recent events)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Data Generation Complete!"
echo ""
echo "📱 NEXT STEPS:"
echo ""
echo "1. Open Live Dashboard:"
echo "   👉 http://localhost:3000/live"
echo ""
echo "2. Login:"
echo "   Username: driver0002 (or any user)"
echo "   Password: (check driver_credentials.csv)"
echo ""
echo "3. Watch Real-Time Updates:"
echo "   • Safety Score"
echo "   • Risk Score"
echo "   • Behavior Metrics"
echo "   • Safety Alerts"
echo "   • Dynamic Pricing"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 To generate more data continuously:"
echo "   docker exec -d simulator sh -c 'CONTINUOUS_MODE=true NUM_DRIVERS=1 python3 telematics_simulator.py'"
echo ""

