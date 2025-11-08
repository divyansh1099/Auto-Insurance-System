"""
Driver management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.models.database import get_db, Driver, User
from app.models.schemas import (
    DriverCreate,
    DriverResponse,
    DriverUpdate,
    TripListResponse,
    DriverStatisticsResponse
)
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new driver."""
    # Check if email already exists
    existing_driver = db.query(Driver).filter(Driver.email == driver_data.email).first()
    if existing_driver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new driver
    driver_id = f"DRV-{uuid.uuid4().hex[:8].upper()}"
    new_driver = Driver(
        driver_id=driver_id,
        **driver_data.model_dump()
    )

    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    return new_driver


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get driver by ID."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Check if user has permission to view this driver
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver"
        )

    return driver


@router.patch("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    driver_update: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update driver information."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this driver"
        )

    # Update fields
    update_data = driver_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)

    db.commit()
    db.refresh(driver)

    return driver


@router.get("/{driver_id}/trips", response_model=TripListResponse)
async def get_driver_trips(
    driver_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trip history for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view trips for this driver"
        )

    from app.models.database import Trip

    # Get total count
    total = db.query(Trip).filter(Trip.driver_id == driver_id).count()

    # Get paginated trips
    trips = (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id)
        .order_by(Trip.start_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "trips": trips,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{driver_id}/statistics", response_model=DriverStatisticsResponse)
async def get_driver_statistics(
    driver_id: str,
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get driving statistics for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view statistics for this driver"
        )

    from app.models.database import DriverStatistics, TelematicsEvent
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_, extract

    period_end = datetime.now()
    period_start = period_end - timedelta(days=period_days)

    # Try to get pre-aggregated statistics first
    stats = (
        db.query(DriverStatistics)
        .filter(
            DriverStatistics.driver_id == driver_id,
            DriverStatistics.period_start >= period_start.date(),
            DriverStatistics.period_end <= period_end.date()
        )
        .order_by(DriverStatistics.created_at.desc())
        .first()
    )

    if stats:
        return stats

    # If no pre-aggregated stats, calculate from events
    events = (
        db.query(TelematicsEvent)
        .filter(
            TelematicsEvent.driver_id == driver_id,
            TelematicsEvent.timestamp >= period_start,
            TelematicsEvent.timestamp <= period_end
        )
        .all()
    )

    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No events found for this driver in the specified period"
        )

    # Calculate statistics from events
    total_events = len(events)
    speeds = [e.speed for e in events if e.speed is not None]
    harsh_brakes = sum(1 for e in events if e.event_type == 'harsh_brake')
    rapid_accels = sum(1 for e in events if e.event_type == 'rapid_accel')
    speeding = sum(1 for e in events if e.event_type == 'speeding')
    
    # Estimate distance from events (rough calculation: assume 10 seconds between events)
    # Average speed * time = distance
    if speeds:
        avg_speed = sum(speeds) / len(speeds)
        # Estimate: events are ~10 seconds apart, so total time = events * 10 seconds
        total_hours = (total_events * 10) / 3600
        total_miles = avg_speed * total_hours if avg_speed > 0 else 0
    else:
        total_miles = 0
        avg_speed = 0

    # Count trips (unique trip_ids, excluding None)
    unique_trips = len(set(e.trip_id for e in events if e.trip_id))
    total_trips = unique_trips if unique_trips > 0 else 1  # At least 1 trip if events exist

    # Calculate rates per 100 miles
    harsh_braking_rate = (harsh_brakes / total_miles * 100) if total_miles > 0 else 0
    rapid_accel_rate = (rapid_accels / total_miles * 100) if total_miles > 0 else 0
    speeding_rate = (speeding / total_miles * 100) if total_miles > 0 else 0

    # Calculate time-based percentages
    night_driving = sum(1 for e in events if e.timestamp.hour >= 22 or e.timestamp.hour < 6)
    night_driving_pct = (night_driving / total_events * 100) if total_events > 0 else 0
    
    rush_hour = sum(1 for e in events if (7 <= e.timestamp.hour < 9) or (17 <= e.timestamp.hour < 19))
    rush_hour_pct = (rush_hour / total_events * 100) if total_events > 0 else 0
    
    weekend_driving = sum(1 for e in events if e.timestamp.weekday() >= 5)
    weekend_driving_pct = (weekend_driving / total_events * 100) if total_events > 0 else 0

    max_speed = max(speeds) if speeds else 0

    # Return calculated statistics
    return DriverStatisticsResponse(
        driver_id=driver_id,
        period_start=period_start.date(),
        period_end=period_end.date(),
        total_miles=round(total_miles, 2),
        total_trips=total_trips,
        avg_speed=round(avg_speed, 2),
        max_speed=round(max_speed, 2),
        harsh_braking_rate=round(harsh_braking_rate, 4),
        rapid_accel_rate=round(rapid_accel_rate, 4),
        speeding_rate=round(speeding_rate, 4),
        night_driving_pct=round(night_driving_pct, 2),
        rush_hour_pct=round(rush_hour_pct, 2),
        weekend_driving_pct=round(weekend_driving_pct, 2)
    )


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a driver (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    db.delete(driver)
    db.commit()

    return None
