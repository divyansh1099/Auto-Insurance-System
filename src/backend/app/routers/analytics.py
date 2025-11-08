"""
Analytics and reporting endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import get_db, User, Driver, Trip, RiskScore, Premium
from app.models.schemas import FleetSummary, RiskDistribution, RiskCategory
from app.utils.auth import get_current_admin_user

router = APIRouter()


@router.get("/fleet/summary", response_model=FleetSummary)
async def get_fleet_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get fleet-wide summary statistics (admin only)."""
    # Total drivers
    total_drivers = db.query(Driver).count()

    # Active drivers (with recent trips)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    active_drivers = (
        db.query(Driver.driver_id)
        .join(Trip)
        .filter(Trip.start_time >= thirty_days_ago)
        .distinct()
        .count()
    )

    # Total miles YTD
    year_start = datetime(datetime.utcnow().year, 1, 1)
    total_miles = (
        db.query(func.sum(Trip.distance_miles))
        .filter(Trip.start_time >= year_start)
        .scalar() or 0
    )

    # Total trips YTD
    total_trips = (
        db.query(func.count(Trip.trip_id))
        .filter(Trip.start_time >= year_start)
        .scalar() or 0
    )

    # Average risk score
    avg_risk_score = (
        db.query(func.avg(RiskScore.risk_score))
        .filter(RiskScore.calculation_date >= thirty_days_ago)
        .scalar() or 0
    )

    # Risk distribution
    risk_distribution = {
        "excellent": 0,
        "good": 0,
        "average": 0,
        "below_average": 0,
        "high_risk": 0
    }

    # Get latest risk scores for each driver
    from sqlalchemy import distinct
    from sqlalchemy.orm import aliased

    subquery = (
        db.query(
            RiskScore.driver_id,
            func.max(RiskScore.calculation_date).label('max_date')
        )
        .group_by(RiskScore.driver_id)
        .subquery()
    )

    latest_scores = (
        db.query(RiskScore.risk_score)
        .join(
            subquery,
            (RiskScore.driver_id == subquery.c.driver_id) &
            (RiskScore.calculation_date == subquery.c.max_date)
        )
        .all()
    )

    for score_tuple in latest_scores:
        score = score_tuple[0]
        if score <= 20:
            risk_distribution["excellent"] += 1
        elif score <= 40:
            risk_distribution["good"] += 1
        elif score <= 60:
            risk_distribution["average"] += 1
        elif score <= 80:
            risk_distribution["below_average"] += 1
        else:
            risk_distribution["high_risk"] += 1

    # Average premium
    avg_premium = (
        db.query(func.avg(Premium.monthly_premium))
        .filter(Premium.status == "active")
        .scalar() or 0
    )

    # Total savings (simplified calculation)
    # This would compare traditional vs telematics premiums
    total_savings = total_drivers * 50  # Placeholder

    return FleetSummary(
        total_drivers=total_drivers,
        active_drivers=active_drivers,
        total_miles_ytd=float(total_miles),
        total_trips_ytd=total_trips,
        avg_risk_score=float(avg_risk_score),
        risk_distribution=risk_distribution,
        avg_premium=float(avg_premium),
        total_savings=total_savings
    )


@router.get("/risk-distribution", response_model=RiskDistribution)
async def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get risk score distribution across fleet (admin only)."""
    # Get latest risk scores for each driver
    subquery = (
        db.query(
            RiskScore.driver_id,
            func.max(RiskScore.calculation_date).label('max_date')
        )
        .group_by(RiskScore.driver_id)
        .subquery()
    )

    latest_scores = (
        db.query(RiskScore.risk_score)
        .join(
            subquery,
            (RiskScore.driver_id == subquery.c.driver_id) &
            (RiskScore.calculation_date == subquery.c.max_date)
        )
        .all()
    )

    distribution = {
        "excellent": 0,
        "good": 0,
        "average": 0,
        "below_average": 0,
        "high_risk": 0
    }

    for score_tuple in latest_scores:
        score = score_tuple[0]
        if score <= 20:
            distribution["excellent"] += 1
        elif score <= 40:
            distribution["good"] += 1
        elif score <= 60:
            distribution["average"] += 1
        elif score <= 80:
            distribution["below_average"] += 1
        else:
            distribution["high_risk"] += 1

    total = len(latest_scores)

    return RiskDistribution(
        excellent=distribution["excellent"],
        good=distribution["good"],
        average=distribution["average"],
        below_average=distribution["below_average"],
        high_risk=distribution["high_risk"],
        total=total
    )


@router.get("/savings")
async def get_program_savings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get program-wide savings analysis (admin only)."""
    # This is a simplified version
    # In production, this would do detailed comparisons

    total_drivers = db.query(Driver).count()

    # Calculate average telematics premium
    avg_telematics_premium = (
        db.query(func.avg(Premium.final_premium))
        .filter(Premium.status == "active")
        .scalar() or 1200
    )

    # Estimated average traditional premium (simplified)
    avg_traditional_premium = 1200

    total_telematics_revenue = total_drivers * avg_telematics_premium
    total_traditional_revenue = total_drivers * avg_traditional_premium

    total_savings = total_traditional_revenue - total_telematics_revenue

    # Breakdown by risk category
    savings_by_category = {
        "excellent": {"count": 0, "avg_savings": 360},  # 30% discount
        "good": {"count": 0, "avg_savings": 180},  # 15% discount
        "average": {"count": 0, "avg_savings": 0},
        "below_average": {"count": 0, "avg_savings": -240},  # 20% surcharge
        "high_risk": {"count": 0, "avg_savings": -600}  # 50% surcharge
    }

    return {
        "total_drivers": total_drivers,
        "avg_telematics_premium": float(avg_telematics_premium),
        "avg_traditional_premium": avg_traditional_premium,
        "total_program_savings": total_savings,
        "savings_by_category": savings_by_category,
        "drivers_saving_money": total_drivers * 0.40,  # Estimated 40%
        "drivers_paying_more": total_drivers * 0.20,  # Estimated 20%
    }
