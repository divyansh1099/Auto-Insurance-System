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

        # Combine all features
        all_features = {
            **speed_features,
            **braking_accel_features,
            **time_pattern_features,
            **trip_pattern_features,
            **risk_features
        }

        # Add demographic features if available
        if driver_demographics:
            all_features.update({
                'age': driver_demographics.get('age', 30),
                'years_licensed': driver_demographics.get('years_licensed', 5),
                'vehicle_age': driver_demographics.get('vehicle_age', 5),
                'vehicle_safety_rating': driver_demographics.get('vehicle_safety_rating', 3)
            })

        return all_features

    def create_risk_score_target(self, features: Dict[str, float]) -> float:
        """
        Create risk score target from features (for initial model training).

        This is a weighted combination of key risk metrics.
        In production, this would be based on actual claims data.
        """
        weights = {
            'harsh_braking_per_100mi': 0.25,
            'rapid_accel_per_100mi': 0.15,
            'speeding_incidents_per_100mi': 0.20,
            'night_driving_pct': 0.10,
            'max_speed_recorded': 0.15,
            'phone_usage_trip_pct': 0.10,
            'late_night_driving_pct': 0.05
        }

        risk_score = 0

        for feature, weight in weights.items():
            if feature in features:
                # Normalize each feature to 0-1 range (simplified)
                if feature == 'max_speed_recorded':
                    normalized = min(features[feature] / 100, 1.0)
                elif 'pct' in feature:
                    normalized = features[feature] / 100
                elif 'per_100mi' in feature:
                    normalized = min(features[feature] / 10, 1.0)
                else:
                    normalized = min(features[feature] / 50, 1.0)

                risk_score += normalized * weight * 100

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
