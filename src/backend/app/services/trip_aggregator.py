"""
Trip aggregation service.
Groups telematics events into trips and calculates trip metrics.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import TelematicsEvent, Trip, Device


def group_events_into_trips(events: List[TelematicsEvent], inactivity_threshold_minutes: int = 10) -> List[Dict]:
    """
    Group events into trips based on inactivity threshold.
    
    Args:
        events: List of telematics events
        inactivity_threshold_minutes: Minutes of inactivity to consider trip end
        
    Returns:
        List of trip dictionaries with events
    """
    if not events:
        return []
    
    trips = []
    current_trip = []
    
    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda e: e.timestamp)
    
    for i, event in enumerate(sorted_events):
        if not current_trip:
            # Start new trip
            current_trip = [event]
        else:
            # Check time gap from last event
            time_gap = (event.timestamp - current_trip[-1].timestamp).total_seconds() / 60
            
            if time_gap > inactivity_threshold_minutes:
                # Gap is too large, end current trip and start new one
                trips.append(current_trip)
                current_trip = [event]
            else:
                # Continue current trip
                current_trip.append(event)
        
        # If this is the last event, close the trip
        if i == len(sorted_events) - 1:
            trips.append(current_trip)
    
    return trips


def calculate_trip_metrics(trip_events: List[TelematicsEvent]) -> Dict:
    """
    Calculate metrics for a trip from events.
    
    Args:
        trip_events: List of events belonging to a trip
        
    Returns:
        Dictionary with trip metrics
    """
    if not trip_events:
        return {}
    
    # Sort by timestamp
    sorted_events = sorted(trip_events, key=lambda e: e.timestamp)
    start_event = sorted_events[0]
    end_event = sorted_events[-1]
    
    # Calculate duration
    duration_seconds = (end_event.timestamp - start_event.timestamp).total_seconds()
    duration_minutes = duration_seconds / 60
    
    # Calculate distance (rough estimate using Haversine or speed * time)
    speeds = [e.speed for e in sorted_events if e.speed is not None]
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    distance_miles = (avg_speed * duration_seconds) / 3600 if avg_speed > 0 else 0
    
    # Calculate metrics
    max_speed = max(speeds) if speeds else 0
    harsh_braking_count = sum(1 for e in trip_events if e.event_type == 'harsh_brake')
    rapid_accel_count = sum(1 for e in trip_events if e.event_type == 'rapid_accel')
    speeding_count = sum(1 for e in trip_events if e.event_type == 'speeding')
    harsh_corner_count = sum(1 for e in trip_events if e.event_type == 'harsh_corner')
    phone_usage_detected = any(e.event_type == 'phone_usage' for e in trip_events)
    
    # Determine trip type (simplified)
    hour = start_event.timestamp.hour
    weekday = start_event.timestamp.weekday()
    
    if 7 <= hour < 9 or 17 <= hour < 19:
        trip_type = 'commute'
    elif weekday >= 5:
        trip_type = 'leisure'
    else:
        trip_type = 'business'
    
    return {
        'start_time': start_event.timestamp,
        'end_time': end_event.timestamp,
        'duration_minutes': duration_minutes,
        'distance_miles': distance_miles,
        'start_latitude': start_event.latitude,
        'start_longitude': start_event.longitude,
        'end_latitude': end_event.latitude,
        'end_longitude': end_event.longitude,
        'avg_speed': avg_speed,
        'max_speed': max_speed,
        'harsh_braking_count': harsh_braking_count,
        'rapid_accel_count': rapid_accel_count,
        'speeding_count': speeding_count,
        'harsh_corner_count': harsh_corner_count,
        'phone_usage_detected': phone_usage_detected,
        'trip_type': trip_type,
        'device_id': start_event.device_id,
        'driver_id': start_event.driver_id
    }


def create_trips_from_events(
    driver_id: str,
    db: Session,
    period_days: int = 30,
    inactivity_threshold_minutes: int = 10
) -> List[Trip]:
    """
    Create trip records from telematics events for a driver.
    
    Args:
        driver_id: Driver ID
        db: Database session
        period_days: Number of days to look back
        inactivity_threshold_minutes: Minutes of inactivity to consider trip end
        
    Returns:
        List of Trip objects created
    """
    from datetime import datetime, timedelta
    
    # Early return if trips already exist for this driver
    # This prevents creating duplicate trips from events when trips were already created directly
    existing_trip_count = db.query(Trip).filter(Trip.driver_id == driver_id).count()
    if existing_trip_count > 0:
        return []
    
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)
    
    # Get events for driver that are NOT already associated with a trip
    # Skip events that already have a trip_id to prevent duplicate trip creation
    events = (
        db.query(TelematicsEvent)
        .filter(
            TelematicsEvent.driver_id == driver_id,
            TelematicsEvent.timestamp >= period_start,
            TelematicsEvent.timestamp <= period_end,
            TelematicsEvent.trip_id.is_(None)  # Only process events not already linked to trips
        )
        .order_by(TelematicsEvent.timestamp)
        .all()
    )
    
    if not events:
        return []
    
    # Group events into trips
    trip_groups = group_events_into_trips(events, inactivity_threshold_minutes)
    
    created_trips = []
    
    for trip_events in trip_groups:
        if len(trip_events) < 2:  # Need at least 2 events for a trip
            continue
        
        # Calculate trip metrics
        metrics = calculate_trip_metrics(trip_events)
        
        # Generate trip ID
        trip_id = f"TRP-{driver_id}-{int(trip_events[0].timestamp.timestamp())}"
        
        # Check if trip already exists
        existing_trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
        if existing_trip:
            continue
        
        # Create trip record
        trip = Trip(
            trip_id=trip_id,
            driver_id=driver_id,
            device_id=metrics['device_id'],
            start_time=metrics['start_time'],
            end_time=metrics['end_time'],
            duration_minutes=metrics['duration_minutes'],
            distance_miles=metrics['distance_miles'],
            start_latitude=metrics['start_latitude'],
            start_longitude=metrics['start_longitude'],
            end_latitude=metrics['end_latitude'],
            end_longitude=metrics['end_longitude'],
            avg_speed=metrics['avg_speed'],
            max_speed=metrics['max_speed'],
            harsh_braking_count=metrics['harsh_braking_count'],
            rapid_accel_count=metrics['rapid_accel_count'],
            speeding_count=metrics['speeding_count'],
            harsh_corner_count=metrics['harsh_corner_count'],
            phone_usage_detected=metrics['phone_usage_detected'],
            trip_type=metrics['trip_type']
        )
        
        db.add(trip)
        created_trips.append(trip)
    
    if created_trips:
        db.commit()
        for trip in created_trips:
            db.refresh(trip)
    
    return created_trips

