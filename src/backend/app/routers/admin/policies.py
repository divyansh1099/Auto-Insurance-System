"""
Admin Policies Management Endpoints

This module provides policy management operations:
- Get policy summary statistics (total policies, active policies, monthly revenue, total savings)
- List all policies with enriched data (driver info, discounts, savings, coverage details)

All endpoints require admin authentication.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date

from app.models.database import get_db, User, Driver, Premium, Trip
from app.models.schemas import PoliciesSummaryResponse, PolicyCardResponse
from app.utils.auth import get_current_admin_user

router = APIRouter()


@router.get("/summary", response_model=PoliciesSummaryResponse)
async def get_policies_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get policy summary statistics for admin dashboard."""
    total_policies = db.query(func.count(Premium.premium_id)).scalar() or 0

    active_policies = (
        db.query(func.count(Premium.premium_id))
        .filter(Premium.status == 'active')
        .scalar() or 0
    )

    monthly_revenue = (
        db.query(func.sum(Premium.monthly_premium))
        .filter(Premium.status == 'active')
        .scalar() or 0.0
    )

    # If monthly_premium is NULL, use final_premium
    if monthly_revenue == 0.0:
        monthly_revenue = (
            db.query(func.sum(Premium.final_premium))
            .filter(Premium.status == 'active')
            .scalar() or 0.0
        )

    # Total savings: sum of annual savings for active policies
    total_savings = (
        db.query(
            func.sum((Premium.base_premium - func.coalesce(Premium.monthly_premium, Premium.final_premium, 0)) * 12)
        )
        .filter(Premium.status == 'active')
        .scalar() or 0.0
    )

    return PoliciesSummaryResponse(
        total_policies=total_policies,
        active_policies=active_policies,
        monthly_revenue=round(monthly_revenue, 2),
        total_savings=round(total_savings, 2)
    )


@router.get("", response_model=List[PolicyCardResponse])
async def list_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    policy_type: Optional[str] = Query(None, description="Filter by policy type: PAYD, PHYD, Hybrid, or None for all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all policies with enriched data for admin cards."""
    # Base query with JOIN
    query = (
        db.query(Premium, Driver)
        .join(Driver, Premium.driver_id == Driver.driver_id)
    )

    # Search filter
    if search:
        query = query.filter(
            (Premium.policy_id.ilike(f"%{search}%")) |
            (Driver.first_name.ilike(f"%{search}%")) |
            (Driver.last_name.ilike(f"%{search}%")) |
            (Driver.email.ilike(f"%{search}%"))
        )

    # Policy type filter
    if policy_type and policy_type != "All":
        # Try to filter by policy_type, but handle if column doesn't exist
        try:
            query = query.filter(Premium.policy_type == policy_type)
        except Exception:
            # If policy_type doesn't exist, ignore filter
            pass

    # Order and paginate
    results = query.order_by(Premium.created_at.desc()).offset(skip).limit(limit).all()

    enriched_policies = []
    for premium, driver in results:
        # Calculate discount percentage
        monthly_premium = premium.monthly_premium or premium.final_premium or 0.0
        if premium.base_premium and monthly_premium:
            discount_percentage = (
                (premium.base_premium - monthly_premium) / premium.base_premium
            ) * 100
        else:
            discount_percentage = 0.0

        # Calculate annual savings
        annual_savings = (premium.base_premium - monthly_premium) * 12 if premium.base_premium and monthly_premium else 0.0

        # Get policy_type, default to PHYD if not available
        try:
            pt = getattr(premium, 'policy_type', None) or 'PHYD'
        except AttributeError:
            pt = 'PHYD'

        # Calculate miles used for PAYD policies
        miles_used = None
        if pt == "PAYD" and premium.effective_date and premium.expiration_date:
            miles_used = (
                db.query(func.sum(Trip.distance_miles))
                .filter(
                    Trip.driver_id == premium.driver_id,
                    Trip.start_time >= premium.effective_date,
                    Trip.start_time <= premium.expiration_date
                )
                .scalar() or 0.0
            )

        # Get coverage details (handle if columns don't exist)
        try:
            coverage_type = getattr(premium, 'coverage_type', None)
            coverage_limit = getattr(premium, 'coverage_limit', None)
            total_miles_allowed = getattr(premium, 'total_miles_allowed', None)
        except AttributeError:
            coverage_type = None
            coverage_limit = None
            total_miles_allowed = None

        # Format policy_id
        policy_id = premium.policy_id or f"POL-{premium.premium_id}"

        enriched_policies.append(PolicyCardResponse(
            premium_id=premium.premium_id,
            policy_id=policy_id,
            driver_id=premium.driver_id,
            driver_name=f"{driver.first_name} {driver.last_name}",
            policy_type=pt,
            status=premium.status or 'inactive',
            base_premium=premium.base_premium or 0.0,
            current_premium=monthly_premium,
            discount_percentage=round(discount_percentage, 1),
            annual_savings=round(annual_savings, 2),
            coverage_type=coverage_type,
            coverage_limit=coverage_limit,
            effective_date=premium.effective_date or date.today(),
            expiration_date=premium.expiration_date or date.today(),
            miles_used=round(miles_used, 1) if miles_used is not None else None,
            total_miles_allowed=total_miles_allowed
        ))

    return enriched_policies
