"""
Pricing calculation endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Dict, Any

from app.models.database import get_db, User, Premium, RiskScore, Driver
from app.models.schemas import (
    PremiumBreakdown,
    PremiumResponse,
    PremiumSimulation,
    PremiumComponent
)
from app.utils.auth import get_current_user

router = APIRouter()


# Base rates by state (simplified)
BASE_RATES = {
    "CA": 1200.0,
    "NY": 1400.0,
    "TX": 1100.0,
    "FL": 1300.0,
    # Default
    "default": 1200.0
}


def calculate_risk_multiplier(risk_score: float) -> float:
    """Calculate risk multiplier from risk score."""
    if risk_score <= 20:
        return 0.70  # 30% discount
    elif risk_score <= 40:
        return 0.85  # 15% discount
    elif risk_score <= 60:
        return 1.00  # no change
    elif risk_score <= 80:
        return 1.20  # 20% surcharge
    else:
        return 1.50  # 50% surcharge


def calculate_usage_multiplier(annual_mileage: float) -> float:
    """Calculate usage multiplier from annual mileage."""
    baseline = 12000

    if annual_mileage < 5000:
        return 0.75
    elif annual_mileage < baseline:
        return 0.80 + (annual_mileage / baseline) * 0.20
    elif annual_mileage < 15000:
        return 1.00
    elif annual_mileage < 20000:
        return 1.15
    else:
        return 1.30


def calculate_discount_factor(driver_data: Dict[str, Any]) -> float:
    """Calculate discount factor based on various criteria."""
    discount = 0.0

    # Data completeness bonus
    if driver_data.get("data_completeness", 0) > 0.95:
        discount += 0.02

    # Improvement bonus
    if driver_data.get("risk_score_trend", 0) < -5:
        discount += 0.03

    # Safety course
    if driver_data.get("completed_safety_course", False):
        discount += 0.05

    # Device active
    if driver_data.get("device_active_days", 0) > 90:
        discount += 0.02

    return max(1.0 - discount, 0.70)  # Max 30% total discount


@router.get("/{driver_id}/current", response_model=PremiumResponse)
async def get_current_premium(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current premium for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's premium"
        )

    # Get the latest active premium
    premium = (
        db.query(Premium)
        .filter(
            Premium.driver_id == driver_id,
            Premium.status == "active"
        )
        .order_by(Premium.effective_date.desc())
        .first()
    )

    if not premium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active premium found for this driver"
        )

    return PremiumResponse(
        driver_id=driver_id,
        monthly_premium=premium.monthly_premium,
        final_premium=premium.final_premium,
        effective_date=premium.effective_date,
        status=premium.status
    )


@router.get("/{driver_id}/breakdown", response_model=PremiumBreakdown)
async def get_premium_breakdown(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed premium breakdown."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's premium breakdown"
        )

    # Get driver
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Get latest premium
    premium = (
        db.query(Premium)
        .filter(
            Premium.driver_id == driver_id,
            Premium.status == "active"
        )
        .order_by(Premium.effective_date.desc())
        .first()
    )

    if not premium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active premium found for this driver"
        )

    # Calculate traditional premium for comparison
    state = driver.state or "default"
    traditional_premium = BASE_RATES.get(state, BASE_RATES["default"])

    # Create component breakdown
    components = [
        PremiumComponent(
            name="Base Premium",
            value=premium.base_premium,
            description=f"Base rate for {state} state"
        ),
        PremiumComponent(
            name="Risk Adjustment",
            value=premium.base_premium * (premium.risk_multiplier - 1),
            description=f"Based on risk score (multiplier: {premium.risk_multiplier:.2f}x)"
        ),
        PremiumComponent(
            name="Usage Adjustment",
            value=premium.base_premium * premium.risk_multiplier * (premium.usage_multiplier - 1),
            description=f"Based on mileage (multiplier: {premium.usage_multiplier:.2f}x)"
        ),
        PremiumComponent(
            name="Discounts",
            value=premium.base_premium * premium.risk_multiplier * premium.usage_multiplier * (premium.discount_factor - 1),
            description=f"Applied discounts (factor: {premium.discount_factor:.2f}x)"
        )
    ]

    savings = traditional_premium - premium.final_premium

    return PremiumBreakdown(
        driver_id=driver_id,
        base_premium=premium.base_premium,
        risk_multiplier=premium.risk_multiplier,
        usage_multiplier=premium.usage_multiplier,
        discount_factor=premium.discount_factor,
        final_premium=premium.final_premium,
        monthly_premium=premium.monthly_premium,
        effective_date=premium.effective_date,
        components=components,
        savings_vs_traditional=savings
    )


@router.post("/{driver_id}/simulate", response_model=PremiumSimulation)
async def simulate_premium(
    driver_id: str,
    assumptions: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simulate premium with what-if scenarios."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to simulate premium for this driver"
        )

    # Get current premium
    current_premium = (
        db.query(Premium)
        .filter(
            Premium.driver_id == driver_id,
            Premium.status == "active"
        )
        .order_by(Premium.effective_date.desc())
        .first()
    )

    if not current_premium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active premium found for this driver"
        )

    # Get simulated values from assumptions
    simulated_risk_score = assumptions.get("risk_score", None)
    simulated_mileage = assumptions.get("annual_mileage", 12000)

    # Calculate new multipliers
    if simulated_risk_score is not None:
        risk_multiplier = calculate_risk_multiplier(simulated_risk_score)
    else:
        risk_multiplier = current_premium.risk_multiplier

    usage_multiplier = calculate_usage_multiplier(simulated_mileage)
    discount_factor = current_premium.discount_factor

    # Calculate projected premium
    projected_premium = (
        current_premium.base_premium *
        risk_multiplier *
        usage_multiplier *
        discount_factor
    )

    potential_savings = current_premium.final_premium - projected_premium

    return PremiumSimulation(
        current_premium=current_premium.final_premium,
        projected_premium=projected_premium,
        potential_savings=potential_savings,
        assumptions=assumptions
    )


@router.get("/{driver_id}/comparison")
async def compare_with_traditional(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare telematics-based premium with traditional pricing."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this comparison"
        )

    # Get driver
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Get current premium
    current_premium = (
        db.query(Premium)
        .filter(
            Premium.driver_id == driver_id,
            Premium.status == "active"
        )
        .order_by(Premium.effective_date.desc())
        .first()
    )

    if not current_premium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active premium found for this driver"
        )

    # Calculate traditional premium
    state = driver.state or "default"
    traditional_premium = BASE_RATES.get(state, BASE_RATES["default"])

    # Apply basic demographic factors to traditional premium
    # (simplified - in reality this would be more complex)
    age = (date.today() - driver.date_of_birth).days // 365 if driver.date_of_birth else 30

    age_factor = 1.0
    if age < 25:
        age_factor = 1.5
    elif age >= 65:
        age_factor = 1.2

    traditional_premium *= age_factor

    savings = traditional_premium - current_premium.final_premium
    savings_pct = (savings / traditional_premium) * 100 if traditional_premium > 0 else 0

    return {
        "driver_id": driver_id,
        "telematics_premium": current_premium.final_premium,
        "traditional_premium": traditional_premium,
        "savings": savings,
        "savings_percentage": savings_pct,
        "comparison_details": {
            "telematics_monthly": current_premium.monthly_premium,
            "traditional_monthly": traditional_premium / 12,
            "based_on_behavior": True,
            "based_on_demographics": False
        }
    }


@router.get("/{driver_id}/history")
async def get_premium_history(
    driver_id: str,
    months: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get premium history for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's premium history"
        )

    # Get historical premiums
    cutoff_date = date.today() - timedelta(days=months * 30)

    premiums = (
        db.query(Premium)
        .filter(
            Premium.driver_id == driver_id,
            Premium.effective_date >= cutoff_date
        )
        .order_by(Premium.effective_date.desc())
        .all()
    )

    if not premiums:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No premium history found for this driver"
        )

    history = [
        {
            "effective_date": p.effective_date,
            "monthly_premium": p.monthly_premium,
            "final_premium": p.final_premium,
            "risk_multiplier": p.risk_multiplier,
            "status": p.status
        }
        for p in premiums
    ]

    return {
        "driver_id": driver_id,
        "history": history,
        "total_records": len(history)
    }
