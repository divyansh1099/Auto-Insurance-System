"""
Real-Time ML Inference Service

Processes telematics events in real-time to:
- Analyze driving behavior
- Calculate risk scores
- Detect safety issues
- Update dynamic pricing
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import structlog
import numpy as np

from app.ml.model_loader import get_model
from app.services.redis_client import get_redis_client, update_feature_store

logger = structlog.get_logger()


class RealTimeBehaviorAnalyzer:
    """Analyzes driving behavior in real-time from streaming events."""

    def __init__(self, window_size: int = 100):
        """
        Initialize analyzer.
        
        Args:
            window_size: Number of recent events to keep in memory for analysis
        """
        self.window_size = window_size
        self.model = get_model()
        self.event_windows: Dict[str, deque] = {}  # driver_id -> deque of events
        self.redis_client = get_redis_client()

    def add_event(self, event: Dict) -> Dict:
        """
        Process a new event and return real-time analysis.
        
        Args:
            event: Telematics event dictionary
            
        Returns:
            Analysis results with risk score, behavior metrics, alerts
        """
        driver_id = event.get('driver_id')
        if not driver_id:
            return {}

        # Maintain sliding window of events
        if driver_id not in self.event_windows:
            self.event_windows[driver_id] = deque(maxlen=self.window_size)
        
        self.event_windows[driver_id].append(event)

        # Get recent events for analysis
        recent_events = list(self.event_windows[driver_id])
        
        # Calculate real-time features
        features = self._calculate_realtime_features(recent_events, driver_id)
        
        # Get ML model prediction
        risk_score = self.model.predict(features)
        
        # Detect safety issues
        safety_alerts = self._detect_safety_issues(recent_events)
        
        # Calculate behavior metrics
        behavior_metrics = self._calculate_behavior_metrics(recent_events)
        
        # Update feature store
        update_feature_store(driver_id, features)
        
        return {
            'driver_id': driver_id,
            'risk_score': float(risk_score),
            'safety_score': float(max(0, 100 - risk_score)),
            'safety_alerts': safety_alerts,
            'behavior_metrics': behavior_metrics,
            'features': features,
            'timestamp': datetime.utcnow().isoformat(),
            'events_analyzed': len(recent_events)
        }

    def _calculate_realtime_features(self, events: List[Dict], driver_id: str) -> Dict:
        """Calculate features from recent events for ML model."""
        if not events:
            return {}

        # Convert to format expected by model
        events_data = []
        for event in events:
            events_data.append({
                'speed': event.get('speed', 0),
                'acceleration': event.get('acceleration', 0),
                'braking_force': event.get('braking_force', 0),
                'event_type': event.get('event_type', 'normal'),
                'timestamp': event.get('timestamp', datetime.utcnow()),
                'latitude': event.get('latitude', 0),
                'longitude': event.get('longitude', 0),
            })

        # Use model's feature calculation
        features = self.model.calculate_features_from_events(events_data, {})
        
        return features

    def _detect_safety_issues(self, events: List[Dict]) -> List[Dict]:
        """Detect immediate safety issues from recent events."""
        alerts = []
        
        if not events:
            return alerts

        # Get last 10 events (last ~100 seconds)
        recent = events[-10:] if len(events) >= 10 else events
        
        # Check for harsh braking
        harsh_brakes = [e for e in recent if e.get('event_type') == 'harsh_brake']
        if len(harsh_brakes) >= 2:
            alerts.append({
                'type': 'harsh_braking',
                'severity': 'high',
                'message': f'{len(harsh_brakes)} harsh braking events detected',
                'timestamp': datetime.utcnow().isoformat()
            })

        # Check for rapid acceleration
        rapid_accels = [e for e in recent if e.get('event_type') == 'rapid_accel']
        if len(rapid_accels) >= 3:
            alerts.append({
                'type': 'aggressive_acceleration',
                'severity': 'medium',
                'message': f'{len(rapid_accels)} rapid acceleration events',
                'timestamp': datetime.utcnow().isoformat()
            })

        # Check for speeding
        speeding_events = [e for e in recent if e.get('event_type') == 'speeding']
        if len(speeding_events) >= 2:
            max_speed = max([e.get('speed', 0) for e in speeding_events])
            alerts.append({
                'type': 'speeding',
                'severity': 'high',
                'message': f'Speeding detected: {max_speed:.0f} mph',
                'timestamp': datetime.utcnow().isoformat()
            })

        # Check for phone usage
        phone_usage = [e for e in recent if e.get('event_type') == 'phone_usage']
        if phone_usage:
            alerts.append({
                'type': 'distracted_driving',
                'severity': 'high',
                'message': 'Phone usage detected while driving',
                'timestamp': datetime.utcnow().isoformat()
            })

        # Check for excessive speed
        speeds = [e.get('speed', 0) for e in recent if e.get('speed')]
        if speeds:
            max_speed = max(speeds)
            if max_speed > 80:
                alerts.append({
                    'type': 'excessive_speed',
                    'severity': 'high',
                    'message': f'Excessive speed: {max_speed:.0f} mph',
                    'timestamp': datetime.utcnow().isoformat()
                })

        return alerts

    def _calculate_behavior_metrics(self, events: List[Dict]) -> Dict:
        """Calculate real-time behavior metrics."""
        if not events:
            return {}

        speeds = [e.get('speed', 0) for e in events if e.get('speed')]
        accelerations = [e.get('acceleration', 0) for e in events if e.get('acceleration')]
        
        # Count event types
        event_counts = {}
        for event in events:
            event_type = event.get('event_type', 'normal')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            'current_speed': speeds[-1] if speeds else 0,
            'avg_speed': float(np.mean(speeds)) if speeds else 0,
            'max_speed': float(np.max(speeds)) if speeds else 0,
            'avg_acceleration': float(np.mean(accelerations)) if accelerations else 0,
            'harsh_braking_count': event_counts.get('harsh_brake', 0),
            'rapid_accel_count': event_counts.get('rapid_accel', 0),
            'speeding_count': event_counts.get('speeding', 0),
            'phone_usage_count': event_counts.get('phone_usage', 0),
            'total_events': len(events)
        }

    def get_current_analysis(self, driver_id: str) -> Optional[Dict]:
        """Get current analysis for a driver."""
        if driver_id not in self.event_windows:
            return None
        
        events = list(self.event_windows[driver_id])
        if not events:
            return None

        features = self._calculate_realtime_features(events, driver_id)
        risk_score = self.model.predict(features)
        safety_alerts = self._detect_safety_issues(events)
        behavior_metrics = self._calculate_behavior_metrics(events)

        return {
            'driver_id': driver_id,
            'risk_score': float(risk_score),
            'safety_score': float(max(0, 100 - risk_score)),
            'safety_alerts': safety_alerts,
            'behavior_metrics': behavior_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }

    def clear_driver_data(self, driver_id: str):
        """Clear stored data for a driver (e.g., when trip ends)."""
        if driver_id in self.event_windows:
            del self.event_windows[driver_id]


# Global analyzer instance
_analyzer_instance: Optional[RealTimeBehaviorAnalyzer] = None


def get_analyzer() -> RealTimeBehaviorAnalyzer:
    """Get or create analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = RealTimeBehaviorAnalyzer()
    return _analyzer_instance


def analyze_event_realtime(event: Dict) -> Dict:
    """Convenience function to analyze an event in real-time."""
    analyzer = get_analyzer()
    return analyzer.add_event(event)

