"""
Admin CRUD endpoints for managing all entities.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime

from app.models.database import (
    get_db, User, Driver, Vehicle, Device, Trip, 
    RiskScore, Premium, TelematicsEvent, DriverStatistics
)
from app.models.schemas import (
    DriverResponse, DriverCreate, DriverUpdate,
    UserResponse, UserCreate, UserUpdate
)
from app.utils.auth import get_current_admin_user

router = APIRouter()


# ==================== DRIVERS ====================

@router.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all drivers with pagination and search."""
    query = db.query(Driver)
    
    if search:
        query = query.filter(
            (Driver.driver_id.ilike(f"%{search}%")) |
            (Driver.first_name.ilike(f"%{search}%")) |
            (Driver.last_name.ilike(f"%{search}%")) |
            (Driver.email.ilike(f"%{search}%"))
        )
    
    drivers = query.order_by(Driver.created_at.desc()).offset(skip).limit(limit).all()
    return drivers


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver_admin(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get driver by ID."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


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

