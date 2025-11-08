"""
Risk scoring service.
Calculates risk scores using ML model or rule-based approach.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd

from app.models.database import RiskScore, TelematicsEvent, Driver, Trip
from app.ml.model_loader import get_model


def calculate_risk_score_for_driver(
    driver_id: str,
    db: Session,
    period_days: int = 30
) -> Dict:
    """
    Calculate risk score for a driver from telematics events.
    
    Args:
        driver_id: Driver ID
        db: Database session
        period_days: Number of days to look back
        
    Returns:
        Dictionary with risk_score, features, confidence, etc.
    """
    model = get_model()
    
    # Get driver info
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise ValueError(f"Driver {driver_id} not found")
    
    # Get events from period
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)
    
    events = (
        db.query(TelematicsEvent)
        .filter(
            TelematicsEvent.driver_id == driver_id,
            TelematicsEvent.timestamp >= period_start,
            TelematicsEvent.timestamp <= period_end
        )
        .all()
    )
    
    if not events:
        # Return default score if no events
        return {
            'risk_score': 50.0,
            'confidence': 0.0,
            'features': {},
            'model_version': model.model_version
        }
    
    # Convert events to list of dicts
    events_data = []
    for event in events:
        events_data.append({
            'speed': event.speed or 0,
            'acceleration': event.acceleration or 0,
            'braking_force': event.braking_force or 0,
            'event_type': event.event_type or 'normal',
            'timestamp': event.timestamp,
            'latitude': event.latitude or 0,
            'longitude': event.longitude or 0,
        })
    
    # Get driver info for features
    driver_info = {
        'age': driver.date_of_birth and (datetime.utcnow().year - driver.date_of_birth.year) or 35,
        'years_licensed': driver.years_licensed or 10,
        'gender': driver.gender,
    }
    
    # Calculate features
    features = model.calculate_features_from_events(events_data, driver_info)
    
    # Predict risk score
    risk_score = model.predict(features)
    
    # Calculate confidence based on data quality
    total_events = len(events)
    confidence = min(1.0, total_events / 1000.0)  # More events = higher confidence
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_to_native(obj):
        """Convert numpy types to native Python types."""
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        try:
            if pd.isna(obj):
                return None
        except:
            pass
        return obj
    
    # Clean features dictionary
    clean_features = convert_to_native(features)
    
    return {
        'risk_score': float(risk_score),
        'confidence': float(confidence),
        'features': clean_features,
        'model_version': model.model_version,
        'events_used': total_events
    }


def save_risk_score(
    driver_id: str,
    risk_data: Dict,
    db: Session
) -> RiskScore:
    """
    Save risk score to database.
    
    Args:
        driver_id: Driver ID
        risk_data: Risk score data from calculate_risk_score_for_driver
        db: Database session
        
    Returns:
        RiskScore object
    """
    risk_score = RiskScore(
        driver_id=driver_id,
        risk_score=risk_data['risk_score'],
        confidence=risk_data['confidence'],
        model_version=risk_data['model_version'],
        features=risk_data['features'],
        calculation_date=datetime.utcnow()
    )
    
    db.add(risk_score)
    db.commit()
    db.refresh(risk_score)
    
    return risk_score

