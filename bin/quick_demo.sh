#!/bin/bash

# Quick Real-Time Demo
# Shows the system working step by step

echo "🚀 Real-Time Telematics System - Live Demo"
echo "=========================================="
echo ""

DRIVER_ID="DRV-0001"
API_URL="http://localhost:8000"

# Step 1: Login and get token
echo "📝 Step 1: Authenticating..."
TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "⚠️  Could not login. Make sure backend is running and demo user exists."
    echo "   Try: docker exec backend python /app/../scripts/populate_sample_data.py"
    exit 1
fi

echo "✅ Authenticated"
echo ""

# Step 2: Generate some initial data
echo "📡 Step 2: Generating telematics events..."
python3 src/backend/scripts/generate_telematics_data.py \
  --driver-id "$DRIVER_ID" \
  --events 30 \
  --lat 37.7749 \
  --lon -122.4194 2>&1 | grep -E "(Generated|Sent|Successfully)" || true

echo "✅ Events generated"
echo ""

# Step 3: Wait a moment for processing
echo "⏳ Step 3: Waiting for processing (3 seconds)..."
sleep 3

# Step 4: Get real-time analysis
echo "📊 Step 4: Getting real-time analysis..."
ANALYSIS=$(curl -s "$API_URL/api/v1/realtime/analysis/$DRIVER_ID" \
  -H "Authorization: Bearer $TOKEN")

if [ ! -z "$ANALYSIS" ] && [ "$ANALYSIS" != "null" ]; then
    echo "✅ Analysis received!"
    echo ""
    echo "$ANALYSIS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
analysis = data.get('analysis', {})
pricing = data.get('pricing', {})

print('🛡️  SAFETY SCORE:', round(analysis.get('safety_score', 0), 1))
print('⚠️  RISK SCORE:', round(analysis.get('risk_score', 0), 1))
print('')
print('📊 BEHAVIOR METRICS:')
metrics = analysis.get('behavior_metrics', {})
print('   Current Speed:', round(metrics.get('current_speed', 0), 1), 'mph')
print('   Avg Speed:', round(metrics.get('avg_speed', 0), 1), 'mph')
print('   Max Speed:', round(metrics.get('max_speed', 0), 1), 'mph')
print('   Harsh Braking:', metrics.get('harsh_braking_count', 0))
print('   Speeding:', metrics.get('speeding_count', 0))
print('')
alerts = analysis.get('safety_alerts', [])
if alerts:
    print('🚨 SAFETY ALERTS:', len(alerts))
    for alert in alerts:
        print('   -', alert.get('type', 'unknown'), ':', alert.get('message', ''))
else:
    print('✅ No safety alerts')
print('')
if pricing:
    print('💰 PRICING:')
    print('   Monthly Premium: $' + str(round(pricing.get('adjusted_premium', 0), 2)))
    print('   Discount:', str(round(pricing.get('discount_percent', 0), 1)) + '%')
" 2>/dev/null || echo "$ANALYSIS"
else
    echo "⚠️  Analysis not available yet (may need more events)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Demo Complete!"
echo ""
echo "📱 Next: Open Live Dashboard"
echo "   URL: http://localhost:3000/live"
echo "   Login: demo / demo123"
echo ""
echo "🔄 To see continuous updates, run:"
echo "   python3 src/backend/scripts/generate_telematics_data.py \\"
echo "     --driver-id $DRIVER_ID \\"
echo "     --duration 60 \\"
echo "     --interval 10"
echo ""

