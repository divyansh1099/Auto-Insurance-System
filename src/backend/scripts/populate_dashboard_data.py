#!/usr/bin/env python3
"""
Populate database with realistic dashboard data for driver dashboard.
This script adds trips with location data, risk scores, premiums, and events.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, date, timedelta
import random
from sqlalchemy import func
from app.models.database import (
    SessionLocal,
    Driver, Vehicle, Device, Trip, RiskScore, Premium, User, TelematicsEvent, DriverStatistics
)

# US Cities and States for realistic location data
CITIES_STATES = [
    ("Los Angeles", "CA"), ("San Francisco", "CA"), ("San Diego", "CA"),
    ("New York", "NY"), ("Buffalo", "NY"), ("Albany", "NY"),
    ("Houston", "TX"), ("Dallas", "TX"), ("Austin", "TX"),
    ("Miami", "FL"), ("Tampa", "FL"), ("Orlando", "FL"),
    ("Chicago", "IL"), ("Phoenix", "AZ"), ("Seattle", "WA"),
    ("Boston", "MA"), ("Denver", "CO"), ("Portland", "OR")
]

def get_random_location():
    """Get a random city and state."""
    return random.choice(CITIES_STATES)

def calculate_trip_score(trip):
    """Calculate trip score based on events."""
    base_score = 100
    score = base_score
    
    # Deduct points for safety events
    score -= (trip.harsh_braking_count or 0) * 5
    score -= (trip.rapid_accel_count or 0) * 3
    score -= (trip.speeding_count or 0) * 8
    score -= (trip.harsh_corner_count or 0) * 4
    
    # Bonus for longer trips (more data)
    if trip.distance_miles and trip.distance_miles > 10:
        score += min(5, trip.distance_miles / 20)
    
    # Penalty for phone usage
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

def populate_trips_with_locations(session, driver_id):
    """Populate trips with location data, scores, and risk levels."""
    print(f"  Updating trips for driver {driver_id}...")
    
    trips = session.query(Trip).filter(Trip.driver_id == driver_id).all()
    
    for trip in trips:
        # Add location data if missing
        if not trip.origin_city:
            origin_city, origin_state = get_random_location()
            trip.origin_city = origin_city
            trip.origin_state = origin_state
        
        if not trip.destination_city:
            # Destination should be different from origin
            destination_city, destination_state = get_random_location()
            while destination_city == trip.origin_city:
                destination_city, destination_state = get_random_location()
            trip.destination_city = destination_city
            trip.destination_state = destination_state
        
        # Calculate and add trip score if missing
        if trip.trip_score is None:
            trip.trip_score = calculate_trip_score(trip)
        
        # Add risk level if missing
        if not trip.risk_level:
            trip.risk_level = get_risk_level(trip.trip_score)
    
    session.commit()
    print(f"    Updated {len(trips)} trips")

def create_realistic_trips(session, driver_id, device_id, num_trips=30):
    """Create realistic trips for a driver."""
    print(f"  Creating {num_trips} trips for driver {driver_id}...")
    
    trips = []
    now = datetime.utcnow()
    
    for i in range(num_trips):
        # Random date in last 30 days
        days_ago = random.randint(0, 30)
        start_time = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        # Trip duration: 10-90 minutes
        duration_minutes = random.uniform(10, 90)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Distance: roughly 0.5-1 mile per minute
        distance_miles = duration_minutes * random.uniform(0.4, 1.2)
        
        # Get origin and destination
        origin_city, origin_state = get_random_location()
        destination_city, destination_state = get_random_location()
        while destination_city == origin_city:
            destination_city, destination_state = get_random_location()
        
        # Safety events (more events = lower score)
        harsh_braking = random.randint(0, 3) if random.random() < 0.3 else 0
        rapid_accel = random.randint(0, 5) if random.random() < 0.4 else 0
        speeding = random.randint(0, 2) if random.random() < 0.2 else 0
        harsh_corner = random.randint(0, 2) if random.random() < 0.25 else 0
        phone_usage = random.random() < 0.1
        
        # Calculate trip score
        trip_score = calculate_trip_score(type('obj', (object,), {
            'harsh_braking_count': harsh_braking,
            'rapid_accel_count': rapid_accel,
            'speeding_count': speeding,
            'harsh_corner_count': harsh_corner,
            'phone_usage_detected': phone_usage,
            'distance_miles': distance_miles
        })())
        
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
            avg_speed=random.uniform(25, 55),
            max_speed=random.uniform(45, 75),
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
    print(f"    Created {len(trips)} trips")
    return trips

def create_risk_scores_with_categories(session, driver_id):
    """Create risk scores with category scores and detailed factors."""
    print(f"  Creating risk scores for driver {driver_id}...")
    
    # Get trips to calculate realistic risk factors
    trips = session.query(Trip).filter(Trip.driver_id == driver_id).all()
    
    if not trips:
        return
    
    # Calculate aggregated metrics
    total_trips = len(trips)
    total_miles = sum(t.distance_miles or 0 for t in trips)
    avg_trip_score = sum(t.trip_score or 70 for t in trips) / total_trips if total_trips > 0 else 70
    
    # Calculate risk score (inverse of safety score)
    safety_score = avg_trip_score
    risk_score = max(0, min(100, 100 - safety_score))
    
    # Category scores (0-100, higher is better)
    behavior_score = max(0, min(100, safety_score + random.uniform(-10, 10)))
    mileage_score = max(0, min(100, 80 - (total_miles / 1000) * 2 + random.uniform(-5, 5)))
    time_pattern_score = max(0, min(100, 75 + random.uniform(-10, 10)))
    location_score = max(0, min(100, 70 + random.uniform(-10, 10)))
    
    # Detailed risk factors
    speeding_frequency = sum(t.speeding_count or 0 for t in trips) / max(1, total_miles / 100)
    acceleration_pattern = sum(t.rapid_accel_count or 0 for t in trips) / max(1, total_miles / 100)
    hard_braking_frequency = sum(t.harsh_braking_count or 0 for t in trips) / max(1, total_miles / 100)
    
    # Night driving percentage
    night_trips = sum(1 for t in trips if t.start_time and (t.start_time.hour >= 22 or t.start_time.hour < 6))
    night_driving_percentage = (night_trips / total_trips * 100) if total_trips > 0 else 0
    
    # High risk area exposure (mock)
    high_risk_area_exposure = random.uniform(5, 25)
    
    # Weather risk exposure (mock)
    weather_risk_exposure = random.uniform(10, 30)
    
    # Phone usage incidents
    phone_usage_incidents = sum(1 for t in trips if t.phone_usage_detected)
    
    # Create risk score record
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
        high_risk_area_exposure=round(high_risk_area_exposure, 2),
        weather_risk_exposure=round(weather_risk_exposure, 2),
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
    print(f"    Created risk score: {risk_score:.1f}")

def update_premiums_with_policy_details(session, driver_id):
    """Update premiums with policy details."""
    print(f"  Updating premiums for driver {driver_id}...")
    
    premiums = session.query(Premium).filter(
        Premium.driver_id == driver_id,
        Premium.status == 'active'
    ).all()
    
    for premium in premiums:
        # Add policy details if missing
        if premium.policy_type is None:
            premium.policy_type = random.choice(['PHYD', 'PAYD', 'Hybrid'])
        
        if premium.coverage_type is None:
            premium.coverage_type = random.choice(['Comprehensive', 'Full Coverage', 'Liability'])
        
        if premium.coverage_limit is None:
            premium.coverage_limit = random.choice([50000, 100000, 250000, 500000])
        
        if premium.deductible is None:
            premium.deductible = random.choice([500, 1000, 1500, 2000])
        
        if premium.policy_type == 'PAYD' and premium.total_miles_allowed is None:
            premium.total_miles_allowed = random.choice([6000, 8000, 10000, 12000])
        
        if premium.policy_last_updated is None:
            premium.policy_last_updated = datetime.utcnow()
    
    session.commit()
    print(f"    Updated {len(premiums)} premiums")

def create_telematics_events(session, driver_id, device_id, trips):
    """Create telematics events for trips (for alerts and risk factors)."""
    print(f"  Creating telematics events for driver {driver_id}...")
    
    events = []
    
    for trip in trips[:10]:  # Create events for first 10 trips
        if not trip.start_time or not trip.end_time:
            continue
        
        # Create events throughout the trip
        num_events = random.randint(5, 20)
        event_interval = (trip.end_time - trip.start_time).total_seconds() / num_events
        
        for i in range(num_events):
            event_time = trip.start_time + timedelta(seconds=i * event_interval)
            
            # Determine event type based on trip data
            event_type = None
            if trip.harsh_braking_count and i < trip.harsh_braking_count:
                event_type = 'harsh_brake'
            elif trip.rapid_accel_count and i < trip.rapid_accel_count:
                event_type = 'rapid_accel'
            elif trip.speeding_count and i < trip.speeding_count:
                event_type = 'speeding'
            elif trip.phone_usage_detected and i == 0:
                event_type = 'phone_usage'
            
            event = TelematicsEvent(
                event_id=f"EVT-{driver_id[4:]}-{trip.trip_id[4:]}-{i}",
                device_id=device_id,
                driver_id=driver_id,
                trip_id=trip.trip_id,
                timestamp=event_time,
                latitude=trip.start_latitude + (trip.end_latitude - trip.start_latitude) * (i / num_events) if trip.start_latitude and trip.end_latitude else None,
                longitude=trip.start_longitude + (trip.end_longitude - trip.start_longitude) * (i / num_events) if trip.start_longitude and trip.end_longitude else None,
                speed=random.uniform(20, 70),
                acceleration=random.uniform(-5, 5),
                braking_force=random.uniform(0, 10),
                heading=random.uniform(0, 360),
                altitude=random.uniform(0, 500),
                gps_accuracy=random.uniform(1, 10),
                event_type=event_type
            )
            events.append(event)
    
    if events:
        session.add_all(events)
        session.commit()
        print(f"    Created {len(events)} events")

def create_driver_statistics(session, driver_id):
    """Create driver statistics."""
    print(f"  Creating driver statistics for driver {driver_id}...")
    
    trips = session.query(Trip).filter(Trip.driver_id == driver_id).all()
    
    if not trips:
        return
    
    # Calculate statistics for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_trips = [t for t in trips if t.start_time and t.start_time >= thirty_days_ago]
    
    if not recent_trips:
        return
    
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
    
    # Night driving percentage
    night_trips = sum(1 for t in recent_trips if t.start_time and (t.start_time.hour >= 22 or t.start_time.hour < 6))
    night_driving_pct = (night_trips / total_trips * 100) if total_trips > 0 else 0
    
    # Rush hour percentage (7-9 AM, 5-7 PM)
    rush_hour_trips = sum(1 for t in recent_trips if t.start_time and 
                          ((7 <= t.start_time.hour < 9) or (17 <= t.start_time.hour < 19)))
    rush_hour_pct = (rush_hour_trips / total_trips * 100) if total_trips > 0 else 0
    
    # Weekend percentage
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
    print(f"    Created driver statistics")

def main():
    """Main function."""
    print("=" * 60)
    print("Populating Dashboard Data")
    print("=" * 60)
    
    session = SessionLocal()
    
    try:
        # Get all drivers
        drivers = session.query(Driver).all()
        
        if not drivers:
            print("\n❌ No drivers found. Please run populate_sample_data.py first.")
            return
        
        print(f"\nFound {len(drivers)} drivers")
        
        for driver in drivers:
            print(f"\n📊 Processing driver: {driver.driver_id} ({driver.first_name} {driver.last_name})")
            
            # Get or create device
            device = session.query(Device).filter(Device.driver_id == driver.driver_id).first()
            if not device:
                # Get vehicle
                vehicle = session.query(Vehicle).filter(Vehicle.driver_id == driver.driver_id).first()
                if vehicle:
                    device = Device(
                        device_id=f"DEV-{driver.driver_id[4:]}",
                        driver_id=driver.driver_id,
                        vehicle_id=vehicle.vehicle_id,
                        device_type="OBD-II",
                        manufacturer="TelematicsCorp",
                        firmware_version="v2.1",
                        installed_date=date.today() - timedelta(days=90),
                        is_active=True,
                        last_heartbeat=datetime.utcnow()
                    )
                    session.add(device)
                    session.commit()
                else:
                    print(f"    ⚠️  No vehicle found, skipping device creation")
                    continue
            
            # Check if trips exist
            existing_trips = session.query(Trip).filter(Trip.driver_id == driver.driver_id).count()
            
            if existing_trips == 0:
                # Create new trips
                trips = create_realistic_trips(session, driver.driver_id, device.device_id, num_trips=30)
            else:
                # Update existing trips
                populate_trips_with_locations(session, driver.driver_id)
                trips = session.query(Trip).filter(Trip.driver_id == driver.driver_id).all()
            
            # Create/update risk scores
            existing_risk_scores = session.query(RiskScore).filter(
                RiskScore.driver_id == driver.driver_id
            ).count()
            
            if existing_risk_scores == 0:
                create_risk_scores_with_categories(session, driver.driver_id)
            
            # Update premiums
            update_premiums_with_policy_details(session, driver.driver_id)
            
            # Create telematics events
            existing_events = session.query(TelematicsEvent).filter(
                TelematicsEvent.driver_id == driver.driver_id
            ).count()
            
            if existing_events == 0:
                create_telematics_events(session, driver.driver_id, device.device_id, trips)
            
            # Create driver statistics
            existing_stats = session.query(DriverStatistics).filter(
                DriverStatistics.driver_id == driver.driver_id
            ).count()
            
            if existing_stats == 0:
                create_driver_statistics(session, driver.driver_id)
        
        print("\n" + "=" * 60)
        print("✅ Dashboard Data Population Complete!")
        print("=" * 60)
        print("\n📈 Summary:")
        print(f"  • Processed {len(drivers)} drivers")
        print(f"  • Trips updated/created with location data")
        print(f"  • Risk scores created with category scores")
        print(f"  • Premiums updated with policy details")
        print(f"  • Telematics events created")
        print(f"  • Driver statistics created")
        print("\n🎉 Dashboard should now show real data instead of placeholders!")
        
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

