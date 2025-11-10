#!/bin/bash
# Quick Pipeline Test Script

echo "🧪 Testing Telematics Pipeline"
echo "================================"
echo ""

# Check if services are running
echo "1. Checking services..."
docker compose ps | grep -E "(backend|kafka|redis|postgres)" | grep -q "Up" && echo "✅ Services are running" || echo "❌ Services not running - start with: docker compose up -d"

echo ""
echo "2. Testing Kafka Producer..."
python3 bin/test_pipeline.py --driver-id DRV-0001 --events 5 --verbose

echo ""
echo "3. Checking backend logs for processing..."
docker compose logs --tail=20 backend | grep -E "(event_processed|realtime_updates_published|message_forwarded)" || echo "No recent processing logs found"

echo ""
echo "4. Testing WebSocket connection..."
echo "   Open http://localhost:3000/live in browser to see real-time updates"
echo "   Or use: python3 bin/test_pipeline.py --driver-id DRV-0001 --events 10"

echo ""
echo "✅ Pipeline test complete!"
echo ""
echo "To test manually:"
echo "  1. Open http://localhost:3000/live"
echo "  2. Click 'Start Live Drive'"
echo "  3. Watch for real-time updates"

