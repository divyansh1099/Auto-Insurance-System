"""
Kafka Producer Service for Real-Time Telematics Data Ingestion

Publishes telematics events to Kafka for near real-time processing.
"""

import os
import json
from typing import Optional, List, Dict
from datetime import datetime
import structlog
from confluent_kafka import Producer, KafkaException
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class TelematicsEventProducer:
    """Kafka producer for telematics events."""

    def __init__(self):
        self.settings = get_settings()
        self.producer = None
        self.avro_serializer = None
        self._init_producer()

    def _init_producer(self):
        """Initialize Kafka producer with Avro serialization."""
        try:
            # Producer configuration optimized for throughput
            producer_conf = {
                'bootstrap.servers': self.settings.KAFKA_BOOTSTRAP_SERVERS,
                'client.id': 'telematics-producer',
                'acks': '1',  # Leader acknowledgment for better throughput
                'compression.type': 'snappy',  # Compress messages
                'linger.ms': 10,  # Wait 10ms to batch messages
                'batch.size': 32768,  # 32KB batch size
                'max.in.flight.requests.per.connection': 5,  # Allow parallel requests
                'retries': 3,
                'retry.backoff.ms': 100,
                'enable.idempotence': True,  # Prevent duplicates
            }

            self.producer = Producer(producer_conf)

            # Schema Registry configuration
            schema_registry_conf = {
                'url': self.settings.SCHEMA_REGISTRY_URL
            }

            schema_registry_client = SchemaRegistryClient(schema_registry_conf)

            # Load Avro schema
            possible_paths = [
                '/app/schemas/telematics_event.avsc',
                os.path.join(os.path.dirname(__file__), '../../..', 'schemas', 'telematics_event.avsc'),
                os.path.join(os.path.dirname(__file__), '../../../..', 'schemas', 'telematics_event.avsc'),
            ]

            schema_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    schema_path = path
                    break

            if schema_path and os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_str = f.read()
                    schema_dict = json.loads(schema_str)

                self.avro_serializer = AvroSerializer(
                    schema_registry_client,
                    schema_str,
                    lambda event, ctx: event
                )
                logger.info("avro_serializer_initialized", path=schema_path)
            else:
                logger.warning("avro_schema_not_found_using_json", tried_paths=possible_paths)
                self.avro_serializer = None

            logger.info("kafka_producer_initialized")

        except Exception as e:
            logger.error("kafka_producer_init_failed", error=str(e))
            raise

    def _delivery_callback(self, err, msg):
        """Kafka delivery callback."""
        if err is not None:
            logger.error(
                "message_delivery_failed",
                error=str(err),
                topic=msg.topic() if msg else None
            )
        else:
            logger.debug(
                "message_delivered",
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset()
            )

    def _serialize_event(self, event: Dict) -> bytes:
        """Serialize event for Kafka."""
        try:
            # Ensure timestamp is in milliseconds
            if 'timestamp' in event:
                if isinstance(event['timestamp'], datetime):
                    event['timestamp'] = int(event['timestamp'].timestamp() * 1000)
                elif isinstance(event['timestamp'], str):
                    # Parse ISO format
                    dt = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    event['timestamp'] = int(dt.timestamp() * 1000)

            # Try Avro serialization first
            if self.avro_serializer:
                try:
                    return self.avro_serializer(event, None)
                except Exception as e:
                    logger.debug("avro_serialization_failed_fallback_json", error=str(e))
                    # Fallback to JSON
                    return json.dumps(event, default=str).encode('utf-8')
            else:
                # Use JSON serialization
                return json.dumps(event, default=str).encode('utf-8')
        except Exception as e:
            logger.error("event_serialization_failed", error=str(e))
            raise

    def publish_event(self, event: Dict, topic: str = "telematics-events") -> bool:
        """
        Publish a single event to Kafka.
        
        Args:
            event: Event dictionary
            topic: Kafka topic name
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("producer_not_initialized")
            return False

        try:
            # Use driver_id as key for partitioning (ensures events from same driver go to same partition)
            key = event.get('driver_id', 'unknown').encode('utf-8')
            
            # Serialize event
            serialized_value = self._serialize_event(event)

            # Publish to Kafka (async)
            self.producer.produce(
                topic=topic,
                key=key,
                value=serialized_value,
                on_delivery=self._delivery_callback
            )

            # Trigger delivery callbacks (non-blocking)
            self.producer.poll(0)

            logger.debug(
                "event_published",
                event_id=event.get('event_id'),
                driver_id=event.get('driver_id'),
                topic=topic
            )

            return True

        except Exception as e:
            logger.error(
                "event_publish_failed",
                event_id=event.get('event_id'),
                error=str(e)
            )
            return False

    def publish_events_batch(self, events: List[Dict], topic: str = "telematics-events") -> int:
        """
        Publish multiple events to Kafka in batch.
        
        Args:
            events: List of event dictionaries
            topic: Kafka topic name
            
        Returns:
            Number of events successfully published
        """
        if not self.producer:
            logger.error("producer_not_initialized")
            return 0

        published_count = 0

        try:
            for event in events:
                if self.publish_event(event, topic):
                    published_count += 1

            # Flush remaining messages (wait up to 30 seconds)
            remaining = self.producer.flush(timeout=30)
            
            if remaining > 0:
                logger.warning(
                    "messages_not_delivered",
                    count=remaining,
                    total=len(events)
                )
            else:
                logger.info(
                    "batch_published",
                    published=published_count,
                    total=len(events),
                    topic=topic
                )

            return published_count

        except Exception as e:
            logger.error("batch_publish_failed", error=str(e), count=len(events))
            return published_count

    def flush(self, timeout: int = 30):
        """Flush all pending messages."""
        if self.producer:
            remaining = self.producer.flush(timeout=timeout)
            if remaining > 0:
                logger.warning("messages_remaining_after_flush", count=remaining)
            return remaining
        return 0

    def close(self):
        """Close the producer."""
        if self.producer:
            self.flush(timeout=60)
            self.producer = None
            logger.info("kafka_producer_closed")


# Global producer instance
_producer_instance: Optional[TelematicsEventProducer] = None


def get_producer() -> TelematicsEventProducer:
    """Get or create producer instance."""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = TelematicsEventProducer()
    return _producer_instance


def publish_telematics_event(event: Dict, topic: str = "telematics-events") -> bool:
    """Convenience function to publish a single event."""
    producer = get_producer()
    return producer.publish_event(event, topic)


def publish_telematics_events_batch(events: List[Dict], topic: str = "telematics-events") -> int:
    """Convenience function to publish multiple events."""
    producer = get_producer()
    return producer.publish_events_batch(events, topic)

