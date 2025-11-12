"""
Admin Resources Management Endpoints

This module provides CRUD operations for various resources:
- Vehicles (list, get, delete)
- Devices (list, get, delete)
- Trips (list, get, delete)
- Telematics Events (list, get stats)

All endpoints require admin authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.models.database import (
    get_db, User, Vehicle, Device, Trip, TelematicsEvent
)
from app.utils.auth import get_current_admin_user

router = APIRouter()


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
