"""
Driver management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from typing import List, Optional
import uuid

from app.models.database import get_db, Driver, User, Trip, RiskScore
from app.models.schemas import (
    DriverCreate,
    DriverResponse,
    DriverUpdate,
    TripListResponse,
    TripSummaryResponse,
    TripResponse,
    DriverStatisticsResponse
)
from app.utils.auth import get_current_user
from app.services.redis_client import get_cached_driver_statistics, cache_driver_statistics

router = APIRouter()


def _normalize_trip_type(trip_type: Optional[str]) -> Optional[str]:
    """Normalize trip_type to valid enum values."""
    if not trip_type:
        return None
    trip_type_lower = trip_type.lower()
    # Map invalid values to valid ones
    mapping = {
        'errand': 'business',
        'work': 'business',
        'commute': 'commute',
        'leisure': 'leisure',
        'business': 'business',
        'unknown': 'unknown'
    }
    return mapping.get(trip_type_lower, 'unknown')


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
    # Optimize query with eager loading if needed
    query = db.query(Driver).filter(Driver.driver_id == driver_id)
    query = optimize_driver_query(query, include_vehicles=False, include_devices=False)
    driver = query.first()

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


@router.get("/{driver_id}/trips/summary", response_model=TripSummaryResponse)
async def get_trip_summary(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trip summary statistics for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view trips for this driver"
        )
    
    from app.services.trip_aggregator import create_trips_from_events
    
    # If no trips exist, try to create them from events
    trip_count = db.query(Trip).filter(Trip.driver_id == driver_id).count()
    if trip_count == 0:
        try:
            create_trips_from_events(driver_id, db, period_days=30)
        except Exception as e:
            pass
    
    # Calculate summary statistics
    total_trips = db.query(func.count(Trip.trip_id)).filter(Trip.driver_id == driver_id).scalar() or 0
    
    total_miles = (
        db.query(func.sum(Trip.distance_miles))
        .filter(Trip.driver_id == driver_id)
        .scalar() or 0.0
    )
    
    # Calculate average trip score (if trip_score exists, otherwise estimate)
    avg_score_query = (
        db.query(func.avg(
            case(
                (Trip.trip_score.isnot(None), Trip.trip_score),
                else_=100 - (
                    func.coalesce(Trip.harsh_braking_count, 0) * 5 +
                    func.coalesce(Trip.rapid_accel_count, 0) * 3 +
                    func.coalesce(Trip.speeding_count, 0) * 8 +
                    func.coalesce(Trip.harsh_corner_count, 0) * 4
                )
            )
        ))
        .filter(Trip.driver_id == driver_id)
    )
    avg_trip_score = avg_score_query.scalar()
    
    return TripSummaryResponse(
        total_trips=total_trips,
        total_miles=round(total_miles, 2),
        avg_trip_score=round(avg_trip_score, 1) if avg_trip_score else None
    )


@router.get("/{driver_id}/trips", response_model=TripListResponse)
async def get_driver_trips(
    driver_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: low, medium, high"),
    search: Optional[str] = Query(None, description="Search by origin/destination city"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trip history for a driver with enhanced fields."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view trips for this driver"
        )

    from app.services.trip_aggregator import create_trips_from_events

    # Optimize: Only check if trips exist (LIMIT 1 is faster than COUNT)
    # This avoids scanning the entire table
    has_trips = db.query(Trip.trip_id).filter(Trip.driver_id == driver_id).limit(1).first()
    if not has_trips:
        try:
            create_trips_from_events(driver_id, db, period_days=30)
        except Exception as e:
            # Log error but continue - trips might not be ready yet
            pass

    # Build query with filters
    # Use indexed column (driver_id) first for optimal performance
    query = db.query(Trip).filter(Trip.driver_id == driver_id)
    
    # Risk level filter - Optimize: Use risk_level column if available, otherwise use trip_score
    # This allows PostgreSQL to use the idx_trips_risk_level index
    if risk_level:
        # First try to use the risk_level column (indexed)
        # If risk_level is NULL, fall back to trip_score-based filtering
        if risk_level == 'low':
            query = query.filter(
                or_(
                    Trip.risk_level == 'low',
                    and_(
                        Trip.risk_level.is_(None),
                        or_(
                            Trip.trip_score >= 80,
                            and_(
                                Trip.trip_score.is_(None),
                                100 - (
                                    func.coalesce(Trip.harsh_braking_count, 0) * 5 +
                                    func.coalesce(Trip.rapid_accel_count, 0) * 3 +
                                    func.coalesce(Trip.speeding_count, 0) * 8 +
                                    func.coalesce(Trip.harsh_corner_count, 0) * 4
                                ) >= 80
                            )
                        )
                    )
                )
            )
        elif risk_level == 'medium':
            query = query.filter(
                or_(
                    Trip.risk_level == 'medium',
                    and_(
                        Trip.risk_level.is_(None),
                        or_(
                            and_(Trip.trip_score >= 60, Trip.trip_score < 80),
                            and_(
                                Trip.trip_score.is_(None),
                                100 - (
                                    func.coalesce(Trip.harsh_braking_count, 0) * 5 +
                                    func.coalesce(Trip.rapid_accel_count, 0) * 3 +
                                    func.coalesce(Trip.speeding_count, 0) * 8 +
                                    func.coalesce(Trip.harsh_corner_count, 0) * 4
                                ) >= 60,
                                100 - (
                                    func.coalesce(Trip.harsh_braking_count, 0) * 5 +
                                    func.coalesce(Trip.rapid_accel_count, 0) * 3 +
                                    func.coalesce(Trip.speeding_count, 0) * 8 +
                                    func.coalesce(Trip.harsh_corner_count, 0) * 4
                                ) < 80
                            )
                        )
                    )
                )
            )
        elif risk_level == 'high':
            query = query.filter(
                or_(
                    Trip.risk_level == 'high',
                    and_(
                        Trip.risk_level.is_(None),
                        or_(
                            Trip.trip_score < 60,
                            and_(
                                Trip.trip_score.is_(None),
                                100 - (
                                    func.coalesce(Trip.harsh_braking_count, 0) * 5 +
                                    func.coalesce(Trip.rapid_accel_count, 0) * 3 +
                                    func.coalesce(Trip.speeding_count, 0) * 8 +
                                    func.coalesce(Trip.harsh_corner_count, 0) * 4
                                ) < 60
                            )
                        )
                    )
                )
            )
    
    # Search filter - Optimize: Use case-insensitive search but try to use indexes
    # For better performance with ILIKE, consider using full-text search or trigram indexes
    if search:
        search_term = search.strip()
        if search_term:  # Only search if not empty
            # Use OR with indexed columns first, then ILIKE
            # PostgreSQL can use indexes for prefix searches (without leading %)
            # For now, we'll use ILIKE but recommend adding trigram indexes for better performance
            query = query.filter(
                or_(
                    Trip.origin_city.ilike(f"%{search_term}%"),
                    Trip.origin_state.ilike(f"%{search_term}%"),
                    Trip.destination_city.ilike(f"%{search_term}%"),
                    Trip.destination_state.ilike(f"%{search_term}%")
                )
            )

    # Optimize: Get total count efficiently
    # For large datasets, consider using an approximate count or caching
    # For now, we'll use the actual count but it's optimized by the filters above
    total = query.count()

    # Get paginated trips
    # Order by start_time DESC uses idx_trips_start_time index
    # Combined with driver_id filter, this should use idx_trips_driver_id + idx_trips_start_time
    trips = (
        query
        .order_by(Trip.start_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    # Enrich trips with calculated fields and convert to TripResponse
    enriched_trips = []
    for trip in trips:
        # Calculate trip_score if not exists
        trip_score = trip.trip_score
        if trip_score is None:
            trip_score = max(0, min(100, 100 - (
                (trip.harsh_braking_count or 0) * 5 +
                (trip.rapid_accel_count or 0) * 3 +
                (trip.speeding_count or 0) * 8 +
                (trip.harsh_corner_count or 0) * 4
            )))
        
        # Determine risk_level
        if trip_score >= 80:
            risk_level_str = 'low'
        elif trip_score >= 60:
            risk_level_str = 'medium'
        else:
            risk_level_str = 'high'
        
        # Get location fields (handle if columns don't exist)
        origin_city = getattr(trip, 'origin_city', None)
        origin_state = getattr(trip, 'origin_state', None)
        destination_city = getattr(trip, 'destination_city', None)
        destination_state = getattr(trip, 'destination_state', None)
        
        # Create TripResponse with all fields
        trip_dict = {
            'trip_id': trip.trip_id,
            'driver_id': trip.driver_id,
            'device_id': trip.device_id,
            'start_time': trip.start_time,
            'end_time': trip.end_time,
            'duration_minutes': trip.duration_minutes,
            'distance_miles': trip.distance_miles,
            'start_latitude': trip.start_latitude,
            'start_longitude': trip.start_longitude,
            'end_latitude': trip.end_latitude,
            'end_longitude': trip.end_longitude,
            'avg_speed': trip.avg_speed,
            'max_speed': trip.max_speed,
            'harsh_braking_count': trip.harsh_braking_count or 0,
            'rapid_accel_count': trip.rapid_accel_count or 0,
            'speeding_count': trip.speeding_count or 0,
            'harsh_corner_count': trip.harsh_corner_count or 0,
            'phone_usage_detected': trip.phone_usage_detected or False,
            'trip_type': _normalize_trip_type(trip.trip_type),
            'created_at': trip.created_at or trip.start_time,
            'origin_city': origin_city,
            'origin_state': origin_state,
            'destination_city': destination_city,
            'destination_state': destination_state,
            'trip_score': trip_score,
            'risk_level': risk_level_str,
        }
        
        enriched_trips.append(TripResponse(**trip_dict))

    return TripListResponse(
        trips=enriched_trips,
        total=total,
        page=page,
        page_size=page_size
    )


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

    # Try to get cached statistics first
    cache_key = f"{driver_id}:{period_days}"
    cached_stats = get_cached_driver_statistics(cache_key)
    if cached_stats:
        return DriverStatisticsResponse(**cached_stats)

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

    # Prepare response
    stats_response = DriverStatisticsResponse(
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
    
    # Cache the statistics
    cache_driver_statistics(cache_key, stats_response.dict())
    
    return stats_response


@router.get("/{driver_id}/summary")
async def get_driver_summary(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get driver summary for dashboard."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's summary"
        )

    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Get trip summary (uses actual trips, not events)
    trip_summary = await get_trip_summary(driver_id, db, current_user)
    
    # Get risk score from database (use latest RiskScore record for consistency)
    latest_risk_score = (
        db.query(RiskScore)
        .filter(RiskScore.driver_id == driver_id)
        .order_by(RiskScore.calculation_date.desc())
        .first()
    )
    
    if latest_risk_score:
        risk_score = latest_risk_score.risk_score
        safety_score = max(0, 100 - risk_score)
    else:
        # If no risk score exists, calculate one
        from app.services.risk_scoring import calculate_risk_score_for_driver
        try:
            risk_data = calculate_risk_score_for_driver(driver_id, db, period_days=30)
            risk_score = risk_data.get('risk_score', 50)
            safety_score = max(0, 100 - risk_score)
        except:
            risk_score = 50
            safety_score = 50

    # Get premium info
    try:
        from app.routers.pricing import get_current_premium
        premium_response = await get_current_premium(driver_id, db, current_user)
        current_premium = premium_response.monthly_premium if hasattr(premium_response, 'monthly_premium') else 100
        traditional_premium = 150.0  # Mock traditional premium
        total_savings = (traditional_premium - current_premium) * 12
    except Exception as e:
        current_premium = 127.5
        traditional_premium = 150.0
        total_savings = 270.0

    # Calculate reward points using the same method as rewards endpoint
    from app.routers.rewards import calculate_reward_points
    reward_points = calculate_reward_points(driver_id, db)

    # Calculate score change (compare current avg with previous period)
    try:
        from datetime import datetime, timedelta
        # Get trips from last 30 days
        recent_trips = db.query(Trip).filter(
            Trip.driver_id == driver_id,
            Trip.start_time >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        # Get trips from previous 30 days (30-60 days ago)
        previous_trips = db.query(Trip).filter(
            Trip.driver_id == driver_id,
            Trip.start_time >= datetime.utcnow() - timedelta(days=60),
            Trip.start_time < datetime.utcnow() - timedelta(days=30)
        ).all()
        
        # Calculate average scores
        recent_avg = trip_summary.avg_trip_score or 0
        if previous_trips:
            prev_scores = []
            for trip in previous_trips:
                if trip.trip_score is not None:
                    prev_scores.append(trip.trip_score)
                else:
                    # Calculate from events
                    score = 100 - (
                        (trip.harsh_braking_count or 0) * 5 +
                        (trip.rapid_accel_count or 0) * 3 +
                        (trip.speeding_count or 0) * 8 +
                        (trip.harsh_corner_count or 0) * 4
                    )
                    prev_scores.append(max(0, min(100, score)))
            prev_avg = sum(prev_scores) / len(prev_scores) if prev_scores else recent_avg
            score_change = recent_avg - prev_avg
            score_change_str = f"{'+' if score_change >= 0 else ''}{round(score_change)}"
            is_improving = score_change > 0
        else:
            score_change_str = "+0"
            is_improving = True
    except:
        score_change_str = "+0"
        is_improving = True

    return {
        "driver_name": f"{driver.first_name} {driver.last_name}",
        "safety_score": round(safety_score),
        "risk_score": round(risk_score),
        "total_savings": round(total_savings, 2),
        "reward_points": reward_points,
        "total_trips": trip_summary.total_trips,
        "miles_driven": round(trip_summary.total_miles),
        "avg_trip_score": round(trip_summary.avg_trip_score) if trip_summary.avg_trip_score else 0,
        "score_change": score_change_str,
        "is_improving": is_improving
    }


@router.get("/{driver_id}/alerts")
async def get_safety_alerts(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get safety alerts for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    from app.models.database import TelematicsEvent
    from datetime import datetime, timedelta
    
    # Get recent events (last 7 days)
    cutoff = datetime.utcnow() - timedelta(days=7)
    events = db.query(TelematicsEvent).filter(
        TelematicsEvent.driver_id == driver_id,
        TelematicsEvent.timestamp >= cutoff
    ).all()

    alerts = []
    
    # Count harsh braking
    harsh_braking = [e for e in events if e.event_type == 'harsh_brake']
    if len(harsh_braking) >= 3:
        alerts.append({
            "type": "hard_braking",
            "description": "Multiple hard braking events detected",
            "incidents": len(harsh_braking),
            "period": "recent trips"
        })
    
    # Count rapid acceleration
    rapid_accel = [e for e in events if e.event_type == 'rapid_accel']
    if len(rapid_accel) >= 5:
        alerts.append({
            "type": "rapid_acceleration",
            "description": "Aggressive acceleration patterns",
            "incidents": len(rapid_accel),
            "period": "recent events"
        })
    
    # Count speeding
    speeding = [e for e in events if e.event_type == 'speeding']
    if len(speeding) >= 3:
        alerts.append({
            "type": "speeding",
            "description": "Multiple speeding incidents detected",
            "incidents": len(speeding),
            "period": "recent trips"
        })

    return {
        "total_alerts": len(alerts),
        "alerts": alerts
    }


@router.get("/{driver_id}/risk-factors")
async def get_risk_factors(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get risk factor analysis for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    from app.models.database import TelematicsEvent
    from datetime import datetime, timedelta
    
    # Get events from last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    events = db.query(TelematicsEvent).filter(
        TelematicsEvent.driver_id == driver_id,
        TelematicsEvent.timestamp >= cutoff
    ).all()

    # Count risk factors
    speeding_count = len([e for e in events if e.event_type == 'speeding'])
    hard_braking_count = len([e for e in events if e.event_type == 'harsh_brake'])
    acceleration_count = len([e for e in events if e.event_type == 'rapid_accel'])
    night_driving_count = len([e for e in events if e.timestamp.hour >= 22 or e.timestamp.hour < 6])
    phone_usage_count = len([e for e in events if e.event_type == 'phone_usage'])
    
    # High risk areas (mock - would use geolocation data)
    high_risk_areas = len(events) // 10  # Simplified

    return {
        "speeding": speeding_count,
        "hard_braking": hard_braking_count,
        "acceleration": acceleration_count,
        "night_driving": night_driving_count,
        "high_risk_areas": high_risk_areas,
        "phone_usage": phone_usage_count
    }


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
