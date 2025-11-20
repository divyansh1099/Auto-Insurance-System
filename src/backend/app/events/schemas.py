"""
Event Schemas for Event-Driven Architecture

Defines Pydantic models for Kafka events to ensure type safety
and consistent event structure across the system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Event types for the system."""
    TRIP_COMPLETED = "trip.completed"
    RISK_SCORE_CALCULATED = "risk.score.calculated"
    PREMIUM_UPDATED = "premium.updated"
    DRIVER_CREATED = "driver.created"
    DRIVER_UPDATED = "driver.updated"
    SAFETY_ALERT = "safety.alert"


class BaseEvent(BaseModel):
    """Base event schema with common fields."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    source: str = Field(..., description="Service that generated the event")
    version: str = Field(default="1.0", description="Event schema version")


class TripCompletedEvent(BaseEvent):
    """Event published when a trip is completed."""
    event_type: EventType = EventType.TRIP_COMPLETED
    
    # Trip data
    trip_id: str
    driver_id: str
    duration_minutes: float
    distance_miles: float
    avg_speed: Optional[float] = None
    max_speed: Optional[float] = None
    
    # Safety metrics
    harsh_braking_count: int = 0
    rapid_accel_count: int = 0
    speeding_count: int = 0
    harsh_corner_count: int = 0
    phone_usage_detected: bool = False
    
    # Risk assessment
    trip_score: Optional[int] = None
    risk_level: Optional[str] = None


class RiskScoreCalculatedEvent(BaseEvent):
    """Event published when a risk score is calculated."""
    event_type: EventType = EventType.RISK_SCORE_CALCULATED
    
    driver_id: str
    risk_score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    model_version: str
    previous_score: Optional[float] = None
    score_change: Optional[float] = None
    
    # Context
    events_analyzed: int
    period_days: int
    
    # Trigger for downstream actions
    requires_premium_update: bool = False
    requires_notification: bool = False


class PremiumUpdatedEvent(BaseEvent):
    """Event published when a premium is updated."""
    event_type: EventType = EventType.PREMIUM_UPDATED
    
    driver_id: str
    premium_id: int
    
    # Premium details
    previous_premium: Optional[float] = None
    new_premium: float
    discount_percentage: float
    
    # Reason for update
    reason: str  # "risk_score_change", "manual_adjustment", "policy_renewal"
    triggered_by_event: Optional[str] = None  # Reference to triggering event


class DriverCreatedEvent(BaseEvent):
    """Event published when a new driver is created."""
    event_type: EventType = EventType.DRIVER_CREATED
    
    driver_id: str
    email: str
    created_by: str  # user_id or "system"
    
    # Trigger onboarding workflows
    requires_device_assignment: bool = True
    requires_welcome_email: bool = True


class DriverUpdatedEvent(BaseEvent):
    """Event published when a driver is updated."""
    event_type: EventType = EventType.DRIVER_UPDATED
    
    driver_id: str
    updated_by: str
    fields_updated: list[str]
    
    # Context for downstream processing
    requires_risk_recalculation: bool = False


class SafetyAlertEvent(BaseEvent):
    """Event published for safety alerts."""
    event_type: EventType = EventType.SAFETY_ALERT
    
    driver_id: str
    alert_type: str  # "harsh_braking", "speeding", "phone_usage", etc.
    severity: str  # "low", "medium", "high", "critical"
    
    # Event details
    trip_id: Optional[str] = None
    location: Optional[Dict[str, float]] = None  # {"lat": ..., "lon": ...}
    speed: Optional[float] = None
    
    # Actions
    requires_notification: bool = True
    requires_coaching: bool = False


# Event Registry for easy lookup
EVENT_SCHEMAS = {
    EventType.TRIP_COMPLETED: TripCompletedEvent,
    EventType.RISK_SCORE_CALCULATED: RiskScoreCalculatedEvent,
    EventType.PREMIUM_UPDATED: PremiumUpdatedEvent,
    EventType.DRIVER_CREATED: DriverCreatedEvent,
    EventType.DRIVER_UPDATED: DriverUpdatedEvent,
    EventType.SAFETY_ALERT: SafetyAlertEvent,
}


def get_event_schema(event_type: EventType):
    """Get the Pydantic schema for a given event type."""
    return EVENT_SCHEMAS.get(event_type, BaseEvent)
