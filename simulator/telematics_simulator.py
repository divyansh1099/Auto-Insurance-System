"""
Telematics Data Simulator

Generates realistic driving behavior data for testing the insurance system.
"""

import os
import json
import time
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from enum import Enum

import numpy as np
from faker import Faker
import structlog
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()
fake = Faker()


class DriverProfile(Enum):
    """Driver behavior profiles."""
    SAFE = "safe"
    AVERAGE = "average"
    RISKY = "risky"


class EventType(Enum):
    """Telematics event types."""
    NORMAL = "normal"
    HARSH_BRAKE = "harsh_brake"
    RAPID_ACCEL = "rapid_accel"
    SPEEDING = "speeding"
    HARSH_CORNER = "harsh_corner"
    PHONE_USAGE = "phone_usage"


class TripType(Enum):
    """Trip types."""
    COMMUTE = "commute"
    LEISURE = "leisure"
    BUSINESS = "business"


class Driver:
    """Represents a simulated driver with specific behavior patterns."""

    def __init__(self, driver_id: str, profile: DriverProfile):
        self.driver_id = driver_id
        self.device_id = f"DEV-{uuid.uuid4().hex[:8].upper()}"
        self.profile = profile
        self.home_location = (
            fake.latitude(),
            fake.longitude()
        )

        # Set behavior parameters based on profile
        if profile == DriverProfile.SAFE:
            self.speed_compliance = 0.95  # 95% within speed limit
            self.max_overspeed = 10  # mph
            self.harsh_brake_prob = 0.02
            self.rapid_accel_prob = 0.01
            self.night_driving_prob = 0.10
            self.phone_usage_prob = 0.02
        elif profile == DriverProfile.AVERAGE:
            self.speed_compliance = 0.80
            self.max_overspeed = 15
            self.harsh_brake_prob = 0.04
            self.rapid_accel_prob = 0.03
            self.night_driving_prob = 0.15
            self.phone_usage_prob = 0.08
        else:  # RISKY
            self.speed_compliance = 0.60
            self.max_overspeed = 25
            self.harsh_brake_prob = 0.08
            self.rapid_accel_prob = 0.06
            self.night_driving_prob = 0.25
            self.phone_usage_prob = 0.15

    def __repr__(self):
        return f"Driver({self.driver_id}, {self.profile.value})"


