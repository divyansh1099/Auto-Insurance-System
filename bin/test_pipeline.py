#!/usr/bin/env python3
"""
Pipeline Test Script

Tests the complete data flow:
Kafka → Consumer → Redis Pub/Sub → WebSocket → Frontend

Usage:
    python bin/test_pipeline.py [--driver-id DRV-0001] [--events 10] [--verbose]
"""

import argparse
import json
import time
import uuid
import asyncio
import websockets
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from confluent_kafka import Producer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("⚠️  Kafka not available. Install with: pip install confluent-kafka")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not available. Install with: pip install redis")

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("⚠️  WebSockets not available. Install with: pip install websockets")

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️  PostgreSQL client not available. Install with: pip install psycopg2-binary")


class PipelineTester:
    """Test the complete telematics pipeline."""
    
    def __init__(self, driver_id: str = "DRV-0001", verbose: bool = False):
        self.driver_id = driver_id
        self.verbose = verbose
        self.kafka_producer = None
        self.redis_client = None
        self.websocket = None
        self.received_messages = []
        self.test_results = {
            'kafka': {'status': 'not_tested', 'messages_sent': 0},
            'consumer': {'status': 'not_tested', 'events_processed': 0},
            'redis_pubsub': {'status': 'not_tested', 'messages_received': 0},
            'websocket': {'status': 'not_tested', 'messages_received': 0},
            'frontend': {'status': 'not_tested'}
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "TEST": "🧪"
        }.get(level, "ℹ️ ")
        
        if self.verbose or level in ["ERROR", "SUCCESS", "TEST"]:
            print(f"[{timestamp}] {prefix} {message}")
    
    def setup_kafka(self):
        """Initialize Kafka producer."""
        if not KAFKA_AVAILABLE:
            self.log("Kafka not available - skipping Kafka tests", "WARNING")
            return False
        
        try:
            self.kafka_producer = Producer({
                'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                'client.id': 'pipeline-tester',
                'acks': '1'
            })
            self.log("Kafka producer initialized", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to initialize Kafka: {e}", "ERROR")
            return False
    
    def setup_redis(self):
        """Initialize Redis client."""
        if not REDIS_AVAILABLE:
            self.log("Redis not available - skipping Redis tests", "WARNING")
            return False
        
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )
            self.redis_client.ping()
            self.log("Redis client initialized", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to initialize Redis: {e}", "ERROR")
            return False
    
    def generate_test_event(self, event_num: int) -> Dict:
        """Generate a test telematics event."""
        base_lat = 37.7749
        base_lon = -122.4194
        
        # Simulate movement
        lat_offset = (event_num * 0.001) % 0.1
        lon_offset = (event_num * 0.001) % 0.1
        
        return {
            "event_id": f"EVT-TEST-{uuid.uuid4().hex[:12].upper()}",
            "device_id": f"DEV-TEST-{self.driver_id}",
            "driver_id": self.driver_id,
            "timestamp": int(datetime.utcnow().timestamp() * 1000),  # milliseconds
            "latitude": round(base_lat + lat_offset, 6),
            "longitude": round(base_lon + lon_offset, 6),
            "speed": round(30 + (event_num % 20), 2),  # 30-50 mph
            "acceleration": round(0.1 + (event_num % 3) * 0.1, 3),
            "braking_force": None if event_num % 5 != 0 else round(0.3 + (event_num % 2) * 0.2, 3),
            "heading": round((event_num * 10) % 360, 2),
            "altitude": round(50 + (event_num % 10), 2),
            "gps_accuracy": 5.0,
            "event_type": "normal" if event_num % 10 != 0 else "harsh_brake"
        }
    
    def publish_to_kafka(self, event: Dict) -> bool:
        """Publish event to Kafka."""
        if not self.kafka_producer:
            return False
        
        try:
            # Serialize event
            event_json = json.dumps(event, default=str)
            
            # Publish
            self.kafka_producer.produce(
                'telematics-events',
                key=self.driver_id.encode('utf-8'),
                value=event_json.encode('utf-8')
            )
            
            # Flush to ensure delivery
            self.kafka_producer.poll(0)
            self.kafka_producer.flush(timeout=5)
            
            self.test_results['kafka']['messages_sent'] += 1
            return True
        except Exception as e:
            self.log(f"Failed to publish to Kafka: {e}", "ERROR")
            return False
    
    def check_redis_pubsub(self, timeout: int = 10) -> int:
        """Check Redis pub/sub channels for messages."""
        if not self.redis_client:
            return 0
        
        messages_received = 0
        start_time = time.time()
        
        try:
            # Subscribe to channels
            pubsub = self.redis_client.pubsub()
            channels = [
                f"realtime:analysis:{self.driver_id}",
                f"realtime:pricing:{self.driver_id}",
                f"realtime:events:{self.driver_id}"
            ]
            
            for channel in channels:
                pubsub.subscribe(channel)
            
            self.log(f"Subscribed to Redis channels: {', '.join(channels)}", "TEST")
            
            # Listen for messages
            while time.time() - start_time < timeout:
                message = pubsub.get_message(timeout=1.0, ignore_subscribe_messages=True)
                if message:
                    messages_received += 1
                    channel = message['channel']
                    data = json.loads(message['data'])
                    self.log(f"Received Redis message from {channel}: {data.get('type', 'unknown')}", "TEST")
                    
                    if self.verbose:
                        print(f"  Data: {json.dumps(data, indent=2, default=str)}")
            
            pubsub.close()
            self.test_results['redis_pubsub']['messages_received'] = messages_received
            
        except Exception as e:
            self.log(f"Redis pub/sub check failed: {e}", "ERROR")
        
        return messages_received
    
    async def test_websocket(self, timeout: int = 30):
        """Test WebSocket connection and receive messages."""
        if not WEBSOCKETS_AVAILABLE:
            self.log("WebSockets library not available - skipping WebSocket test", "WARNING")
            return
        
        ws_url = f"ws://localhost:8000/api/v1/realtime/ws/{self.driver_id}"
        messages_received = 0
        
        try:
            self.log(f"Connecting to WebSocket: {ws_url}", "TEST")
            
            async with websockets.connect(ws_url) as websocket:
                self.log("WebSocket connected", "SUCCESS")
                
                # Wait for initial connection message
                try:
                    initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    msg_data = json.loads(initial_msg)
                    if msg_data.get('type') == 'connected':
                        self.log("Received connection confirmation", "SUCCESS")
                        messages_received += 1
                except asyncio.TimeoutError:
                    self.log("No initial connection message received", "WARNING")
                
                # Listen for updates
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        msg_data = json.loads(message)
                        messages_received += 1
                        
                        msg_type = msg_data.get('type', 'unknown')
                        self.log(f"Received WebSocket message: {msg_type}", "TEST")
                        
                        self.received_messages.append(msg_data)
                        
                        if self.verbose:
                            print(f"  Data: {json.dumps(msg_data, indent=2, default=str)}")
                            
                    except asyncio.TimeoutError:
                        # Continue listening
                        continue
                    except Exception as e:
                        self.log(f"Error receiving WebSocket message: {e}", "ERROR")
                        break
                
                self.test_results['websocket']['messages_received'] = messages_received
                self.log(f"WebSocket test completed. Received {messages_received} messages", "SUCCESS")
                
        except Exception as e:
            self.log(f"WebSocket connection failed: {e}", "ERROR")
            self.test_results['websocket']['status'] = 'failed'
    
    def check_database(self) -> bool:
        """Check if events were stored in database."""
        if not POSTGRES_AVAILABLE:
            self.log("PostgreSQL client not available - skipping database check", "WARNING")
            return False
        
        try:
            
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                database=os.getenv('POSTGRES_DB', 'telematics_db'),
                user=os.getenv('POSTGRES_USER', 'insurance_user'),
                password=os.getenv('POSTGRES_PASSWORD', 'insurance_pass')
            )
            
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM telematics_events WHERE driver_id = %s AND event_id LIKE 'EVT-TEST-%'",
                (self.driver_id,)
            )
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.test_results['consumer']['events_processed'] = count
            self.log(f"Found {count} test events in database", "SUCCESS")
            return count > 0
            
        except Exception as e:
            self.log(f"Database check failed: {e}", "ERROR")
            return False
    
    def run_test(self, num_events: int = 10):
        """Run complete pipeline test."""
        self.log("=" * 60, "TEST")
        self.log("Starting Pipeline Test", "TEST")
        self.log(f"Driver ID: {self.driver_id}", "TEST")
        self.log(f"Events to send: {num_events}", "TEST")
        self.log("=" * 60, "TEST")
        
        # Setup
        kafka_ok = self.setup_kafka()
        redis_ok = self.setup_redis()
        
        if not kafka_ok:
            self.log("Cannot proceed without Kafka", "ERROR")
            return
        
        # Step 1: Publish events to Kafka
        self.log("\n📤 Step 1: Publishing events to Kafka...", "TEST")
        events_sent = 0
        for i in range(num_events):
            event = self.generate_test_event(i)
            if self.publish_to_kafka(event):
                events_sent += 1
                if self.verbose:
                    self.log(f"Published event {i+1}/{num_events}: {event['event_id']}", "INFO")
            time.sleep(0.5)  # Small delay between events
        
        self.test_results['kafka']['status'] = 'success' if events_sent > 0 else 'failed'
        self.log(f"Published {events_sent}/{num_events} events to Kafka", "SUCCESS" if events_sent > 0 else "ERROR")
        
        # Wait for consumer to process
        self.log("\n⏳ Waiting for Kafka consumer to process events (10 seconds)...", "TEST")
        time.sleep(10)
        
        # Step 2: Check database
        self.log("\n📊 Step 2: Checking database for processed events...", "TEST")
        db_ok = self.check_database()
        self.test_results['consumer']['status'] = 'success' if db_ok else 'failed'
        
        # Step 3: Check Redis pub/sub
        if redis_ok:
            self.log("\n📡 Step 3: Checking Redis pub/sub channels...", "TEST")
            redis_messages = self.check_redis_pubsub(timeout=15)
            self.test_results['redis_pubsub']['status'] = 'success' if redis_messages > 0 else 'failed'
            self.log(f"Received {redis_messages} messages from Redis pub/sub", 
                    "SUCCESS" if redis_messages > 0 else "WARNING")
        
        # Step 4: Test WebSocket (send more events while listening)
        self.log("\n🔌 Step 4: Testing WebSocket connection...", "TEST")
        self.log("Sending additional events while WebSocket is connected...", "TEST")
        
        # Start WebSocket test in background
        async def websocket_test_with_events():
            # Send events while WebSocket is connected
            await asyncio.sleep(2)  # Wait for connection
            
            for i in range(5):
                event = self.generate_test_event(num_events + i)
                self.publish_to_kafka(event)
                await asyncio.sleep(2)  # Wait between events
            
            # Continue listening
            await asyncio.sleep(10)
        
        async def run_websocket_test():
            await asyncio.gather(
                self.test_websocket(timeout=30),
                websocket_test_with_events()
            )
        
        try:
            asyncio.run(run_websocket_test())
            self.test_results['websocket']['status'] = 'success' if self.test_results['websocket']['messages_received'] > 0 else 'failed'
        except Exception as e:
            self.log(f"WebSocket test failed: {e}", "ERROR")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        self.log("\n" + "=" * 60, "TEST")
        self.log("Test Results Summary", "TEST")
        self.log("=" * 60, "TEST")
        
        results = self.test_results
        
        # Kafka
        status_icon = "✅" if results['kafka']['status'] == 'success' else "❌"
        print(f"{status_icon} Kafka Producer:")
        print(f"   Status: {results['kafka']['status']}")
        print(f"   Messages Sent: {results['kafka']['messages_sent']}")
        
        # Consumer
        status_icon = "✅" if results['consumer']['status'] == 'success' else "❌"
        print(f"\n{status_icon} Kafka Consumer:")
        print(f"   Status: {results['consumer']['status']}")
        print(f"   Events Processed: {results['consumer']['events_processed']}")
        
        # Redis Pub/Sub
        status_icon = "✅" if results['redis_pubsub']['status'] == 'success' else "⚠️ "
        print(f"\n{status_icon} Redis Pub/Sub:")
        print(f"   Status: {results['redis_pubsub']['status']}")
        print(f"   Messages Received: {results['redis_pubsub']['messages_received']}")
        
        # WebSocket
        status_icon = "✅" if results['websocket']['status'] == 'success' else "❌"
        print(f"\n{status_icon} WebSocket:")
        print(f"   Status: {results['websocket']['status']}")
        print(f"   Messages Received: {results['websocket']['messages_received']}")
        
        if self.received_messages:
            print(f"\n📨 WebSocket Message Types Received:")
            msg_types = {}
            for msg in self.received_messages:
                msg_type = msg.get('type', 'unknown')
                msg_types[msg_type] = msg_types.get(msg_type, 0) + 1
            
            for msg_type, count in msg_types.items():
                print(f"   - {msg_type}: {count}")
        
        # Overall status
        all_passed = all([
            results['kafka']['status'] == 'success',
            results['consumer']['status'] == 'success',
            results['websocket']['status'] == 'success'
        ])
        
        self.log("\n" + "=" * 60, "TEST")
        if all_passed:
            self.log("✅ Pipeline Test PASSED", "SUCCESS")
        else:
            self.log("❌ Pipeline Test FAILED - Some components did not work", "ERROR")
        self.log("=" * 60, "TEST")


def main():
    parser = argparse.ArgumentParser(description='Test the telematics pipeline')
    parser.add_argument('--driver-id', default='DRV-0001', help='Driver ID to test with')
    parser.add_argument('--events', type=int, default=10, help='Number of events to send')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    tester = PipelineTester(driver_id=args.driver_id, verbose=args.verbose)
    tester.run_test(num_events=args.events)


if __name__ == '__main__':
    main()

