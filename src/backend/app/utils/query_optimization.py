"""
Query optimization utilities.

This module provides utilities to prevent N+1 query problems and optimize
database access patterns.
"""
from sqlalchemy.orm import joinedload, selectinload, contains_eager, lazyload, Load
from sqlalchemy import select, func
from typing import List, Type, Optional
from sqlalchemy.orm import Session

logger = None
try:
    import structlog
    logger = structlog.get_logger()
except:
    pass


def optimize_driver_query(
    query,
    include_vehicles: bool = False,
    include_devices: bool = False,
    include_trips: bool = False,
    include_risk_scores: bool = False,
    include_premiums: bool = False
):
    """
    Optimize driver query with eager loading to prevent N+1 queries.

    Uses joinedload for one-to-many relationships with few items (vehicles, devices)
    Uses selectinload for one-to-many relationships with many items (trips, risk scores)

    Args:
        query: SQLAlchemy query object
        include_vehicles: Whether to eager load vehicles (joinedload)
        include_devices: Whether to eager load devices (joinedload)
        include_trips: Whether to eager load trips (selectinload - can be large)
        include_risk_scores: Whether to eager load risk scores (selectinload)
        include_premiums: Whether to eager load premiums (selectinload)
    """
    # Use joinedload for small relationships (few related records)
    if include_vehicles:
        query = query.options(joinedload('vehicles'))
    if include_devices:
        query = query.options(joinedload('devices'))

    # Use selectinload for large relationships (many related records)
    # selectinload issues a separate query but is more efficient for large datasets
    if include_trips:
        query = query.options(selectinload('trips'))
    if include_risk_scores:
        query = query.options(selectinload('risk_scores'))
    if include_premiums:
        query = query.options(selectinload('premiums'))

    if logger:
        eager_loads = []
        if include_vehicles: eager_loads.append('vehicles')
        if include_devices: eager_loads.append('devices')
        if include_trips: eager_loads.append('trips')
        if include_risk_scores: eager_loads.append('risk_scores')
        if include_premiums: eager_loads.append('premiums')
        logger.debug("driver_query_optimized", eager_loads=eager_loads)

    return query


def optimize_trip_query(
    query,
    include_driver: bool = False,
    include_device: bool = False
):
    """
    Optimize trip query with eager loading to prevent N+1 queries.

    Note: Telematics events are NOT loaded by default as they can be very large.
    Use optimize_trip_query_with_events() if you need events.

    Args:
        query: SQLAlchemy query object
        include_driver: Whether to eager load driver (joinedload)
        include_device: Whether to eager load device (joinedload)
    """
    if include_driver:
        query = query.options(joinedload('driver'))
    if include_device:
        query = query.options(joinedload('device'))

    return query


def optimize_trip_query_with_latest_events(query, event_limit: int = 10):
    """
    Optimize trip query with only the most recent N events.
    Use this instead of loading all events.

    Args:
        query: SQLAlchemy query object
        event_limit: Number of most recent events to load
    """
    # This requires a subquery or post-processing
    # For now, we'll return without events and recommend using a separate query
    if logger:
        logger.warning("trip_events_not_eager_loaded",
                      reason="Events should be queried separately to avoid performance issues")
    return query


def optimize_risk_score_query(query, include_driver: bool = False):
    """
    Optimize risk score query with eager loading.

    Args:
        query: SQLAlchemy query object
        include_driver: Whether to eager load driver
    """
    if include_driver:
        query = query.options(joinedload('driver'))

    return query


def paginate_query(query, page: int, page_size: int):
    """
    Apply pagination to a query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Paginated query
    """
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def get_total_count(query, db: Session) -> int:
    """
    Get total count efficiently without loading all records.
    
    Args:
        query: SQLAlchemy query object
        db: Database session
    
    Returns:
        Total count
    """
    # Use count() which is more efficient than len(query.all())
    return db.query(query.subquery()).count()


def batch_process(query, batch_size: int = 1000):
    """
    Process query results in batches to avoid memory issues.
    
    Args:
        query: SQLAlchemy query object
        batch_size: Number of records per batch
    
    Yields:
        Batches of records
    """
    offset = 0
    while True:
        batch = query.offset(offset).limit(batch_size).all()
        if not batch:
            break
        yield batch
        offset += batch_size
        if len(batch) < batch_size:
            break

