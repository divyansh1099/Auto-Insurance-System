"""
Data Generator API Endpoints

Provides REST API endpoints to generate telematics data for testing.
Useful for generating data without physical devices.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import random
import structlog

from app.models.database import get_db, User
from app.utils.auth import get_current_user
from app.services.kafka_producer import publish_telematics_event, publish_telematics_events_batch
from app.services.stream_processor import process_telematics_event
from app.services.realistic_data_generator import RealisticDataGenerator, generate_realistic_event

logger = structlog.get_logger()
router = APIRouter()


class GenerateEventRequest(BaseModel):
    """Request to generate a single event."""
    driver_id: str = Field(..., description="Driver ID")
    device_id: Optional[str] = Field(None, description="Device ID (auto-generated if not provided)")
    latitude: float = Field(37.7749, ge=-90, le=90, description="Latitude")
    longitude: float = Field(-122.4194, ge=-180, le=180, description="Longitude")
    speed: Optional[float] = Field(None, ge=0, le=200, description="Speed in mph (random if not provided)")
    event_type: Optional[str] = Field(None, description="Event type (random if not provided)")


class GenerateBatchRequest(BaseModel):
    """Request to generate multiple events."""
    driver_id: str = Field(..., description="Driver ID")
    device_id: Optional[str] = Field(None, description="Device ID (auto-generated if not provided)")
    count: int = Field(100, ge=1, le=1000, description="Number of events to generate")
    latitude: float = Field(37.7749, ge=-90, le=90, description="Base latitude")
    longitude: float = Field(-122.4194, ge=-180, le=180, description="Base longitude")
    interval_seconds: float = Field(10.0, ge=1, le=60, description="Interval between events in seconds")


class GenerateTripRequest(BaseModel):
    """Request to generate a complete trip."""
    driver_id: str = Field(..., description="Driver ID")
    device_id: Optional[str] = Field(None, description="Device ID (auto-generated if not provided)")
    start_latitude: float = Field(37.7749, ge=-90, le=90, description="Trip start latitude")
    start_longitude: float = Field(-122.4194, ge=-180, le=180, description="Trip start longitude")
    duration_minutes: int = Field(20, ge=5, le=120, description="Trip duration in minutes")
    events_per_minute: int = Field(6, ge=1, le=60, description="Events per minute")


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    status: str = "success"
    events_generated: Optional[int] = None


# Global state storage for realistic generation
_generator_states = {}

def _generate_event(driver_id: str, device_id: str, base_lat: float, base_lon: float,
                   speed: float = None, event_type: str = None) -> dict:
    """Generate a single realistic telematics event using physics-based model."""
    # Get or create generator state for this driver
    state_key = f"{driver_id}:{device_id}"
    
    if state_key not in _generator_states:
        # Create new generator
        generator = RealisticDataGenerator(driver_id, device_id, base_lat, base_lon)
        _generator_states[state_key] = generator
    else:
        generator = _generator_states[state_key]
    
    # Generate realistic event
    event = generator.generate_event(time_interval=10.0)
    
    # Override if specific speed/event_type requested (for backward compatibility)
    if speed is not None:
        generator.state.speed = speed
        generator.state.target_speed = speed
        event['speed'] = round(speed, 2)
    
    if event_type is not None:
        event['event_type'] = event_type
    
    return event


@router.post("/generate-event", response_model=MessageResponse)
async def generate_single_event(
    request: GenerateEventRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Generate and send a single telematics event.
    
    Useful for testing individual events or manual data generation.
    """
    device_id = request.device_id or f"DEV-{uuid.uuid4().hex[:8].upper()}"
    
    # Generate event
    event = _generate_event(
        driver_id=request.driver_id,
        device_id=device_id,
        base_lat=request.latitude,
        base_lon=request.longitude,
        speed=request.speed,
        event_type=request.event_type
    )
    
    # Process and publish
    processed_event = process_telematics_event(event)
    if processed_event:
        success = publish_telematics_event(processed_event)
        if success:
            logger.info("event_generated", driver_id=request.driver_id, event_id=event['event_id'])
            return MessageResponse(
                message="Event generated and published successfully",
                events_generated=1
            )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to generate event"
    )


@router.post("/generate-batch", response_model=MessageResponse)
async def generate_batch_events(
    request: GenerateBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Generate and send a batch of telematics events.
    
    Generates multiple events with configurable intervals.
    Events are sent to Kafka for processing.
    """
    device_id = request.device_id or f"DEV-{uuid.uuid4().hex[:8].upper()}"
    
    events = []
    current_lat = request.latitude
    current_lon = request.longitude
    
    for i in range(request.count):
        # Small movement for each event
        current_lat += random.uniform(-0.001, 0.001)
        current_lon += random.uniform(-0.001, 0.001)
        
        event = _generate_event(
            driver_id=request.driver_id,
            device_id=device_id,
            base_lat=current_lat,
            base_lon=current_lon
        )
        events.append(event)
    
    # Process and publish batch
    from app.services.stream_processor import process_telematics_events_batch
    processed_events, invalid_events = process_telematics_events_batch(events)
    
    if processed_events:
        published_count = publish_telematics_events_batch(processed_events)
        logger.info(
            "batch_generated",
            driver_id=request.driver_id,
            total=len(events),
            published=published_count
        )
        
        return MessageResponse(
            message=f"Generated and published {published_count} events",
            events_generated=published_count
        )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to generate events"
    )


@router.post("/generate-trip", response_model=MessageResponse)
async def generate_trip(
    request: GenerateTripRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a complete trip with realistic driving patterns.
    
    Simulates a trip with acceleration, cruising, and deceleration phases.
    Generates events at regular intervals throughout the trip.
    """
    device_id = request.device_id or f"DEV-{uuid.uuid4().hex[:8].upper()}"
    
    # Use realistic data generator for trip
    generator = RealisticDataGenerator(
        request.driver_id,
        device_id,
        request.start_latitude,
        request.start_longitude
    )
    
    # Generate realistic trip
    events = generator.generate_trip(
        duration_minutes=request.duration_minutes,
        events_per_minute=request.events_per_minute
    )
    
    # Process and publish batch
    from app.services.stream_processor import process_telematics_events_batch
    processed_events, invalid_events = process_telematics_events_batch(events)
    
    if processed_events:
        published_count = publish_telematics_events_batch(processed_events)
        logger.info(
            "trip_generated",
            driver_id=request.driver_id,
            duration_minutes=request.duration_minutes,
            events=published_count
        )
        
        return MessageResponse(
            message=f"Generated trip with {published_count} events",
            events_generated=published_count
        )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to generate trip"
    )

