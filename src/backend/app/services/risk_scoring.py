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
from app.services.redis_client import (
    cache_risk_score,
    get_cached_risk_score,
    cache_driver_statistics,
    update_feature_store
)
from app.services.ml_risk_scoring import calculate_ml_risk_score
from app.utils.metrics import (
    risk_score_calculations_total,
    risk_score_duration_seconds
)
import time


def calculate_risk_score_for_driver(
    driver_id: str,
    db: Session,
    period_days: int = 30
) -> Dict:
    """
    Calculate risk score for a driver using ML-based approach.
    
    This function now delegates to the ML-based risk scoring service
    which uses XGBoost and includes discount calculation.
    
    Args:
        driver_id: Driver ID
        db: Database session
        period_days: Number of days to look back
        
    Returns:
        Dictionary with risk_score, features, confidence, discount_info, etc.
    """
    # Use ML-based risk scoring (includes discount calculation)
    return calculate_ml_risk_score(driver_id, db, period_days)


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

