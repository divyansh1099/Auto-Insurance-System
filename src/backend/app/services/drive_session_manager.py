"""
Drive Session Manager

Manages active drive sessions and continuous data generation for drivers.
"""

import asyncio
import structlog
from typing import Dict, Optional
from datetime import datetime
import random
import uuid
from sqlalchemy.orm import Session

from app.services.kafka_producer import publish_telematics_event
from app.services.stream_processor import process_telematics_event
from app.models.database import SessionLocal
from app.services.realistic_data_generator import RealisticDataGenerator

logger = structlog.get_logger()


class DriveSession:
    """Represents an active drive session."""
    
    def __init__(self, driver_id: str, device_id: str, start_lat: float, start_lon: float):
        self.driver_id = driver_id
        self.device_id = device_id
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.current_lat = start_lat
        self.current_lon = start_lon
        self.current_speed = 0
        self.start_time = datetime.utcnow()
        self.is_running = True
        self.task: Optional[asyncio.Task] = None
        self.events_generated = 0
        
        # Use realistic data generator for better accuracy
        self.data_generator = RealisticDataGenerator(driver_id, device_id, start_lat, start_lon)
    
    def generate_event(self) -> dict:
        """Generate a single realistic telematics event using physics-based model."""
        # Use realistic data generator
        event = self.data_generator.generate_event(time_interval=10.0)
        
        # Update session state
        self.current_lat = event['latitude']
        self.current_lon = event['longitude']
        self.current_speed = event['speed']
        self.events_generated += 1
        
        return event
    
    async def run(self, interval_seconds: float = 10.0):
        """Run continuous event generation."""
        logger.info("drive_session_started", driver_id=self.driver_id, device_id=self.device_id)
        
        try:
            while self.is_running:
                try:
                    # Check if we should stop before generating
                    if not self.is_running:
                        break
                    
                    # Generate event
                    event = self.generate_event()
                    
                    # Check again before publishing
                    if not self.is_running:
                        break
                    
                    # Process and publish
                    processed_event = process_telematics_event(event)
                    if processed_event:
                        success = publish_telematics_event(processed_event, topic="telematics-events")
                        if success:
                            logger.debug(
                                "drive_event_generated",
                                driver_id=self.driver_id,
                                event_id=event['event_id'],
                                speed=event['speed']
                            )
                    
                    # Wait for next interval (with cancellation check)
                    try:
                        await asyncio.wait_for(
                            asyncio.sleep(interval_seconds),
                            timeout=interval_seconds
                        )
                    except asyncio.CancelledError:
                        # Task was cancelled
                        break
                    
                except asyncio.CancelledError:
                    # Task cancellation requested
                    break
                except Exception as e:
                    logger.error("drive_session_error", driver_id=self.driver_id, error=str(e))
                    # Only sleep if still running
                    if self.is_running:
                        try:
                            await asyncio.sleep(min(interval_seconds, 1.0))
                        except asyncio.CancelledError:
                            break
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        finally:
            # Ensure we mark as stopped
            self.is_running = False
            logger.info("drive_session_stopped", driver_id=self.driver_id, events=self.events_generated)


class DriveSessionManager:
    """Manages active drive sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, DriveSession] = {}
        self._lock = asyncio.Lock()
    
    async def start_session(
        self,
        driver_id: str,
        device_id: Optional[str] = None,
        start_lat: float = 37.7749,
        start_lon: float = -122.4194,
        interval_seconds: float = 10.0
    ) -> bool:
        """
        Start a drive session for a driver.
        
        Returns True if started, False if already running.
        """
        async with self._lock:
            if driver_id in self.sessions:
                session = self.sessions[driver_id]
                if session.is_running:
                    logger.warning("drive_session_already_running", driver_id=driver_id)
                    return False
                else:
                    # Clean up old session
                    del self.sessions[driver_id]
            
            # Create new session
            device_id = device_id or f"DEV-{uuid.uuid4().hex[:8].upper()}"
            session = DriveSession(driver_id, device_id, start_lat, start_lon)
            
            # Start background task
            session.task = asyncio.create_task(session.run(interval_seconds))
            self.sessions[driver_id] = session
            
            logger.info("drive_session_started", driver_id=driver_id, device_id=device_id)
            return True
    
    async def stop_session(self, driver_id: str) -> bool:
        """
        Stop a drive session for a driver.
        
        Returns True if stopped, False if not running.
        """
        async with self._lock:
            if driver_id not in self.sessions:
                logger.warning("drive_session_not_found", driver_id=driver_id)
                return False
            
            session = self.sessions[driver_id]
            if not session.is_running:
                # Clean up anyway
                if session.task:
                    session.task.cancel()
                del self.sessions[driver_id]
                return False
            
            # Stop session FIRST (before canceling task)
            session.is_running = False
            
            # Cancel task and wait for it to finish
            if session.task and not session.task.done():
                session.task.cancel()
                try:
                    # Wait for task to finish cancellation
                    await asyncio.wait_for(session.task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    # Task was cancelled or timed out - that's fine
                    pass
                except Exception as e:
                    logger.warning("task_cancellation_error", driver_id=driver_id, error=str(e))
            
            # Get stats before removing
            events_count = session.events_generated
            
            # Remove from sessions
            del self.sessions[driver_id]
            
            logger.info("drive_session_stopped", driver_id=driver_id, events=events_count)
            return True
    
    def is_session_active(self, driver_id: str) -> bool:
        """Check if a drive session is active."""
        if driver_id not in self.sessions:
            return False
        return self.sessions[driver_id].is_running
    
    def get_session_info(self, driver_id: str) -> Optional[dict]:
        """Get information about an active session."""
        if driver_id not in self.sessions:
            return None
        
        session = self.sessions[driver_id]
        return {
            "driver_id": session.driver_id,
            "device_id": session.device_id,
            "start_time": session.start_time.isoformat(),
            "events_generated": session.events_generated,
            "current_speed": session.current_speed,
            "current_location": {
                "latitude": session.current_lat,
                "longitude": session.current_lon
            }
        }


# Global manager instance
_manager_instance: Optional[DriveSessionManager] = None


def get_drive_session_manager() -> DriveSessionManager:
    """Get or create the global drive session manager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DriveSessionManager()
    return _manager_instance

