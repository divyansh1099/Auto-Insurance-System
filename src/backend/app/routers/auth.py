"""
Authentication endpoints.
"""

from datetime import timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import uuid
import random

from app.config import get_settings
from app.models.database import get_db, User
from app.models.schemas import Token, UserLogin, UserCreate, UserResponse, QuoteRequest, QuoteResponse
from app.utils.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user
)
from app.utils.rate_limit import limiter

settings = get_settings()
router = APIRouter()


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # Rate limit: 5 login attempts per minute per IP
async def login(request: Request, user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    # Input validation
    if not user_credentials.username or not user_credentials.username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required"
        )
    
    if not user_credentials.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    # Authenticate user (this handles user existence, password verification, and timing attack prevention)
    user = authenticate_user(db, user_credentials.username.strip(), user_credentials.password)

    if not user:
        # Always return same error message to prevent username enumeration via timing attacks
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active (after authentication to prevent information leakage)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact administrator.",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "driver_id": user.driver_id},
        expires_delta=access_token_expires
    )

    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Input validation
    if not user_data.username or not user_data.username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required"
        )
    
    if len(user_data.username.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters"
        )
    
    if len(user_data.username.strip()) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be less than 50 characters"
        )
    
    if not user_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    if len(user_data.password) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be less than 128 characters"
        )
    
    username = user_data.username.strip()
    
    # Check if username exists (with proper error handling for race conditions)
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    # Use try-except to handle potential race conditions
    try:
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=username,
            email=user_data.email,
            hashed_password=hashed_password,
            driver_id=user_data.driver_id,
            is_active=user_data.is_active if user_data.is_active is not None else True,
            is_admin=user_data.is_admin if user_data.is_admin is not None else False
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        # Check if it's a unique constraint violation (race condition)
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    return new_user


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user."""
    # In a real implementation, you might want to blacklist the token
    return {"message": "Successfully logged out"}


@router.post("/quote-request", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")  # Rate limit quote requests
async def request_quote(request: Request, quote_data: QuoteRequest, db: Session = Depends(get_db)):
    """
    Submit a quote request for background check.
    This does not create a user account, but collects information for quote generation.
    """
    # Generate a unique quote ID
    quote_id = f"QUOTE-{uuid.uuid4().hex[:8].upper()}"
    
    # Simulate background check and quote calculation
    # In a real system, this would:
    # 1. Check driving record
    # 2. Check credit score
    # 3. Analyze risk factors
    # 4. Calculate premium based on multiple factors
    
    # Base premium calculation (simplified)
    base_premium = 150.0  # Base monthly premium
    
    # Age factor
    today = date.today()
    age = today.year - quote_data.date_of_birth.year - ((today.month, today.day) < (quote_data.date_of_birth.month, quote_data.date_of_birth.day))
    
    if age < 25:
        age_factor = 1.5
    elif age < 30:
        age_factor = 1.3
    elif age < 50:
        age_factor = 1.0
    else:
        age_factor = 1.1
    
    # Experience factor
    if quote_data.years_licensed < 1:
        experience_factor = 1.4
    elif quote_data.years_licensed < 3:
        experience_factor = 1.2
    elif quote_data.years_licensed < 5:
        experience_factor = 1.1
    else:
        experience_factor = 1.0
    
    # Mileage factor
    mileage_factor = 1.0
    if quote_data.annual_mileage:
        if quote_data.annual_mileage > 15000:
            mileage_factor = 1.2
        elif quote_data.annual_mileage > 12000:
            mileage_factor = 1.1
        elif quote_data.annual_mileage < 5000:
            mileage_factor = 0.9
    
    # Calculate premium
    monthly_premium = base_premium * age_factor * experience_factor * mileage_factor
    annual_premium = monthly_premium * 12
    
    # Traditional insurance estimate (higher)
    traditional_premium = monthly_premium * 1.4  # 40% more than telematics
    discount_percentage = round(((traditional_premium - monthly_premium) / traditional_premium) * 100, 1)
    
    # Add some randomness to make it feel realistic (±5%)
    variation = random.uniform(0.95, 1.05)
    monthly_premium = round(monthly_premium * variation, 2)
    annual_premium = round(monthly_premium * 12, 2)
    
    # In a real system, you would:
    # 1. Store the quote request in a database
    # 2. Queue it for background check processing
    # 3. Send confirmation email
    # 4. Schedule follow-up
    
    return QuoteResponse(
        quote_id=quote_id,
        estimated_monthly_premium=monthly_premium,
        estimated_annual_premium=annual_premium,
        discount_percentage=discount_percentage,
        message=f"Thank you {quote_data.first_name}! We've received your information and will run a background check. "
                f"Based on your initial profile, we estimate you could save up to {discount_percentage}% compared to traditional insurance. "
                f"An agent will contact you within 24 hours with your personalized quote.",
        status="pending_background_check"
    )
