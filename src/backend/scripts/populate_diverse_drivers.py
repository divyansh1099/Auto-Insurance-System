#!/usr/bin/env python3
"""
Create diverse, realistic driver profiles with varied data.
Each driver will have unique characteristics, risk profiles, and data patterns.
"""

import sys
import os
import csv
from datetime import datetime, date, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.database import (
    SessionLocal, Driver, Vehicle, Device, Trip, RiskScore, Premium, 
    User, TelematicsEvent, DriverStatistics
)
from app.utils.auth import get_password_hash

# Realistic names for diversity
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Daniel", "Nancy", "Matthew", "Lisa",
    "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor",
    "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Sanchez"
]

# US Cities and States for realistic location data
CITIES_STATES = [
    ("Los Angeles", "CA"), ("San Francisco", "CA"), ("San Diego", "CA"), ("Sacramento", "CA"),
    ("New York", "NY"), ("Buffalo", "NY"), ("Albany", "NY"), ("Rochester", "NY"),
    ("Houston", "TX"), ("Dallas", "TX"), ("Austin", "TX"), ("San Antonio", "TX"),
    ("Miami", "FL"), ("Tampa", "FL"), ("Orlando", "FL"), ("Jacksonville", "FL"),
    ("Chicago", "IL"), ("Phoenix", "AZ"), ("Seattle", "WA"), ("Boston", "MA"),
    ("Denver", "CO"), ("Portland", "OR"), ("Atlanta", "GA"), ("Nashville", "TN")
]

# Vehicle makes and models
VEHICLE_MAKES = ["Toyota", "Honda", "Ford", "Chevrolet", "Tesla", "BMW", "Mercedes-Benz", "Audi", "Nissan", "Hyundai"]
VEHICLE_MODELS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Prius", "4Runner", "Tacoma"],
    "Honda": ["Accord", "Civic", "CR-V", "Pilot", "Odyssey", "HR-V", "Ridgeline"],
    "Ford": ["F-150", "Escape", "Explorer", "Mustang", "Edge", "Bronco", "Ranger"],
    "Chevrolet": ["Silverado", "Equinox", "Tahoe", "Malibu", "Traverse", "Blazer", "Colorado"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X"],
    "BMW": ["3 Series", "5 Series", "X3", "X5", "X1", "X7"],
    "Mercedes-Benz": ["C-Class", "E-Class", "GLC", "GLE", "A-Class", "S-Class"],
    "Audi": ["A4", "A6", "Q5", "Q7", "A3", "Q3"],
    "Nissan": ["Altima", "Sentra", "Rogue", "Pathfinder", "Frontier"],
    "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "Palisade"]
}

# Driver profiles with different risk characteristics
DRIVER_PROFILES = [
    {
        "name": "Safe Driver",
        "risk_multiplier": 0.7,
        "trip_incident_rate": 0.05,  # 5% chance of incidents
        "speeding_rate": 0.02,
        "harsh_braking_rate": 0.03,
        "rapid_accel_rate": 0.04,
        "night_driving_pct": 10,
        "policy_type": "PHYD"
    },
    {
        "name": "Moderate Driver",
        "risk_multiplier": 1.0,
        "trip_incident_rate": 0.15,
        "speeding_rate": 0.10,
        "harsh_braking_rate": 0.12,
        "rapid_accel_rate": 0.15,
        "night_driving_pct": 25,
        "policy_type": "Hybrid"
    },
    {
        "name": "Risky Driver",
        "risk_multiplier": 1.3,
        "trip_incident_rate": 0.30,
        "speeding_rate": 0.25,
        "harsh_braking_rate": 0.20,
        "rapid_accel_rate": 0.25,
        "night_driving_pct": 40,
        "policy_type": "PAYD"
    },
    {
        "name": "Very Safe Driver",
        "risk_multiplier": 0.6,
        "trip_incident_rate": 0.02,
        "speeding_rate": 0.01,
        "harsh_braking_rate": 0.02,
        "rapid_accel_rate": 0.02,
        "night_driving_pct": 5,
        "policy_type": "PHYD"
    },
    {
        "name": "Aggressive Driver",
        "risk_multiplier": 1.5,
        "trip_incident_rate": 0.40,
        "speeding_rate": 0.35,
        "harsh_braking_rate": 0.30,
        "rapid_accel_rate": 0.35,
        "night_driving_pct": 50,
        "policy_type": "PAYD"
    },
    {
        "name": "City Commuter",
        "risk_multiplier": 0.9,
        "trip_incident_rate": 0.10,
        "speeding_rate": 0.05,
        "harsh_braking_rate": 0.15,  # More braking in city
        "rapid_accel_rate": 0.08,
        "night_driving_pct": 15,
        "policy_type": "Hybrid"
    },
    {
        "name": "Highway Driver",
        "risk_multiplier": 0.85,
        "trip_incident_rate": 0.08,
        "speeding_rate": 0.20,  # More speeding on highways
        "harsh_braking_rate": 0.05,
        "rapid_accel_rate": 0.06,
        "night_driving_pct": 20,
        "policy_type": "PHYD"
    }
]

