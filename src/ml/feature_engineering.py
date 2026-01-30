"""
Feature Engineering for Risk Scoring Model

Calculates comprehensive features from raw telematics data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List


class FeatureEngineer:
    """Feature engineering for driver risk assessment."""

    def __init__(self):
        self.feature_names = []

    def calculate_speed_features(self, trips_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate speed-related features."""
        if trips_df.empty:
            return {}

        features = {
            'avg_speed_overall': trips_df['avg_speed'].mean(),
            'max_speed_recorded': trips_df['max_speed'].max(),
            'speed_variance': trips_df['avg_speed'].std(),
            'speeding_incidents_per_100mi': (
                trips_df['speeding_count'].sum() / trips_df['distance_miles'].sum() * 100
                if trips_df['distance_miles'].sum() > 0 else 0
            )
        }

        return features

    def calculate_braking_accel_features(self, trips_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate braking and acceleration features."""
        if trips_df.empty:
            return {}

        total_miles = trips_df['distance_miles'].sum()

        features = {
            'harsh_braking_per_100mi': (
                trips_df['harsh_braking_count'].sum() / total_miles * 100
                if total_miles > 0 else 0
            ),
            'rapid_accel_per_100mi': (
                trips_df['rapid_accel_count'].sum() / total_miles * 100
                if total_miles > 0 else 0
            ),
            'smooth_driving_score': 100 - min(
                (trips_df['harsh_braking_count'].sum() + trips_df['rapid_accel_count'].sum()) / total_miles * 10,
                100
            ) if total_miles > 0 else 50
        }

        return features

    def calculate_time_pattern_features(self, trips_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate time-based pattern features."""
        if trips_df.empty:
            return {}

        trips_df['hour'] = pd.to_datetime(trips_df['start_time']).dt.hour
        trips_df['day_of_week'] = pd.to_datetime(trips_df['start_time']).dt.dayofweek

        total_trips = len(trips_df)
        total_miles = trips_df['distance_miles'].sum()

        # Night driving (10 PM - 5 AM)
        night_trips = trips_df[(trips_df['hour'] >= 22) | (trips_df['hour'] <= 5)]
        night_driving_pct = (night_trips['distance_miles'].sum() / total_miles * 100
                             if total_miles > 0 else 0)

        # Rush hour driving (7-9 AM, 5-7 PM)
        rush_hour_trips = trips_df[
            ((trips_df['hour'] >= 7) & (trips_df['hour'] <= 9)) |
            ((trips_df['hour'] >= 17) & (trips_df['hour'] <= 19))
        ]
        rush_hour_pct = (rush_hour_trips['distance_miles'].sum() / total_miles * 100
                         if total_miles > 0 else 0)

        # Weekend driving
        weekend_trips = trips_df[trips_df['day_of_week'] >= 5]
        weekend_driving_pct = (weekend_trips['distance_miles'].sum() / total_miles * 100
                               if total_miles > 0 else 0)

        # Late night driving (12 AM - 4 AM)
        late_night_trips = trips_df[(trips_df['hour'] >= 0) & (trips_df['hour'] <= 4)]
        late_night_pct = (late_night_trips['distance_miles'].sum() / total_miles * 100
                          if total_miles > 0 else 0)

        features = {
            'night_driving_pct': night_driving_pct,
            'rush_hour_pct': rush_hour_pct,
            'weekend_driving_pct': weekend_driving_pct,
            'late_night_driving_pct': late_night_pct
        }

        return features

    def calculate_trip_pattern_features(self, trips_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate trip pattern features."""
        if trips_df.empty:
            return {}

        features = {
            'avg_trip_duration_min': trips_df['duration_minutes'].mean(),
            'avg_trip_distance_miles': trips_df['distance_miles'].mean(),
            'total_trips': len(trips_df),
            'trip_consistency_score': 100 - min(
                trips_df['duration_minutes'].std() / trips_df['duration_minutes'].mean() * 100
                if trips_df['duration_minutes'].mean() > 0 else 50,
                100
            )
        }

        return features

    def calculate_risk_features(self, trips_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate aggregate risk features."""
        if trips_df.empty:
            return {}

        total_miles = trips_df['distance_miles'].sum()
        total_trips = len(trips_df)

        # Phone usage
        phone_usage_trips = trips_df[trips_df['phone_usage_detected'] == True].shape[0]

        features = {
            'total_miles': total_miles,
            'phone_usage_trip_pct': (phone_usage_trips / total_trips * 100
                                     if total_trips > 0 else 0),
            'harsh_corner_per_100mi': (
                trips_df['harsh_corner_count'].sum() / total_miles * 100
                if total_miles > 0 else 0
            )
        }

        return features


    def calculate_interaction_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate interaction and non-linear features."""
        interactions = {}
        
        # Interaction: Speeding during night
        # High speed at night is riskier than high speed during day
        speeding = features.get('speeding_incidents_per_100mi', 0)
        night_pct = features.get('night_driving_pct', 0)
        interactions['interaction_speed_night'] = speeding * night_pct / 100

        # Interaction: Harsh braking during rush hour
        # Braking in heavy traffic might be more common but high frequent harsh braking is risky
        braking = features.get('harsh_braking_per_100mi', 0)
        rush_pct = features.get('rush_hour_pct', 0)
        interactions['interaction_braking_rush'] = braking * rush_pct / 100
        
        # Age risk factor (Young drivers < 25 are statistically riskier)
        age = features.get('age', 35)
        interactions['is_young_driver'] = 1.0 if age < 25 else 0.0
        interactions['is_senior_driver'] = 1.0 if age > 65 else 0.0
        
        # Vehicle risk interaction
        vehicle_age = features.get('vehicle_age', 5)
        safety_rating = features.get('vehicle_safety_rating', 3)
        # Older cars with low safety ratings are riskier
        interactions['vehicle_risk_factor'] = (vehicle_age / 15) * (6 - safety_rating)
        
        return interactions

    def engineer_features(self, trips_df: pd.DataFrame, driver_demographics: Dict = None) -> Dict[str, float]:
        """
        Engineer all features for a driver.

        Args:
            trips_df: DataFrame with trip data for the driver
            driver_demographics: Optional dict with demographic information

        Returns:
            Dictionary of engineered features
        """
        if trips_df.empty:
            return {}

        # Calculate all feature groups
        speed_features = self.calculate_speed_features(trips_df)
        braking_accel_features = self.calculate_braking_accel_features(trips_df)
        time_pattern_features = self.calculate_time_pattern_features(trips_df)
        trip_pattern_features = self.calculate_trip_pattern_features(trips_df)
        risk_features = self.calculate_risk_features(trips_df)

        # Combine base features
        base_features = {
            **speed_features,
            **braking_accel_features,
            **time_pattern_features,
            **trip_pattern_features,
            **risk_features
        }

        # Add demographic features if available
        if driver_demographics:
            base_features.update({
                'age': driver_demographics.get('age', 30),
                'years_licensed': driver_demographics.get('years_licensed', 5),
                'vehicle_age': driver_demographics.get('vehicle_age', 5),
                'vehicle_safety_rating': driver_demographics.get('vehicle_safety_rating', 3)
            })
            
        # Calculate interaction features
        interaction_features = self.calculate_interaction_features(base_features)
        
        # Combine all
        all_features = {**base_features, **interaction_features}

        return all_features

    def create_risk_score_target(self, features: Dict[str, float]) -> float:
        """
        Create risk score target from features (for initial model training).
        
        This is a weighted combination of key risk metrics.
        In production, this would be based on actual claims data.
        """
        weights = {
            'harsh_braking_per_100mi': 0.20,
            'rapid_accel_per_100mi': 0.10,
            'speeding_incidents_per_100mi': 0.15,
            'night_driving_pct': 0.05,
            'max_speed_recorded': 0.10,
            'phone_usage_trip_pct': 0.10,
            'late_night_driving_pct': 0.05,
            'interaction_speed_night': 0.10,  # New
            'interaction_braking_rush': 0.05, # New
            'is_young_driver': 5.0,           # New (Absolute adder, not weight in loop if treated differently, but here we treat as keys)
            'vehicle_risk_factor': 2.0        # New
        }

        risk_score = 0
        
        # Handle special binary/categorical features separately or normalize them
        if features.get('is_young_driver', 0) > 0:
            risk_score += 15.0 # Penalty for young drivers
            
        if features.get('is_senior_driver', 0) > 0:
            risk_score += 5.0 # Slight penalty for senior drivers

        for feature, weight in weights.items():
            if feature in features and feature not in ['is_young_driver', 'vehicle_risk_factor']:
                # Normalize each feature to 0-1 range (simplified)
                if feature == 'max_speed_recorded':
                    normalized = min(features[feature] / 120, 1.0) # Adjusted max
                elif 'pct' in feature:
                    normalized = features[feature] / 100
                elif 'per_100mi' in feature:
                    normalized = min(features[feature] / 15, 1.0)
                elif 'interaction' in feature:
                    normalized = min(features[feature] / 10, 1.0) # Approximate normalization
                else:
                    normalized = min(features[feature] / 50, 1.0)

                risk_score += normalized * weight * 100
        
        # Add vehicle risk
        risk_score += features.get('vehicle_risk_factor', 0) * 3.0

        return min(max(risk_score, 0), 100)  # Clip to 0-100


def calculate_driver_features(trips_data: List[Dict], driver_info: Dict = None) -> Dict[str, float]:
    """
    Calculate features for a single driver.

    Args:
        trips_data: List of trip dictionaries
        driver_info: Optional driver demographic information

    Returns:
        Dictionary of calculated features
    """
    # Convert to DataFrame
    trips_df = pd.DataFrame(trips_data)

    # Create feature engineer
    engineer = FeatureEngineer()

    # Calculate features
    features = engineer.engineer_features(trips_df, driver_info)

    return features


if __name__ == "__main__":
    # Example usage
    sample_trips = [
        {
            'trip_id': 'TRP-001',
            'start_time': '2024-11-01 08:00:00',
            'duration_minutes': 25,
            'distance_miles': 15,
            'avg_speed': 35,
            'max_speed': 55,
            'harsh_braking_count': 2,
            'rapid_accel_count': 1,
            'speeding_count': 3,
            'harsh_corner_count': 1,
            'phone_usage_detected': False
        },
        {
            'trip_id': 'TRP-002',
            'start_time': '2024-11-01 17:30:00',
            'duration_minutes': 30,
            'distance_miles': 18,
            'avg_speed': 40,
            'max_speed': 65,
            'harsh_braking_count': 1,
            'rapid_accel_count': 0,
            'speeding_count': 5,
            'harsh_corner_count': 0,
            'phone_usage_detected': True
        }
    ]

    driver_info = {
        'age': 35,
        'years_licensed': 15,
        'vehicle_age': 3,
        'vehicle_safety_rating': 5
    }

    features = calculate_driver_features(sample_trips, driver_info)
    print("Calculated Features:")
    for key, value in features.items():
        print(f"  {key}: {value:.2f}")
