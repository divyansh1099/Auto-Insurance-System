"""
Model loader for risk scoring.
Loads trained XGBoost model and provides inference.
"""
import os
import pickle
import sys
from typing import Dict, Optional
import numpy as np
import pandas as pd

# Import feature engineering - use inline implementation to avoid path issues
import pandas as pd
import numpy as np


class RiskScoringModel:
    """Risk scoring model wrapper."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_names = []
        self.model_version = "v1.0"
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            # Use rule-based scoring as fallback
            self.model = None
    
    def load_model(self, model_path: str):
        """Load trained model from file."""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.feature_names = model_data.get('feature_names', [])
                self.model_version = model_data.get('version', 'v1.0')
        except Exception as e:
            print(f"Warning: Could not load model from {model_path}: {e}")
            print("Falling back to rule-based scoring")
            self.model = None
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict risk score from features.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Risk score (0-100)
        """
        if self.model is not None:
            # Use ML model
            try:
                # Convert features to DataFrame
                feature_df = pd.DataFrame([features])
                
                # Ensure all required features are present
                for feature_name in self.feature_names:
                    if feature_name not in feature_df.columns:
                        feature_df[feature_name] = 0.0
                
                # Reorder columns to match training
                feature_df = feature_df[self.feature_names]
                
                # Predict
                prediction = self.model.predict(feature_df)[0]
                return float(np.clip(prediction, 0, 100))
            except Exception as e:
                print(f"Error in model prediction: {e}")
                # Fall back to rule-based
                return self._rule_based_score(features)
        else:
            # Use rule-based scoring
            return self._rule_based_score(features)
    
    def _rule_based_score(self, features: Dict[str, float]) -> float:
        """Calculate risk score using rule-based approach."""
        weights = {
            'harsh_braking_per_100mi': 0.25,
            'rapid_accel_per_100mi': 0.15,
            'speeding_incidents_per_100mi': 0.20,
            'night_driving_pct': 0.10,
            'max_speed_recorded': 0.15,
        }
        
        risk_score = 0
        for feature, weight in weights.items():
            if feature in features:
                if feature == 'max_speed_recorded':
                    normalized = min(features[feature] / 100, 1.0)
                elif 'pct' in feature:
                    normalized = features[feature] / 100
                elif 'per_100mi' in feature:
                    normalized = min(features[feature] / 10, 1.0)
                else:
                    normalized = min(features[feature] / 50, 1.0)
                risk_score += normalized * weight * 100
        
        return min(max(risk_score, 0), 100)
    
    def calculate_features_from_events(self, events_data: list, driver_info: Optional[Dict] = None) -> Dict[str, float]:
        """
        Calculate features from telematics events.
        
        Args:
            events_data: List of telematics event dictionaries
            driver_info: Optional driver demographic information
            
        Returns:
            Dictionary of calculated features
        """
        # Convert events to trip-like structure for feature engineering
        # Group events by trip_id or create single trip
        trips_data = []
        current_trip = {
            'distance_miles': 0,
            'avg_speed': 0,
            'max_speed': 0,
            'harsh_braking_count': 0,
            'rapid_accel_count': 0,
            'speeding_count': 0,
            'harsh_corner_count': 0,
            'phone_usage_detected': False,
        }
        
        speeds = []
        for event in events_data:
            if event.get('speed'):
                speeds.append(event['speed'])
            if event.get('event_type') == 'harsh_brake':
                current_trip['harsh_braking_count'] += 1
            elif event.get('event_type') == 'rapid_accel':
                current_trip['rapid_accel_count'] += 1
            elif event.get('event_type') == 'speeding':
                current_trip['speeding_count'] += 1
            elif event.get('event_type') == 'harsh_corner':
                current_trip['harsh_corner_count'] += 1
            elif event.get('event_type') == 'phone_usage':
                current_trip['phone_usage_detected'] = True
        
        if speeds:
            current_trip['avg_speed'] = sum(speeds) / len(speeds)
            current_trip['max_speed'] = max(speeds)
        
        # Estimate distance (rough: assume events are 10 seconds apart)
        if current_trip['avg_speed'] > 0:
            total_hours = (len(events_data) * 10) / 3600
            current_trip['distance_miles'] = current_trip['avg_speed'] * total_hours
        
        trips_data.append(current_trip)
        
        # Calculate features from trips data
        features = self._calculate_features_from_trips(trips_data, driver_info)
        
        # Add default values for missing features that model might expect
        default_features = {
            'avg_speed_overall': features.get('avg_speed_overall', 0),
            'max_speed_recorded': features.get('max_speed_recorded', 0),
            'speed_variance': features.get('speed_variance', 0),
            'speeding_incidents_per_100mi': features.get('speeding_incidents_per_100mi', 0),
            'harsh_braking_per_100mi': features.get('harsh_braking_per_100mi', 0),
            'rapid_accel_per_100mi': features.get('rapid_accel_per_100mi', 0),
            'smooth_driving_score': features.get('smooth_driving_score', 50),
            'night_driving_pct': features.get('night_driving_pct', 0),
            'rush_hour_pct': features.get('rush_hour_pct', 0),
            'weekend_driving_pct': features.get('weekend_driving_pct', 0),
            'late_night_driving_pct': features.get('late_night_driving_pct', 0),
            'avg_trip_duration_min': features.get('avg_trip_duration_min', 0),
            'avg_trip_distance_miles': features.get('avg_trip_distance_miles', 0),
            'total_trips': features.get('total_trips', 1),
            'trip_consistency_score': features.get('trip_consistency_score', 50),
            'total_miles': features.get('total_miles', 0),
            'phone_usage_trip_pct': features.get('phone_usage_trip_pct', 0),
            'harsh_corner_per_100mi': features.get('harsh_corner_per_100mi', 0),
            'age': driver_info.get('age', 35) if driver_info else 35,
            'years_licensed': driver_info.get('years_licensed', 10) if driver_info else 10,
            'vehicle_age': 5,  # Default
            'vehicle_safety_rating': 4,  # Default
        }
        
        # Merge with calculated features
        default_features.update(features)
        
        return default_features
    
    def _calculate_features_from_trips(self, trips_data: list, driver_info: Optional[Dict] = None) -> Dict[str, float]:
        """Calculate features from trips data."""
        if not trips_data:
            return {}
        
        trips_df = pd.DataFrame(trips_data)
        
        total_miles = trips_df['distance_miles'].sum() if 'distance_miles' in trips_df.columns else 0
        total_trips = len(trips_data)
        
        features = {
            'avg_speed_overall': float(trips_df['avg_speed'].mean()) if 'avg_speed' in trips_df.columns and not trips_df['avg_speed'].empty else 0.0,
            'max_speed_recorded': float(trips_df['max_speed'].max()) if 'max_speed' in trips_df.columns and not trips_df['max_speed'].empty else 0.0,
            'speed_variance': float(trips_df['avg_speed'].std()) if 'avg_speed' in trips_df.columns and not trips_df['avg_speed'].empty and not trips_df['avg_speed'].std() != trips_df['avg_speed'].std() else 0.0,
            'speeding_incidents_per_100mi': (trips_df['speeding_count'].sum() / total_miles * 100) if total_miles > 0 else 0,
            'harsh_braking_per_100mi': (trips_df['harsh_braking_count'].sum() / total_miles * 100) if total_miles > 0 else 0,
            'rapid_accel_per_100mi': (trips_df['rapid_accel_count'].sum() / total_miles * 100) if total_miles > 0 else 0,
            'harsh_corner_per_100mi': (trips_df['harsh_corner_count'].sum() / total_miles * 100) if total_miles > 0 else 0,
            'smooth_driving_score': max(0, 100 - (trips_df['harsh_braking_count'].sum() + trips_df['rapid_accel_count'].sum()) * 3),
            'total_miles': total_miles,
            'total_trips': total_trips,
            'avg_trip_distance_miles': trips_df['distance_miles'].mean() if 'distance_miles' in trips_df.columns else 0,
            'phone_usage_trip_pct': (trips_df['phone_usage_detected'].sum() / total_trips * 100) if total_trips > 0 else 0,
        }
        
        # Add driver info
        if driver_info:
            features['age'] = driver_info.get('age', 35)
            features['years_licensed'] = driver_info.get('years_licensed', 10)
            features['vehicle_age'] = 5 # Default
            features['vehicle_safety_rating'] = 4 # Default
            
        # --- Interaction Features (Must match src/ml/feature_engineering.py) ---
        
        # Interaction: Speeding during night
        speeding = features.get('speeding_incidents_per_100mi', 0)
        night_pct = features.get('night_driving_pct', 0)
        features['interaction_speed_night'] = speeding * night_pct / 100

        # Interaction: Harsh braking during rush hour
        braking = features.get('harsh_braking_per_100mi', 0)
        rush_pct = features.get('rush_hour_pct', 0)
        features['interaction_braking_rush'] = braking * rush_pct / 100
        
        # Age risk factor
        age = features.get('age', 35)
        features['is_young_driver'] = 1.0 if age < 25 else 0.0
        features['is_senior_driver'] = 1.0 if age > 65 else 0.0
        
        # Vehicle risk interaction
        vehicle_age = features.get('vehicle_age', 5)
        safety_rating = features.get('vehicle_safety_rating', 4)
        features['vehicle_risk_factor'] = (vehicle_age / 15) * (6 - safety_rating)
        
        return features


# Global model instance
_model_instance: Optional[RiskScoringModel] = None


def get_model() -> RiskScoringModel:
    """Get or create model instance."""
    global _model_instance
    
    if _model_instance is None:
        # Try to load from common locations
        possible_paths = [
            '/app/ml/models/risk_model_v1.0.pkl',
            '/app/../ml/models/risk_model_v1.0.pkl',
            os.path.join(os.path.dirname(__file__), '../../..', 'ml', 'models', 'risk_model_v1.0.pkl'),
        ]
        
        model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        _model_instance = RiskScoringModel(model_path)
    
    return _model_instance