def get_random_location():
    """Get a random city and state."""
    return random.choice(CITIES_STATES)

def calculate_trip_score(trip):
    """Calculate trip score based on events."""
    base_score = 100
    score = base_score
    
    score -= (trip.harsh_braking_count or 0) * 5
    score -= (trip.rapid_accel_count or 0) * 3
    score -= (trip.speeding_count or 0) * 8
    score -= (trip.harsh_corner_count or 0) * 4
    
    if trip.distance_miles and trip.distance_miles > 10:
        score += min(5, trip.distance_miles / 20)
    
    if trip.phone_usage_detected:
        score -= 10
    
    return max(0, min(100, int(score)))

def get_risk_level(trip_score):
    """Get risk level from trip score."""
    if trip_score >= 80:
        return 'low'
    elif trip_score >= 60:
        return 'medium'
    else:
        return 'high'

def create_diverse_driver(session, driver_id, profile_index):
    """Create a driver with diverse, realistic data."""
    profile = DRIVER_PROFILES[profile_index % len(DRIVER_PROFILES)]
    
    # Generate realistic name
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Generate realistic date of birth (age 25-65)
    age = random.randint(25, 65)
    birth_year = datetime.now().year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    date_of_birth = date(birth_year, birth_month, birth_day)
    
    # Generate realistic years licensed (at least 18 years old)
    years_licensed = max(1, age - 18 + random.randint(0, 5))
    
    # Generate location
    city, state = get_random_location()
    
    # Generate realistic address
    street_number = random.randint(100, 9999)
    street_names = ["Main St", "Oak Ave", "Park Blvd", "Maple Dr", "Cedar Ln", "Elm St", "Pine Rd"]
    address = f"{street_number} {random.choice(street_names)}"
    
    # Generate phone number
    phone = f"{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
    
    # Generate license number
    license_number = f"{state}{random.randint(1000000, 9999999)}"
    
    # Generate email
    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@example.com"
    
    # Check if driver exists
    existing = session.query(Driver).filter(Driver.driver_id == driver_id).first()
    if existing:
        # Update existing driver
        existing.first_name = first_name
        existing.last_name = last_name
        existing.email = email
        existing.phone = phone
        existing.date_of_birth = date_of_birth
        existing.license_number = license_number
        existing.license_state = state
        existing.years_licensed = years_licensed
        existing.gender = random.choice(["M", "F"])
        existing.marital_status = random.choice(["Single", "Married", "Divorced", "Widowed"])
        existing.address = address
        existing.city = city
        existing.state = state
        existing.zip_code = f"{random.randint(10000, 99999)}"
        session.commit()
        session.refresh(existing)
        return existing
    
    driver = Driver(
        driver_id=driver_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        date_of_birth=date_of_birth,
        license_number=license_number,
        license_state=state,
        years_licensed=years_licensed,
        gender=random.choice(["M", "F"]),
        marital_status=random.choice(["Single", "Married", "Divorced", "Widowed"]),
        address=address,
        city=city,
        state=state,
        zip_code=f"{random.randint(10000, 99999)}"
    )
    session.add(driver)
    session.commit()
    session.refresh(driver)
    return driver, profile

