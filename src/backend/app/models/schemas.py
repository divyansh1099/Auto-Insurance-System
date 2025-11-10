"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# Enums
class EventType(str, Enum):
    """Telematics event types."""
    NORMAL = "normal"
    HARSH_BRAKE = "harsh_brake"
    RAPID_ACCEL = "rapid_accel"
    SPEEDING = "speeding"
    HARSH_CORNER = "harsh_corner"
    PHONE_USAGE = "phone_usage"


class RiskCategory(str, Enum):
    """Risk score categories."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    HIGH_RISK = "high_risk"


class TripType(str, Enum):
    """Trip types."""
    COMMUTE = "commute"
    LEISURE = "leisure"
    BUSINESS = "business"
    UNKNOWN = "unknown"


# Telematics Schemas
class TelematicsEventBase(BaseModel):
    """Base telematics event schema."""
    device_id: str
    timestamp: datetime
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: float = Field(..., ge=0, le=150)
    acceleration: float
    braking_force: Optional[float] = None
    heading: float = Field(..., ge=0, le=360)
    altitude: Optional[float] = None
    gps_accuracy: float
    event_type: EventType = EventType.NORMAL
    trip_id: Optional[str] = None

    @validator('speed')
    def speed_reasonable(cls, v):
        if v > 150:
            raise ValueError('Speed exceeds maximum reasonable value')
        return v


class TelematicsEventCreate(TelematicsEventBase):
    """Schema for creating telematics event."""
    pass


class TelematicsEventResponse(TelematicsEventBase):
    """Schema for telematics event response."""
    event_id: str
    driver_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TelematicsEventBatch(BaseModel):
    """Schema for batch telematics events."""
    events: List[TelematicsEventCreate]


# Driver Schemas
class DriverBase(BaseModel):
    """Base driver schema."""
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    date_of_birth: date
    license_number: str
    license_state: str
    years_licensed: int
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class DriverCreate(DriverBase):
    """Schema for creating a driver."""
    pass


class DriverUpdate(BaseModel):
    """Schema for updating a driver."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class DriverResponse(DriverBase):
    """Schema for driver response."""
    driver_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Vehicle Schemas
class VehicleBase(BaseModel):
    """Base vehicle schema."""
    make: str
    model: str
    year: int = Field(..., ge=1900, le=2030)
    vin: str
    vehicle_type: str
    safety_rating: int = Field(..., ge=1, le=5)


class VehicleCreate(VehicleBase):
    """Schema for creating a vehicle."""
    driver_id: str


class VehicleResponse(VehicleBase):
    """Schema for vehicle response."""
    vehicle_id: str
    driver_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Trip Schemas
class TripBase(BaseModel):
    """Base trip schema."""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    distance_miles: Optional[float] = None
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    avg_speed: Optional[float] = None
    max_speed: Optional[float] = None
    harsh_braking_count: int = 0
    rapid_accel_count: int = 0
    speeding_count: int = 0
    harsh_corner_count: int = 0
    phone_usage_detected: bool = False
    trip_type: Optional[TripType] = TripType.UNKNOWN


class TripCreate(TripBase):
    """Schema for creating a trip."""
    driver_id: str
    device_id: str


class TripResponse(TripBase):
    """Schema for trip response."""
    trip_id: str
    driver_id: str
    device_id: str
    created_at: datetime
    
    # Enhanced fields
    origin_city: Optional[str] = None
    origin_state: Optional[str] = None
    destination_city: Optional[str] = None
    destination_state: Optional[str] = None
    trip_score: Optional[int] = None  # 0-100
    risk_level: Optional[str] = None  # 'low', 'medium', 'high'
    harsh_braking_count: Optional[int] = 0
    rapid_accel_count: Optional[int] = 0
    speeding_count: Optional[int] = 0
    harsh_corner_count: Optional[int] = 0

    class Config:
        from_attributes = True


class TripListResponse(BaseModel):
    """Schema for trip list response."""
    trips: List[TripResponse]
    total: int
    page: int
    page_size: int


class TripSummaryResponse(BaseModel):
    """Trip summary statistics."""
    total_trips: int
    total_miles: float
    avg_trip_score: Optional[float] = None


# Risk Scoring Schemas
class FeatureImportance(BaseModel):
    """Feature importance from SHAP values."""
    feature: str
    value: float
    importance: float


class RiskScoreBreakdown(BaseModel):
    """Risk score breakdown with explanations."""
    driver_id: str
    risk_score: float = Field(..., ge=0, le=100)
    risk_category: RiskCategory
    confidence: float = Field(..., ge=0, le=1)
    model_version: str
    calculated_at: datetime
    features: Dict[str, float]
    feature_importances: List[FeatureImportance]
    recommendations: List[str]


