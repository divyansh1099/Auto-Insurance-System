"""
Realistic Telematics Data Generator

Uses physics-based models to generate accurate telematics data:
- Realistic vehicle acceleration/deceleration curves
- Proper GPS movement based on heading and speed
- Realistic speed profiles (urban, highway, city)
- Accurate event detection based on physics
"""

import math
import random
import uuid
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger()


class RoadType(Enum):
    """Road type affects speed limits and behavior."""
    RESIDENTIAL = "residential"  # 25-35 mph
    CITY_STREET = "city_street"  # 35-45 mph
    ARTERIAL = "arterial"  # 45-55 mph
    HIGHWAY = "highway"  # 55-75 mph
    FREEWAY = "freeway"  # 65-80 mph


class VehicleState:
    """Tracks vehicle state for realistic physics simulation."""
    
    def __init__(self, start_lat: float, start_lon: float, start_heading: float = None):
        self.latitude = start_lat
        self.longitude = start_lon
        self.heading = start_heading or random.uniform(0, 360)  # degrees
        self.speed = 0.0  # mph
        self.acceleration = 0.0  # m/s²
        self.road_type = RoadType.CITY_STREET
        self.speed_limit = 45.0  # mph
        self.target_speed = 0.0  # mph
        self.time_at_current_speed = 0.0  # seconds
        
    def update_road_type(self):
        """Update road type based on current speed (simplified)."""
        if self.speed < 30:
            self.road_type = RoadType.RESIDENTIAL
            self.speed_limit = 30.0
        elif self.speed < 50:
            self.road_type = RoadType.CITY_STREET
            self.speed_limit = 45.0
        elif self.speed < 65:
            self.road_type = RoadType.ARTERIAL
            self.speed_limit = 55.0
        else:
            self.road_type = RoadType.HIGHWAY
            self.speed_limit = 70.0


