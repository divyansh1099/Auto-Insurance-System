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
from app.utils.metrics import (
    kafka_messages_consumed_total,
    kafka_processing_duration_seconds,
    events_processed_total,
    kafka_consumer_lag_messages,
    kafka_consumer_errors_total,
    kafka_processing_errors_total
)
from app.services.realtime_trip_detector import detect_trip_from_event
from app.services.realtime_ml_inference import analyze_event_realtime
from app.services.websocket_manager import get_connection_manager
from app.services.realtime_pricing import calculate_realtime_premium

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
            # Check if message starts with '{' (JSON) or Avro magic byte (0x00)
            if msg_value and len(msg_value) > 0:
                first_byte = msg_value[0]
                # Magic byte 123 is '{' (JSON)
                if first_byte == 123:  # JSON format
                    logger.debug("deserializing_json_message", first_byte=first_byte)
                    return json.loads(msg_value.decode('utf-8'))
                # Try Avro deserialization
                elif self.avro_deserializer:
                    try:
                        logger.debug("deserializing_avro_message", first_byte=first_byte)
                        return self.avro_deserializer(msg_value, None)
                    except Exception as avro_error:
                        # If Avro fails, try JSON as fallback
                        logger.debug("avro_deserialization_failed_fallback_json", error=str(avro_error))
                        try:
                            return json.loads(msg_value.decode('utf-8'))
                        except Exception as json_error:
                            logger.error("json_fallback_failed", avro_error=str(avro_error), json_error=str(json_error))
                            return None
                else:
                    # Fallback to JSON
                    logger.debug("no_avro_deserializer_using_json")
                    return json.loads(msg_value.decode('utf-8'))
            return None
        except Exception as e:
            logger.error("message_deserialization_failed", error=str(e), first_byte=msg_value[0] if msg_value else None)
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

    def _monitor_consumer_lag(self, topic: str):
        """
        Monitor and report Kafka consumer lag to Prometheus.

        Args:
            topic: Kafka topic name
        """
        try:
            # Get all assigned partitions
            assignment = self.consumer.assignment()

            if not assignment:
                logger.debug("no_partitions_assigned_yet")
                return

            for partition in assignment:
                try:
                    # Get committed offset (where consumer is at)
                    committed = self.consumer.committed([partition])
                    if committed and len(committed) > 0:
                        current_offset = committed[0].offset if committed[0].offset >= 0 else 0
                    else:
                        current_offset = 0

                    # Get high water mark (latest offset available)
                    low, high = self.consumer.get_watermark_offsets(partition)

                    # Calculate lag
                    lag = max(0, high - current_offset)

                    # Report to Prometheus
                    kafka_consumer_lag_messages.labels(
                        topic=topic,
                        partition=partition.partition,
                        consumer_group=self.settings.KAFKA_CONSUMER_GROUP
                    ).set(lag)

                    # Log warning if lag is high
                    if lag > 10000:
                        logger.warning(
                            "high_consumer_lag",
                            topic=topic,
                            partition=partition.partition,
                            lag=lag,
                            current_offset=current_offset,
                            high_water_mark=high
                        )
                    else:
                        logger.debug(
                            "consumer_lag_checked",
                            topic=topic,
                            partition=partition.partition,
                            lag=lag
                        )

                except Exception as e:
                    logger.error(
                        "lag_monitoring_error",
                        topic=topic,
                        partition=partition.partition,
                        error=str(e)
                    )
                    kafka_consumer_errors_total.labels(
                        topic=topic,
                        error_type="lag_monitoring_error"
                    ).inc()

        except Exception as e:
            logger.error("consumer_lag_monitoring_failed", topic=topic, error=str(e))

    def consume_events(self, topic: str = "telematics-events", batch_size: int = 100, batch_timeout_ms: int = 1000):
        """
        Consume events from Kafka topic with batch processing for better throughput.

        Args:
            topic: Kafka topic name
            batch_size: Maximum number of events to process in a batch
            batch_timeout_ms: Maximum time to wait for batch to fill (milliseconds)
        """
        import time

        self.consumer.subscribe([topic])
        self.running = True

        logger.info(
            "kafka_consumer_started",
            topic=topic,
            batch_size=batch_size,
            batch_timeout_ms=batch_timeout_ms
        )

        db = SessionLocal()
        message_count = 0
        lag_check_interval = 100  # Check lag every 100 messages

        try:
            while self.running:
                # Collect messages for batch processing
                messages = []
                batch_start_time = time.time()

                # Collect messages until batch is full or timeout
                while len(messages) < batch_size and (time.time() - batch_start_time) * 1000 < batch_timeout_ms:
                    msg = self.consumer.poll(timeout=0.1)  # Short poll for batching

                    if msg is None:
                        continue

                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            logger.debug("reached_end_of_partition", partition=msg.partition())
                            continue
                        else:
                            logger.error("kafka_error", error=msg.error())
                            kafka_consumer_errors_total.labels(
                                topic=topic,
                                error_type=msg.error().name()
                            ).inc()
                            continue

                    messages.append(msg)
                    message_count += 1

                # Process batch if we have messages
                if messages:
                    self._process_batch(messages, db, topic)

                # Monitor consumer lag periodically
                if message_count % lag_check_interval == 0:
                    self._monitor_consumer_lag(topic)

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

    def _process_batch(self, messages, db: Session, topic: str):
        """Process a batch of Kafka messages."""
        import time
        
        batch_start_time = time.time()
        processed_count = 0
        failed_count = 0

        try:
            # Deserialize all messages
            events = []
            for msg in messages:
                event_data = self._deserialize_message(msg.value())
                if event_data:
                    events.append((event_data, msg))

            # Process events in batch
            for event_data, msg in events:
                try:
                    # Track metrics
                    kafka_messages_consumed_total.labels(topic=topic).inc()
                    start_time = time.time()
                    
                    # Store in database
                    self._store_event(event_data, db)
                    
                    # Real-time trip detection
                    try:
                        trip = detect_trip_from_event(event_data, db)
                        if trip:
                            logger.debug("trip_detected_from_event", trip_id=trip.trip_id, driver_id=event_data.get('driver_id'))
                    except Exception as trip_error:
                        # Don't fail event processing if trip detection fails
                        logger.warning("trip_detection_failed", error=str(trip_error))
                    
                    # Real-time ML analysis and publish to Redis pub/sub
                    try:
                        driver_id = event_data.get('driver_id')
                        if driver_id:
                            # Analyze event with ML model
                            analysis = analyze_event_realtime(event_data)
                            
                            if analysis:
                                from app.services.redis_client import get_redis_client
                                redis_client = get_redis_client()
                                if redis_client:
                                    import json
                                    
                                    # Store analysis in Redis cache (for fallback/backward compatibility)
                                    redis_client.setex(
                                        f"realtime:analysis:{driver_id}",
                                        60,  # 60 second TTL
                                        json.dumps(analysis)
                                    )
                                    
                                    # Calculate pricing
                                    pricing = calculate_realtime_premium(
                                        driver_id=driver_id,
                                        risk_score=analysis['risk_score'],
                                        behavior_metrics=analysis['behavior_metrics'],
                                        db=db
                                    )
                                    redis_client.setex(
                                        f"realtime:pricing:{driver_id}",
                                        60,
                                        json.dumps(pricing)
                                    )
                                    
                                    # Publish to Redis pub/sub channels for real-time updates
                                    # Channel 1: Analysis updates
                                    redis_client.publish(
                                        f"realtime:analysis:{driver_id}",
                                        json.dumps({
                                            'type': 'analysis',
                                            'driver_id': driver_id,
                                            'data': analysis,
                                            'timestamp': datetime.utcnow().isoformat()
                                        })
                                    )
                                    
                                    # Channel 2: Pricing updates
                                    redis_client.publish(
                                        f"realtime:pricing:{driver_id}",
                                        json.dumps({
                                            'type': 'pricing',
                                            'driver_id': driver_id,
                                            'data': pricing,
                                            'timestamp': datetime.utcnow().isoformat()
                                        })
                                    )
                                    
                                    # Channel 3: Raw event (for immediate display)
                                    redis_client.publish(
                                        f"realtime:events:{driver_id}",
                                        json.dumps({
                                            'type': 'event',
                                            'driver_id': driver_id,
                                            'data': event_data,
                                            'analysis': analysis,
                                            'timestamp': datetime.utcnow().isoformat()
                                        })
                                    )
                                    
                                    logger.debug(
                                        "realtime_updates_published",
                                        driver_id=driver_id,
                                        event_id=event_data.get('event_id')
                                    )
                    except Exception as analysis_error:
                        # Don't fail event processing if real-time analysis fails
                        logger.warning("realtime_analysis_failed", error=str(analysis_error))
                    
                    # Track successful processing
                    event_type = event_data.get('event_type', 'unknown')
                    events_processed_total.labels(event_type=event_type, status='success').inc()
                    
                    processing_time = time.time() - start_time
                    kafka_processing_duration_seconds.labels(topic=topic).observe(processing_time)
                    
                    processed_count += 1
                    
                except Exception as e:
                    # Track failed processing
                    event_type = event_data.get('event_type', 'unknown')
                    events_processed_total.labels(event_type=event_type, status='failed').inc()
                    logger.error(
                        "event_processing_failed",
                        event_id=event_data.get('event_id'),
                        error=str(e)
                    )
                    failed_count += 1

            # Commit batch offset
            if processed_count > 0:
                # Commit the last message offset for each partition
                offsets_to_commit = {}
                for msg in messages:
                    partition = msg.partition()
                    offset = msg.offset()
                    if partition not in offsets_to_commit or offset > offsets_to_commit[partition]:
                        offsets_to_commit[partition] = offset

                # Note: Auto-commit is enabled, but we log for monitoring
                batch_time = time.time() - batch_start_time
                logger.info(
                    "batch_processed",
                    batch_size=len(messages),
                    processed=processed_count,
                    failed=failed_count,
                    processing_time_ms=round(batch_time * 1000, 2),
                    throughput=round(processed_count / batch_time, 2) if batch_time > 0 else 0
                )

        except Exception as e:
            logger.error("batch_processing_error", error=str(e), batch_size=len(messages))

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

