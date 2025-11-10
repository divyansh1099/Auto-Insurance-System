"""
Real-Time Driving Behavior and Pricing API

Provides WebSocket endpoints for real-time updates and REST endpoints
for real-time analysis.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict
import structlog
import asyncio

from app.models.database import get_db, User, SessionLocal
from app.utils.auth import get_current_user
from app.services.websocket_manager import get_connection_manager
from app.services.realtime_ml_inference import get_analyzer, analyze_event_realtime
from app.services.realtime_pricing import get_pricing_engine, calculate_realtime_premium
from app.services.kafka_consumer import detect_trip_from_event
from app.services.drive_session_manager import get_drive_session_manager
from pydantic import BaseModel, Field
from typing import Optional

logger = structlog.get_logger()
router = APIRouter()


@router.websocket("/ws/{driver_id}")
async def websocket_endpoint(websocket: WebSocket, driver_id: str):
    """
    WebSocket endpoint for real-time driving updates.
    
    Connects driver to receive:
    - Real-time driving behavior analysis
    - Safety alerts
    - Dynamic pricing updates
    - Risk score changes
    """
    manager = get_connection_manager()
    await manager.connect(websocket, driver_id)
    
    # Subscribe to Redis channels for this driver (pub/sub)
    try:
        from app.services.redis_subscriber import get_subscriber
        subscriber = get_subscriber()
        if subscriber.running:
            await subscriber.subscribe_to_driver(driver_id)
            logger.debug("subscribed_to_redis_channels", driver_id=driver_id)
    except Exception as e:
        logger.warning("redis_subscription_failed", driver_id=driver_id, error=str(e))
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            'type': 'connected',
            'driver_id': driver_id,
            'message': 'Connected to real-time updates'
        }, websocket)
        
        # Send initial analysis if available
        try:
            db = SessionLocal()
            analyzer = get_analyzer()
            initial_analysis = analyzer.get_current_analysis(driver_id)
            
            if initial_analysis:
                # Send initial driving data
                await manager.send_driving_update(driver_id, {
                    'risk_score': initial_analysis.get('risk_score'),
                    'safety_score': initial_analysis.get('safety_score'),
                    'behavior_metrics': initial_analysis.get('behavior_metrics', {})
                })
                
                # Send initial pricing
                from app.services.realtime_pricing import calculate_realtime_premium
                if initial_analysis.get('behavior_metrics'):
                    pricing = calculate_realtime_premium(
                        driver_id=driver_id,
                        risk_score=initial_analysis.get('risk_score', 50),
                        behavior_metrics=initial_analysis.get('behavior_metrics', {}),
                        db=db
                    )
                    await manager.send_pricing_update(driver_id, pricing)
            db.close()
        except Exception as e:
            logger.warning("initial_analysis_failed", driver_id=driver_id, error=str(e))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (can be used for ping/pong or commands)
                data = await websocket.receive_text()
                # Echo back or handle commands
                await manager.send_personal_message({
                    'type': 'pong',
                    'message': 'Connection active'
                }, websocket)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("websocket_error", driver_id=driver_id, error=str(e))
                break
                
    except Exception as e:
        logger.error("websocket_error", driver_id=driver_id, error=str(e))
    finally:
        # Unsubscribe from Redis channels when connection closes
        try:
            from app.services.redis_subscriber import get_subscriber
            subscriber = get_subscriber()
            if subscriber.running:
                await subscriber.unsubscribe_from_driver(driver_id)
                logger.debug("unsubscribed_from_redis_channels", driver_id=driver_id)
        except Exception as e:
            logger.warning("redis_unsubscription_failed", driver_id=driver_id, error=str(e))
        
        # Disconnect WebSocket
        manager.disconnect(websocket)


class StartDriveRequest(BaseModel):
    """Request to start a drive session."""
    device_id: Optional[str] = Field(None, description="Device ID (auto-generated if not provided)")
    start_latitude: float = Field(37.7749, ge=-90, le=90, description="Starting latitude")
    start_longitude: float = Field(-122.4194, ge=-180, le=180, description="Starting longitude")
    interval_seconds: float = Field(10.0, ge=1, le=60, description="Interval between events in seconds")


@router.post("/start-drive/{driver_id}")
async def start_drive(
    driver_id: str,
    request: StartDriveRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start a live drive session.
    
    Begins continuous telematics data generation for the specified driver.
    Data will be generated at regular intervals and sent to Kafka for processing.
    """
    manager = get_drive_session_manager()
    
    # Check if session already exists
    if manager.is_session_active(driver_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Drive session already active for this driver"
        )
    
    # Start session
    success = await manager.start_session(
        driver_id=driver_id,
        device_id=request.device_id,
        start_lat=request.start_latitude,
        start_lon=request.start_longitude,
        interval_seconds=request.interval_seconds
    )
    
    if success:
        return {
            "message": "Drive session started",
            "driver_id": driver_id,
            "status": "active"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start drive session"
        )