def create_user_for_driver(session, driver):
    """Create user account for driver."""
    existing = session.query(User).filter(User.driver_id == driver.driver_id).first()
    if existing:
        return existing
    
    username = f"driver{driver.driver_id[4:]}"
    password = f"password{driver.driver_id[4:]}"
    
    user = User(
        username=username,
        email=driver.email,
        hashed_password=get_password_hash(password),
        driver_id=driver.driver_id,
        is_active=True,
        is_admin=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, password

def create_vehicle(session, driver, profile):
    """Create vehicle for driver based on profile."""
    existing = session.query(Vehicle).filter(Vehicle.driver_id == driver.driver_id).first()
    if existing:
        return existing
    
    # Higher risk drivers might have sportier/older vehicles
    if profile["risk_multiplier"] > 1.2:
        make = random.choice(["BMW", "Mercedes-Benz", "Audi", "Ford", "Chevrolet"])
    elif profile["risk_multiplier"] < 0.8:
        make = random.choice(["Toyota", "Honda", "Tesla", "Hyundai"])
    else:
        make = random.choice(VEHICLE_MAKES)
    
    model = random.choice(VEHICLE_MODELS[make])
    
    # Year based on risk (safer drivers might have newer cars)
    if profile["risk_multiplier"] < 0.8:
        year = random.randint(2020, 2024)
    elif profile["risk_multiplier"] > 1.2:
        year = random.randint(2015, 2020)
    else:
        year = random.randint(2018, 2024)
    
    vehicle = Vehicle(
        vehicle_id=f"VEH-{driver.driver_id[4:]}",
        driver_id=driver.driver_id,
        make=make,
        model=model,
        year=year,
        vin=f"{random.randint(10000000000000000, 99999999999999999)}",
        vehicle_type=random.choice(["sedan", "suv", "truck", "coupe"]),
        safety_rating=random.randint(3, 5) if profile["risk_multiplier"] < 1.0 else random.randint(2, 4)
    )
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)
    return vehicle

def create_device(session, driver, vehicle):
    """Create device for driver."""
    existing = session.query(Device).filter(Device.driver_id == driver.driver_id).first()
    if existing:
        return existing
    
    device = Device(
        device_id=f"DEV-{driver.driver_id[4:]}",
        driver_id=driver.driver_id,
        vehicle_id=vehicle.vehicle_id,
        device_type="OBD-II",
        manufacturer="TelematicsCorp",
        firmware_version=f"v{random.randint(1, 3)}.{random.randint(0, 9)}",
        installed_date=date.today() - timedelta(days=random.randint(60, 365)),
        is_active=True,
        last_heartbeat=datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
    )
    session.add(device)
    session.commit()
    session.refresh(device)
    return device