class RiskScoreResponse(BaseModel):
    """Simple risk score response."""
    driver_id: str
    risk_score: float = Field(..., ge=0, le=100)
    risk_category: RiskCategory
    confidence: float
    calculated_at: datetime


class RiskScoreHistory(BaseModel):
    """Risk score history response."""
    driver_id: str
    scores: List[RiskScoreResponse]
    trend: str  # improving, stable, declining


# Risk Profile Schemas
class RiskProfileSummaryResponse(BaseModel):
    """Risk profile summary for Risk Profile page."""
    overall_risk_score: float
    overall_risk_trend_status: str  # 'improving', 'stable', 'declining'
    behavior_score: float
    last_updated_date: datetime
    change_from_previous: float
    previous_score: Optional[float] = None
    # Trip statistics
    total_trips: int = 0
    total_miles: float = 0.0
    avg_trip_score: Optional[float] = None
    # Trip performance metrics
    perfect_trips: int = 0  # Score >= 95
    low_risk_trips: int = 0  # Score >= 80
    high_risk_trips: int = 0  # Score < 60
    total_incidents: int = 0  # All safety events


class RiskScoreTrendPoint(BaseModel):
    """Single point in risk score trend."""
    date: str  # ISO format date
    risk_score: float


class RiskScoreTrendResponse(BaseModel):
    """Risk score trend time series."""
    scores: List[RiskScoreTrendPoint]
    period: str
    interval: str


class RiskFactorBreakdownResponse(BaseModel):
    """Risk factor breakdown for radar chart and detailed factors."""
    # Category scores for radar chart
    behavior: float
    mileage: float
    time_pattern: float
    location: float
    
    # Detailed risk factors
    speeding_frequency: float
    acceleration_pattern: float
    high_risk_area_exposure: float
    weather_risk_exposure: float
    hard_braking_frequency: float
    night_driving_percentage: float
    phone_usage_incidents: float


# Pricing Schemas
class PremiumComponent(BaseModel):
    """Individual premium component."""
    name: str
    value: float
    description: str


class PremiumBreakdown(BaseModel):
    """Detailed premium breakdown."""
    driver_id: str
    base_premium: float
    risk_multiplier: float
    usage_multiplier: float
    discount_factor: float
    final_premium: float
    monthly_premium: float
    effective_date: date
    components: List[PremiumComponent]
    savings_vs_traditional: float


class PremiumResponse(BaseModel):
    """Simple premium response."""
    driver_id: str
    monthly_premium: float
    final_premium: float
    effective_date: date
    status: str


# Policy Page Schemas
class PolicyDetailsResponse(BaseModel):
    """Policy details for Policy page."""
    policy_number: str
    status: str
    policy_type: str
    traditional_monthly_premium: float
    monthly_premium: float
    discount_percentage: float
    monthly_savings: float
    annual_savings: float
    effective_date: date
    expiration_date: date
    last_updated: Optional[datetime] = None
    coverage_type: Optional[str] = None
    coverage_limit: Optional[float] = None
    deductible: Optional[float] = None


# Rewards Schemas
class RewardsSummaryResponse(BaseModel):
    """Rewards summary for Rewards page."""
    current_points: int
    next_milestone: dict  # Contains points_threshold, reward_description, points_needed, progress_percentage


class MilestoneResponse(BaseModel):
    """Reward milestone."""
    milestone_id: int
    points_threshold: int
    reward_name: str
    reward_description: str
    status: str  # 'unlocked', 'pending'


class AchievementResponse(BaseModel):
    """Achievement."""
    achievement_id: str
    achievement_name: str
    achievement_description: str
    status: str  # 'achieved', 'pending'


class PointsRuleResponse(BaseModel):
    """Points earning rule."""
    rule_id: int
    rule_name: str
    rule_description: str
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    points_awarded: int


class PremiumSimulation(BaseModel):
    """What-if premium simulation."""
    current_premium: float
    projected_premium: float
    potential_savings: float
    assumptions: Dict[str, Any]


# Driver Statistics Schemas
class DriverStatisticsResponse(BaseModel):
    """Driver statistics response."""
    driver_id: str
    period_start: date
    period_end: date
    total_miles: float
    total_trips: int
    avg_speed: float
    max_speed: float
    harsh_braking_rate: float
    rapid_accel_rate: float
    speeding_rate: float
    night_driving_pct: float
    rush_hour_pct: float
    weekend_driving_pct: float

    class Config:
        from_attributes = True


# Authentication Schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    driver_id: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class UserCreate(BaseModel):
    """User creation request."""
    username: str
    email: EmailStr
    password: str
    driver_id: Optional[str] = None
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False


