"""
Events Package

Event-driven architecture components for the telematics system.

Usage:
    from app.events import publish_event, TripCompletedEvent
    
    event = TripCompletedEvent(
        event_id=str(uuid.uuid4()),
        source="trip-service",
        trip_id="TRIP-001",
        driver_id="DRV-001",
        ...
    )
    
    publish_event(event)
"""

from app.events.schemas import (
    EventType,
    BaseEvent,
    TripCompletedEvent,
    RiskScoreCalculatedEvent,
    PremiumUpdatedEvent,
    DriverCreatedEvent,
    DriverUpdatedEvent,
    SafetyAlertEvent,
)

from app.events.producer import publish_event, get_event_producer
from app.events.consumers import start_consumer, CONSUMERS

__all__ = [
    # Event types
    "EventType",
    
    # Event schemas
    "BaseEvent",
    "TripCompletedEvent",
    "RiskScoreCalculatedEvent",
    "PremiumUpdatedEvent",
    "DriverCreatedEvent",
    "DriverUpdatedEvent",
    "SafetyAlertEvent",
    
    # Producer
    "publish_event",
    "get_event_producer",
    
    # Consumers
    "start_consumer",
    "CONSUMERS",
]
