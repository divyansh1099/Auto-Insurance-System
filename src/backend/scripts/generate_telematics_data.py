#!/usr/bin/env python3
"""
Simple Telematics Data Generator

Generates realistic telematics events and sends them to the API.
Can be used for testing without physical devices.

Usage:
    python generate_telematics_data.py --driver-id DRV-0001 --events 100
    python generate_telematics_data.py --driver-id DRV-0001 --duration 60 --interval 10
"""

import argparse
import requests
import time
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

# Default API URL
API_BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{API_BASE_URL}/api/v1/telematics/events"


def generate_event(driver_id: str, device_id: str, base_lat: float, base_lon: float, 
                  speed: float = None, event_type: str = None) -> Dict:
    """Generate a single telematics event."""
    # Generate realistic speed if not provided
    if speed is None:
        speed = random.uniform(0, 70)
    
    # Generate event type if not provided
    if event_type is None:
        rand = random.random()
        if rand < 0.02:  # 2% harsh braking
            event_type = "harsh_brake"
            speed = max(0, speed - random.uniform(10, 30))
        elif rand < 0.05:  # 3% rapid acceleration
            event_type = "rapid_accel"
            speed = min(80, speed + random.uniform(10, 25))
        elif rand < 0.10:  # 5% speeding
            event_type = "speeding"
            speed = random.uniform(75, 90)
        elif rand < 0.12:  # 2% harsh corner
            event_type = "harsh_corner"
        elif rand < 0.15:  # 3% phone usage
            event_type = "phone_usage"
        else:
            event_type = "normal"
    
    # Calculate acceleration based on speed change
    acceleration = random.uniform(-0.5, 0.5)
    if event_type == "harsh_brake":
        acceleration = random.uniform(-1.5, -0.5)
    elif event_type == "rapid_accel":
        acceleration = random.uniform(0.5, 1.5)
    
    # Generate GPS coordinates (small random movement)
    lat_offset = random.uniform(-0.01, 0.01)  # ~0.6 miles
    lon_offset = random.uniform(-0.01, 0.01)
    
    event = {
        "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
        "device_id": device_id,
        "driver_id": driver_id,
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
        "latitude": round(base_lat + lat_offset, 6),
        "longitude": round(base_lon + lon_offset, 6),
        "speed": round(speed, 2),
        "acceleration": round(acceleration, 3),
        "braking_force": round(abs(acceleration), 3) if acceleration < -0.3 else None,
        "heading": round(random.uniform(0, 360), 2),
        "altitude": round(random.uniform(0, 500), 2),
        "gps_accuracy": round(random.uniform(5, 15), 2),
        "event_type": event_type
    }
    
    return event


def send_event(event: Dict, token: str = None) -> bool:
    """Send a single event to the API."""
    headers = {
        "Content-Type": "application/json"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.post(API_ENDPOINT, json=event, headers=headers, timeout=5)
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"Error sending event: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error sending event: {e}")
        return False


