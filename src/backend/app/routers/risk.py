"""
Risk scoring endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, case
from datetime import datetime, timedelta, date
from typing import List, Optional
import random

from app.models.database import get_db, User, RiskScore, Trip, TelematicsEvent
from app.models.schemas import (
    RiskScoreResponse,
    RiskScoreBreakdown,
    RiskScoreHistory,
    RiskCategory,
    FeatureImportance,
    RiskProfileSummaryResponse,
    RiskScoreTrendResponse,
    RiskScoreTrendPoint,
    RiskFactorBreakdownResponse,
    BatchRiskCalculateRequest
)
from app.utils.auth import get_current_user
from app.services.redis_client import get_cached_risk_score
from app.utils.cache import cache_response

router = APIRouter()


def calculate_risk_category(score: float) -> RiskCategory:
    """Calculate risk category from score."""
    if score <= 20:
        return RiskCategory.EXCELLENT
    elif score <= 40:
        return RiskCategory.GOOD
    elif score <= 60:
        return RiskCategory.AVERAGE
    elif score <= 80:
        return RiskCategory.BELOW_AVERAGE
    else:
        return RiskCategory.HIGH_RISK


def generate_recommendations(score: float, features: dict) -> List[str]:
    """Generate personalized recommendations based on risk score."""
    recommendations = []

    if features.get("harsh_braking_rate", 0) > 3:
        recommendations.append("Try to maintain smoother braking by anticipating stops earlier")

    if features.get("speeding_rate", 0) > 5:
        recommendations.append("Reduce speeding incidents to improve your risk score")

    if features.get("night_driving_pct", 0) > 20:
        recommendations.append("Consider reducing night driving when possible for better safety")

    if features.get("rapid_accel_rate", 0) > 3:
        recommendations.append("Practice gradual acceleration for better fuel economy and safety")

    if score > 60:
        recommendations.append("Complete a defensive driving course for potential discounts")

    return recommendations


@router.get("/{driver_id}/score", response_model=RiskScoreResponse)
async def get_risk_score(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    recalculate: bool = False
):
    """Get current risk score for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's risk score"
        )

    # Check cache first (unless recalculating)
    if not recalculate:
        cached_score = get_cached_risk_score(driver_id)
        if cached_score:
            # Get latest score from DB for metadata
            latest_score = (
                db.query(RiskScore)
                .filter(RiskScore.driver_id == driver_id)
                .order_by(RiskScore.calculation_date.desc())
                .first()
            )
            if latest_score:
                return RiskScoreResponse(
                    driver_id=driver_id,
                    risk_score=cached_score,
                    risk_category=calculate_risk_category(cached_score),
                    confidence=latest_score.confidence,
                    calculated_at=latest_score.calculation_date
                )

    # Get the latest risk score
    latest_score = (
        db.query(RiskScore)
        .filter(RiskScore.driver_id == driver_id)
        .order_by(RiskScore.calculation_date.desc())
        .first()
    )

    # If no score exists or recalculate requested, calculate new score
    if not latest_score or recalculate:
        try:
            from app.services.risk_scoring import calculate_risk_score_for_driver, save_risk_score
            
            # Calculate new risk score
            risk_data = calculate_risk_score_for_driver(driver_id, db, period_days=30)
            
            # Save to database
            latest_score = save_risk_score(driver_id, risk_data, db)
        except Exception as e:
            # If calculation fails and no existing score, return error
            if not latest_score:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error calculating risk score: {str(e)}"
                )
            # Otherwise use existing score

    return RiskScoreResponse(
        driver_id=driver_id,
        risk_score=latest_score.risk_score,
        risk_category=calculate_risk_category(latest_score.risk_score),
        confidence=latest_score.confidence,
        calculated_at=latest_score.calculation_date
    )