@router.post("/stop-drive/{driver_id}")
async def stop_drive(
    driver_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Stop a live drive session.
    
    Stops continuous telematics data generation for the specified driver.
    Also clears the real-time analyzer's event window for this driver.
    """
    manager = get_drive_session_manager()
    
    # Get session info before stopping
    session_info = manager.get_session_info(driver_id)
    
    # Stop the session
    success = await manager.stop_session(driver_id)
    
    # Clear analyzer data for this driver (so analysis stops updating)
    try:
        analyzer = get_analyzer()
        analyzer.clear_driver_data(driver_id)
        logger.info("analyzer_data_cleared", driver_id=driver_id)
    except Exception as e:
        logger.warning("failed_to_clear_analyzer", driver_id=driver_id, error=str(e))
    
    # Clear Redis cache for this driver
    try:
        from app.services.redis_client import get_redis_client
        redis_client = get_redis_client()
        if redis_client:
            redis_client.delete(f"realtime:analysis:{driver_id}")
            redis_client.delete(f"realtime:pricing:{driver_id}")
            logger.info("redis_cache_cleared", driver_id=driver_id)
    except Exception as e:
        logger.warning("failed_to_clear_redis", driver_id=driver_id, error=str(e))
    
    # Verify it's actually stopped
    await asyncio.sleep(0.5)  # Brief wait to ensure task cancellation
    is_still_active = manager.is_session_active(driver_id)
    
    if is_still_active:
        logger.warning("drive_session_stop_failed", driver_id=driver_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop drive session. Please try again."
        )
    
    if success or session_info:
        return {
            "message": "Drive session stopped",
            "driver_id": driver_id,
            "status": "stopped",
            "session_info": session_info
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active drive session found for this driver"
        )


@router.get("/drive-status/{driver_id}")
async def get_drive_status(
    driver_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a drive session.
    
    Returns information about an active drive session if one exists.
    """
    manager = get_drive_session_manager()
    
    is_active = manager.is_session_active(driver_id)
    session_info = manager.get_session_info(driver_id) if is_active else None
    
    return {
        "driver_id": driver_id,
        "is_active": is_active,
        "session_info": session_info
    }


@router.get("/analysis/{driver_id}")
async def get_realtime_analysis(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current real-time analysis for a driver.
    
    Returns current risk score, behavior metrics, and safety alerts.
    Only returns analysis if there's an active drive session or recent events.
    """
    # Check if there's an active drive session
    manager = get_drive_session_manager()
    has_active_session = manager.is_session_active(driver_id)
    
    analyzer = get_analyzer()
    analysis = analyzer.get_current_analysis(driver_id)
    
    # If no active session and no analysis, return empty/null
    if not has_active_session and not analysis:
        return {
            "analysis": None,
            "pricing": None,
            "has_active_session": False,
            "message": "No active drive session. Start a drive to see real-time analysis."
        }
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    analyzer = get_analyzer()
    analysis = analyzer.get_current_analysis(driver_id)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recent data available for analysis"
        )

    # Calculate real-time pricing
    pricing = calculate_realtime_premium(
        driver_id=driver_id,
        risk_score=analysis['risk_score'],
        behavior_metrics=analysis['behavior_metrics'],
        db=db
    )

    return {
        'analysis': analysis,
        'pricing': pricing
    }


@router.post("/process-event/{driver_id}")
async def process_event_realtime(
    driver_id: str,
    event: Dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a telematics event in real-time.
    
    This endpoint:
    1. Analyzes the event using ML model
    2. Detects safety issues
    3. Updates pricing
    4. Sends real-time updates via WebSocket
    """
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Ensure driver_id matches
    event['driver_id'] = driver_id

    # Analyze event in real-time
    analysis = analyze_event_realtime(event)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to analyze event"
        )

    # Calculate real-time pricing
    pricing = calculate_realtime_premium(
        driver_id=driver_id,
        risk_score=analysis['risk_score'],
        behavior_metrics=analysis['behavior_metrics'],
        db=db
    )

    # Send updates via WebSocket
    manager = get_connection_manager()
    
    # Send driving update
    await manager.send_driving_update(driver_id, {
        'risk_score': analysis['risk_score'],
        'safety_score': analysis['safety_score'],
        'behavior_metrics': analysis['behavior_metrics']
    })

    # Send safety alerts if any
    if analysis.get('safety_alerts'):
        for alert in analysis['safety_alerts']:
            await manager.send_safety_alert(driver_id, alert)

    # Send pricing update
    await manager.send_pricing_update(driver_id, pricing)

    # Send risk score update
    await manager.send_risk_score_update(driver_id, {
        'risk_score': analysis['risk_score'],
        'safety_score': analysis['safety_score']
    })

    return {
        'analysis': analysis,
        'pricing': pricing,
        'alerts_sent': len(analysis.get('safety_alerts', []))
    }

