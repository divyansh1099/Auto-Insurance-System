from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import uuid

from app.models.database import get_db, Driver, User
from app.models.schemas import (
    DriverCreate,
    DriverResponse,
    DriverUpdate
)
from app.utils.auth import get_current_user
from app.utils.query_optimization import optimize_driver_query
from app.services.audit import log_action

router = APIRouter()

@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    request: Request,
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

    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action="CREATE",
        resource_type="Driver",
        resource_id=driver_id,
        details=driver_data.model_dump(mode='json'),
        ip_address=request.client.host
    )

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
    request: Request,
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

    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action="UPDATE",
        resource_type="Driver",
        resource_id=driver_id,
        details=update_data,
        ip_address=request.client.host
    )

    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    request: Request,
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

    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action="DELETE",
        resource_type="Driver",
        resource_id=driver_id,
        details={"driver_id": driver_id},
        ip_address=request.client.host
    )

    return None
