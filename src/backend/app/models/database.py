"""
SQLAlchemy database models.
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Date, Text, JSON, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from app.config import get_settings

settings = get_settings()

# Create engine with optimized settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for SQL query logging in debug mode
    future=True,  # Use SQLAlchemy 2.0 style
    connect_args={
        "connect_timeout": 10,
        "application_name": "telematics_insurance_api"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Driver(Base):
    """Driver model."""
    __tablename__ = "drivers"

    driver_id = Column(String(50), primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    license_number = Column(String(50), unique=True)
    license_state = Column(String(2))
    years_licensed = Column(Integer)
    gender = Column(String(10))
    marital_status = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="driver", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="driver", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="driver", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="driver", cascade="all, delete-orphan")
    premiums = relationship("Premium", back_populates="driver", cascade="all, delete-orphan")


class Vehicle(Base):
    """Vehicle model."""
    __tablename__ = "vehicles"

    vehicle_id = Column(String(50), primary_key=True)
    driver_id = Column(String(50), ForeignKey("drivers.driver_id", ondelete="CASCADE"))
    make = Column(String(50))
    model = Column(String(50))
    year = Column(Integer)
    vin = Column(String(17), unique=True)
    vehicle_type = Column(String(50))
    safety_rating = Column(Integer, CheckConstraint("safety_rating BETWEEN 1 AND 5"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    driver = relationship("Driver", back_populates="vehicles")
    devices = relationship("Device", back_populates="vehicle", cascade="all, delete-orphan")


class Device(Base):
    """Telematics device model."""
    __tablename__ = "devices"

    device_id = Column(String(50), primary_key=True)
    driver_id = Column(String(50), ForeignKey("drivers.driver_id", ondelete="CASCADE"))
    vehicle_id = Column(String(50), ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"))
    device_type = Column(String(50))
    manufacturer = Column(String(100))
    firmware_version = Column(String(20))
    installed_date = Column(Date)
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    driver = relationship("Driver", back_populates="devices")
    vehicle = relationship("Vehicle", back_populates="devices")
    trips = relationship("Trip", back_populates="device")


class Trip(Base):
    """Trip model."""
    __tablename__ = "trips"

    trip_id = Column(String(50), primary_key=True)
    driver_id = Column(String(50), ForeignKey("drivers.driver_id", ondelete="CASCADE"))
    device_id = Column(String(50), ForeignKey("devices.device_id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_minutes = Column(Float)
    distance_miles = Column(Float)
    start_latitude = Column(Float)
    start_longitude = Column(Float)
    end_latitude = Column(Float)
    end_longitude = Column(Float)
    avg_speed = Column(Float)
    max_speed = Column(Float)
    harsh_braking_count = Column(Integer, default=0)
    rapid_accel_count = Column(Integer, default=0)
    speeding_count = Column(Integer, default=0)
    harsh_corner_count = Column(Integer, default=0)
    phone_usage_detected = Column(Boolean, default=False)
    trip_type = Column(String(20))
    # New columns from migration
    origin_city = Column(String(100))
    origin_state = Column(String(50))
    destination_city = Column(String(100))
    destination_state = Column(String(50))
    trip_score = Column(Integer, CheckConstraint("trip_score IS NULL OR (trip_score >= 0 AND trip_score <= 100)"))
    risk_level = Column(String(20), CheckConstraint("risk_level IS NULL OR risk_level IN ('low', 'medium', 'high')"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    driver = relationship("Driver", back_populates="trips")
    device = relationship("Device", back_populates="trips")


class RiskScore(Base):
    """Risk score model."""
    __tablename__ = "risk_scores"

    score_id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String(50), ForeignKey("drivers.driver_id", ondelete="CASCADE"))
    risk_score = Column(Float, CheckConstraint("risk_score BETWEEN 0 AND 100"))
    risk_category = Column(String(20))
    confidence = Column(Float)
    model_version = Column(String(20))
    calculation_date = Column(DateTime, default=datetime.utcnow)
    features = Column(JSON)
    shap_values = Column(JSON)
    # New columns from migration
    behavior_score = Column(Float, CheckConstraint("behavior_score IS NULL OR (behavior_score >= 0 AND behavior_score <= 100)"))
    mileage_score = Column(Float, CheckConstraint("mileage_score IS NULL OR (mileage_score >= 0 AND mileage_score <= 100)"))
    time_pattern_score = Column(Float, CheckConstraint("time_pattern_score IS NULL OR (time_pattern_score >= 0 AND time_pattern_score <= 100)"))
    location_score = Column(Float, CheckConstraint("location_score IS NULL OR (location_score >= 0 AND location_score <= 100)"))
    speeding_frequency = Column(Float)
    acceleration_pattern = Column(Float)
    high_risk_area_exposure = Column(Float)
    weather_risk_exposure = Column(Float)
    hard_braking_frequency = Column(Float)
    night_driving_percentage = Column(Float)
    phone_usage_incidents = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    driver = relationship("Driver", back_populates="risk_scores")


class Premium(Base):
    """Premium model."""
    __tablename__ = "premiums"

    premium_id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String(50), ForeignKey("drivers.driver_id", ondelete="CASCADE"))
    policy_id = Column(String(50))
    base_premium = Column(Float)
    risk_multiplier = Column(Float)
    usage_multiplier = Column(Float)
    discount_factor = Column(Float)
    final_premium = Column(Float)
    monthly_premium = Column(Float)
    effective_date = Column(Date)
    expiration_date = Column(Date)
    status = Column(String(20))
    # New columns from migration
    policy_type = Column(String(20))
    coverage_type = Column(String(50))
    coverage_limit = Column(Float)
    total_miles_allowed = Column(Float)
    deductible = Column(Float)
    policy_last_updated = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    driver = relationship("Driver", back_populates="premiums")


class DriverStatistics(Base):
    """Driver statistics model."""
    __tablename__ = "driver_statistics"

    stat_id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String(50), ForeignKey("drivers.driver_id", ondelete="CASCADE"))
    period_start = Column(Date)
    period_end = Column(Date)
    total_miles = Column(Float)
    total_trips = Column(Integer)
    avg_speed = Column(Float)
    max_speed = Column(Float)
    harsh_braking_rate = Column(Float)
    rapid_accel_rate = Column(Float)
    speeding_rate = Column(Float)
    night_driving_pct = Column(Float)
    rush_hour_pct = Column(Float)
    weekend_driving_pct = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelematicsEvent(Base):
    """Telematics event model."""
    __tablename__ = "telematics_events"

    event_id = Column(String(50), primary_key=True)
    device_id = Column(String(50), ForeignKey("devices.device_id"))
    driver_id = Column(String(50), ForeignKey("drivers.driver_id", ondelete="CASCADE"))
    trip_id = Column(String(50), ForeignKey("trips.trip_id"))
    timestamp = Column(DateTime, primary_key=True, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    acceleration = Column(Float)
    braking_force = Column(Float)
    heading = Column(Float)
    altitude = Column(Float)
    gps_accuracy = Column(Float)
    event_type = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """User authentication model."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String(50), ForeignKey("drivers.driver_id"), unique=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