def create_trips(session, driver_id, device_id, profile, num_trips=40):
    """Create realistic trips based on driver profile."""
    # Delete existing telematics events first (due to foreign key constraint)
    session.query(TelematicsEvent).filter(TelematicsEvent.driver_id == driver_id).delete()
    session.commit()
    
    # Delete existing trips
    session.query(Trip).filter(Trip.driver_id == driver_id).delete()
    session.commit()
    
    trips = []
    now = datetime.utcnow()
    
    for i in range(num_trips):
        days_ago = random.randint(0, 60)
        
        # Adjust time based on night driving percentage
        if random.random() < (profile["night_driving_pct"] / 100):
            hour = random.choice([22, 23, 0, 1, 2, 3, 4, 5])
        else:
            hour = random.randint(6, 21)
        
        start_time = now - timedelta(days=days_ago, hours=hour, minutes=random.randint(0, 59))
        duration_minutes = random.uniform(15, 120)
        end_time = start_time + timedelta(minutes=duration_minutes)
        distance_miles = duration_minutes * random.uniform(0.5, 1.5)
        
        origin_city, origin_state = get_random_location()
        destination_city, destination_state = get_random_location()
        while destination_city == origin_city:
            destination_city, destination_state = get_random_location()
        
        # Generate incidents based on profile with MUCH more variation
        # Create a mix: some perfect trips, some with incidents, some really bad
        trip_random = random.random()
        
        # Determine trip quality: 0-0.3 = perfect, 0.3-0.7 = some incidents, 0.7-1.0 = many incidents
        if trip_random < 0.3:
            # Perfect trip (30% chance for safe drivers, less for risky)
            perfect_chance = 0.5 if profile["risk_multiplier"] < 0.8 else 0.1 if profile["risk_multiplier"] > 1.2 else 0.3
            if random.random() < perfect_chance:
                harsh_braking = 0
                rapid_accel = 0
                speeding = 0
                harsh_corner = 0
                phone_usage = False
            else:
                # Some incidents but minimal
                harsh_braking = random.randint(0, 1) if random.random() < 0.2 else 0
                rapid_accel = random.randint(0, 2) if random.random() < 0.3 else 0
                speeding = 0
                harsh_corner = 0
                phone_usage = False
        elif trip_random < 0.7:
            # Moderate incidents (40% of trips)
            harsh_braking = random.randint(0, int(profile["risk_multiplier"] * 2)) if random.random() < profile["harsh_braking_rate"] else 0
            rapid_accel = random.randint(0, int(profile["risk_multiplier"] * 3)) if random.random() < profile["rapid_accel_rate"] else 0
            speeding = random.randint(0, int(profile["risk_multiplier"] * 2)) if random.random() < profile["speeding_rate"] else 0
            harsh_corner = random.randint(0, int(profile["risk_multiplier"] * 2)) if random.random() < profile["trip_incident_rate"] else 0
            phone_usage_rate = 0.02 if profile["risk_multiplier"] < 0.8 else 0.1 if profile["risk_multiplier"] > 1.2 else 0.05
            phone_usage = random.random() < phone_usage_rate
        else:
            # Bad trip with many incidents (30% chance, more for risky drivers)
            bad_trip_chance = 0.1 if profile["risk_multiplier"] < 0.8 else 0.5 if profile["risk_multiplier"] > 1.2 else 0.3
            if random.random() < bad_trip_chance:
                harsh_braking = random.randint(2, int(profile["risk_multiplier"] * 8))
                rapid_accel = random.randint(3, int(profile["risk_multiplier"] * 10))
                speeding = random.randint(2, int(profile["risk_multiplier"] * 6))
                harsh_corner = random.randint(1, int(profile["risk_multiplier"] * 5))
                phone_usage_rate = 0.05 if profile["risk_multiplier"] < 0.8 else 0.3 if profile["risk_multiplier"] > 1.2 else 0.15
                phone_usage = random.random() < phone_usage_rate
            else:
                # Moderate incidents
                harsh_braking = random.randint(0, int(profile["risk_multiplier"] * 3))
                rapid_accel = random.randint(0, int(profile["risk_multiplier"] * 5))
                speeding = random.randint(0, int(profile["risk_multiplier"] * 3))
                harsh_corner = random.randint(0, int(profile["risk_multiplier"] * 2))
                phone_usage_rate = 0.02 if profile["risk_multiplier"] < 0.8 else 0.15 if profile["risk_multiplier"] > 1.2 else 0.05
                phone_usage = random.random() < phone_usage_rate
        
        trip_obj = type('obj', (object,), {
            'harsh_braking_count': harsh_braking,
            'rapid_accel_count': rapid_accel,
            'speeding_count': speeding,
            'harsh_corner_count': harsh_corner,
            'phone_usage_detected': phone_usage,
            'distance_miles': distance_miles
        })()
        
        trip_score = calculate_trip_score(trip_obj)
        risk_level = get_risk_level(trip_score)
        
        trip = Trip(
            trip_id=f"TRP-{driver_id[4:]}-{i+1:04d}",
            driver_id=driver_id,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=round(duration_minutes, 2),
            distance_miles=round(distance_miles, 2),
            start_latitude=random.uniform(32.0, 45.0),
            start_longitude=random.uniform(-122.0, -74.0),
            end_latitude=random.uniform(32.0, 45.0),
            end_longitude=random.uniform(-122.0, -74.0),
            avg_speed=random.uniform(25, 60) + (10 if speeding > 0 else 0),
            max_speed=random.uniform(45, 80) + (15 if speeding > 0 else 0),
            harsh_braking_count=harsh_braking,
            rapid_accel_count=rapid_accel,
            speeding_count=speeding,
            harsh_corner_count=harsh_corner,
            phone_usage_detected=phone_usage,
            trip_type=random.choice(["commute", "errand", "leisure", "work"]),
            origin_city=origin_city,
            origin_state=origin_state,
            destination_city=destination_city,
            destination_state=destination_state,
            trip_score=trip_score,
            risk_level=risk_level
        )
        trips.append(trip)
    
    session.add_all(trips)
    session.commit()
    return trips

