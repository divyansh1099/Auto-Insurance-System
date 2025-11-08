"""
Risk scoring endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import random

from app.models.database import get_db, User, RiskScore
from app.models.schemas import (
    RiskScoreResponse,
    RiskScoreBreakdown,
    RiskScoreHistory,
    RiskCategory,
    FeatureImportance
)
from app.utils.auth import get_current_user

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