class UserUpdate(BaseModel):
    """User update request."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    driver_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserResponse(BaseModel):
    """User response."""
    user_id: int
    username: str
    email: str
    driver_id: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics Schemas
class FleetSummary(BaseModel):
    """Fleet-wide summary statistics."""
    total_drivers: int
    active_drivers: int
    total_miles_ytd: float
    total_trips_ytd: int
    avg_risk_score: float
    risk_distribution: Dict[str, int]
    avg_premium: float
    total_savings: float


class RiskDistribution(BaseModel):
    """Risk score distribution."""
    excellent: int
    good: int
    average: int
    below_average: int
    high_risk: int
    total: int


# Generic Responses
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    status: str = "success"


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    error_code: Optional[str] = None


# Admin Dashboard Schemas
class AdminDashboardSummary(BaseModel):
    """Admin dashboard summary statistics."""
    total_drivers: int
    total_vehicles: int
    monthly_revenue: float
    avg_risk_score: float


class DailyTripActivity(BaseModel):
    """Daily trip activity data."""
    date: str  # ISO format: "YYYY-MM-DD"
    trip_count: int
    avg_score: Optional[float] = None


class RiskDistributionResponse(BaseModel):
    """Risk distribution for admin dashboard."""
    low_risk_percentage: float
    medium_risk_percentage: float
    high_risk_percentage: float
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    total_drivers: int


class SafetyEventBreakdown(BaseModel):
    """Safety event breakdown."""
    event_type: str
    count: int


class PolicyTypeDistribution(BaseModel):
    """Policy type distribution."""
    policy_type: str
    count: int


# Admin Drivers Schemas
class DriverCardResponse(BaseModel):
    """Enriched driver card response for admin drivers page."""
    driver_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    city: Optional[str]
    state: Optional[str]
    
    # Performance Metrics
    safety_score: float  # 0-100, higher is better
    risk_score: float    # 0-100, lower is better
    total_trips: int
    reward_points: int
    
    # Policy Information
    policy_type: Optional[str]  # "PHYD", "PAYD", "Traditional"
    policy_status: Optional[str]  # "active", "inactive", "pending"
    monthly_premium: Optional[float]
    discount_percentage: Optional[float]  # e.g., 15.0 for 15%


class DriverDetailsResponse(BaseModel):
    """Comprehensive driver details for admin driver details modal."""
    # Basic Information
    driver_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    date_of_birth: Optional[date]
    license_number: Optional[str]
    license_state: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    
    # Formatted Address
    full_address: Optional[str]  # "123 Main St, San Francisco, CA 94102"
    
    # Performance Metrics
    safety_score: float
    risk_score: float
    total_miles: float
    total_trips: int
    
    # Policy Information (optional)
    policy_type: Optional[str]
    policy_status: Optional[str]
    monthly_premium: Optional[float]
    discount_percentage: Optional[float]
    policy_number: Optional[str] = None
    base_premium: Optional[float] = None
    current_premium: Optional[float] = None
    annual_savings: Optional[float] = None
    coverage_type: Optional[str] = None
    coverage_limit: Optional[float] = None
    deductible: Optional[float] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    total_miles_allowed: Optional[float] = None
    miles_used: Optional[float] = None
    
    # Rewards Information (optional)
    reward_points: Optional[int] = None
    achievements: Optional[List[dict]] = None
    
    # Additional fields
    years_licensed: Optional[int]
    gender: Optional[str]
    marital_status: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


# Admin Policies Schemas
class PoliciesSummaryResponse(BaseModel):
    """Policy summary statistics."""
    total_policies: int
    active_policies: int
    monthly_revenue: float
    total_savings: float


class PolicyCardResponse(BaseModel):
    """Enriched policy card response for admin policies page."""
    premium_id: int
    policy_id: str
    driver_id: str
    driver_name: str  # "John Smith" (first_name + last_name)
    policy_type: str  # "PHYD", "PAYD", "Hybrid"
    status: str  # "active", "inactive", "pending"
    
    # Financial Details
    base_premium: float
    current_premium: float  # monthly_premium
    discount_percentage: float  # Calculated: ((base_premium - monthly_premium) / base_premium) * 100
    annual_savings: float  # (base_premium - monthly_premium) * 12
    
    # Coverage Details
    coverage_type: Optional[str]  # "Comprehensive", "Full", etc.
    coverage_limit: Optional[float]
    effective_date: date
    expiration_date: date
    
    # PAYD-Specific
    miles_used: Optional[float]  # Only for PAYD policies
    total_miles_allowed: Optional[float]  # Only for PAYD policies
