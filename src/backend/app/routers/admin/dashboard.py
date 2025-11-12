"""
Admin Dashboard Endpoints

This module provides dashboard statistics and analytics:
- System-wide statistics (drivers, users, vehicles, devices, trips, events)
- Summary cards (drivers, vehicles, revenue, avg risk score)
- Daily trip activity (line chart data)
- Risk distribution (pie chart data)
- Safety events breakdown (bar chart data)
- Policy type distribution (pie chart data)

All endpoints require admin authentication.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case
from typing import List
from datetime import datetime, timedelta

from app.models.database import (
    get_db, User, Driver, Vehicle, Device, Trip,
    RiskScore, Premium, TelematicsEvent
)
from app.models.schemas import (
    AdminDashboardSummary, DailyTripActivity,
    RiskDistributionResponse, SafetyEventBreakdown,
    PolicyTypeDistribution
)
from app.utils.auth import get_current_admin_user

router = APIRouter()


@router.get("/stats")
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get admin dashboard statistics."""
    total_drivers = db.query(func.count(Driver.driver_id)).scalar()
    total_users = db.query(func.count(User.user_id)).scalar()
    total_vehicles = db.query(func.count(Vehicle.vehicle_id)).scalar()
    total_devices = db.query(func.count(Device.device_id)).scalar()
    total_trips = db.query(func.count(Trip.trip_id)).scalar()
    total_events = db.query(func.count(TelematicsEvent.event_id)).scalar()

    # Recent activity
    recent_drivers = db.query(Driver).order_by(Driver.created_at.desc()).limit(5).all()
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()

    return {
        "totals": {
            "drivers": total_drivers,
            "users": total_users,
            "vehicles": total_vehicles,
            "devices": total_devices,
            "trips": total_trips,
            "events": total_events
        },
        "recent_drivers": recent_drivers,
        "recent_users": recent_users
    }