def create_risk_score(session, driver_id, trips, profile):
    """Create risk score with categories based on profile."""
    if not trips:
        return None
    
    # Delete existing risk scores
    session.query(RiskScore).filter(RiskScore.driver_id == driver_id).delete()
    session.commit()
    
    total_trips = len(trips)
    total_miles = sum(t.distance_miles or 0 for t in trips)
    avg_trip_score = sum(t.trip_score or 70 for t in trips) / total_trips if total_trips > 0 else 70
    
    # Adjust risk score based on profile
    base_risk_score = 100 - avg_trip_score
    adjusted_risk_score = base_risk_score * profile["risk_multiplier"]
    risk_score = max(0, min(100, adjusted_risk_score))
    
    # Category scores adjusted by profile
    behavior_score = max(0, min(100, 100 - (risk_score * 0.8) + random.uniform(-5, 5)))
    mileage_score = max(0, min(100, 80 - (total_miles / 1000) * 2 + random.uniform(-5, 5)))
    time_pattern_score = max(0, min(100, 100 - (profile["night_driving_pct"] * 0.5) + random.uniform(-5, 5)))
    location_score = max(0, min(100, 70 + random.uniform(-10, 10)))
    
    speeding_frequency = sum(t.speeding_count or 0 for t in trips) / max(1, total_miles / 100)
    acceleration_pattern = sum(t.rapid_accel_count or 0 for t in trips) / max(1, total_miles / 100)
    hard_braking_frequency = sum(t.harsh_braking_count or 0 for t in trips) / max(1, total_miles / 100)
    
    night_trips = sum(1 for t in trips if t.start_time and (t.start_time.hour >= 22 or t.start_time.hour < 6))
    night_driving_percentage = (night_trips / total_trips * 100) if total_trips > 0 else 0
    
    phone_usage_incidents = sum(1 for t in trips if t.phone_usage_detected)
    
    risk_score_obj = RiskScore(
        driver_id=driver_id,
        risk_score=round(risk_score, 2),
        risk_category="low" if risk_score < 40 else "medium" if risk_score < 60 else "high",
        confidence=random.uniform(0.85, 0.95),
        model_version="v2.0",
        calculation_date=datetime.utcnow(),
        behavior_score=round(behavior_score, 2),
        mileage_score=round(mileage_score, 2),
        time_pattern_score=round(time_pattern_score, 2),
        location_score=round(location_score, 2),
        speeding_frequency=round(speeding_frequency, 2),
        acceleration_pattern=round(acceleration_pattern, 2),
        hard_braking_frequency=round(hard_braking_frequency, 2),
        high_risk_area_exposure=round(random.uniform(5, 25), 2),
        weather_risk_exposure=round(random.uniform(10, 30), 2),
        night_driving_percentage=round(night_driving_percentage, 2),
        phone_usage_incidents=phone_usage_incidents,
        features={
            "total_trips": total_trips,
            "total_miles": round(total_miles, 2),
            "avg_trip_score": round(avg_trip_score, 2)
        },
        shap_values={
            "speeding_frequency": round(random.uniform(-5, 5), 2),
            "acceleration_pattern": round(random.uniform(-3, 3), 2),
            "hard_braking_frequency": round(random.uniform(-4, 4), 2)
        }
    )
    
    session.add(risk_score_obj)
    session.commit()
    return risk_score_obj