class Trip:
    """Represents a single trip."""

    def __init__(
        self,
        trip_id: str,
        driver: Driver,
        trip_type: TripType,
        start_time: datetime,
        duration_minutes: int,
        distance_miles: float
    ):
        self.trip_id = trip_id
        self.driver = driver
        self.trip_type = trip_type
        self.start_time = start_time
        self.duration_minutes = duration_minutes
        self.distance_miles = distance_miles
        self.start_location = driver.home_location
        self.end_location = self._generate_end_location()
        self.events: List[Dict] = []

    def _generate_end_location(self) -> Tuple[float, float]:
        """Generate realistic end location based on distance."""
        # Simplified: random point within distance radius
        lat_offset = (random.random() - 0.5) * (self.distance_miles / 69)  # 69 miles per degree latitude
        lon_offset = (random.random() - 0.5) * (self.distance_miles / 54.6)  # 54.6 miles per degree longitude (at 40° latitude)

        # Convert to float if Decimal
        start_lat = float(self.start_location[0])
        start_lon = float(self.start_location[1])

        return (
            start_lat + lat_offset,
            start_lon + lon_offset
        )

    def generate_events(self) -> List[Dict]:
        """Generate telematics events for this trip."""
        events = []

        # Calculate number of events (one per 10 seconds of driving)
        num_events = int((self.duration_minutes * 60) / 10)

        # Determine speed limit based on trip type
        if self.trip_type == TripType.COMMUTE:
            base_speed_limit = random.choice([35, 45, 55, 65])  # Mix of urban and highway
        elif self.trip_type == TripType.BUSINESS:
            base_speed_limit = random.choice([45, 55, 65])  # More highway
        else:  # LEISURE
            base_speed_limit = random.choice([25, 35, 45, 55])  # More varied

        current_time = self.start_time
        current_speed = 0
        trip_phone_usage = random.random() < self.driver.phone_usage_prob

        for i in range(num_events):
            # Interpolate location along trip
            progress = i / num_events
            # Convert to float if Decimal
            start_lat = float(self.start_location[0])
            start_lon = float(self.start_location[1])
            end_lat = float(self.end_location[0])
            end_lon = float(self.end_location[1])
            
            current_lat = start_lat + (end_lat - start_lat) * progress
            current_lon = start_lon + (end_lon - start_lon) * progress

            # Generate realistic speed profile
            if i < 3:  # Starting
                target_speed = min(25, base_speed_limit)
            elif i > num_events - 3:  # Stopping
                target_speed = 0
            else:  # Cruising
                target_speed = base_speed_limit

                # Random speed variations
                if random.random() > self.driver.speed_compliance:
                    target_speed += random.uniform(0, self.driver.max_overspeed)
                else:
                    target_speed += random.uniform(-5, 5)  # Minor variations

            # Smooth speed transitions
            speed_change = np.clip(target_speed - current_speed, -10, 10)
            current_speed = max(0, current_speed + speed_change)

            # Calculate acceleration (simplified)
            acceleration = speed_change / 10  # g-force approximation

            # Determine braking force
            braking_force = None
            if acceleration < -0.3:
                braking_force = abs(acceleration)

            # Determine event type
            event_type = EventType.NORMAL

            # Check for harsh braking
            if braking_force and braking_force > 0.4 and random.random() < self.driver.harsh_brake_prob:
                event_type = EventType.HARSH_BRAKE

            # Check for rapid acceleration
            elif acceleration > 0.35 and random.random() < self.driver.rapid_accel_prob:
                event_type = EventType.RAPID_ACCEL

            # Check for speeding
            elif current_speed > base_speed_limit + 15:
                event_type = EventType.SPEEDING

            # Check for phone usage
            elif trip_phone_usage and random.random() < 0.05:  # Occasional phone events during trip
                event_type = EventType.PHONE_USAGE

            # Create event
            event = {
                "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                "device_id": self.driver.device_id,
                "driver_id": self.driver.driver_id,
                "timestamp": int(current_time.timestamp() * 1000),  # milliseconds
                "latitude": round(current_lat, 6),
                "longitude": round(current_lon, 6),
                "speed": round(current_speed, 2),
                "acceleration": round(acceleration, 3),
                "braking_force": round(braking_force, 3) if braking_force else None,
                "heading": round(random.uniform(0, 360), 2),
                "altitude": round(random.uniform(0, 500), 2),
                "gps_accuracy": round(random.uniform(5, 15), 2),
                "event_type": event_type.value,
                "trip_id": self.trip_id
            }

            events.append(event)

            # Advance time
            current_time += timedelta(seconds=10)

        self.events = events
        return events


