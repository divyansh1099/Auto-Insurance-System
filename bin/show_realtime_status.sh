#!/bin/bash

# Show Real-Time System Status

echo "🚀 Real-Time Telematics System Status"
echo "======================================"
echo ""

# Check services
echo "📋 Services:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "backend|kafka|redis|postgres" || echo "  (Some services may not be running)"
echo ""

# Check events
echo "📊 Events in Database:"
TOTAL=$(docker exec backend python3 -c "
from app.models.database import SessionLocal, TelematicsEvent
print(SessionLocal().query(TelematicsEvent).count())
" 2>/dev/null || echo "0")

RECENT=$(docker exec backend python3 -c "
from app.models.database import SessionLocal, TelematicsEvent
from datetime import datetime, timedelta
db = SessionLocal()
count = db.query(TelematicsEvent).filter(
    TelematicsEvent.timestamp >= datetime.utcnow() - timedelta(minutes=5)
).count()
print(count)
" 2>/dev/null || echo "0")

echo "  Total Events: $TOTAL"
echo "  Events (last 5 min): $RECENT"
echo ""

# Check Kafka consumer
echo "📡 Kafka Consumer:"
if docker logs backend 2>&1 | tail -50 | grep -q "kafka_consumer_started\|batch_processed"; then
    echo "  ✅ Consumer is processing events"
    docker logs backend 2>&1 | grep "batch_processed" | tail -1 | sed 's/^/  /'
else
    echo "  ⚠️  Consumer may not be active"
fi
echo ""

# Check real-time analysis
echo "🤖 Real-Time ML Analysis:"
DRIVER_ID=$(docker exec backend python3 -c "
from app.models.database import SessionLocal, Driver
driver = SessionLocal().query(Driver).first()
print(driver.driver_id if driver else 'DRV-0001')
" 2>/dev/null || echo "DRV-0001")

echo "  Testing with driver: $DRIVER_ID"

ANALYSIS=$(docker exec backend python3 -c "
from app.services.realtime_ml_inference import get_analyzer
from app.models.database import SessionLocal, TelematicsEvent
from datetime import datetime, timedelta

db = SessionLocal()
analyzer = get_analyzer()

# Get recent events
events = db.query(TelematicsEvent).filter(
    TelematicsEvent.driver_id == '$DRIVER_ID',
    TelematicsEvent.timestamp >= datetime.utcnow() - timedelta(hours=1)
).order_by(TelematicsEvent.timestamp.desc()).limit(50).all()

if events:
    for event in reversed(events[-20:]):
        event_dict = {
            'driver_id': event.driver_id,
            'device_id': event.device_id,
            'speed': event.speed or 0,
            'acceleration': event.acceleration or 0,
            'event_type': event.event_type,
            'timestamp': event.timestamp.isoformat(),
            'latitude': event.latitude,
            'longitude': event.longitude
        }
        analyzer.add_event(event_dict)
    
    current = analyzer.get_current_analysis('$DRIVER_ID')
    if current:
        import json
        print(json.dumps({
            'safety_score': round(current.get('safety_score', 0), 1),
            'risk_score': round(current.get('risk_score', 0), 1),
            'alerts': len(current.get('safety_alerts', []))
        }))
" 2>/dev/null)

if [ ! -z "$ANALYSIS" ]; then
    echo "$ANALYSIS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"  ✅ Safety Score: {data.get('safety_score', 0)}/100\")
print(f\"  ✅ Risk Score: {data.get('risk_score', 0)}/100\")
print(f\"  ✅ Safety Alerts: {data.get('alerts', 0)}\")
" 2>/dev/null || echo "  ✅ Analysis available"
else
    echo "  ⚠️  Analysis not available (may need more events)"
fi
echo ""

# Check WebSocket
echo "🔌 WebSocket:"
echo "  Endpoint: ws://localhost:8000/api/v1/realtime/ws/{driver_id}"
echo "  Status: Check Live Dashboard connection"
echo ""

# Instructions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 To See It In Action:"
echo ""
echo "1. Open Live Dashboard:"
echo "   👉 http://localhost:3000/live"
echo ""
echo "2. Login with any user (e.g., driver0002)"
echo ""
echo "3. Generate more data:"
echo "   docker exec -d simulator sh -c 'CONTINUOUS_MODE=true NUM_DRIVERS=1 python3 telematics_simulator.py'"
echo ""
echo "4. Watch real-time updates appear!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

