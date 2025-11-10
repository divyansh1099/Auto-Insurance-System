#!/usr/bin/env python3
"""
Comprehensive data population script for 5-7 selected drivers.
Populates all tables with realistic data.
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

# US Cities and States for realistic location data
CITIES_STATES = [
    ("Los Angeles", "CA"), ("San Francisco", "CA"), ("San Diego", "CA"),
    ("New York", "NY"), ("Buffalo", "NY"), ("Albany", "NY"),
    ("Houston", "TX"), ("Dallas", "TX"), ("Austin", "TX"),
    ("Miami", "FL"), ("Tampa", "FL"), ("Orlando", "FL"),
    ("Chicago", "IL"), ("Phoenix", "AZ"), ("Seattle", "WA"),
    ("Boston", "MA"), ("Denver", "CO"), ("Portland", "OR")
]

# Vehicle makes and models
VEHICLE_MAKES = ["Toyota", "Honda", "Ford", "Chevrolet", "Tesla", "BMW", "Mercedes-Benz"]
VEHICLE_MODELS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Prius"],
    "Honda": ["Accord", "Civic", "CR-V", "Pilot", "Odyssey"],
    "Ford": ["F-150", "Escape", "Explorer", "Mustang", "Edge"],
    "Chevrolet": ["Silverado", "Equinox", "Tahoe", "Malibu", "Traverse"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X"],
    "BMW": ["3 Series", "5 Series", "X3", "X5"],
    "Mercedes-Benz": ["C-Class", "E-Class", "GLC", "GLE"]
}

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

def create_vehicle(session, driver):
    """Create vehicle for driver."""
    existing = session.query(Vehicle).filter(Vehicle.driver_id == driver.driver_id).first()
    if existing:
        return existing
    
    make = random.choice(VEHICLE_MAKES)
    model = random.choice(VEHICLE_MODELS[make])
    
    vehicle = Vehicle(
        vehicle_id=f"VEH-{driver.driver_id[4:]}",
        driver_id=driver.driver_id,
        make=make,
        model=model,
        year=random.randint(2018, 2024),
        vin=f"{random.randint(10000000000000000, 99999999999999999)}",
        vehicle_type=random.choice(["sedan", "suv", "truck", "coupe"]),
        safety_rating=random.randint(3, 5)
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
        firmware_version="v2.1",
        installed_date=date.today() - timedelta(days=random.randint(60, 180)),
        is_active=True,
        last_heartbeat=datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
    )
    session.add(device)
    session.commit()
    session.refresh(device)
    return device

def create_trips(session, driver_id, device_id, num_trips=40):
    """Create realistic trips."""
    # Check existing trips count
    existing_count = session.query(Trip).filter(Trip.driver_id == driver_id).count()
    
    if existing_count >= num_trips:
        # Return existing trips
        return session.query(Trip).filter(Trip.driver_id == driver_id).order_by(Trip.start_time.desc()).limit(num_trips).all()
    
    # Delete existing trips for this driver to avoid conflicts
    session.query(Trip).filter(Trip.driver_id == driver_id).delete()
    session.commit()
    
    trips = []
    now = datetime.utcnow()
    
    # Generate unique trip IDs
    for i in range(num_trips):
        days_ago = random.randint(0, 60)
        start_time = now - timedelta(days=days_ago, hours=random.randint(6, 22), minutes=random.randint(0, 59))
        duration_minutes = random.uniform(15, 120)
        end_time = start_time + timedelta(minutes=duration_minutes)
        distance_miles = duration_minutes * random.uniform(0.5, 1.5)
        
        origin_city, origin_state = get_random_location()
        destination_city, destination_state = get_random_location()
        while destination_city == origin_city:
            destination_city, destination_state = get_random_location()
        
        harsh_braking = random.randint(0, 2) if random.random() < 0.25 else 0
        rapid_accel = random.randint(0, 4) if random.random() < 0.3 else 0
        speeding = random.randint(0, 1) if random.random() < 0.15 else 0
        harsh_corner = random.randint(0, 2) if random.random() < 0.2 else 0
        phone_usage = random.random() < 0.05
        
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
            avg_speed=random.uniform(25, 60),
            max_speed=random.uniform(45, 80),
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

def create_risk_score(session, driver_id, trips):
    """Create risk score with categories."""
    if not trips:
        return None
    
    # Delete existing risk scores for this driver
    session.query(RiskScore).filter(RiskScore.driver_id == driver_id).delete()
    session.commit()
    
    total_trips = len(trips)
    total_miles = sum(t.distance_miles or 0 for t in trips)
    avg_trip_score = sum(t.trip_score or 70 for t in trips) / total_trips if total_trips > 0 else 70
    
    safety_score = avg_trip_score
    risk_score = max(0, min(100, 100 - safety_score))
    
    behavior_score = max(0, min(100, safety_score + random.uniform(-8, 8)))
    mileage_score = max(0, min(100, 80 - (total_miles / 1000) * 2 + random.uniform(-5, 5)))
    time_pattern_score = max(0, min(100, 75 + random.uniform(-10, 10)))
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

def create_premium(session, driver_id, risk_score_obj):
    """Create premium with policy details."""
    existing = session.query(Premium).filter(
        Premium.driver_id == driver_id,
        Premium.status == 'active'
    ).first()
    
    if existing:
        # Update existing premium
        existing.policy_type = random.choice(['PHYD', 'PAYD', 'Hybrid'])
        existing.coverage_type = random.choice(['Comprehensive', 'Full Coverage', 'Liability'])
        existing.coverage_limit = random.choice([50000, 100000, 250000, 500000])
        existing.deductible = random.choice([500, 1000, 1500, 2000])
        if existing.policy_type == 'PAYD':
            existing.total_miles_allowed = random.choice([6000, 8000, 10000, 12000])
        existing.policy_last_updated = datetime.utcnow()
        session.commit()
        return existing
    
    risk_score = risk_score_obj.risk_score if risk_score_obj else 50
    base_premium = random.choice([1000, 1200, 1400, 1600])
    risk_multiplier = 0.7 if risk_score < 40 else 1.2 if risk_score > 60 else 1.0
    usage_multiplier = random.uniform(0.9, 1.1)
    discount_factor = random.uniform(0.95, 1.0)
    
    final_premium = base_premium * risk_multiplier * usage_multiplier * discount_factor
    
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
        policy_type=random.choice(['PHYD', 'PAYD', 'Hybrid']),
        coverage_type=random.choice(['Comprehensive', 'Full Coverage', 'Liability']),
        coverage_limit=random.choice([50000, 100000, 250000, 500000]),
        deductible=random.choice([500, 1000, 1500, 2000]),
        policy_last_updated=datetime.utcnow()
    )
    
    if premium.policy_type == 'PAYD':
        premium.total_miles_allowed = random.choice([6000, 8000, 10000, 12000])
    
    session.add(premium)
    session.commit()
    session.refresh(premium)
    return premium

def create_telematics_events(session, driver_id, device_id, trips):
    """Create telematics events."""
    # Delete existing events for this driver
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
    if not trips:
        return None
    
    # Delete existing statistics for this driver
    session.query(DriverStatistics).filter(DriverStatistics.driver_id == driver_id).delete()
    session.commit()
    
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
    print("Comprehensive Data Population for Selected Drivers")
    print("=" * 70)
    
    session = SessionLocal()
    credentials = []
    
    try:
        # Get first 7 drivers
        drivers = session.query(Driver).order_by(Driver.driver_id).limit(7).all()
        print(f"\nSelected {len(drivers)} drivers for comprehensive data population\n")
        
        for driver in drivers:
            print(f"📊 Processing {driver.driver_id}: {driver.first_name} {driver.last_name}")
            
            # Create user account
            user_result = create_user_for_driver(session, driver)
            if isinstance(user_result, tuple):
                user, password = user_result
            else:
                user = user_result
                password = f"password{driver.driver_id[4:]}"
            print(f"  ✅ User: {user.username} / {password}")
            
            # Create vehicle
            vehicle = create_vehicle(session, driver)
            print(f"  ✅ Vehicle: {vehicle.make} {vehicle.model} ({vehicle.year})")
            
            # Create device
            device = create_device(session, driver, vehicle)
            print(f"  ✅ Device: {device.device_id}")
            
            # Create trips
            trips = create_trips(session, driver.driver_id, device.device_id, num_trips=40)
            print(f"  ✅ Created {len(trips)} trips")
            
            # Create risk score
            risk_score = create_risk_score(session, driver.driver_id, trips)
            print(f"  ✅ Risk Score: {risk_score.risk_score:.1f}")
            
            # Create premium
            premium = create_premium(session, driver.driver_id, risk_score)
            print(f"  ✅ Premium: ${premium.monthly_premium:.2f}/month ({premium.policy_type})")
            
            # Create telematics events
            try:
                events = create_telematics_events(session, driver.driver_id, device.device_id, trips)
                print(f"  ✅ Created {len(events)} telematics events")
            except Exception as e:
                print(f"  ⚠️  Skipped telematics events: {str(e)[:50]}")
                events = []
            
            # Create driver statistics
            stats = create_driver_statistics(session, driver.driver_id, trips)
            print(f"  ✅ Driver Statistics: {stats.total_trips} trips, {stats.total_miles:.1f} miles")
            
            credentials.append({
                'driver_id': driver.driver_id,
                'username': user.username,
                'password': password,
                'email': driver.email or 'N/A',
                'full_name': f"{driver.first_name} {driver.last_name}",
                'phone': driver.phone or 'N/A',
                'license_number': driver.license_number or 'N/A',
                'license_state': driver.license_state or 'N/A',
                'years_licensed': driver.years_licensed or 'N/A',
                'address': driver.address or 'N/A',
                'city': driver.city or 'N/A',
                'state': driver.state or 'N/A',
                'zip_code': driver.zip_code or 'N/A',
                'date_of_birth': str(driver.date_of_birth) if driver.date_of_birth else 'N/A',
                'gender': driver.gender or 'N/A',
                'marital_status': driver.marital_status or 'N/A',
                'vehicle': f"{vehicle.make} {vehicle.model}",
                'premium': f"${premium.monthly_premium:.2f}/month",
                'policy_type': premium.policy_type,
                'risk_score': f"{risk_score.risk_score:.1f}",
                'total_trips': len(trips),
                'total_miles': f"{sum(t.distance_miles or 0 for t in trips):.1f}"
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
                    'vehicle', 'premium', 'policy_type', 'risk_score', 'total_trips', 'total_miles'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(credentials)
            
            print(f"✅ Credentials saved to: {csv_path}")
        
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Drivers processed: {len(drivers)}")
        print(f"Users created: {len([c for c in credentials])}")
        print(f"Total trips created: {sum(int(c['total_trips']) for c in credentials)}")
        print(f"\n📄 Credentials file: {csv_filename}")
        print("\n💡 Login format:")
        print("   Username: driver{number} (e.g., driver0001)")
        print("   Password: password{number} (e.g., password0001)")
        
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

