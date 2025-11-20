"""
ML-Based Risk Scoring Service

Uses XGBoost model to calculate driver risk scores.
Integrates with discount calculator for premium adjustments.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
import structlog

from app.models.database import RiskScore, TelematicsEvent, Driver, Trip
from app.ml.model_loader import get_model
from app.services.discount_calculator import calculate_discount_score
from app.utils.metrics import (
    risk_score_calculations_total,
    risk_score_duration_seconds
)
import time

logger = structlog.get_logger()


def calculate_ml_risk_score(
    driver_id: str,
    db: Session,
    period_days: int = 30
) -> Dict:
    """
    Calculate risk score using XGBoost ML model.
    
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
            'model_version': model.model_version,
            'discount_info': None
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
    
    # Track calculation start time
    calc_start_time = time.time()
    
    # Calculate features
    features = model.calculate_features_from_events(events_data, driver_info)
    
    # Predict risk score using XGBoost
    risk_score = model.predict(features)
    
    # Track metrics
    risk_score_calculations_total.labels(driver_id=driver_id).inc()
    calc_duration = time.time() - calc_start_time
    risk_score_duration_seconds.observe(calc_duration)
    
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
    
    # Calculate discount information
    discount_info = calculate_discount_score(driver_id, db, period_days=90)
    
    result = {
        'risk_score': float(risk_score),
        'confidence': float(confidence),
        'features': clean_features,
        'model_version': model.model_version,
        'events_used': total_events,
        'discount_info': discount_info
    }
    
    logger.info(
        "ml_risk_score_calculated",
        driver_id=driver_id,
        risk_score=float(risk_score),
        discount_percent=discount_info.get('discount_percent', 0),
        clean_trips=discount_info.get('clean_trips', 0)
    )
    
    return result


def calculate_premium_with_discount(
    driver_id: str,
    base_premium: float,
    db: Session
) -> Dict:
    """
    Calculate final premium with discount applied.
    
    Args:
        driver_id: Driver ID
        base_premium: Base premium before discount
        db: Database session
        
    Returns:
        Dictionary with premium breakdown
    """
    # Get risk score
    risk_data = calculate_ml_risk_score(driver_id, db)
    risk_score = risk_data['risk_score']
    
    # Get discount information
    discount_info = risk_data.get('discount_info', {})
    discount_percent = discount_info.get('discount_percent', 0.0)
    
    # Apply risk multiplier (from risk score)
    # Risk score 0-100 maps to multiplier 0.7-1.5
    risk_multiplier = 0.7 + (risk_score / 100) * 0.8  # 0.7 to 1.5
    
    # Calculate premium after risk adjustment
    risk_adjusted_premium = base_premium * risk_multiplier
    
    # Apply discount (only if eligible)
    if discount_info.get('eligible_for_discount', False):
        discount_amount = risk_adjusted_premium * (discount_percent / 100)
        final_premium = risk_adjusted_premium - discount_amount
    else:
        discount_amount = 0.0
        final_premium = risk_adjusted_premium
    
    return {
        'driver_id': driver_id,
        'base_premium': round(base_premium, 2),
        'risk_score': round(risk_score, 2),
        'risk_multiplier': round(risk_multiplier, 3),
        'risk_adjusted_premium': round(risk_adjusted_premium, 2),
        'discount_percent': round(discount_percent, 2),
        'discount_amount': round(discount_amount, 2),
        'final_premium': round(final_premium, 2),
        'monthly_premium': round(final_premium / 12, 2),
        'discount_info': discount_info,
        'calculated_at': datetime.utcnow().isoformat()
    }


def calculate_ml_risk_score_batch(
    driver_ids: List[str],
    db: Session,
    period_days: int = 30
) -> Dict[str, Dict]:
    """
    Calculate risk scores for multiple drivers in batch.
    Optimized for performance with single DB query and vectorized operations.
    
    Args:
        driver_ids: List of driver IDs to process
        db: Database session
        period_days: Number of days to look back
        
    Returns:
        Dictionary mapping driver_id to risk_data
        
    Example:
        results = calculate_ml_risk_score_batch(['DRV-0001', 'DRV-0002'], db)
        # {'DRV-0001': {...}, 'DRV-0002': {...}}
    """
    if not driver_ids:
        return {}
    
    model = get_model()
    batch_start_time = time.time()
    
    logger.info(
        "batch_risk_scoring_started",
        driver_count=len(driver_ids),
        period_days=period_days
    )
    
    # Calculate period
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)
    
    # Single query to get all drivers
    drivers = (
        db.query(Driver)
        .filter(Driver.driver_id.in_(driver_ids))
        .all()
    )
    driver_map = {d.driver_id: d for d in drivers}
    
    # Single query to get all events for all drivers
    all_events = (
        db.query(TelematicsEvent)
        .filter(
            TelematicsEvent.driver_id.in_(driver_ids),
            TelematicsEvent.timestamp >= period_start,
            TelematicsEvent.timestamp <= period_end
        )
        .all()
    )
    
    # Group events by driver
    events_by_driver = {}
    for event in all_events:
        if event.driver_id not in events_by_driver:
            events_by_driver[event.driver_id] = []
        events_by_driver[event.driver_id].append(event)
    
    # Process each driver
    results = {}
    for driver_id in driver_ids:
        driver = driver_map.get(driver_id)
        if not driver:
            logger.warning("driver_not_found_in_batch", driver_id=driver_id)
            results[driver_id] = {
                'error': 'Driver not found',
                'risk_score': None
            }
            continue
        
        events = events_by_driver.get(driver_id, [])
        
        if not events:
            # Return default score if no events
            results[driver_id] = {
                'risk_score': 50.0,
                'confidence': 0.0,
                'features': {},
                'model_version': model.model_version,
                'discount_info': None,
                'events_used': 0
            }
            continue
        
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
        
        # Calculate confidence
        total_events = len(events)
        confidence = min(1.0, total_events / 1000.0)
        
        # Convert numpy types to native Python types
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
        
        clean_features = convert_to_native(features)
        
        # Calculate discount information
        discount_info = calculate_discount_score(driver_id, db, period_days=90)
        
        results[driver_id] = {
            'risk_score': float(risk_score),
            'confidence': float(confidence),
            'features': clean_features,
            'model_version': model.model_version,
            'events_used': total_events,
            'discount_info': discount_info
        }
        
        # Track metrics for each driver
        risk_score_calculations_total.labels(driver_id=driver_id).inc()
    
    batch_duration = time.time() - batch_start_time
    
    logger.info(
        "batch_risk_scoring_completed",
        driver_count=len(driver_ids),
        successful=len([r for r in results.values() if 'error' not in r]),
        duration_seconds=round(batch_duration, 2),
        avg_per_driver=round(batch_duration / len(driver_ids), 3)
    )
    
    return results