class TelematicsSimulator:
    """Main simulator class."""

    def __init__(self, num_drivers: int = 100, enable_kafka: bool = True):
        self.num_drivers = num_drivers
        self.enable_kafka = enable_kafka
        self.drivers = self._create_drivers()

        # Initialize Kafka producer if enabled
        self.producer = None
        self.avro_serializer = None
        if self.enable_kafka:
            self._init_kafka()

    def _create_drivers(self) -> List[Driver]:
        """Create a population of drivers with different profiles."""
        drivers = []

        # Distribution: 40% safe, 45% average, 15% risky
        safe_count = int(self.num_drivers * 0.40)
        average_count = int(self.num_drivers * 0.45)
        risky_count = self.num_drivers - safe_count - average_count

        driver_id = 1

        for _ in range(safe_count):
            drivers.append(Driver(f"DRV-{driver_id:04d}", DriverProfile.SAFE))
            driver_id += 1

        for _ in range(average_count):
            drivers.append(Driver(f"DRV-{driver_id:04d}", DriverProfile.AVERAGE))
            driver_id += 1

        for _ in range(risky_count):
            drivers.append(Driver(f"DRV-{driver_id:04d}", DriverProfile.RISKY))
            driver_id += 1

        logger.info(
            "drivers_created",
            total=self.num_drivers,
            safe=safe_count,
            average=average_count,
            risky=risky_count
        )

        return drivers

    def _init_kafka(self):
        """Initialize Kafka producer with Avro serialization."""
        try:
            # Kafka configuration
            kafka_config = {
                'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092'),
                'client.id': 'telematics-simulator',
                'acks': 'all',
                'compression.type': 'snappy',
                'linger.ms': 10,  # Batch messages for efficiency
                'batch.size': 32768  # 32KB batch size
            }

            self.producer = Producer(kafka_config)

            # Schema Registry configuration
            schema_registry_conf = {
                'url': os.getenv('SCHEMA_REGISTRY_URL', 'http://schema-registry:8081')
            }
            schema_registry_client = SchemaRegistryClient(schema_registry_conf)

            # Load Avro schema
            schema_path = os.getenv('SCHEMA_PATH', '/app/telematics_event.avsc')
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_str = f.read()
            else:
                # Fallback: inline schema
                schema_str = '''
                {
                  "type": "record",
                  "name": "TelematicsEvent",
                  "namespace": "com.insurance.telematics",
                  "fields": [
                    {"name": "event_id", "type": "string"},
                    {"name": "device_id", "type": "string"},
                    {"name": "driver_id", "type": "string"},
                    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
                    {"name": "latitude", "type": "double"},
                    {"name": "longitude", "type": "double"},
                    {"name": "speed", "type": "double"},
                    {"name": "acceleration", "type": "double"},
                    {"name": "braking_force", "type": ["null", "double"], "default": null},
                    {"name": "heading", "type": "double"},
                    {"name": "altitude", "type": ["null", "double"], "default": null},
                    {"name": "gps_accuracy", "type": "double"},
                    {"name": "event_type", "type": {"type": "enum", "name": "EventType", "symbols": ["normal", "harsh_brake", "rapid_accel", "speeding", "harsh_corner", "phone_usage"]}, "default": "normal"},
                    {"name": "trip_id", "type": ["null", "string"], "default": null}
                  ]
                }
                '''

            self.avro_serializer = AvroSerializer(
                schema_registry_client,
                schema_str,
                lambda event, ctx: event  # Event is already a dict
            )

            logger.info(
                "kafka_initialized",
                bootstrap_servers=kafka_config['bootstrap.servers'],
                schema_registry=schema_registry_conf['url']
            )

        except Exception as e:
            logger.error("kafka_initialization_failed", error=str(e))
            self.enable_kafka = False
            self.producer = None
            self.avro_serializer = None

    def _delivery_report(self, err, msg):
        """Kafka delivery callback."""
        if err is not None:
            logger.error('message_delivery_failed', error=str(err))
        elif msg is not None:
            logger.debug(
                'message_delivered',
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset()
            )

    def publish_event(self, event: Dict, topic: str = "telematics-events"):
        """Publish a single event to Kafka."""
        if not self.enable_kafka or not self.producer:
            return

        try:
            # Use driver_id as the key for partitioning
            key = event['driver_id']
            
            # Try Avro serialization first, fallback to JSON
            if self.avro_serializer:
                try:
                    serialized_value = self.avro_serializer(event, None)
                except Exception:
                    # Fallback to JSON if Avro fails
                    serialized_value = json.dumps(event).encode('utf-8')
            else:
                # Use JSON serialization as fallback
                serialized_value = json.dumps(event).encode('utf-8')

            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8'),
                value=serialized_value,
                on_delivery=self._delivery_report
            )

        except Exception as e:
            logger.error("event_publish_failed", event_id=event.get('event_id'), error=str(e))

    def publish_events_batch(self, events: List[Dict], topic: str = "telematics-events"):
        """Publish multiple events to Kafka."""
        if not self.enable_kafka or not self.producer:
            logger.warning("kafka_disabled", message="Events not published")
            return

        logger.info("publishing_events", count=len(events), topic=topic)

        for event in events:
            self.publish_event(event, topic)

        # Flush remaining messages
        remaining = self.producer.flush(timeout=30)
        if remaining > 0:
            logger.warning("messages_not_delivered", count=remaining)
        else:
            logger.info("all_messages_delivered", count=len(events))

    def generate_trip(self, driver: Driver, base_time: datetime) -> Trip:
        """Generate a single trip for a driver."""
        # Determine trip type and timing
        hour = base_time.hour
        is_weekday = base_time.weekday() < 5

        # Trip type probability
        if is_weekday and (7 <= hour <= 9 or 17 <= hour <= 19):
            trip_type = TripType.COMMUTE
        elif 9 <= hour <= 17:
            trip_type = TripType.BUSINESS if random.random() < 0.3 else TripType.LEISURE
        else:
            trip_type = TripType.LEISURE

        # Trip duration and distance
        if trip_type == TripType.COMMUTE:
            duration = int(random.gauss(25, 10))  # 15-35 minutes typical
            distance = duration * random.uniform(0.4, 0.8)  # 20-40 mph average
        elif trip_type == TripType.BUSINESS:
            duration = int(random.gauss(45, 20))  # Longer trips
            distance = duration * random.uniform(0.6, 1.0)  # Faster on highway
        else:  # LEISURE
            duration = int(random.gauss(20, 15))  # More varied
            distance = duration * random.uniform(0.3, 0.7)

        duration = max(5, duration)  # At least 5 minutes
        distance = max(1, distance)  # At least 1 mile

        trip_id = f"TRP-{uuid.uuid4().hex[:8].upper()}"

        return Trip(trip_id, driver, trip_type, base_time, duration, distance)

    def simulate_day(self, simulation_date: datetime, publish_to_kafka: bool = True) -> List[Dict]:
        """Simulate one day of driving for all drivers."""
        all_events = []

        for driver in self.drivers:
            # Determine number of trips for this driver (2-4 per day)
            num_trips = random.randint(2, 4)

            for trip_num in range(num_trips):
                # Generate trip start time
                if trip_num == 0:  # Morning commute/first trip
                    hour = random.randint(6, 9)
                elif trip_num == 1:  # Mid-day or lunch
                    hour = random.randint(11, 14)
                elif trip_num == 2:  # Evening commute
                    hour = random.randint(16, 19)
                else:  # Evening/night activity
                    hour = random.randint(19, 22)

                # Check night driving probability
                if hour >= 22 or hour <= 5:
                    if random.random() > driver.night_driving_prob:
                        continue  # Skip night trips based on driver profile

                trip_time = simulation_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )

                # Generate trip
                trip = self.generate_trip(driver, trip_time)
                events = trip.generate_events()
                all_events.extend(events)

                # Publish events to Kafka in real-time if enabled
                if publish_to_kafka and self.enable_kafka:
                    self.publish_events_batch(events)

        logger.info(
            "day_simulated",
            date=simulation_date.date().isoformat(),
            total_events=len(all_events),
            drivers=len(self.drivers),
            kafka_enabled=self.enable_kafka
        )

        return all_events

    def run_simulation(self, days: int = 7, output_file: Optional[str] = None,
                      publish_to_kafka: bool = True):
        """Run simulation for multiple days."""
        logger.info(
            "simulation_starting",
            days=days,
            drivers=len(self.drivers),
            kafka_enabled=self.enable_kafka
        )

        all_events = []
        start_date = datetime.now() - timedelta(days=days)

        for day in range(days):
            simulation_date = start_date + timedelta(days=day)
            day_events = self.simulate_day(simulation_date, publish_to_kafka)
            all_events.extend(day_events)

        # Save to file if output_file is specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(all_events, f, indent=2)
            logger.info("events_saved_to_file", file=output_file)

        logger.info(
            "simulation_completed",
            total_events=len(all_events),
            days=days,
            kafka_published=publish_to_kafka and self.enable_kafka
        )

        return all_events

    def run_continuous(self, interval_seconds: int = 10):
        """Run simulator continuously, generating events at regular intervals."""
        logger.info("continuous_simulation_starting", interval=interval_seconds)

        try:
            while True:
                # Generate events for current time
                current_time = datetime.now()
                events = self.simulate_day(current_time, publish_to_kafka=True)

                logger.info(
                    "continuous_batch_generated",
                    events=len(events),
                    timestamp=current_time.isoformat()
                )

                # Wait before next batch
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("continuous_simulation_stopped")
            if self.producer:
                self.producer.flush()
        except Exception as e:
            logger.error("continuous_simulation_error", error=str(e))
            raise


