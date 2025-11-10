"""
Real-Time Stream Processor for Telematics Events

Validates, cleans, and enriches telematics events in near real-time.
"""

from typing import Dict, Optional, List
from datetime import datetime
import structlog

logger = structlog.get_logger()


class EventValidator:
    """Validates telematics event data."""

    @staticmethod
    def validate_event(event: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate a telematics event.
        
        Returns:
            (is_valid, error_message)
        """
        # Required fields
        required_fields = ['device_id', 'driver_id', 'timestamp', 'latitude', 'longitude']
        for field in required_fields:
            if field not in event or event[field] is None:
                return False, f"Missing required field: {field}"

        # Validate coordinates
        lat = event.get('latitude')
        lon = event.get('longitude')
        if not (-90 <= lat <= 90):
            return False, f"Invalid latitude: {lat}"
        if not (-180 <= lon <= 180):
            return False, f"Invalid longitude: {lon}"

        # Validate speed (reasonable range: 0-200 mph)
        speed = event.get('speed')
        if speed is not None and (speed < 0 or speed > 200):
            return False, f"Invalid speed: {speed} mph"

        # Validate acceleration (reasonable range: -2g to 2g)
        acceleration = event.get('acceleration')
        if acceleration is not None and (acceleration < -2.0 or acceleration > 2.0):
            return False, f"Invalid acceleration: {acceleration} g"

        # Validate timestamp (not too far in future or past)
        timestamp = event.get('timestamp')
        if isinstance(timestamp, int):
            event_time = datetime.fromtimestamp(timestamp / 1000.0)
        elif isinstance(timestamp, datetime):
            event_time = timestamp
        else:
            return False, f"Invalid timestamp format: {timestamp}"

        now = datetime.utcnow()
        time_diff = abs((now - event_time).total_seconds())
        
        # Allow events up to 1 hour in future (clock drift) and up to 7 days in past
        if time_diff > 7 * 24 * 3600:  # 7 days
            return False, f"Timestamp too old: {event_time}"
        if (event_time - now).total_seconds() > 3600:  # 1 hour future
            return False, f"Timestamp too far in future: {event_time}"

        return True, None

    @staticmethod
    def validate_batch(events: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """
        Validate a batch of events.
        
        Returns:
            (valid_events, invalid_events)
        """
        valid_events = []
        invalid_events = []

        for event in events:
            is_valid, error = EventValidator.validate_event(event)
            if is_valid:
                valid_events.append(event)
            else:
                event['_validation_error'] = error
                invalid_events.append(event)
                logger.warning(
                    "event_validation_failed",
                    event_id=event.get('event_id'),
                    error=error
                )

        return valid_events, invalid_events


class EventCleaner:
    """Cleans and normalizes telematics event data."""

    @staticmethod
    def clean_event(event: Dict) -> Dict:
        """
        Clean and normalize an event.
        
        - Removes outliers
        - Normalizes values
        - Adds missing fields with defaults
        """
        cleaned = event.copy()

        # Normalize event_type
        event_type = cleaned.get('event_type', 'normal').lower()
        valid_types = ['normal', 'harsh_brake', 'rapid_accel', 'speeding', 'harsh_corner', 'phone_usage']
        if event_type not in valid_types:
            cleaned['event_type'] = 'normal'
            logger.debug("normalized_event_type", original=event.get('event_type'), normalized='normal')

        # Remove extreme outliers for speed
        speed = cleaned.get('speed')
        if speed is not None:
            if speed < 0:
                cleaned['speed'] = 0.0
            elif speed > 200:  # Cap at 200 mph
                cleaned['speed'] = 200.0
                logger.debug("capped_speed", original=speed, capped=200.0)

        # Remove extreme outliers for acceleration
        acceleration = cleaned.get('acceleration')
        if acceleration is not None:
            if acceleration < -2.0:
                cleaned['acceleration'] = -2.0
            elif acceleration > 2.0:
                cleaned['acceleration'] = 2.0
                logger.debug("capped_acceleration", original=acceleration, capped=2.0)

        # Ensure GPS accuracy is reasonable
        gps_accuracy = cleaned.get('gps_accuracy')
        if gps_accuracy is None:
            cleaned['gps_accuracy'] = 10.0  # Default 10 meters
        elif gps_accuracy < 0 or gps_accuracy > 100:
            cleaned['gps_accuracy'] = min(100.0, max(0.0, gps_accuracy))

        # Normalize altitude (set to 0 if negative or missing)
        altitude = cleaned.get('altitude')
        if altitude is None or altitude < 0:
            cleaned['altitude'] = 0.0

        # Ensure heading is 0-360
        heading = cleaned.get('heading')
        if heading is not None:
            cleaned['heading'] = heading % 360

        # Add processing timestamp
        cleaned['_processed_at'] = datetime.utcnow().isoformat()

        return cleaned

    @staticmethod
    def clean_batch(events: List[Dict]) -> List[Dict]:
        """Clean a batch of events."""
        return [EventCleaner.clean_event(event) for event in events]


class EventEnricher:
    """Enriches events with additional metadata."""

    @staticmethod
    def enrich_event(event: Dict) -> Dict:
        """
        Enrich event with additional metadata.
        
        - Adds trip detection hints
        - Calculates derived metrics
        - Adds geolocation context
        """
        enriched = event.copy()

        # Calculate speed category
        speed = enriched.get('speed', 0)
        if speed == 0:
            speed_category = 'stopped'
        elif speed < 25:
            speed_category = 'low'
        elif speed < 55:
            speed_category = 'medium'
        else:
            speed_category = 'high'
        enriched['_speed_category'] = speed_category

        # Detect potential trip start/end
        # (This is a hint for trip aggregation service)
        if speed == 0:
            enriched['_trip_hint'] = 'potential_stop'
        elif speed > 5 and enriched.get('_trip_hint') != 'in_trip':
            enriched['_trip_hint'] = 'potential_start'

        # Calculate risk indicators
        risk_indicators = []
        if enriched.get('event_type') == 'harsh_brake':
            risk_indicators.append('harsh_braking')
        if enriched.get('event_type') == 'rapid_accel':
            risk_indicators.append('aggressive_acceleration')
        if enriched.get('event_type') == 'speeding':
            risk_indicators.append('speeding')
        if enriched.get('event_type') == 'phone_usage':
            risk_indicators.append('distracted_driving')
        
        enriched['_risk_indicators'] = risk_indicators

        # Add time-based context
        timestamp = enriched.get('timestamp')
        if isinstance(timestamp, int):
            event_time = datetime.fromtimestamp(timestamp / 1000.0)
        elif isinstance(timestamp, datetime):
            event_time = timestamp
        else:
            event_time = datetime.utcnow()

        hour = event_time.hour
        weekday = event_time.weekday()

        # Time of day category
        if 6 <= hour < 12:
            time_category = 'morning'
        elif 12 <= hour < 18:
            time_category = 'afternoon'
        elif 18 <= hour < 22:
            time_category = 'evening'
        else:
            time_category = 'night'

        enriched['_time_category'] = time_category
        enriched['_is_weekend'] = weekday >= 5
        enriched['_is_rush_hour'] = (7 <= hour < 9) or (17 <= hour < 19)

        return enriched

    @staticmethod
    def enrich_batch(events: List[Dict]) -> List[Dict]:
        """Enrich a batch of events."""
        return [EventEnricher.enrich_event(event) for event in events]


class StreamProcessor:
    """Main stream processor that orchestrates validation, cleaning, and enrichment."""

    def __init__(self):
        self.validator = EventValidator()
        self.cleaner = EventCleaner()
        self.enricher = EventEnricher()

    def process_event(self, event: Dict) -> Optional[Dict]:
        """
        Process a single event through the pipeline.
        
        Returns:
            Processed event or None if invalid
        """
        # Validate
        is_valid, error = self.validator.validate_event(event)
        if not is_valid:
            logger.warning("event_validation_failed", event_id=event.get('event_id'), error=error)
            return None

        # Clean
        cleaned = self.cleaner.clean_event(event)

        # Enrich
        enriched = self.enricher.enrich_event(cleaned)

        return enriched

    def process_batch(self, events: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """
        Process a batch of events.
        
        Returns:
            (processed_events, invalid_events)
        """
        # Validate batch
        valid_events, invalid_events = self.validator.validate_batch(events)

        # Clean valid events
        cleaned_events = self.cleaner.clean_batch(valid_events)

        # Enrich cleaned events
        processed_events = self.enricher.enrich_batch(cleaned_events)

        logger.info(
            "batch_processed",
            total=len(events),
            processed=len(processed_events),
            invalid=len(invalid_events)
        )

        return processed_events, invalid_events


# Global processor instance
_processor_instance: Optional[StreamProcessor] = None


def get_processor() -> StreamProcessor:
    """Get or create processor instance."""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = StreamProcessor()
    return _processor_instance


def process_telematics_event(event: Dict) -> Optional[Dict]:
    """Convenience function to process a single event."""
    processor = get_processor()
    return processor.process_event(event)


def process_telematics_events_batch(events: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """Convenience function to process a batch of events."""
    processor = get_processor()
    return processor.process_batch(events)

