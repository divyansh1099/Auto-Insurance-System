from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from typing import Optional, List

from app.models.database import get_db, User, Trip
from app.models.schemas import (
    TripListResponse,
    TripSummaryResponse,
    TripResponse
)
from app.utils.auth import get_current_user

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
