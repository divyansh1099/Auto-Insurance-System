"""
Event Consumers for Kafka

Consumes events from Kafka topics and triggers appropriate actions.
"""

import json
from typing import Callable, Dict
import structlog

from app.services.kafka_client import get_kafka_consumer
from app.events.schemas import (
    EventType,
    TripCompletedEvent,
    RiskScoreCalculatedEvent,
    get_event_schema
)

logger = structlog.get_logger()


class EventConsumer:
    """Base event consumer."""
    
    def __init__(self, topic: str, group_id: str):
        self.topic = topic
        self.group_id = group_id
        self.consumer = get_kafka_consumer(topic, group_id)
        self.handlers: Dict[EventType, Callable] = {}
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register a handler function for an event type."""
        self.handlers[event_type] = handler
        logger.info(
            "handler_registered",
            event_type=event_type.value,
            topic=self.topic
        )
    
    def start(self):
        """Start consuming events."""
        logger.info(
            "consumer_started",
            topic=self.topic,
            group_id=self.group_id
        )
        
        try:
            for message in self.consumer:
                self._process_message(message)
        except KeyboardInterrupt:
            logger.info("consumer_stopped", topic=self.topic)
        finally:
            self.consumer.close()
    
    def _process_message(self, message):
        """Process a single message."""
        try:
            # Decode message
            event_data = json.loads(message.value.decode('utf-8'))
            event_type = EventType(event_data.get('event_type'))
            
            # Get appropriate schema
            schema_class = get_event_schema(event_type)
            event = schema_class(**event_data)
            
            # Find and execute handler
            handler = self.handlers.get(event_type)
            if handler:
                handler(event)
                logger.info(
                    "event_processed",
                    event_id=event.event_id,
                    event_type=event_type.value
                )
            else:
                logger.warning(
                    "no_handler_found",
                    event_type=event_type.value
                )
            
        except Exception as e:
            logger.error(
                "event_processing_failed",
                error=str(e),
                message_offset=message.offset
            )


class RiskScoringConsumer(EventConsumer):
    """Consumer for trip events to trigger risk scoring."""
    
    def __init__(self):
        super().__init__(topic="trips", group_id="risk-scoring-service")
        self.register_handler(EventType.TRIP_COMPLETED, self.handle_trip_completed)
    
    def handle_trip_completed(self, event: TripCompletedEvent):
        """Handle trip completed event by calculating risk score."""
        from app.services.ml_risk_scoring import calculate_ml_risk_score
        from app.models.database import SessionLocal
        from app.events.producer import publish_event
        from app.events.schemas import RiskScoreCalculatedEvent
        import uuid
        
        logger.info(
            "processing_trip_for_risk_scoring",
            trip_id=event.trip_id,
            driver_id=event.driver_id
        )
        
        db = SessionLocal()
        try:
            # Calculate risk score
            risk_data = calculate_ml_risk_score(
                driver_id=event.driver_id,
                db=db,
                period_days=30
            )
            
            # Publish risk score calculated event
            risk_event = RiskScoreCalculatedEvent(
                event_id=str(uuid.uuid4()),
                source="risk-scoring-service",
                driver_id=event.driver_id,
                risk_score=risk_data['risk_score'],
                confidence=risk_data['confidence'],
                model_version=risk_data['model_version'],
                events_analyzed=risk_data.get('events_used', 0),
                period_days=30,
                requires_premium_update=True,  # Trigger premium recalculation
                requires_notification=risk_data['risk_score'] > 70  # High risk
            )
            
            publish_event(risk_event)
            
            logger.info(
                "risk_score_calculated_and_published",
                driver_id=event.driver_id,
                risk_score=risk_data['risk_score']
            )
            
        except Exception as e:
            logger.error(
                "risk_scoring_failed",
                driver_id=event.driver_id,
                error=str(e)
            )
        finally:
            db.close()


class NotificationConsumer(EventConsumer):
    """Consumer for events that require notifications."""
    
    def __init__(self):
        super().__init__(topic="risk-scores", group_id="notification-service")
        self.register_handler(
            EventType.RISK_SCORE_CALCULATED,
            self.handle_risk_score_calculated
        )
    
    def handle_risk_score_calculated(self, event: RiskScoreCalculatedEvent):
        """Handle risk score calculated event by sending notifications."""
        if not event.requires_notification:
            return
        
        logger.info(
            "sending_risk_notification",
            driver_id=event.driver_id,
            risk_score=event.risk_score
        )
        
        # TODO: Implement actual notification logic
        # - Send email
        # - Send push notification
        # - Create in-app notification
        
        # For now, just log
        logger.info(
            "notification_sent",
            driver_id=event.driver_id,
            notification_type="high_risk_alert"
        )


# Consumer registry
CONSUMERS = {
    "risk-scoring": RiskScoringConsumer,
    "notification": NotificationConsumer,
}


def start_consumer(consumer_name: str):
    """Start a specific consumer by name."""
    consumer_class = CONSUMERS.get(consumer_name)
    if not consumer_class:
        raise ValueError(f"Unknown consumer: {consumer_name}")
    
    consumer = consumer_class()
    consumer.start()