@router.get("/{driver_id}/breakdown", response_model=RiskScoreBreakdown)
@cache_response(ttl=300, key_prefix="risk_breakdown")
async def get_risk_breakdown(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed risk score breakdown with SHAP explanations."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's risk score"
        )

    # Get the latest risk score
    latest_score = (
        db.query(RiskScore)
        .filter(RiskScore.driver_id == driver_id)
        .order_by(RiskScore.calculation_date.desc())
        .first()
    )

    if not latest_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk score found for this driver"
        )

    # Extract features and SHAP values
    features = latest_score.features or {}
    shap_vals = latest_score.shap_values or {}

    # Create feature importance list
    feature_importances = [
        FeatureImportance(
            feature=feature_name,
            value=features.get(feature_name, 0),
            importance=shap_vals.get(feature_name, 0)
        )
        for feature_name in features.keys()
    ]

    # Sort by absolute importance
    feature_importances.sort(key=lambda x: abs(x.importance), reverse=True)

    # Generate recommendations
    recommendations = generate_recommendations(latest_score.risk_score, features)

    return RiskScoreBreakdown(
        driver_id=driver_id,
        risk_score=latest_score.risk_score,
        risk_category=calculate_risk_category(latest_score.risk_score),
        confidence=latest_score.confidence,
        model_version=latest_score.model_version,
        calculated_at=latest_score.calculation_date,
        features=features,
        feature_importances=feature_importances[:10],  # Top 10 features
        recommendations=recommendations
    )


@router.get("/{driver_id}/history", response_model=RiskScoreHistory)
@cache_response(ttl=600, key_prefix="risk_history")
async def get_risk_history(
    driver_id: str,
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get historical risk scores for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's risk history"
        )

    # Get historical scores
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    scores = (
        db.query(RiskScore)
        .filter(
            RiskScore.driver_id == driver_id,
            RiskScore.calculation_date >= cutoff_date
        )
        .order_by(RiskScore.calculation_date.asc())
        .all()
    )

    if not scores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk score history found for this driver"
        )

    # Convert to response format
    score_responses = [
        RiskScoreResponse(
            driver_id=driver_id,
            risk_score=score.risk_score,
            risk_category=calculate_risk_category(score.risk_score),
            confidence=score.confidence,
            calculated_at=score.calculation_date
        )
        for score in scores
    ]

    # Determine trend
    if len(scores) >= 2:
        first_score = scores[0].risk_score
        last_score = scores[-1].risk_score
        score_change = last_score - first_score

        if score_change < -5:
            trend = "improving"
        elif score_change > 5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return RiskScoreHistory(
        driver_id=driver_id,
        scores=score_responses,
        trend=trend
    )


@router.get("/{driver_id}/recommendations")
@cache_response(ttl=600, key_prefix="risk_recommendations")
async def get_recommendations(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get personalized driving recommendations."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's recommendations"
        )

    # Get the latest risk score
    latest_score = (
        db.query(RiskScore)
        .filter(RiskScore.driver_id == driver_id)
        .order_by(RiskScore.calculation_date.desc())
        .first()
    )

    if not latest_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk score found for this driver"
        )

    features = latest_score.features or {}
    recommendations = generate_recommendations(latest_score.risk_score, features)

    return {
        "driver_id": driver_id,
        "risk_score": latest_score.risk_score,
        "recommendations": recommendations,
        "generated_at": datetime.utcnow()
    }


