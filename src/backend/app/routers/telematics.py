"""
Telematics data ingestion endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import structlog

from app.models.database import get_db, User
from app.models.schemas import (
    TelematicsEventCreate,
    TelematicsEventResponse,
    TelematicsEventBatch,
    MessageResponse
)
from app.utils.auth import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.post("/events", response_model=TelematicsEventResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    event: TelematicsEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest a single telematics event."""
    try:
        # Get driver_id from device_id (in real implementation, query from devices table)
        # For now, use current user's driver_id
        driver_id = current_user.driver_id

        if not driver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver not associated with user"
            )

        # Create event ID
        event_id = f"EVT-{uuid.uuid4().hex[:12].upper()}"

        # In a production system, we would:
        # 1. Validate the event data
        # 2. Publish to Kafka for stream processing
        # 3. Store in database

        # For MVP, create a simple response
        event_data = event.model_dump()
        event_data["event_id"] = event_id
        event_data["driver_id"] = driver_id

        logger.info(
            "telematics_event_ingested",
            event_id=event_id,
            driver_id=driver_id,
            event_type=event.event_type
        )

        return TelematicsEventResponse(**event_data, created_at=event.timestamp)

    except Exception as e:
        logger.error("telematics_ingestion_error", error=str(e))
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
    """Ingest a batch of telematics events."""
    try:
        driver_id = current_user.driver_id

        if not driver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver not associated with user"
            )

        # In a production system, publish batch to Kafka
        event_count = len(batch.events)

        logger.info(
            "telematics_batch_ingested",
            driver_id=driver_id,
            event_count=event_count
        )

        return MessageResponse(
            message=f"Successfully ingested {event_count} events",
            status="success"
        )

    except Exception as e:
        logger.error("telematics_batch_ingestion_error", error=str(e))
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