def create_premium(session, driver_id, risk_score_obj, profile):
    """Create premium with policy details based on profile."""
    existing = session.query(Premium).filter(
        Premium.driver_id == driver_id,
        Premium.status == 'active'
    ).first()
    
    risk_score = risk_score_obj.risk_score if risk_score_obj else 50
    
    # Base premium varies by state (simplified)
    base_premiums = [1000, 1200, 1400, 1600, 1800]
    base_premium = random.choice(base_premiums)
    
    # Risk multiplier based on risk score
    if risk_score <= 20:
        risk_multiplier = 0.70
    elif risk_score <= 40:
        risk_multiplier = 0.85
    elif risk_score <= 60:
        risk_multiplier = 1.00
    elif risk_score <= 80:
        risk_multiplier = 1.20
    else:
        risk_multiplier = 1.50
    
    # Apply profile multiplier
    risk_multiplier *= profile["risk_multiplier"]
    
    usage_multiplier = random.uniform(0.9, 1.1)
    discount_factor = random.uniform(0.95, 1.0)
    
    final_premium = base_premium * risk_multiplier * usage_multiplier * discount_factor
    
    policy_type = profile["policy_type"]
    
    if existing:
        existing.policy_type = policy_type
        existing.coverage_type = random.choice(['Comprehensive', 'Full Coverage', 'Liability'])
        existing.coverage_limit = random.choice([50000, 100000, 250000, 500000])
        existing.deductible = random.choice([500, 1000, 1500, 2000])
        existing.base_premium = base_premium
        existing.risk_multiplier = risk_multiplier
        existing.usage_multiplier = usage_multiplier
        existing.discount_factor = discount_factor
        existing.final_premium = final_premium
        existing.monthly_premium = final_premium / 12
        if policy_type == 'PAYD':
            existing.total_miles_allowed = random.choice([6000, 8000, 10000, 12000])
        existing.policy_last_updated = datetime.utcnow()
        session.commit()
        return existing
    
    premium = Premium(
        driver_id=driver_id,
        policy_id=f"POL-{driver_id[4:]}",
        base_premium=base_premium,
        risk_multiplier=risk_multiplier,
        usage_multiplier=usage_multiplier,
        discount_factor=discount_factor,
        final_premium=final_premium,
        monthly_premium=final_premium / 12,
        effective_date=date.today() - timedelta(days=random.randint(30, 180)),
        expiration_date=date.today() + timedelta(days=random.randint(180, 365)),
        status='active',
        policy_type=policy_type,
        coverage_type=random.choice(['Comprehensive', 'Full Coverage', 'Liability']),
        coverage_limit=random.choice([50000, 100000, 250000, 500000]),
        deductible=random.choice([500, 1000, 1500, 2000]),
        policy_last_updated=datetime.utcnow()
    )
    
    if policy_type == 'PAYD':
        premium.total_miles_allowed = random.choice([6000, 8000, 10000, 12000])
    
    session.add(premium)
    session.commit()
    session.refresh(premium)
    return premium

def create_telematics_events(session, driver_id, device_id, trips):
    """Create telematics events."""
    # Delete existing events
    session.query(TelematicsEvent).filter(TelematicsEvent.driver_id == driver_id).delete()
    session.commit()
    
    events = []
    
    for trip in trips[:15]:  # Create events for first 15 trips
        if not trip.start_time or not trip.end_time:
            continue
        
        num_events = random.randint(8, 25)
        event_interval = (trip.end_time - trip.start_time).total_seconds() / num_events
        
        event_types_created = {
            'harsh_brake': 0,
            'rapid_accel': 0,
            'speeding': 0
        }
        
        for i in range(num_events):
            event_time = trip.start_time + timedelta(seconds=i * event_interval)
            
            # Ensure events are within partition range (September-November 2025)
            # Adjust to November 2025 if outside partition range
            if event_time.year != 2025 or event_time.month not in [9, 10, 11]:
                # Move to November 2025
                days_offset = (event_time - datetime(2025, 11, 1)).days % 30
                event_time = datetime(2025, 11, 1) + timedelta(days=days_offset, hours=event_time.hour, minutes=event_time.minute)
            
            event_type = None
            if trip.harsh_braking_count and event_types_created['harsh_brake'] < trip.harsh_braking_count:
                event_type = 'harsh_brake'
                event_types_created['harsh_brake'] += 1
            elif trip.rapid_accel_count and event_types_created['rapid_accel'] < trip.rapid_accel_count:
                event_type = 'rapid_accel'
                event_types_created['rapid_accel'] += 1
            elif trip.speeding_count and event_types_created['speeding'] < trip.speeding_count:
                event_type = 'speeding'
                event_types_created['speeding'] += 1
            elif trip.phone_usage_detected and i == 0:
                event_type = 'phone_usage'
            
            progress = i / num_events
            event = TelematicsEvent(
                event_id=f"EVT-{driver_id[4:]}-{trip.trip_id[4:]}-{i}",
                device_id=device_id,
                driver_id=driver_id,
                trip_id=trip.trip_id,
                timestamp=event_time,
                latitude=trip.start_latitude + (trip.end_latitude - trip.start_latitude) * progress if trip.start_latitude and trip.end_latitude else None,
                longitude=trip.start_longitude + (trip.end_longitude - trip.start_longitude) * progress if trip.start_longitude and trip.end_longitude else None,
                speed=random.uniform(20, 75),
                acceleration=random.uniform(-6, 6),
                braking_force=random.uniform(0, 12),
                heading=random.uniform(0, 360),
                altitude=random.uniform(0, 500),
                gps_accuracy=random.uniform(1, 8),
                event_type=event_type
            )
            events.append(event)
    
    if events:
        session.add_all(events)
        session.commit()
    return events

