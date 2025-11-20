"""
Admin Driver Management Endpoints

This module provides driver CRUD operations:
- List drivers with enriched data (performance metrics, policy info)
- Get driver by ID (basic info)
- Get driver details (comprehensive info for detail modal)
- Create new driver
- Update driver
- Delete driver

All endpoints require admin authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date

from app.models.database import (
    get_db, User, Driver, Trip, RiskScore, Premium
)
from app.models.schemas import (
    DriverResponse, DriverCreate, DriverUpdate,
    DriverCardResponse, DriverDetailsResponse
)
from app.utils.auth import get_current_admin_user
from app.utils.cache import cache_response, invalidate_cache_pattern

router = APIRouter()


@router.get("", response_model=List[DriverCardResponse])
@cache_response(ttl=120, key_prefix="drivers_list")
async def list_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all drivers with enriched data (performance metrics and policy info)."""
    
    # 1. Subquery for latest risk score
    risk_sub = (
        db.query(
            RiskScore.driver_id,
            RiskScore.risk_score,
            func.row_number().over(
                partition_by=RiskScore.driver_id,
                order_by=RiskScore.calculation_date.desc()
            ).label('rn')
        ).subquery()
    )
    
    # 2. Subquery for total trips
    trips_sub = (
        db.query(
            Trip.driver_id,
            func.count(Trip.trip_id).label('total_trips')
        ).group_by(Trip.driver_id).subquery()
    )
    
    # 3. Subquery for active premium
    premium_sub_inner = (
        db.query(
            Premium.driver_id,
            Premium.monthly_premium,
            Premium.final_premium,
            Premium.base_premium,
            Premium.policy_type,
            Premium.status,
            func.row_number().over(
                partition_by=Premium.driver_id,
                order_by=Premium.created_at.desc()
            ).label('rn')
        )
        .filter(Premium.status == 'active')
        .subquery()
    )
    
    premium_sub = (
        db.query(
            premium_sub_inner.c.driver_id,
            premium_sub_inner.c.monthly_premium,
            premium_sub_inner.c.final_premium,
            premium_sub_inner.c.base_premium,
            premium_sub_inner.c.policy_type,
            premium_sub_inner.c.status
        )
        .filter(premium_sub_inner.c.rn == 1)
        .subquery()
    )

    # Main query joining everything
    query = (
        db.query(
            Driver,
            risk_sub.c.risk_score,
            func.coalesce(trips_sub.c.total_trips, 0).label('total_trips'),
            premium_sub.c.monthly_premium,
            premium_sub.c.final_premium,
            premium_sub.c.base_premium,
            premium_sub.c.policy_type,
            premium_sub.c.status
        )
        .outerjoin(risk_sub, (Driver.driver_id == risk_sub.c.driver_id) & (risk_sub.c.rn == 1))
        .outerjoin(trips_sub, Driver.driver_id == trips_sub.c.driver_id)
        .outerjoin(premium_sub, Driver.driver_id == premium_sub.c.driver_id)
    )

    # Filter to only show drivers DRV-0001 through DRV-0007
    allowed_driver_ids = [f"DRV-{i:04d}" for i in range(1, 8)]  # DRV-0001 to DRV-0007
    query = query.filter(Driver.driver_id.in_(allowed_driver_ids))

    if search:
        query = query.filter(
            (Driver.driver_id.ilike(f"%{search}%")) |
            (Driver.first_name.ilike(f"%{search}%")) |
            (Driver.last_name.ilike(f"%{search}%")) |
            (Driver.email.ilike(f"%{search}%"))
        )

    results = query.order_by(Driver.driver_id.asc()).offset(skip).limit(limit).all()

    # Enrich each driver with performance metrics and policy info
    enriched_drivers = []
    for row in results:
        driver = row.Driver
        risk_score = row.risk_score if row.risk_score is not None else 50.0
        safety_score = max(0, min(100, 100 - risk_score))
        total_trips = row.total_trips
        
        # Calculate reward points
        reward_points = int(safety_score * 5 + total_trips * 2)
        
        # Policy info
        policy_status = row.status
        monthly_premium = row.monthly_premium or row.final_premium
        policy_type = row.policy_type or 'PHYD'
        
        discount_percentage = 0.0
        if row.base_premium and monthly_premium:
            discount_percentage = (
                (row.base_premium - monthly_premium) / row.base_premium
            ) * 100

        enriched_drivers.append(DriverCardResponse(
            driver_id=driver.driver_id,
            first_name=driver.first_name or '',
            last_name=driver.last_name or '',
            email=driver.email or '',
            phone=driver.phone,
            city=driver.city,
            state=driver.state,
            safety_score=round(safety_score, 1),
            risk_score=round(risk_score, 1),
            total_trips=total_trips,
            reward_points=reward_points,
            policy_type=policy_type,
            policy_status=policy_status,
            monthly_premium=round(monthly_premium, 2) if monthly_premium else None,
            discount_percentage=round(discount_percentage, 1) if discount_percentage else None
        ))

    return enriched_drivers


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver_admin(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get driver by ID (basic)."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.get("/{driver_id}/details", response_model=DriverDetailsResponse)
@cache_response(ttl=180, key_prefix="driver_detail")
async def get_driver_details(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get comprehensive driver details for admin driver details modal."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Get latest risk score
    latest_risk_score = (
        db.query(RiskScore.risk_score)
        .filter(RiskScore.driver_id == driver_id)
        .order_by(RiskScore.calculation_date.desc())
        .first()
    )

    risk_score = latest_risk_score[0] if latest_risk_score else 50.0
    safety_score = max(0, min(100, 100 - risk_score))

    # Get total trips and total miles
    total_trips = (
        db.query(func.count(Trip.trip_id))
        .filter(Trip.driver_id == driver_id)
        .scalar() or 0
    )

    total_miles = (
        db.query(func.sum(Trip.distance_miles))
        .filter(Trip.driver_id == driver_id)
        .scalar() or 0.0
    )

    # Get active policy information
    active_premium = (
        db.query(Premium)
        .filter(
            Premium.driver_id == driver_id,
            Premium.status == 'active'
        )
        .order_by(Premium.created_at.desc())
        .first()
    )

    policy_type = None
    policy_status = None
    monthly_premium = None
    discount_percentage = None
    policy_number = None
    base_premium = None
    current_premium = None
    annual_savings = None
    coverage_type = None
    coverage_limit = None
    deductible = None
    effective_date = None
    expiration_date = None
    total_miles_allowed = None
    miles_used = None

    if active_premium:
        policy_status = active_premium.status
        monthly_premium = active_premium.monthly_premium or (active_premium.final_premium / 12 if active_premium.final_premium else None)
        current_premium = monthly_premium

        try:
            policy_type = getattr(active_premium, 'policy_type', None) or 'PHYD'
        except AttributeError:
            policy_type = 'PHYD'

        policy_number = active_premium.policy_id or f"POL-{active_premium.premium_id}"
        base_premium = active_premium.base_premium
        coverage_type = getattr(active_premium, 'coverage_type', None) or 'Comprehensive'
        coverage_limit = getattr(active_premium, 'coverage_limit', None) or 100000.0
        deductible = getattr(active_premium, 'deductible', None) or 1000.0
        effective_date = active_premium.effective_date
        expiration_date = active_premium.expiration_date
        total_miles_allowed = getattr(active_premium, 'total_miles_allowed', None)

        # Calculate miles used (sum of trip distances)
        if total_miles_allowed:
            miles_used = total_miles

        if base_premium and monthly_premium:
            discount_percentage = (
                (base_premium - monthly_premium) / base_premium
            ) * 100
            annual_savings = (base_premium - monthly_premium) * 12
        else:
            discount_percentage = 0.0
            annual_savings = 0.0

    # Calculate reward points
    reward_points = int(safety_score * 5 + total_trips * 2)

    # Get achievements (mock - based on driver performance)
    achievements = []
    if safety_score >= 90:
        achievements.append({'achievement_name': 'Safe Week', 'status': 'achieved'})
    if total_trips >= 50:
        achievements.append({'achievement_name': 'Smooth Operator', 'status': 'achieved'})
    if total_trips >= 100:
        achievements.append({'achievement_name': 'Century Club', 'status': 'achieved'})
    if risk_score <= 20:
        achievements.append({'achievement_name': 'Low Risk Driver', 'status': 'achieved'})

    # Format full address
    full_address = None
    if driver.address or driver.city or driver.state or getattr(driver, 'zip_code', None):
        parts = []
        if driver.address:
            parts.append(driver.address)
        if driver.city:
            parts.append(driver.city)
        if driver.state:
            parts.append(driver.state)
        zip_code = getattr(driver, 'zip_code', None)
        if zip_code:
            parts.append(zip_code)
        full_address = ", ".join(parts)

    # Calculate years licensed (if date_of_birth available)
    years_licensed = None
    if hasattr(driver, 'date_of_birth') and driver.date_of_birth:
        try:
            from datetime import date
            today = date.today()
            dob = driver.date_of_birth
            if isinstance(dob, str):
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
            years_licensed = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except:
            pass

    return DriverDetailsResponse(
        driver_id=driver.driver_id,
        first_name=driver.first_name or '',
        last_name=driver.last_name or '',
        email=driver.email or '',
        phone=driver.phone,
        date_of_birth=getattr(driver, 'date_of_birth', None),
        license_number=getattr(driver, 'license_number', None),
        license_state=getattr(driver, 'license_state', None),
        address=driver.address,
        city=driver.city,
        state=driver.state,
        zip_code=getattr(driver, 'zip_code', None),
        full_address=full_address,
        safety_score=round(safety_score, 1),
        risk_score=round(risk_score, 1),
        total_miles=round(total_miles, 2),
        total_trips=total_trips,
        policy_type=policy_type,
        policy_status=policy_status,
        monthly_premium=round(monthly_premium, 2) if monthly_premium else None,
        discount_percentage=round(discount_percentage, 1) if discount_percentage else None,
        policy_number=policy_number,
        base_premium=round(base_premium, 2) if base_premium else None,
        current_premium=round(current_premium, 2) if current_premium else None,
        annual_savings=round(annual_savings, 2) if annual_savings else None,
        coverage_type=coverage_type,
        coverage_limit=coverage_limit,
        deductible=deductible,
        effective_date=effective_date,
        expiration_date=expiration_date,
        total_miles_allowed=total_miles_allowed,
        miles_used=round(miles_used, 0) if miles_used else None,
        reward_points=reward_points,
        achievements=achievements,
        years_licensed=years_licensed,
        gender=getattr(driver, 'gender', None),
        marital_status=getattr(driver, 'marital_status', None),
        created_at=driver.created_at or datetime.utcnow(),
        updated_at=getattr(driver, 'updated_at', None)
    )


@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver_admin(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new driver."""
    # Check if driver already exists
    existing = db.query(Driver).filter(Driver.driver_id == driver_data.driver_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Driver ID already exists")

    driver = Driver(**driver_data.dict())
    db.add(driver)
    db.commit()
    db.refresh(driver)

    # Invalidate related caches
    invalidate_cache_pattern("*drivers_list*")
    invalidate_cache_pattern("*dashboard_*")

    return driver


@router.patch("/{driver_id}", response_model=DriverResponse)
async def update_driver_admin(
    driver_id: str,
    driver_update: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a driver."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    update_data = driver_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)

    driver.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(driver)

    # Invalidate related caches
    invalidate_cache_pattern(f"*driver_detail*{driver_id}*")
    invalidate_cache_pattern("*drivers_list*")
    invalidate_cache_pattern("*dashboard_*")

    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver_admin(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a driver."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    db.delete(driver)
    db.commit()

    # Invalidate related caches
    invalidate_cache_pattern(f"*driver_detail*{driver_id}*")
    invalidate_cache_pattern("*drivers_list*")
    invalidate_cache_pattern("*dashboard_*")

    return None
