"""
Admin CRUD endpoints for managing all entities.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct, case, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta, date

from app.models.database import (
    get_db, User, Driver, Vehicle, Device, Trip, 
    RiskScore, Premium, TelematicsEvent, DriverStatistics
)
from app.models.schemas import (
    DriverResponse, DriverCreate, DriverUpdate,
    UserResponse, UserCreate, UserUpdate,
    AdminDashboardSummary, DailyTripActivity,
    RiskDistributionResponse, SafetyEventBreakdown,
    PolicyTypeDistribution, DriverCardResponse,
    PoliciesSummaryResponse, PolicyCardResponse,
    DriverDetailsResponse
)
from app.utils.auth import get_current_admin_user

router = APIRouter()


# ==================== DRIVERS ====================

@router.get("/drivers", response_model=List[DriverCardResponse])
async def list_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all drivers with enriched data (performance metrics and policy info)."""
    query = db.query(Driver)
    
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
    
    drivers = query.order_by(Driver.driver_id.asc()).offset(skip).limit(limit).all()
    
    # Enrich each driver with performance metrics and policy info
    enriched_drivers = []
    for driver in drivers:
        # Get latest risk score
        latest_risk_score = (
            db.query(RiskScore.risk_score)
            .filter(RiskScore.driver_id == driver.driver_id)
            .order_by(RiskScore.calculation_date.desc())
            .first()
        )
        
        risk_score = latest_risk_score[0] if latest_risk_score else 50.0
        safety_score = max(0, min(100, 100 - risk_score))  # Inverse of risk score
        
        # Get total trips count
        total_trips = (
            db.query(func.count(Trip.trip_id))
            .filter(Trip.driver_id == driver.driver_id)
            .scalar() or 0
        )
        
        # Calculate reward points (mock calculation: safety_score * 5 + trips * 2)
        reward_points = int(safety_score * 5 + total_trips * 2)
        
        # Get active policy information
        active_premium = (
            db.query(Premium)
            .filter(
                Premium.driver_id == driver.driver_id,
                Premium.status == 'active'
            )
            .order_by(Premium.created_at.desc())
            .first()
        )
        
        policy_type = None
        policy_status = None
        monthly_premium = None
        discount_percentage = None
        
        if active_premium:
            policy_status = active_premium.status
            monthly_premium = active_premium.monthly_premium or active_premium.final_premium
            
            # Try to get policy_type, default to PHYD if not available
            try:
                policy_type = getattr(active_premium, 'policy_type', None) or 'PHYD'
            except AttributeError:
                policy_type = 'PHYD'
            
            # Calculate discount percentage
            if active_premium.base_premium and monthly_premium:
                discount_percentage = (
                    (active_premium.base_premium - monthly_premium) / active_premium.base_premium
                ) * 100
            else:
                discount_percentage = 0.0
        
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


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
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


@router.get("/drivers/{driver_id}/details", response_model=DriverDetailsResponse)
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


@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
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
    return driver


@router.patch("/drivers/{driver_id}", response_model=DriverResponse)
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
    return driver


@router.delete("/drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    return None


# ==================== USERS ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all users."""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get user by ID."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new user."""
    from app.utils.auth import get_password_hash
    
    # Check if username or email exists
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        driver_id=user_data.driver_id,
        is_active=user_data.is_active if user_data.is_active is not None else True,
        is_admin=user_data.is_admin if user_data.is_admin is not None else False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user_admin(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a user."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Handle password update
    if 'password' in update_data:
        from app.utils.auth import get_password_hash
        update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a user."""
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return None


# ==================== VEHICLES ====================

@router.get("/vehicles")
async def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    driver_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all vehicles."""
    query = db.query(Vehicle)
    
    if driver_id:
        query = query.filter(Vehicle.driver_id == driver_id)
    
    vehicles = query.order_by(Vehicle.created_at.desc()).offset(skip).limit(limit).all()
    return vehicles


@router.get("/vehicles/{vehicle_id}")
async def get_vehicle_admin(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get vehicle by ID."""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle_admin(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a vehicle."""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    db.delete(vehicle)
    db.commit()
    return None


# ==================== DEVICES ====================

@router.get("/devices")
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    driver_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all devices."""
    query = db.query(Device)
    
    if driver_id:
        query = query.filter(Device.driver_id == driver_id)
    
    devices = query.order_by(Device.created_at.desc()).offset(skip).limit(limit).all()
    return devices


@router.get("/devices/{device_id}")
async def get_device_admin(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get device by ID."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_admin(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a device."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(device)
    db.commit()
    return None


# ==================== TRIPS ====================

@router.get("/trips")
async def list_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    driver_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all trips."""
    query = db.query(Trip)
    
    if driver_id:
        query = query.filter(Trip.driver_id == driver_id)
    
    trips = query.order_by(Trip.start_time.desc()).offset(skip).limit(limit).all()
    return trips


@router.get("/trips/{trip_id}")
async def get_trip_admin(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get trip by ID."""
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.delete("/trips/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip_admin(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a trip."""
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(trip)
    db.commit()
    return None


# ==================== EVENTS ====================

@router.get("/events")
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    driver_id: Optional[str] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List telematics events."""
    query = db.query(TelematicsEvent)
    
    if driver_id:
        query = query.filter(TelematicsEvent.driver_id == driver_id)
    if event_type:
        query = query.filter(TelematicsEvent.event_type == event_type)
    
    events = query.order_by(TelematicsEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return events


@router.get("/events/stats")
async def get_event_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get event statistics."""
    total_events = db.query(func.count(TelematicsEvent.event_id)).scalar()
    unique_drivers = db.query(func.count(func.distinct(TelematicsEvent.driver_id))).scalar()
    
    event_types = db.query(
        TelematicsEvent.event_type,
        func.count(TelematicsEvent.event_id).label('count')
    ).group_by(TelematicsEvent.event_type).all()
    
    return {
        "total_events": total_events,
        "unique_drivers": unique_drivers,
        "event_types": {et: count for et, count in event_types if et}
    }


# ==================== DASHBOARD STATS ====================

@router.get("/dashboard/stats")
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


@router.get("/dashboard/summary", response_model=AdminDashboardSummary)
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


@router.get("/dashboard/trip-activity", response_model=List[DailyTripActivity])
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


@router.get("/dashboard/risk-distribution", response_model=RiskDistributionResponse)
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


@router.get("/dashboard/safety-events-breakdown", response_model=List[SafetyEventBreakdown])
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


@router.get("/dashboard/policy-type-distribution", response_model=List[PolicyTypeDistribution])
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


# ==================== POLICIES ====================

@router.get("/policies/summary", response_model=PoliciesSummaryResponse)
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


@router.get("/policies", response_model=List[PolicyCardResponse])
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

