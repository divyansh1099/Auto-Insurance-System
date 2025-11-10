#!/bin/bash

# Watch Real-Time System in Action
# Generates data and shows updates

DRIVER_ID=${1:-DRV-0001}

echo "🚀 Real-Time Telematics System - Live Watch"
echo "============================================"
echo ""
echo "Driver: $DRIVER_ID"
echo "Live Dashboard: http://localhost:3000/live"
echo ""
echo "Generating events every 10 seconds..."
echo "Open the Live Dashboard to see updates!"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Generate initial batch
python3 src/backend/scripts/generate_telematics_data.py \
  --driver-id "$DRIVER_ID" \
  --events 20 \
  --lat 37.7749 \
  --lon -122.4194 > /dev/null 2>&1

echo "✅ Initial events generated"
sleep 2

# Continuous generation
while true; do
    echo "📡 Generating events... $(date +%H:%M:%S)"
    
    python3 src/backend/scripts/generate_telematics_data.py \
      --driver-id "$DRIVER_ID" \
      --events 10 \
      --lat 37.7749 \
      --lon -122.4194 > /dev/null 2>&1
    
    # Show event count
    COUNT=$(docker exec backend python3 -c "
from app.models.database import SessionLocal, TelematicsEvent
db = SessionLocal()
print(db.query(TelematicsEvent).filter(TelematicsEvent.driver_id == '$DRIVER_ID').count())
" 2>/dev/null || echo "0")
    
    echo "   ✓ Events in DB: $COUNT"
    echo ""
    
    sleep 10
done

