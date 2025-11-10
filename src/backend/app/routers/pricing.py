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
    PremiumComponent,
    PolicyDetailsResponse
)
from app.utils.auth import get_current_user
from app.services.ml_risk_scoring import calculate_premium_with_discount
from app.services.discount_calculator import calculate_discount_score

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


def calculate_discount_factor(driver_id: str, db: Session) -> float:
    """
    Calculate discount factor based on clean trips (new strict system).
    
    Uses the discount calculator which:
    - Only counts trips with ZERO risk factors
    - Each risky trip costs -5 points
    - Maximum discount: 45%
    """
    discount_info = calculate_discount_score(driver_id, db, period_days=90)
    discount_percent = discount_info.get('discount_percent', 0.0)
    
    # Convert percentage to factor (1.0 = no discount, 0.55 = 45% discount)
    discount_factor = 1.0 - (discount_percent / 100)
    
    # Ensure minimum factor (max 45% discount)
    return max(0.55, discount_factor)  # 0.55 = 45% discount max


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


@router.get("/{driver_id}/policy-details", response_model=PolicyDetailsResponse)
async def get_policy_details(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get policy details for Policy page."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's policy"
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
            detail="No active policy found for this driver"
        )
    
    # Format policy number
    policy_number = premium.policy_id or f"POL-{premium.premium_id}"
    
    # Get traditional premium (base rate for state)
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    state = driver.state if driver else "default"
    traditional_premium = BASE_RATES.get(state, BASE_RATES["default"]) / 12  # Monthly
    
    # Calculate savings
    monthly_premium = premium.monthly_premium or premium.final_premium / 12
    monthly_savings = traditional_premium - monthly_premium
    annual_savings = monthly_savings * 12
    discount_percentage = (monthly_savings / traditional_premium) * 100 if traditional_premium > 0 else 0.0
    
    # Get coverage details (handle if columns don't exist)
    coverage_type = getattr(premium, 'coverage_type', None) or "Comprehensive"
    coverage_limit = getattr(premium, 'coverage_limit', None) or 100000.0
    deductible = getattr(premium, 'deductible', None) or 1000.0
    
    # Get policy type
    try:
        policy_type = getattr(premium, 'policy_type', None) or "PHYD"
    except AttributeError:
        policy_type = "PHYD"
    
    # Get last updated - fallback to created_at if updated_at and policy_last_updated are None
    last_updated = (
        getattr(premium, 'updated_at', None) or 
        getattr(premium, 'policy_last_updated', None) or 
        getattr(premium, 'created_at', None)
    )
    
    return PolicyDetailsResponse(
        policy_number=policy_number,
        status=premium.status or "active",
        policy_type=policy_type,
        traditional_monthly_premium=round(traditional_premium, 2),
        monthly_premium=round(monthly_premium, 2),
        discount_percentage=round(discount_percentage, 1),
        monthly_savings=round(monthly_savings, 2),
        annual_savings=round(annual_savings, 2),
        effective_date=premium.effective_date or date.today(),
        expiration_date=premium.expiration_date or date.today(),
        last_updated=last_updated,
        coverage_type=coverage_type,
        coverage_limit=coverage_limit,
        deductible=deductible
    )


@router.post("/{driver_id}/recalculate-premium")
async def recalculate_premium(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate premium for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to recalculate premium for this driver"
        )
    
    try:
        # Get driver
        driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Get latest risk score
        from app.models.database import RiskScore
        latest_risk_score = (
            db.query(RiskScore)
            .filter(RiskScore.driver_id == driver_id)
            .order_by(RiskScore.calculation_date.desc())
            .first()
        )
        
        risk_score = latest_risk_score.risk_score if latest_risk_score else 50.0
        
        # Calculate multipliers
        risk_multiplier = calculate_risk_multiplier(risk_score)
        
        # Get annual mileage (from trips or driver statistics)
        from app.models.database import Trip
        from sqlalchemy import func
        total_miles = (
            db.query(func.sum(Trip.distance_miles))
            .filter(Trip.driver_id == driver_id)
            .scalar() or 0.0
        )
        annual_mileage = total_miles * 12  # Estimate annual from total
        
        usage_multiplier = calculate_usage_multiplier(annual_mileage)
        
        # Calculate discount factor using new ML-based system
        discount_factor = calculate_discount_factor(driver_id, db)
        
        # Get base premium
        state = driver.state or "default"
        base_premium = BASE_RATES.get(state, BASE_RATES["default"])
        
        # Calculate final premium
        final_premium = base_premium * risk_multiplier * usage_multiplier * discount_factor
        monthly_premium = final_premium / 12
        
        # Get or create premium record
        premium = (
            db.query(Premium)
            .filter(
                Premium.driver_id == driver_id,
                Premium.status == "active"
            )
            .order_by(Premium.effective_date.desc())
            .first()
        )
        
        if premium:
            # Update existing premium
            premium.base_premium = base_premium
            premium.risk_multiplier = risk_multiplier
            premium.usage_multiplier = usage_multiplier
            premium.discount_factor = discount_factor
            premium.final_premium = final_premium
            premium.monthly_premium = monthly_premium
            premium.updated_at = datetime.utcnow()
            if hasattr(premium, 'policy_last_updated'):
                premium.policy_last_updated = datetime.utcnow()
        else:
            # Create new premium
            from datetime import date, timedelta
            premium = Premium(
                driver_id=driver_id,
                policy_id=f"POL-{datetime.now().year}-{premium.premium_id if premium else 1}",
                base_premium=base_premium,
                risk_multiplier=risk_multiplier,
                usage_multiplier=usage_multiplier,
                discount_factor=discount_factor,
                final_premium=final_premium,
                monthly_premium=monthly_premium,
                effective_date=date.today(),
                expiration_date=date.today() + timedelta(days=365),
                status="active"
            )
            db.add(premium)
        
        db.commit()
        db.refresh(premium)
        
        return {
            "message": "Premium recalculated successfully",
            "new_premium": round(monthly_premium, 2),
            "recalculated_at": datetime.utcnow()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recalculating premium: {str(e)}"
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


@router.get("/{driver_id}/discount-info")
async def get_discount_info(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed discount information for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's discount information"
        )
    
    discount_info = calculate_discount_score(driver_id, db, period_days=90)
    
    return {
        "driver_id": driver_id,
        "discount_info": discount_info
    }