def create_driver_statistics(session, driver_id, trips):
    """Create driver statistics."""
    # Delete existing statistics
    session.query(DriverStatistics).filter(DriverStatistics.driver_id == driver_id).delete()
    session.commit()
    
    if not trips:
        return None
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_trips = [t for t in trips if t.start_time and t.start_time >= thirty_days_ago]
    
    if not recent_trips:
        return None
    
    total_miles = sum(t.distance_miles or 0 for t in recent_trips)
    total_trips = len(recent_trips)
    avg_speed = sum(t.avg_speed or 0 for t in recent_trips) / total_trips if total_trips > 0 else 0
    max_speed = max(t.max_speed or 0 for t in recent_trips)
    
    total_harsh_braking = sum(t.harsh_braking_count or 0 for t in recent_trips)
    total_rapid_accel = sum(t.rapid_accel_count or 0 for t in recent_trips)
    total_speeding = sum(t.speeding_count or 0 for t in recent_trips)
    
    harsh_braking_rate = (total_harsh_braking / total_miles * 100) if total_miles > 0 else 0
    rapid_accel_rate = (total_rapid_accel / total_miles * 100) if total_miles > 0 else 0
    speeding_rate = (total_speeding / total_miles * 100) if total_miles > 0 else 0
    
    night_trips = sum(1 for t in recent_trips if t.start_time and (t.start_time.hour >= 22 or t.start_time.hour < 6))
    night_driving_pct = (night_trips / total_trips * 100) if total_trips > 0 else 0
    
    rush_hour_trips = sum(1 for t in recent_trips if t.start_time and 
                          ((7 <= t.start_time.hour < 9) or (17 <= t.start_time.hour < 19)))
    rush_hour_pct = (rush_hour_trips / total_trips * 100) if total_trips > 0 else 0
    
    weekend_trips = sum(1 for t in recent_trips if t.start_time and t.start_time.weekday() >= 5)
    weekend_driving_pct = (weekend_trips / total_trips * 100) if total_trips > 0 else 0
    
    stat = DriverStatistics(
        driver_id=driver_id,
        period_start=thirty_days_ago.date(),
        period_end=date.today(),
        total_miles=round(total_miles, 2),
        total_trips=total_trips,
        avg_speed=round(avg_speed, 2),
        max_speed=round(max_speed, 2),
        harsh_braking_rate=round(harsh_braking_rate, 4),
        rapid_accel_rate=round(rapid_accel_rate, 4),
        speeding_rate=round(speeding_rate, 4),
        night_driving_pct=round(night_driving_pct, 2),
        rush_hour_pct=round(rush_hour_pct, 2),
        weekend_driving_pct=round(weekend_driving_pct, 2)
    )
    
    session.add(stat)
    session.commit()
    return stat