@router.get("/summary", response_model=AdminDashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get admin dashboard summary (4 cards)."""
    # Total Drivers - count only active policyholders (drivers with active user accounts)
    total_drivers = (
        db.query(func.count(distinct(Driver.driver_id)))
        .join(User, Driver.driver_id == User.driver_id)
        .filter(User.is_active == True)
        .scalar() or 0
    )

    # Total Vehicles
    total_vehicles = db.query(func.count(Vehicle.vehicle_id)).scalar() or 0

    # Monthly Revenue - sum of active monthly premiums
    monthly_revenue = (
        db.query(func.sum(Premium.monthly_premium))
        .filter(Premium.status == 'active')
        .scalar() or 0.0
    )

    # If monthly_premium is NULL, calculate from final_premium
    if monthly_revenue == 0.0:
        monthly_revenue = (
            db.query(func.sum(Premium.final_premium))
            .filter(Premium.status == 'active')
            .scalar() or 0.0
        )

    # Avg Risk Score - portfolio average (latest risk score for each driver)
    # Optimize: Use window function for better performance
    subquery = (
        db.query(
            RiskScore.driver_id,
            RiskScore.risk_score,
            func.row_number()
            .over(
                partition_by=RiskScore.driver_id,
                order_by=RiskScore.calculation_date.desc()
            )
            .label('rn')
        )
        .subquery()
    )

    latest_risk_scores = (
        db.query(subquery.c.risk_score)
        .filter(subquery.c.rn == 1)
        .all()
    )

    if latest_risk_scores:
        avg_risk_score = sum(score[0] for score in latest_risk_scores if score[0] is not None) / len([s for s in latest_risk_scores if s[0] is not None])
    else:
        avg_risk_score = 0.0

    return AdminDashboardSummary(
        total_drivers=total_drivers,
        total_vehicles=total_vehicles,
        monthly_revenue=round(monthly_revenue, 2),
        avg_risk_score=round(avg_risk_score, 2)
    )


@router.get("/trip-activity", response_model=List[DailyTripActivity])
async def get_trip_activity(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get daily trip activity for line chart."""
    from sqlalchemy import cast, Date

    # Calculate date range (use datetime for better index usage)
    end_datetime = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    start_datetime = (end_datetime - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_datetime.date()
    start_date = start_datetime.date()

    # Query trips grouped by date - use date_trunc for better performance
    # This allows PostgreSQL to use the index on start_time
    trip_activity = (
        db.query(
            func.date_trunc('day', Trip.start_time).label('date'),
            func.count(Trip.trip_id).label('trip_count'),
            func.avg(
                case(
                    (Trip.harsh_braking_count.is_(None), None),
                    else_=100 - (
                        func.coalesce(Trip.harsh_braking_count, 0) * 5 +
                        func.coalesce(Trip.rapid_accel_count, 0) * 3 +
                        func.coalesce(Trip.speeding_count, 0) * 8 +
                        func.coalesce(Trip.harsh_corner_count, 0) * 4
                    )
                )
            ).label('avg_score')
        )
        .filter(
            Trip.start_time >= start_datetime,
            Trip.start_time <= end_datetime
        )
        .group_by(func.date_trunc('day', Trip.start_time))
        .order_by(func.date_trunc('day', Trip.start_time))
        .all()
    )

    # Create a dictionary of existing dates
    # Convert date_trunc result to date string
    activity_dict = {}
    for row in trip_activity:
        # date_trunc returns a datetime, convert to date string
        date_key = row.date.date().isoformat() if isinstance(row.date, datetime) else str(row.date)
        activity_dict[date_key] = {'count': row.trip_count, 'score': row.avg_score}

    # Fill in missing dates with 0
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        if date_str in activity_dict:
            result.append(DailyTripActivity(
                date=date_str,
                trip_count=activity_dict[date_str]['count'],
                avg_score=float(activity_dict[date_str]['score']) if activity_dict[date_str]['score'] is not None else None
            ))
        else:
            result.append(DailyTripActivity(
                date=date_str,
                trip_count=0,
                avg_score=None
            ))
        current_date += timedelta(days=1)

    return result


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
async def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get risk distribution for pie chart."""
    # Optimize: Use window function with ROW_NUMBER() for better performance
    # This is more efficient than a subquery join
    # Use window function to get latest risk score per driver
    # This leverages the index on (driver_id, calculation_date DESC)
    subquery = (
        db.query(
            RiskScore.driver_id,
            RiskScore.risk_score,
            func.row_number()
            .over(
                partition_by=RiskScore.driver_id,
                order_by=RiskScore.calculation_date.desc()
            )
            .label('rn')
        )
        .subquery()
    )

    latest_risk_scores = (
        db.query(subquery.c.driver_id, subquery.c.risk_score)
        .filter(subquery.c.rn == 1)
        .all()
    )

    # Categorize risk scores
    low_risk_count = 0
    medium_risk_count = 0
    high_risk_count = 0

    for row in latest_risk_scores:
        score = row.risk_score
        if score is not None:
            if score <= 40:
                low_risk_count += 1
            elif score <= 70:
                medium_risk_count += 1
            else:
                high_risk_count += 1

    total_drivers = low_risk_count + medium_risk_count + high_risk_count

    # Calculate percentages
    if total_drivers > 0:
        low_risk_percentage = (low_risk_count / total_drivers) * 100
        medium_risk_percentage = (medium_risk_count / total_drivers) * 100
        high_risk_percentage = (high_risk_count / total_drivers) * 100
    else:
        low_risk_percentage = 0.0
        medium_risk_percentage = 0.0
        high_risk_percentage = 0.0

    return RiskDistributionResponse(
        low_risk_percentage=round(low_risk_percentage, 2),
        medium_risk_percentage=round(medium_risk_percentage, 2),
        high_risk_percentage=round(high_risk_percentage, 2),
        low_risk_count=low_risk_count,
        medium_risk_count=medium_risk_count,
        high_risk_count=high_risk_count,
        total_drivers=total_drivers
    )


@router.get("/safety-events-breakdown", response_model=List[SafetyEventBreakdown])
async def get_safety_events_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get safety events breakdown for bar chart."""
    # Optimize: Use a single query to get all sums at once
    # This reduces database round trips from 4 to 1
    result = (
        db.query(
            func.sum(func.coalesce(Trip.harsh_braking_count, 0)).label('hard_braking'),
            func.sum(func.coalesce(Trip.rapid_accel_count, 0)).label('rapid_acceleration'),
            func.sum(func.coalesce(Trip.harsh_corner_count, 0)).label('sharp_turns'),
            func.sum(func.coalesce(Trip.speeding_count, 0)).label('speeding_incidents')
        )
        .first()
    )

    return [
        SafetyEventBreakdown(event_type="Hard Braking", count=int(result.hard_braking or 0)),
        SafetyEventBreakdown(event_type="Rapid Acceleration", count=int(result.rapid_acceleration or 0)),
        SafetyEventBreakdown(event_type="Sharp Turn", count=int(result.sharp_turns or 0)),
        SafetyEventBreakdown(event_type="Speeding Incidents", count=int(result.speeding_incidents or 0)),
    ]


@router.get("/policy-type-distribution", response_model=List[PolicyTypeDistribution])
async def get_policy_type_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get policy type distribution for pie chart."""
    # Check if policy_type column exists, if not default to PHYD
    try:
        # Try to query policy_type
        policy_types = (
            db.query(
                func.coalesce(Premium.policy_type, 'PHYD').label('policy_type'),
                func.count(Premium.premium_id).label('count')
            )
            .filter(Premium.status == 'active')
            .group_by(func.coalesce(Premium.policy_type, 'PHYD'))
            .all()
        )
    except Exception:
        # If policy_type doesn't exist, return default PHYD count
        active_policies_count = (
            db.query(func.count(Premium.premium_id))
            .filter(Premium.status == 'active')
            .scalar() or 0
        )
        return [
            PolicyTypeDistribution(policy_type="PHYD", count=active_policies_count)
        ]

    result = []
    for pt in policy_types:
        result.append(PolicyTypeDistribution(
            policy_type=pt.policy_type or "PHYD",
            count=pt.count
        ))

    return result