@router.get("/{driver_id}/risk-profile-summary", response_model=RiskProfileSummaryResponse)
@cache_response(ttl=180, key_prefix="risk_profile_summary")
async def get_risk_profile_summary(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get risk profile summary for Risk Profile page."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's risk profile"
        )
    
    # Get latest risk score
    latest_score = (
        db.query(RiskScore)
        .filter(RiskScore.driver_id == driver_id)
        .order_by(RiskScore.calculation_date.desc())
        .first()
    )
    
    if not latest_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk score found for this driver"
        )
    
    # Get previous score for trend calculation
    previous_score = (
        db.query(RiskScore)
        .filter(
            RiskScore.driver_id == driver_id,
            RiskScore.calculation_date < latest_score.calculation_date
        )
        .order_by(RiskScore.calculation_date.desc())
        .first()
    )
    
    # Calculate change and trend
    change_from_previous = 0.0
    trend_status = "stable"
    previous_score_value = None
    
    if previous_score:
        previous_score_value = previous_score.risk_score
        change_from_previous = latest_score.risk_score - previous_score.risk_score
        
        if change_from_previous < -5:
            trend_status = "improving"
        elif change_from_previous > 5:
            trend_status = "declining"
        else:
            trend_status = "stable"
    
    # Calculate behavior score from actual trip scores (last 30 days)
    period_start = datetime.utcnow() - timedelta(days=30)
    recent_trips = (
        db.query(Trip)
        .filter(
            Trip.driver_id == driver_id,
            Trip.start_time >= period_start
        )
        .all()
    )
    
    behavior_score = 50.0  # Default
    if recent_trips:
        trip_scores = []
        for trip in recent_trips:
            if trip.trip_score is not None:
                trip_scores.append(trip.trip_score)
            else:
                # Calculate from incidents if trip_score not available
                score = 100 - (
                    (trip.harsh_braking_count or 0) * 5 +
                    (trip.rapid_accel_count or 0) * 3 +
                    (trip.speeding_count or 0) * 8 +
                    (trip.harsh_corner_count or 0) * 4
                )
                trip_scores.append(max(0, min(100, score)))
        
        if trip_scores:
            behavior_score = sum(trip_scores) / len(trip_scores)
    
    # Calculate trip statistics from ALL trips (not just last 30 days)
    # Verify we're filtering by the correct driver_id (for debugging)
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's trip statistics"
        )
    
    # Total trips
    total_trips = db.query(func.count(Trip.trip_id)).filter(Trip.driver_id == driver_id).scalar() or 0
    
    # Total miles
    total_miles = (
        db.query(func.sum(Trip.distance_miles))
        .filter(Trip.driver_id == driver_id)
        .scalar() or 0.0
    )
    
    # Average trip score (calculate from all trips)
    avg_score_query = (
        db.query(func.avg(
            case(
                (Trip.trip_score.isnot(None), Trip.trip_score),
                else_=100 - (
                    func.coalesce(Trip.harsh_braking_count, 0) * 5 +
                    func.coalesce(Trip.rapid_accel_count, 0) * 3 +
                    func.coalesce(Trip.speeding_count, 0) * 8 +
                    func.coalesce(Trip.harsh_corner_count, 0) * 4
                )
            )
        ))
        .filter(Trip.driver_id == driver_id)
    )
    avg_trip_score = avg_score_query.scalar()
    
    # Get all trips for performance metrics calculation
    all_trips = (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id)
        .all()
    )
    
    # Calculate trip performance metrics
    perfect_trips = 0
    low_risk_trips = 0
    high_risk_trips = 0
    total_incidents = 0
    
    for trip in all_trips:
        # Calculate trip score if not available
        if trip.trip_score is not None:
            trip_score = trip.trip_score
        else:
            trip_score = max(0, min(100, 100 - (
                (trip.harsh_braking_count or 0) * 5 +
                (trip.rapid_accel_count or 0) * 3 +
                (trip.speeding_count or 0) * 8 +
                (trip.harsh_corner_count or 0) * 4
            )))
        
        # Categorize trips
        if trip_score >= 95:
            perfect_trips += 1
        if trip_score >= 80:
            low_risk_trips += 1
        if trip_score < 60:
            high_risk_trips += 1
        
        # Count incidents
        total_incidents += (
            (trip.harsh_braking_count or 0) +
            (trip.rapid_accel_count or 0) +
            (trip.speeding_count or 0) +
            (trip.harsh_corner_count or 0)
        )
    
    return RiskProfileSummaryResponse(
        overall_risk_score=round(latest_score.risk_score),
        overall_risk_trend_status=trend_status,
        behavior_score=round(behavior_score),
        last_updated_date=latest_score.calculation_date,
        change_from_previous=round(change_from_previous),
        previous_score=round(previous_score_value) if previous_score_value else None,
        total_trips=total_trips,
        total_miles=round(total_miles, 2),
        avg_trip_score=round(avg_trip_score, 1) if avg_trip_score else None,
        perfect_trips=perfect_trips,
        low_risk_trips=low_risk_trips,
        high_risk_trips=high_risk_trips,
        total_incidents=total_incidents
    )


