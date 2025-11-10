"""
Real-Time Trip Detection Service

Detects trips from telematics events in near real-time as events arrive.
This service monitors events and automatically creates trip records when trips are detected.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

from app.models.database import TelematicsEvent, Trip, SessionLocal
from sqlalchemy.orm import Session

logger = structlog.get_logger()


class TripState:
    """Represents the state of a potential trip."""
    def __init__(self, driver_id: str, device_id: str, start_event: Dict):
        self.driver_id = driver_id
        self.device_id = device_id
        self.start_event = start_event
        self.events: List[Dict] = [start_event]
        self.last_event_time = self._get_event_time(start_event)
        self.is_active = True

    def _get_event_time(self, event: Dict) -> datetime:
        """Extract timestamp from event."""
        timestamp = event.get('timestamp')
        if isinstance(timestamp, int):
            return datetime.fromtimestamp(timestamp / 1000.0)
        elif isinstance(timestamp, datetime):
            return timestamp
        else:
            return datetime.utcnow()

    def add_event(self, event: Dict):
        """Add an event to this trip."""
        self.events.append(event)
        self.last_event_time = self._get_event_time(event)

    def should_close(self, inactivity_threshold_minutes: int = 10) -> bool:
        """Check if trip should be closed due to inactivity."""
        if not self.events:
            return True
        
        time_since_last_event = (datetime.utcnow() - self.last_event_time).total_seconds() / 60
        return time_since_last_event > inactivity_threshold_minutes

    def to_trip_dict(self) -> Dict:
        """Convert trip state to trip dictionary."""
        if not self.events:
            return None

        sorted_events = sorted(self.events, key=lambda e: self._get_event_time(e))
        start_event = sorted_events[0]
        end_event = sorted_events[-1]

        start_time = self._get_event_time(start_event)
        end_time = self._get_event_time(end_event)

        # Calculate metrics
        duration_seconds = (end_time - start_time).total_seconds()
        duration_minutes = duration_seconds / 60

        speeds = [e.get('speed', 0) for e in sorted_events if e.get('speed') is not None]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        distance_miles = (avg_speed * duration_seconds) / 3600 if avg_speed > 0 else 0

        # Count event types
        harsh_braking_count = sum(1 for e in self.events if e.get('event_type') == 'harsh_brake')
        rapid_accel_count = sum(1 for e in self.events if e.get('event_type') == 'rapid_accel')
        speeding_count = sum(1 for e in self.events if e.get('event_type') == 'speeding')
        harsh_corner_count = sum(1 for e in self.events if e.get('event_type') == 'harsh_corner')
        phone_usage_detected = any(e.get('event_type') == 'phone_usage' for e in self.events)

        # Determine trip type
        hour = start_time.hour
        weekday = start_time.weekday()
        if 7 <= hour < 9 or 17 <= hour < 19:
            trip_type = 'commute'
        elif weekday >= 5:
            trip_type = 'leisure'
        else:
            trip_type = 'business'

        return {
            'driver_id': self.driver_id,
            'device_id': self.device_id,
            'start_time': start_time,
            'end_time': end_time,
            'duration_minutes': duration_minutes,
            'distance_miles': distance_miles,
            'start_latitude': start_event.get('latitude'),
            'start_longitude': start_event.get('longitude'),
            'end_latitude': end_event.get('latitude'),
            'end_longitude': end_event.get('longitude'),
            'avg_speed': avg_speed,
            'max_speed': max_speed,
            'harsh_braking_count': harsh_braking_count,
            'rapid_accel_count': rapid_accel_count,
            'speeding_count': speeding_count,
            'harsh_corner_count': harsh_corner_count,
            'phone_usage_detected': phone_usage_detected,
            'trip_type': trip_type,
        }


class RealTimeTripDetector:
    """Detects trips from telematics events in real-time."""

    def __init__(self, inactivity_threshold_minutes: int = 10):
        self.inactivity_threshold_minutes = inactivity_threshold_minutes
        # Track active trips by driver_id
        self.active_trips: Dict[str, TripState] = {}

    def process_event(self, event: Dict, db: Session) -> Optional[Trip]:
        """
        Process a telematics event and detect trip start/end.
        
        Returns:
            Trip object if trip was completed, None otherwise
        """
        driver_id = event.get('driver_id')
        device_id = event.get('device_id')
        speed = event.get('speed', 0)
        
        if not driver_id or not device_id:
            return None

        trip_key = f"{driver_id}:{device_id}"

        # Check if we have an active trip for this driver/device
        if trip_key in self.active_trips:
            trip_state = self.active_trips[trip_key]
            
            # Check if trip should be closed due to inactivity
            if trip_state.should_close(self.inactivity_threshold_minutes):
                # Close the trip
                completed_trip = self._close_trip(trip_key, db)
                # Start new trip if speed > 0
                if speed > 5:
                    self._start_trip(event, trip_key)
                return completed_trip
            else:
                # Add event to existing trip
                trip_state.add_event(event)
                return None
        else:
            # No active trip - check if we should start one
            if speed > 5:  # Vehicle is moving
                self._start_trip(event, trip_key)
            return None

    def _start_trip(self, event: Dict, trip_key: str):
        """Start a new trip."""
        driver_id = event.get('driver_id')
        device_id = event.get('device_id')
        trip_state = TripState(driver_id, device_id, event)
        self.active_trips[trip_key] = trip_state
        logger.debug("trip_started", driver_id=driver_id, device_id=device_id)

    def _close_trip(self, trip_key: str, db: Session) -> Optional[Trip]:
        """Close an active trip and create trip record."""
        if trip_key not in self.active_trips:
            return None

        trip_state = self.active_trips[trip_key]
        trip_dict = trip_state.to_trip_dict()
        
        if not trip_dict or len(trip_state.events) < 2:
            # Not enough events for a valid trip
            del self.active_trips[trip_key]
            return None

        # Generate trip ID
        trip_id = f"TRP-{trip_dict['driver_id']}-{int(trip_dict['start_time'].timestamp())}"

        # Check if trip already exists
        existing_trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
        if existing_trip:
            del self.active_trips[trip_key]
            return existing_trip

        # Create trip record
        try:
            trip = Trip(
                trip_id=trip_id,
                **trip_dict
            )
            db.add(trip)
            db.commit()
            db.refresh(trip)

            logger.info(
                "trip_detected",
                trip_id=trip_id,
                driver_id=trip_dict['driver_id'],
                duration_minutes=round(trip_dict['duration_minutes'], 2),
                distance_miles=round(trip_dict['distance_miles'], 2),
                events_count=len(trip_state.events)
            )

            del self.active_trips[trip_key]
            return trip

        except Exception as e:
            db.rollback()
            logger.error("trip_creation_failed", trip_id=trip_id, error=str(e))
            del self.active_trips[trip_key]
            return None

    def close_stale_trips(self, db: Session) -> List[Trip]:
        """Close trips that have been inactive for too long."""
        closed_trips = []
        stale_keys = []

        for trip_key, trip_state in self.active_trips.items():
            if trip_state.should_close(self.inactivity_threshold_minutes):
                trip = self._close_trip(trip_key, db)
                if trip:
                    closed_trips.append(trip)
                stale_keys.append(trip_key)

        return closed_trips


# Global detector instance
_detector_instance: Optional[RealTimeTripDetector] = None


def get_trip_detector(inactivity_threshold_minutes: int = 10) -> RealTimeTripDetector:
    """Get or create trip detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = RealTimeTripDetector(inactivity_threshold_minutes)
    return _detector_instance


def detect_trip_from_event(event: Dict, db: Session) -> Optional[Trip]:
    """Convenience function to detect trip from event."""
    detector = get_trip_detector()
    return detector.process_event(event, db)

