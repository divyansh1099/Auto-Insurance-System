"""
Kafka Consumer Service for Telematics Events

Consumes events from Kafka and stores them in PostgreSQL.
"""

import os
import json
from datetime import datetime
from typing import Optional
import structlog
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.database import SessionLocal, TelematicsEvent

logger = structlog.get_logger()
settings = get_settings()


class TelematicsEventConsumer:
    """Kafka consumer for telematics events."""

    def __init__(self):
        self.settings = get_settings()
        self.consumer = None
        self.avro_deserializer = None
        self.running = False
        self._init_consumer()

    def _init_consumer(self):
        """Initialize Kafka consumer with Avro deserialization."""
        try:
            # Consumer configuration
            consumer_conf = {
                'bootstrap.servers': self.settings.KAFKA_BOOTSTRAP_SERVERS,
                'group.id': self.settings.KAFKA_CONSUMER_GROUP,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True,
                'auto.commit.interval.ms': 1000,
            }

            self.consumer = Consumer(consumer_conf)

            # Schema Registry configuration
            schema_registry_conf = {
                'url': self.settings.SCHEMA_REGISTRY_URL
            }

            schema_registry_client = SchemaRegistryClient(schema_registry_conf)

            # Load Avro schema - try multiple paths
            possible_paths = [
                '/app/schemas/telematics_event.avsc',  # Mounted volume
                os.path.join(os.path.dirname(__file__), '../../..', 'schemas', 'telematics_event.avsc'),
                os.path.join(os.path.dirname(__file__), '../../../..', 'schemas', 'telematics_event.avsc'),
                '/app/../schemas/telematics_event.avsc',
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

                self.avro_deserializer = AvroDeserializer(
                    schema_registry_client,
                    schema_str,
                    from_dict=lambda x, ctx: x
                )
                logger.info("avro_schema_loaded", path=schema_path)
            else:
                logger.warning("avro_schema_not_found", tried_paths=possible_paths)
                # Fallback: use JSON deserialization
                self.avro_deserializer = None

            logger.info("kafka_consumer_initialized")

        except Exception as e:
            logger.error("kafka_consumer_init_failed", error=str(e))
            raise

    def _deserialize_message(self, msg_value: bytes) -> Optional[dict]:
        """Deserialize Kafka message."""
        try:
            if self.avro_deserializer:
                return self.avro_deserializer(msg_value, None)
            else:
                # Fallback to JSON
                return json.loads(msg_value.decode('utf-8'))
        except Exception as e:
            logger.error("message_deserialization_failed", error=str(e))
            return None

    def _store_event(self, event_data: dict, db: Session):
        """Store event in PostgreSQL."""
        try:
            # Convert timestamp from milliseconds to datetime
            timestamp_ms = event_data.get('timestamp')
            if isinstance(timestamp_ms, int):
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)
            else:
                timestamp = datetime.now()

            # Handle foreign key constraints - check if referenced entities exist
            from app.models.database import Device, Driver, Trip
            
            device_id = event_data.get('device_id')
            driver_id = event_data.get('driver_id')
            trip_id = event_data.get('trip_id')
            
            # Check driver exists first (required for device FK)
            if driver_id:
                driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
                if not driver:
                    # Create minimal driver if it doesn't exist
                    driver = Driver(
                        driver_id=driver_id,
                        email=f"{driver_id.lower()}@example.com",
                        first_name="Driver",
                        last_name=driver_id
                    )
                    db.add(driver)
                    db.commit()
                    db.refresh(driver)
                    logger.info("driver_created", driver_id=driver_id)
            
            # Check and create device if it doesn't exist (now that driver exists)
            if device_id:
                device = db.query(Device).filter(Device.device_id == device_id).first()
                if not device:
                    # Create device if it doesn't exist
                    device = Device(device_id=device_id, driver_id=driver_id, is_active=True)
                    db.add(device)
                    db.commit()  # Commit device first so FK constraint is satisfied
                    db.refresh(device)
            
            # Check trip exists
            if trip_id:
                trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
                if not trip:
                    trip_id = None  # Set to None if trip doesn't exist
            
            # Create database record
            db_event = TelematicsEvent(
                event_id=event_data.get('event_id'),
                device_id=device_id,
                driver_id=driver_id,
                timestamp=timestamp,
                latitude=event_data.get('latitude'),
                longitude=event_data.get('longitude'),
                speed=event_data.get('speed'),
                acceleration=event_data.get('acceleration'),
                braking_force=event_data.get('braking_force'),
                heading=event_data.get('heading'),
                altitude=event_data.get('altitude'),
                gps_accuracy=event_data.get('gps_accuracy', 10.0),
                event_type=event_data.get('event_type', 'normal'),
                trip_id=trip_id  # Can be None
            )

            db.add(db_event)
            db.commit()
            db.refresh(db_event)

            logger.debug(
                "event_stored",
                event_id=event_data.get('event_id'),
                driver_id=event_data.get('driver_id')
            )

            return db_event

        except Exception as e:
            db.rollback()
            logger.error(
                "event_storage_failed",
                event_id=event_data.get('event_id'),
                error=str(e)
            )
            raise

    def consume_events(self, topic: str = "telematics-events"):
        """Consume events from Kafka topic."""
        self.consumer.subscribe([topic])
        self.running = True

        logger.info("kafka_consumer_started", topic=topic)

        db = SessionLocal()

        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logger.debug("reached_end_of_partition", partition=msg.partition())
                        continue
                    else:
                        logger.error("kafka_error", error=msg.error())
                        continue

                # Deserialize message
                event_data = self._deserialize_message(msg.value())

                if event_data:
                    # Store in database
                    try:
                        self._store_event(event_data, db)
                        logger.info(
                            "event_processed",
                            event_id=event_data.get('event_id'),
                            driver_id=event_data.get('driver_id'),
                            partition=msg.partition(),
                            offset=msg.offset()
                        )
                    except Exception as e:
                        logger.error("event_processing_failed", error=str(e))

        except KeyboardInterrupt:
            logger.info("kafka_consumer_stopping")
            self.running = False
        except Exception as e:
            logger.error("kafka_consumer_error", error=str(e))
            raise
        finally:
            self.consumer.close()
            db.close()
            logger.info("kafka_consumer_stopped")

    def stop(self):
        """Stop the consumer."""
        self.running = False


# Global consumer instance
consumer_instance: Optional[TelematicsEventConsumer] = None


def get_consumer() -> TelematicsEventConsumer:
    """Get or create consumer instance."""
    global consumer_instance
    if consumer_instance is None:
        consumer_instance = TelematicsEventConsumer()
    return consumer_instance


def start_consumer_background(topic: str = "telematics-events"):
    """Start consumer in background thread."""
    import threading
    consumer = get_consumer()
    thread = threading.Thread(target=consumer.consume_events, args=(topic,), daemon=True)
    thread.start()
    logger.info("kafka_consumer_started_background")
    return thread

