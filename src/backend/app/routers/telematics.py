"""
Telematics data ingestion endpoints for near real-time data processing.

This router handles real-time ingestion of telematics data from devices/smartphones,
validates and cleans the data, and publishes to Kafka for stream processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import structlog

from app.models.database import get_db, User, Device
from app.models.schemas import (
    TelematicsEventCreate,
    TelematicsEventResponse,
    TelematicsEventBatch,
    MessageResponse
)
from app.utils.auth import get_current_user
from app.services.kafka_producer import publish_telematics_event, publish_telematics_events_batch
from app.services.stream_processor import process_telematics_event, process_telematics_events_batch

logger = structlog.get_logger()
router = APIRouter()


@router.post("/events", response_model=TelematicsEventResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    event: TelematicsEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a single telematics event in near real-time.
    
    This endpoint:
    1. Validates the event data
    2. Cleans and enriches the event
    3. Publishes to Kafka for stream processing
    4. Returns immediately (async processing)
    
    The event will be processed by the Kafka consumer and stored in PostgreSQL.
    """
    try:
        # Get driver_id from device_id or current user
        driver_id = current_user.driver_id
        
        # If device_id is provided, try to get driver_id from device
        if event.device_id:
            device = db.query(Device).filter(Device.device_id == event.device_id).first()
            if device:
                driver_id = device.driver_id
            elif not driver_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Device not found or driver not associated with user"
                )

        if not driver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver not associated with user"
            )

        # Create event ID if not provided
        event_id = event.event_id or f"EVT-{uuid.uuid4().hex[:12].upper()}"

        # Prepare event data
        event_data = event.model_dump()
        event_data["event_id"] = event_id
        event_data["driver_id"] = driver_id
        
        # Ensure timestamp is set
        if not event_data.get("timestamp"):
            event_data["timestamp"] = datetime.utcnow()

        # Process event (validate, clean, enrich)
        processed_event = process_telematics_event(event_data)
        
        if not processed_event:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Event validation failed"
            )

        # Publish to Kafka for near real-time processing
        success = publish_telematics_event(processed_event, topic="telematics-events")
        
        if not success:
            logger.warning("kafka_publish_failed_fallback_to_db", event_id=event_id)
            # Fallback: store directly in database if Kafka fails
            from app.models.database import TelematicsEvent
            db_event = TelematicsEvent(**processed_event)
            db.add(db_event)
            db.commit()
        else:
            logger.info(
                "telematics_event_ingested",
                event_id=event_id,
                driver_id=driver_id,
                event_type=event.event_type,
                kafka_published=True
            )

        return TelematicsEventResponse(**processed_event, created_at=processed_event.get('timestamp', datetime.utcnow()))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("telematics_ingestion_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error ingesting telematics event"
        )


@router.post("/events/batch", response_model=MessageResponse)
async def ingest_events_batch(
    batch: TelematicsEventBatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a batch of telematics events in near real-time.
    
    Optimized for high-throughput ingestion from devices/smartphones.
    Events are validated, cleaned, and published to Kafka for processing.
    """
    try:
        driver_id = current_user.driver_id

        if not driver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver not associated with user"
            )

        # Prepare events with driver_id and event_ids
        events_to_process = []
        for event in batch.events:
            event_dict = event.model_dump() if hasattr(event, 'model_dump') else event
            event_dict["event_id"] = event_dict.get("event_id") or f"EVT-{uuid.uuid4().hex[:12].upper()}"
            event_dict["driver_id"] = driver_id
            
            # Set timestamp if missing
            if not event_dict.get("timestamp"):
                event_dict["timestamp"] = datetime.utcnow()
            
            events_to_process.append(event_dict)

        # Process batch (validate, clean, enrich)
        processed_events, invalid_events = process_telematics_events_batch(events_to_process)

        if invalid_events:
            logger.warning(
                "batch_contains_invalid_events",
                invalid_count=len(invalid_events),
                total=len(events_to_process)
            )

        # Publish valid events to Kafka
        published_count = 0
        if processed_events:
            published_count = publish_telematics_events_batch(processed_events, topic="telematics-events")
        
        logger.info(
            "telematics_batch_ingested",
            driver_id=driver_id,
            total_events=len(events_to_process),
            processed=len(processed_events),
            published=published_count,
            invalid=len(invalid_events)
        )

        return MessageResponse(
            message=f"Successfully ingested {published_count} of {len(events_to_process)} events",
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("telematics_batch_ingestion_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error ingesting batch events"
        )


@router.get("/devices/{device_id}/health")
async def check_device_health(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check device health status."""
    from app.models.database import Device
    from datetime import datetime, timedelta

    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Check permissions
    if not current_user.is_admin and current_user.driver_id != device.driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this device"
        )

    # Determine health status
    health_status = "healthy"
    if device.last_heartbeat:
        time_since_heartbeat = datetime.utcnow() - device.last_heartbeat
        if time_since_heartbeat > timedelta(hours=24):
            health_status = "stale"
        elif time_since_heartbeat > timedelta(hours=72):
            health_status = "offline"

    return {
        "device_id": device_id,
        "is_active": device.is_active,
        "health_status": health_status,
        "last_heartbeat": device.last_heartbeat,
        "firmware_version": device.firmware_version
    }