class RealisticDataGenerator:
    """Generates realistic telematics data using physics-based models."""
    
    def __init__(self, driver_id: str, device_id: str, start_lat: float = 37.7749, start_lon: float = -122.4194):
        self.driver_id = driver_id
        self.device_id = device_id
        self.state = VehicleState(start_lat, start_lon)
        self.previous_speed = 0.0
        self.previous_acceleration = 0.0
        self.event_history = []  # Last 10 events for pattern detection
        
    def generate_event(self, time_interval: float = 10.0) -> Dict:
        """
        Generate a realistic telematics event.
        
        Args:
            time_interval: Time since last event in seconds
            
        Returns:
            Telematics event dictionary
        """
        # Update vehicle state based on physics
        self._update_physics(time_interval)
        
        # Update GPS position based on speed and heading
        self._update_position(time_interval)
        
        # Detect events based on physics
        event_type = self._detect_event_type()
        
        # Calculate braking force
        braking_force = None
        if self.state.acceleration < -0.3:
            braking_force = round(abs(self.state.acceleration), 3)
        
        # Create event
        event = {
            "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
            "device_id": self.device_id,
            "driver_id": self.driver_id,
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "latitude": round(self.state.latitude, 6),
            "longitude": round(self.state.longitude, 6),
            "speed": round(self.state.speed, 2),
            "acceleration": round(self.state.acceleration, 3),
            "braking_force": braking_force,
            "heading": round(self.state.heading, 2),
            "altitude": round(random.uniform(0, 500), 2),
            "gps_accuracy": round(random.uniform(5, 15), 2),
            "event_type": event_type
        }
        
        # Update history
        self.event_history.append({
            'speed': self.state.speed,
            'acceleration': self.state.acceleration,
            'heading': self.state.heading,
            'event_type': event_type
        })
        if len(self.event_history) > 10:
            self.event_history.pop(0)
        
        # Update previous values
        self.previous_speed = self.state.speed
        self.previous_acceleration = self.state.acceleration
        
        return event
    
    def _update_physics(self, time_interval: float):
        """Update vehicle physics (speed, acceleration) based on realistic models."""
        # Determine target speed based on road type and driving pattern
        if self.state.speed == 0:
            # Starting from stop - accelerate
            self.state.target_speed = self.state.speed_limit * random.uniform(0.85, 1.0)
            self.state.time_at_current_speed = 0.0
        elif self.state.time_at_current_speed > 60:  # Been at speed for > 1 minute
            # May change speed (traffic, turns, etc.)
            if random.random() < 0.3:  # 30% chance of speed change
                speed_change = random.uniform(-15, 15)
                self.state.target_speed = max(0, min(80, self.state.speed_limit + speed_change))
                self.state.time_at_current_speed = 0.0
        else:
            self.state.time_at_current_speed += time_interval
        
        # Calculate acceleration needed to reach target speed
        speed_diff = self.state.target_speed - self.state.speed
        
        # Realistic acceleration limits
        if speed_diff > 0:
            # Accelerating
            max_accel = 2.0  # m/s² (realistic car acceleration)
            # Acceleration decreases as speed increases
            speed_factor = max(0.3, 1.0 - (self.state.speed / 80.0))
            desired_accel = min(max_accel * speed_factor, speed_diff * 0.447 / time_interval)
            self.state.acceleration = random.uniform(desired_accel * 0.8, desired_accel * 1.2)
        elif speed_diff < 0:
            # Decelerating
            max_decel = -3.0  # m/s² (realistic braking)
            desired_decel = max(max_decel, speed_diff * 0.447 / time_interval)
            self.state.acceleration = random.uniform(desired_decel * 0.9, desired_decel * 1.1)
        else:
            # Maintaining speed
            self.state.acceleration = random.uniform(-0.1, 0.1)
        
        # Update speed based on acceleration
        speed_change_mps = self.state.acceleration * time_interval
        speed_change_mph = speed_change_mps / 0.447
        self.state.speed = max(0.0, self.state.speed + speed_change_mph)
        
        # Update road type based on speed
        self.state.update_road_type()
        
        # Occasional heading changes (turns, lane changes)
        if random.random() < 0.15:  # 15% chance of heading change
            turn_angle = random.uniform(-45, 45)  # degrees
            self.state.heading = (self.state.heading + turn_angle) % 360
    
    def _update_position(self, time_interval: float):
        """Update GPS position based on speed, heading, and time."""
        # Convert speed from mph to m/s
        speed_mps = self.state.speed * 0.447
        
        # Calculate distance traveled
        distance_m = speed_mps * time_interval
        
        # Add some randomness for GPS accuracy
        distance_m *= random.uniform(0.95, 1.05)
        
        # Convert heading to radians
        heading_rad = math.radians(self.state.heading)
        
        # Calculate lat/lon offset
        # 1 degree latitude ≈ 111,000 meters
        # 1 degree longitude ≈ 111,000 * cos(latitude) meters
        lat_offset = (distance_m / 111000.0) * math.cos(heading_rad)
        lon_offset = (distance_m / 111000.0) * math.sin(heading_rad) / math.cos(math.radians(self.state.latitude))
        
        # Update position
        self.state.latitude += lat_offset
        self.state.longitude += lon_offset
    
    def _detect_event_type(self) -> str:
        """Detect event type based on physics and patterns."""
        accel = self.state.acceleration
        speed = self.state.speed
        
        # Harsh braking: sudden deceleration > 0.5 m/s²
        if accel < -0.5:
            # Check if it's truly harsh (not just normal braking)
            if abs(accel) > 0.8 or (self.previous_acceleration > -0.2 and accel < -0.5):
                return "harsh_brake"
        
        # Rapid acceleration: sudden acceleration > 0.5 m/s²
        if accel > 0.5:
            # Check if it's rapid (not just normal acceleration)
            if accel > 0.8 or (self.previous_acceleration < 0.2 and accel > 0.5):
                return "rapid_accel"
        
        # Speeding: significantly over speed limit
        if speed > self.state.speed_limit + 15:
            return "speeding"
        
        # Harsh cornering: rapid heading change with high speed
        if len(self.event_history) >= 2:
            recent_headings = [e.get('heading', self.state.heading) for e in self.event_history[-3:]]
            if len(recent_headings) >= 2:
                # Calculate heading change (handle wrap-around)
                heading_change = abs(recent_headings[-1] - recent_headings[0])
                if heading_change > 180:
                    heading_change = 360 - heading_change
                if heading_change > 30 and speed > 30:  # Sharp turn at speed
                    return "harsh_corner"
        
        # Phone usage: occasional random event (simulated)
        if random.random() < 0.01:  # 1% chance
            return "phone_usage"
        
        return "normal"
    
    def generate_trip(self, duration_minutes: int = 20, events_per_minute: int = 6) -> list:
        """
        Generate a realistic trip with proper speed profile.
        
        Args:
            duration_minutes: Trip duration
            events_per_minute: Events per minute
            
        Returns:
            List of telematics events
        """
        events = []
        num_events = duration_minutes * events_per_minute
        time_interval = 60.0 / events_per_minute  # seconds between events
        
        # Trip phases: start (0-15%), cruise (15-85%), end (85-100%)
        for i in range(num_events):
            progress = i / num_events
            
            # Speed profile based on trip phase
            if progress < 0.15:
                # Starting phase: accelerate from stop
                if self.state.speed < 5:
                    self.state.target_speed = self.state.speed_limit * random.uniform(0.7, 0.9)
            elif progress < 0.85:
                # Cruising phase: maintain speed with variations
                if abs(self.state.speed - self.state.target_speed) < 5:
                    # Small variations
                    self.state.target_speed = self.state.speed_limit * random.uniform(0.85, 1.1)
            else:
                # Ending phase: decelerate to stop
                self.state.target_speed = max(0, self.state.target_speed * 0.7)
            
            # Generate event
            event = self.generate_event(time_interval)
            events.append(event)
        
        return events


def generate_realistic_event(
    driver_id: str,
    device_id: str,
    base_lat: float = 37.7749,
    base_lon: float = -122.4194,
    previous_state: Optional[VehicleState] = None
) -> Tuple[Dict, VehicleState]:
    """
    Generate a single realistic telematics event.
    
    Returns:
        (event_dict, updated_state)
    """
    if previous_state is None:
        state = VehicleState(base_lat, base_lon)
    else:
        state = previous_state
    
    generator = RealisticDataGenerator(driver_id, device_id, state.latitude, state.longitude)
    generator.state = state
    
    event = generator.generate_event()
    return event, generator.state