@router.get("/{driver_id}/risk-score-trend", response_model=RiskScoreTrendResponse)
@cache_response(ttl=300, key_prefix="risk_score_trend")
async def get_risk_score_trend(
    driver_id: str,
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
    interval: str = Query("daily", description="Interval: daily, weekly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get risk score trend time series for Risk Profile page."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's risk trend"
        )
    
    # Parse period
    period_days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }.get(period, 30)
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=period_days)
    
    # Query risk scores
    scores = (
        db.query(RiskScore)
        .filter(
            RiskScore.driver_id == driver_id,
            RiskScore.calculation_date >= cutoff_date
        )
        .order_by(RiskScore.calculation_date.asc())
        .all()
    )
    
    if not scores:
        return RiskScoreTrendResponse(
            scores=[],
            period=period,
            interval=interval
        )
    
    # Group by interval
    if interval == "daily":
        # Group by date
        score_dict = {}
        for score in scores:
            date_str = score.calculation_date.date().isoformat()
            if date_str not in score_dict:
                score_dict[date_str] = []
            score_dict[date_str].append(score.risk_score)
        
        # Average scores per day (rounded to whole number)
        trend_points = [
            RiskScoreTrendPoint(
                date=date_str,
                risk_score=round(sum(scores_list) / len(scores_list))
            )
            for date_str, scores_list in sorted(score_dict.items())
        ]
    else:  # weekly
        # Group by week
        score_dict = {}
        for score in scores:
            week_start = score.calculation_date.date() - timedelta(days=score.calculation_date.date().weekday())
            week_str = week_start.isoformat()
            if week_str not in score_dict:
                score_dict[week_str] = []
            score_dict[week_str].append(score.risk_score)
        
        # Average scores per week (rounded to whole number)
        trend_points = [
            RiskScoreTrendPoint(
                date=week_str,
                risk_score=round(sum(scores_list) / len(scores_list))
            )
            for week_str, scores_list in sorted(score_dict.items())
        ]
    
    return RiskScoreTrendResponse(
        scores=trend_points,
        period=period,
        interval=interval
    )


@router.get("/{driver_id}/risk-factor-breakdown", response_model=RiskFactorBreakdownResponse)
@cache_response(ttl=300, key_prefix="risk_factor_breakdown")
async def get_risk_factor_breakdown(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get risk factor breakdown for radar chart and detailed factors."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's risk breakdown"
        )
    
    # Get trips from last 30 days
    period_start = datetime.utcnow() - timedelta(days=30)
    trips = (
        db.query(Trip)
        .filter(
            Trip.driver_id == driver_id,
            Trip.start_time >= period_start
        )
        .all()
    )
    
    # Get events from last 30 days for detailed analysis
    events = (
        db.query(TelematicsEvent)
        .filter(
            TelematicsEvent.driver_id == driver_id,
            TelematicsEvent.timestamp >= period_start
        )
        .all()
    )
    
    if not trips:
        # Return default values if no trips
        return RiskFactorBreakdownResponse(
            behavior=50,
            mileage=50,
            time_pattern=50,
            location=50,
            speeding_frequency=0.0,
            acceleration_pattern=0.0,
            high_risk_area_exposure=0.0,
            weather_risk_exposure=0.0,
            hard_braking_frequency=0.0,
            night_driving_percentage=0.0,
            phone_usage_incidents=0
        )
    
    # Calculate behavior score from trip scores
    trip_scores = []
    for trip in trips:
        if trip.trip_score is not None:
            trip_scores.append(trip.trip_score)
        else:
            score = 100 - (
                (trip.harsh_braking_count or 0) * 5 +
                (trip.rapid_accel_count or 0) * 3 +
                (trip.speeding_count or 0) * 8 +
                (trip.harsh_corner_count or 0) * 4
            )
            trip_scores.append(max(0, min(100, score)))
    
    behavior = round(sum(trip_scores) / len(trip_scores)) if trip_scores else 50
    
    # Calculate mileage score (based on total miles - more miles = better if consistent)
    total_miles = sum(trip.distance_miles or 0 for trip in trips)
    avg_miles_per_trip = total_miles / len(trips) if trips else 0
    # Score: 0-100 based on average miles per trip (optimal range 20-50 miles)
    if avg_miles_per_trip < 10:
        mileage = 30
    elif avg_miles_per_trip <= 50:
        mileage = 80
    elif avg_miles_per_trip <= 100:
        mileage = 60
    else:
        mileage = 40
    
    # Calculate time pattern score (based on night driving percentage)
    night_trips = sum(1 for trip in trips if trip.start_time.hour >= 22 or trip.start_time.hour < 6)
    night_driving_pct = (night_trips / len(trips)) * 100 if trips else 0
    # Lower night driving = better score
    time_pattern = round(max(0, min(100, 100 - (night_driving_pct * 2))))
    
    # Calculate location score (based on high-risk area exposure - simplified)
    # For now, use a default value, can be enhanced with actual location data
    location = 50
    
    # Calculate detailed factors from trips
    total_trips = len(trips)
    total_events_count = len(events)
    
    # Speeding frequency (per 100 trips)
    total_speeding = sum(trip.speeding_count or 0 for trip in trips)
    speeding_frequency = (total_speeding / total_trips * 100) if total_trips > 0 else 0.0
    
    # Acceleration pattern (per 100 trips)
    total_rapid_accel = sum(trip.rapid_accel_count or 0 for trip in trips)
    acceleration_pattern = (total_rapid_accel / total_trips * 100) if total_trips > 0 else 0.0
    
    # Hard braking frequency (per 100 trips)
    total_hard_braking = sum(trip.harsh_braking_count or 0 for trip in trips)
    hard_braking_frequency = (total_hard_braking / total_trips * 100) if total_trips > 0 else 0.0
    
    # Night driving percentage
    night_driving_percentage = night_driving_pct
    
    # Phone usage incidents (count)
    phone_usage_incidents = sum(1 for trip in trips if trip.phone_usage_detected) or 0
    
    # High risk area exposure (simplified - can be enhanced with actual location data)
    high_risk_area_exposure = 0.0  # Placeholder
    
    # Weather risk exposure (simplified - can be enhanced with actual weather data)
    weather_risk_exposure = 0.0  # Placeholder
    
    return RiskFactorBreakdownResponse(
        behavior=behavior,
        mileage=mileage,
        time_pattern=time_pattern,
        location=location,
        speeding_frequency=round(speeding_frequency, 1),
        acceleration_pattern=round(acceleration_pattern, 1),
        high_risk_area_exposure=round(high_risk_area_exposure, 1),
        weather_risk_exposure=round(weather_risk_exposure, 1),
        hard_braking_frequency=round(hard_braking_frequency, 1),
        night_driving_percentage=round(night_driving_percentage, 1),
        phone_usage_incidents=round(phone_usage_incidents)
    )