def main():
    """Main function."""
    print("=" * 70)
    print("Creating Diverse Driver Profiles")
    print("=" * 70)
    
    session = SessionLocal()
    credentials = []
    
    try:
        # Get first 7 drivers
        drivers = session.query(Driver).order_by(Driver.driver_id).limit(7).all()
        print(f"\nCreating diverse profiles for {len(drivers)} drivers\n")
        
        for idx, driver in enumerate(drivers):
            profile = DRIVER_PROFILES[idx % len(DRIVER_PROFILES)]
            print(f"📊 {driver.driver_id}: Creating {profile['name']} profile")
            
            # Create/update diverse driver
            result = create_diverse_driver(session, driver.driver_id, idx)
            if isinstance(result, tuple):
                driver, profile = result
            else:
                driver = result
                profile = DRIVER_PROFILES[idx % len(DRIVER_PROFILES)]
            
            print(f"  👤 {driver.first_name} {driver.last_name} ({driver.city}, {driver.state})")
            
            # Create user account
            user_result = create_user_for_driver(session, driver)
            if isinstance(user_result, tuple):
                user, password = user_result
            else:
                user = user_result
                password = f"password{driver.driver_id[4:]}"
            print(f"  ✅ User: {user.username} / {password}")
            
            # Create vehicle
            vehicle = create_vehicle(session, driver, profile)
            print(f"  🚗 {vehicle.make} {vehicle.model} ({vehicle.year})")
            
            # Create device
            device = create_device(session, driver, vehicle)
            
            # Create trips
            trips = create_trips(session, driver.driver_id, device.device_id, profile, num_trips=40)
            print(f"  ✅ {len(trips)} trips created")
            
            # Create risk score
            risk_score = create_risk_score(session, driver.driver_id, trips, profile)
            print(f"  📊 Risk Score: {risk_score.risk_score:.1f} ({risk_score.risk_category})")
            
            # Create premium
            premium = create_premium(session, driver.driver_id, risk_score, profile)
            print(f"  💰 Premium: ${premium.monthly_premium:.2f}/month ({premium.policy_type})")
            
            # Create telematics events
            try:
                events = create_telematics_events(session, driver.driver_id, device.device_id, trips)
                print(f"  ✅ {len(events)} events created")
            except Exception as e:
                print(f"  ⚠️  Skipped events: {str(e)[:80]}")
                events = []
                session.rollback()  # Rollback on error
            
            # Create driver statistics
            stats = create_driver_statistics(session, driver.driver_id, trips)
            print(f"  📈 Stats: {stats.total_trips} trips, {stats.total_miles:.1f} miles")
            
            credentials.append({
                'driver_id': driver.driver_id,
                'username': user.username,
                'password': password,
                'email': driver.email,
                'full_name': f"{driver.first_name} {driver.last_name}",
                'phone': driver.phone,
                'license_number': driver.license_number,
                'license_state': driver.license_state,
                'years_licensed': driver.years_licensed,
                'address': driver.address,
                'city': driver.city,
                'state': driver.state,
                'zip_code': driver.zip_code,
                'date_of_birth': str(driver.date_of_birth),
                'gender': driver.gender,
                'marital_status': driver.marital_status,
                'vehicle': f"{vehicle.make} {vehicle.model}",
                'premium': f"${premium.monthly_premium:.2f}/month",
                'policy_type': premium.policy_type,
                'risk_score': f"{risk_score.risk_score:.1f}",
                'risk_category': risk_score.risk_category,
                'total_trips': len(trips),
                'total_miles': f"{sum(t.distance_miles or 0 for t in trips):.1f}",
                'profile_type': profile['name']
            })
            
            print()
        
        # Save credentials
        csv_filename = 'driver_credentials.csv'
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', csv_filename)
        
        if credentials:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'driver_id', 'username', 'password', 'email', 'full_name', 'phone',
                    'license_number', 'license_state', 'years_licensed',
                    'address', 'city', 'state', 'zip_code',
                    'date_of_birth', 'gender', 'marital_status',
                    'vehicle', 'premium', 'policy_type', 'risk_score', 'risk_category',
                    'total_trips', 'total_miles', 'profile_type'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(credentials)
            
            print(f"✅ Credentials saved to: {csv_path}")
        
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Drivers processed: {len(drivers)}")
        print(f"Profile types: {', '.join(set(c['profile_type'] for c in credentials))}")
        print(f"Policy types: {', '.join(set(c['policy_type'] for c in credentials))}")
        print(f"Risk categories: {', '.join(set(c['risk_category'] for c in credentials))}")
        print(f"\n📄 Credentials file: {csv_filename}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()

