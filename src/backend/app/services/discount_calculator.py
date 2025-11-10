"""
Discount Calculator Service

Calculates insurance discounts based on driver behavior with strict rules:
- Maximum discount: 45%
- Any trip with even a single risk factor is excluded from discount consideration
- Each trip with risk factors costs -5 points
- Discounts are hard to achieve (requires many clean trips)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
import structlog

from app.models.database import Trip, TelematicsEvent

logger = structlog.get_logger()


# Risk factors that disqualify a trip from discount consideration
RISK_FACTORS = {
    'harsh_brake',
    'rapid_accel',
    'speeding',
    'harsh_corner',
    'phone_usage'
}


def has_risk_factor(trip: Trip) -> bool:
    """
    Check if a trip has any risk factor.
    
    Args:
        trip: Trip object
        
    Returns:
        True if trip has any risk factor, False otherwise
    """
    # Check trip-level risk indicators
    if trip.harsh_braking_count and trip.harsh_braking_count > 0:
        return True
    if trip.rapid_accel_count and trip.rapid_accel_count > 0:
        return True
    if trip.speeding_count and trip.speeding_count > 0:
        return True
    if trip.harsh_corner_count and trip.harsh_corner_count > 0:
        return True
    if trip.phone_usage_detected:
        return True
    
    return False


def evaluate_trip_risk_factors(trip: Trip, db: Session) -> Dict[str, int]:
    """
    Evaluate all risk factors for a trip by checking events.
    
    Args:
        trip: Trip object
        db: Database session
        
    Returns:
        Dictionary with count of each risk factor
    """
    risk_counts = {
        'harsh_brake': 0,
        'rapid_accel': 0,
        'speeding': 0,
        'harsh_corner': 0,
        'phone_usage': 0
    }
    
    # Check trip-level counts first
    if trip.harsh_braking_count:
        risk_counts['harsh_brake'] = trip.harsh_braking_count
    if trip.rapid_accel_count:
        risk_counts['rapid_accel'] = trip.rapid_accel_count
    if trip.speeding_count:
        risk_counts['speeding'] = trip.speeding_count
    if trip.harsh_corner_count:
        risk_counts['harsh_corner'] = trip.harsh_corner_count
    if trip.phone_usage_detected:
        risk_counts['phone_usage'] = 1
    
    # Also check events for this trip if available
    if trip.start_time:
        events = db.query(TelematicsEvent).filter(
            TelematicsEvent.driver_id == trip.driver_id,
            TelematicsEvent.timestamp >= trip.start_time,
            TelematicsEvent.timestamp <= (trip.end_time or trip.start_time + timedelta(hours=2))
        ).all()
        
        for event in events:
            event_type = event.event_type
            if event_type in risk_counts:
                risk_counts[event_type] += 1
    
    return risk_counts


def calculate_discount_score(
    driver_id: str,
    db: Session,
    period_days: int = 90
) -> Dict[str, any]:
    """
    Calculate discount score for a driver based on clean trips.
    
    Rules:
    - Only trips with ZERO risk factors count toward discount
    - Each trip with risk factors costs -5 points
    - Discount is calculated from clean trips only
    - Maximum discount: 45%
    
    Args:
        driver_id: Driver ID
        db: Database session
        period_days: Number of days to look back
        
    Returns:
        Dictionary with discount details
    """
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)
    
    # Get all trips in the period
    trips = db.query(Trip).filter(
        Trip.driver_id == driver_id,
        Trip.start_time >= period_start,
        Trip.start_time <= period_end
    ).order_by(Trip.start_time.desc()).all()
    
    if not trips:
        return {
            'discount_percent': 0.0,
            'discount_score': 0.0,
            'clean_trips': 0,
            'total_trips': 0,
            'trips_with_risk': 0,
            'penalty_points': 0,
            'eligible_for_discount': False,
            'message': 'No trips found in evaluation period'
        }
    
    # Separate trips into clean and risky
    clean_trips = []
    risky_trips = []
    
    for trip in trips:
        if has_risk_factor(trip):
            risky_trips.append(trip)
        else:
            clean_trips.append(trip)
    
    total_trips = len(trips)
    num_clean_trips = len(clean_trips)
    num_risky_trips = len(risky_trips)
    
    # Calculate penalty points (each risky trip costs -5 points)
    penalty_points = num_risky_trips * -5
    
    # Calculate discount score based on clean trips only
    # Discount formula: Based on percentage of clean trips and total clean trips
    # Hard to achieve: Need many clean trips to get meaningful discount
    
    if num_clean_trips == 0:
        discount_percent = 0.0
        discount_score = penalty_points
        eligible = False
    else:
        # Calculate discount based on:
        # 1. Percentage of clean trips (weight: 30%)
        # 2. Total number of clean trips (weight: 70%)
        # 3. Penalty points reduce the score
        
        clean_trip_percentage = (num_clean_trips / total_trips) * 100 if total_trips > 0 else 0
        
        # Base score from clean trip percentage (max 30 points)
        percentage_score = min(30, clean_trip_percentage * 0.3)
        
        # Base score from number of clean trips (max 70 points)
        # Need at least 30 clean trips to start getting meaningful discount
        # Scale: 30 trips = 20%, 50 trips = 30%, 75 trips = 40%, 100+ trips = 45%
        if num_clean_trips < 30:
            clean_trips_score = (num_clean_trips / 30) * 20  # 0-20 points
        elif num_clean_trips < 50:
            clean_trips_score = 20 + ((num_clean_trips - 30) / 20) * 10  # 20-30 points
        elif num_clean_trips < 75:
            clean_trips_score = 30 + ((num_clean_trips - 50) / 25) * 10  # 30-40 points
        else:
            clean_trips_score = 40 + min(5, ((num_clean_trips - 75) / 25) * 5)  # 40-45 points
        
        # Combine scores
        base_score = percentage_score + clean_trips_score
        
        # Apply penalty points
        discount_score = base_score + penalty_points
        
        # Convert to discount percentage (0-45%)
        discount_percent = max(0.0, min(45.0, discount_score))
        
        # Must have at least 20 clean trips to be eligible
        eligible = num_clean_trips >= 20 and discount_percent > 0
    
    # Calculate total miles from clean trips only
    clean_miles = sum(trip.distance_miles or 0 for trip in clean_trips)
    total_miles = sum(trip.distance_miles or 0 for trip in trips)
    
    result = {
        'discount_percent': round(discount_percent, 2),
        'discount_score': round(discount_score, 2),
        'clean_trips': num_clean_trips,
        'total_trips': total_trips,
        'trips_with_risk': num_risky_trips,
        'penalty_points': penalty_points,
        'clean_trip_percentage': round((num_clean_trips / total_trips * 100) if total_trips > 0 else 0, 2),
        'clean_miles': round(clean_miles, 2),
        'total_miles': round(total_miles, 2),
        'eligible_for_discount': eligible,
        'period_days': period_days,
        'evaluation_start': period_start.isoformat(),
        'evaluation_end': period_end.isoformat()
    }
    
    if not eligible:
        if num_clean_trips < 20:
            result['message'] = f'Need at least 20 clean trips. Currently have {num_clean_trips} clean trips.'
        elif discount_percent == 0:
            result['message'] = f'Penalty points ({penalty_points}) offset all discount points.'
        else:
            result['message'] = 'Not eligible for discount based on current driving behavior.'
    else:
        result['message'] = f'Eligible for {discount_percent:.1f}% discount based on {num_clean_trips} clean trips.'
    
    logger.info(
        "discount_calculated",
        driver_id=driver_id,
        discount_percent=discount_percent,
        clean_trips=num_clean_trips,
        total_trips=total_trips,
        penalty_points=penalty_points
    )
    
    return result


def get_trip_risk_breakdown(
    driver_id: str,
    db: Session,
    period_days: int = 90
) -> Dict[str, any]:
    """
    Get detailed breakdown of risk factors by trip.
    
    Args:
        driver_id: Driver ID
        db: Database session
        period_days: Number of days to look back
        
    Returns:
        Dictionary with trip-by-trip risk breakdown
    """
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)
    
    trips = db.query(Trip).filter(
        Trip.driver_id == driver_id,
        Trip.start_time >= period_start,
        Trip.start_time <= period_end
    ).order_by(Trip.start_time.desc()).all()
    
    trip_breakdowns = []
    for trip in trips:
        risk_factors = evaluate_trip_risk_factors(trip, db)
        has_risk = any(count > 0 for count in risk_factors.values())
        
        trip_breakdowns.append({
            'trip_id': trip.trip_id,
            'start_time': trip.start_time.isoformat() if trip.start_time else None,
            'distance_miles': trip.distance_miles,
            'has_risk_factors': has_risk,
            'risk_factors': risk_factors,
            'disqualified_from_discount': has_risk,
            'penalty_points': -5 if has_risk else 0
        })
    
    return {
        'driver_id': driver_id,
        'period_days': period_days,
        'total_trips': len(trips),
        'trip_breakdowns': trip_breakdowns
    }