def main():
    """Main entry point."""
    # Configuration from environment variables
    num_drivers = int(os.getenv("NUM_DRIVERS", "10"))
    simulation_days = int(os.getenv("SIMULATION_DAYS", "1"))
    output_file = os.getenv("OUTPUT_FILE", None)  # Optional file output
    enable_kafka = os.getenv("ENABLE_KAFKA", "true").lower() == "true"
    continuous_mode = os.getenv("CONTINUOUS_MODE", "false").lower() == "true"

    logger.info(
        "simulator_starting",
        num_drivers=num_drivers,
        simulation_days=simulation_days,
        enable_kafka=enable_kafka,
        continuous_mode=continuous_mode
    )

    # Create simulator
    simulator = TelematicsSimulator(num_drivers=num_drivers, enable_kafka=enable_kafka)

    # Run simulation
    if continuous_mode:
        # Continuous mode - generates events forever
        logger.info("running_continuous_mode")
        simulator.run_continuous()
    else:
        # Batch mode - generate events for specified days
        events = simulator.run_simulation(
            days=simulation_days,
            output_file=output_file,
            publish_to_kafka=enable_kafka
        )

        logger.info(
            "simulator_finished",
            total_events=len(events),
            avg_events_per_driver=len(events) / num_drivers if num_drivers > 0 else 0
        )


if __name__ == "__main__":
    main()