def send_batch(events: List[Dict], token: str = None) -> int:
    """Send a batch of events to the API."""
    headers = {
        "Content-Type": "application/json"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    batch_endpoint = f"{API_BASE_URL}/api/v1/telematics/events/batch"
    
    try:
        response = requests.post(
            batch_endpoint,
            json={"events": events},
            headers=headers,
            timeout=30
        )
        if response.status_code in [200, 201]:
            result = response.json()
            return result.get("message", "Success")
        else:
            print(f"Error sending batch: {response.status_code} - {response.text}")
            return 0
    except Exception as e:
        print(f"Error sending batch: {e}")
        return 0


def generate_trip_events(driver_id: str, device_id: str, base_lat: float, base_lon: float,
                        duration_minutes: int = 20, events_per_minute: int = 6) -> List[Dict]:
    """Generate events for a complete trip."""
    events = []
    num_events = duration_minutes * events_per_minute
    
    # Trip starts at 0 speed, accelerates, cruises, then decelerates
    current_speed = 0
    current_lat = base_lat
    current_lon = base_lon
    
    for i in range(num_events):
        progress = i / num_events
        
        # Speed profile: accelerate (0-20%), cruise (20-80%), decelerate (80-100%)
        if progress < 0.2:
            # Accelerating
            target_speed = min(50, current_speed + random.uniform(2, 8))
        elif progress < 0.8:
            # Cruising
            target_speed = random.uniform(40, 60)
        else:
            # Decelerating
            target_speed = max(0, current_speed - random.uniform(3, 10))
        
        current_speed = target_speed
        
        # Move location based on speed
        speed_mps = current_speed * 0.447  # Convert mph to m/s
        time_interval = 10  # seconds between events
        distance_m = speed_mps * time_interval
        
        # Simple movement (1 degree latitude ≈ 111 km)
        lat_offset = (distance_m / 111000) * random.uniform(0.8, 1.2)
        lon_offset = (distance_m / 111000) * random.uniform(0.8, 1.2) / abs(random.cos(base_lat * 3.14159 / 180))
        
        current_lat += lat_offset * random.choice([-1, 1])
        current_lon += lon_offset * random.choice([-1, 1])
        
        # Generate event
        event = generate_event(
            driver_id=driver_id,
            device_id=device_id,
            base_lat=current_lat,
            base_lon=current_lon,
            speed=current_speed
        )
        
        events.append(event)
    
    return events


def main():
    parser = argparse.ArgumentParser(description="Generate telematics data for testing")
    parser.add_argument("--driver-id", required=True, help="Driver ID (e.g., DRV-0001)")
    parser.add_argument("--device-id", default=None, help="Device ID (auto-generated if not provided)")
    parser.add_argument("--api-url", default=API_BASE_URL, help="API base URL")
    parser.add_argument("--token", default=None, help="Auth token (optional)")
    
    # Generation modes
    parser.add_argument("--events", type=int, help="Number of events to generate")
    parser.add_argument("--duration", type=int, help="Duration in seconds to generate events")
    parser.add_argument("--interval", type=int, default=10, help="Interval between events (seconds)")
    parser.add_argument("--trip", action="store_true", help="Generate a complete trip")
    parser.add_argument("--trip-duration", type=int, default=20, help="Trip duration in minutes")
    
    # Location
    parser.add_argument("--lat", type=float, default=37.7749, help="Base latitude (default: San Francisco)")
    parser.add_argument("--lon", type=float, default=-122.4194, help="Base longitude (default: San Francisco)")
    
    # Batch options
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for sending events")
    
    args = parser.parse_args()
    
    # Update API endpoint if custom URL provided
    global API_ENDPOINT
    API_ENDPOINT = f"{args.api_url}/api/v1/telematics/events"
    
    # Generate device ID if not provided
    device_id = args.device_id or f"DEV-{uuid.uuid4().hex[:8].upper()}"
    
    print(f"Generating telematics data for driver: {args.driver_id}")
    print(f"Device ID: {device_id}")
    print(f"API URL: {args.api_url}")
    print()
    
    if args.trip:
        # Generate a complete trip
        print(f"Generating trip events ({args.trip_duration} minutes)...")
        events = generate_trip_events(
            driver_id=args.driver_id,
            device_id=device_id,
            base_lat=args.lat,
            base_lon=args.lon,
            duration_minutes=args.trip_duration
        )
        
        print(f"Generated {len(events)} events")
        
        # Send in batches
        batch_size = args.batch_size
        sent = 0
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            result = send_batch(batch, args.token)
            sent += len(batch)
            print(f"Sent {sent}/{len(events)} events...")
            time.sleep(0.1)  # Small delay between batches
        
        print(f"\n✓ Successfully sent {len(events)} trip events")
        
    elif args.duration:
        # Generate events over time
        print(f"Generating events for {args.duration} seconds (interval: {args.interval}s)...")
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < args.duration:
            event = generate_event(
                driver_id=args.driver_id,
                device_id=device_id,
                base_lat=args.lat,
                base_lon=args.lon
            )
            
            if send_event(event, args.token):
                count += 1
                if count % 10 == 0:
                    print(f"Sent {count} events...")
            
            time.sleep(args.interval)
        
        print(f"\n✓ Successfully sent {count} events")
        
    elif args.events:
        # Generate fixed number of events
        print(f"Generating {args.events} events...")
        events = []
        
        for i in range(args.events):
            event = generate_event(
                driver_id=args.driver_id,
                device_id=device_id,
                base_lat=args.lat,
                base_lon=args.lon
            )
            events.append(event)
        
        # Send in batches
        batch_size = args.batch_size
        sent = 0
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            result = send_batch(batch, args.token)
            sent += len(batch)
            print(f"Sent {sent}/{len(events)} events...")
            time.sleep(0.1)
        
        print(f"\n✓ Successfully sent {len(events)} events")
        
    else:
        parser.print_help()
        print("\nError: Must specify --events, --duration, or --trip")


if __name__ == "__main__":
    main()

