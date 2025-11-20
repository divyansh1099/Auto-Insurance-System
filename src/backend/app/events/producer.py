"""
Event Producer for Kafka

Publishes events to Kafka topics for event-driven architecture.
"""

import json
import uuid
from typing import Optional
from datetime import datetime
import structlog

from app.services.kafka_client import get_kafka_producer
from app.events.schemas import BaseEvent, EventType

logger = structlog.get_logger()


class EventProducer:
    """Produces events to Kafka topics."""
    
    def __init__(self):
        self.producer = get_kafka_producer()
        self.source = "telematics-api"
    
    def publish(
        self,
        event: BaseEvent,
        topic: Optional[str] = None
    ) -> bool:
        """
        Publish an event to Kafka.
        
        Args:
            event: Event to publish (must inherit from BaseEvent)
            topic: Optional topic override (defaults to event type)
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Determine topic from event type if not provided
            if topic is None:
                topic = self._get_topic_for_event(event.event_type)
            
            # Ensure event has required fields
            if not event.event_id:
                event.event_id = str(uuid.uuid4())
            
            if not event.source:
                event.source = self.source
            
            # Serialize event to JSON
            event_data = event.model_dump_json()
            
            # Publish to Kafka
            future = self.producer.send(
                topic,
                value=event_data.encode('utf-8'),
                key=event.event_id.encode('utf-8')
            )
            
            # Wait for confirmation (with timeout)
            future.get(timeout=10)
            
            logger.info(
                "event_published",
                event_id=event.event_id,
                event_type=event.event_type.value,
                topic=topic
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "event_publish_failed",
                event_id=getattr(event, 'event_id', 'unknown'),
                event_type=getattr(event, 'event_type', 'unknown'),
                error=str(e)
            )
            return False
    
    def _get_topic_for_event(self, event_type: EventType) -> str:
        """Map event type to Kafka topic."""
        topic_mapping = {
            EventType.TRIP_COMPLETED: "trips",
            EventType.RISK_SCORE_CALCULATED: "risk-scores",
            EventType.PREMIUM_UPDATED: "premiums",
            EventType.DRIVER_CREATED: "drivers",
            EventType.DRIVER_UPDATED: "drivers",
            EventType.SAFETY_ALERT: "safety-alerts",
        }
        
        return topic_mapping.get(event_type, "default")


# Global event producer instance
_event_producer: Optional[EventProducer] = None


def get_event_producer() -> EventProducer:
    """Get or create the global event producer instance."""
    global _event_producer
    
    if _event_producer is None:
        _event_producer = EventProducer()
    
    return _event_producer


def publish_event(event: BaseEvent, topic: Optional[str] = None) -> bool:
    """
    Convenience function to publish an event.
    
    Args:
        event: Event to publish
        topic: Optional topic override
        
    Returns:
        True if published successfully
    """
    producer = get_event_producer()
    return producer.publish(event, topic)