@router.post("/{driver_id}/recalculate-risk")
async def recalculate_risk(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate risk score for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to recalculate risk for this driver"
        )
    
    try:
        from app.services.risk_scoring import calculate_risk_score_for_driver, save_risk_score
        
        # Get previous score
        previous_score = (
            db.query(RiskScore)
            .filter(RiskScore.driver_id == driver_id)
            .order_by(RiskScore.calculation_date.desc())
            .first()
        )
        
        # Calculate new risk score
        risk_data = calculate_risk_score_for_driver(driver_id, db, period_days=30)
        
        # Save to database
        new_score = save_risk_score(driver_id, risk_data, db)
        
        return {
            "message": "Risk score recalculated successfully",
            "new_score": new_score.risk_score,
            "calculated_at": new_score.calculation_date
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recalculating risk score: {str(e)}"
        )


@router.post("/batch-calculate", response_model=dict)
async def batch_calculate_risk_scores(
    request: BatchRiskCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate risk scores for multiple drivers in batch (Admin only).
    Optimized for performance with single DB query.
    
    Args:
        request: Batch calculation request with driver_ids and period_days
        
    Returns:
        Dictionary mapping driver_id to risk_score_data
        
    Example:
        POST /api/v1/risk/batch-calculate
        {
            "driver_ids": ["DRV-0001", "DRV-0002", "DRV-0003"],
            "period_days": 30
        }
    """
    # Admin only
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for batch operations"
        )
    
    try:
        from app.services.ml_risk_scoring import calculate_ml_risk_score_batch
        
        results = calculate_ml_risk_score_batch(
            driver_ids=request.driver_ids,
            db=db,
            period_days=request.period_days
        )
        
        # Calculate summary statistics
        successful = [r for r in results.values() if 'error' not in r]
        failed = [r for r in results.values() if 'error' in r]
        
        avg_risk_score = sum(r['risk_score'] for r in successful) / len(successful) if successful else 0
        
        return {
            "total_requested": len(request.driver_ids),
            "successful": len(successful),
            "failed": len(failed),
            "avg_risk_score": round(avg_risk_score, 2),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing error: {str(e)}"
        )

