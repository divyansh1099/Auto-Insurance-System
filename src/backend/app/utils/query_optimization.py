"""
Query optimization utilities.
"""
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from sqlalchemy import select
from typing import List, Type, Optional
from sqlalchemy.orm import Session

logger = None
try:
    import structlog
    logger = structlog.get_logger()
except:
    pass


def optimize_driver_query(query, include_vehicles: bool = False, include_devices: bool = False):
    """
    Optimize driver query with eager loading.
    
    Args:
        query: SQLAlchemy query object
        include_vehicles: Whether to eager load vehicles
        include_devices: Whether to eager load devices
    """
    if include_vehicles:
        query = query.options(joinedload('vehicles'))
    if include_devices:
        query = query.options(joinedload('devices'))
    
    return query


def optimize_trip_query(query, include_events: bool = False):
    """
    Optimize trip query with eager loading.
    
    Args:
        query: SQLAlchemy query object
        include_events: Whether to eager load events (use selectinload for large datasets)
    """
    if include_events:
        # Use selectinload for better performance with large datasets
        query = query.options(selectinload('events'))
    
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

