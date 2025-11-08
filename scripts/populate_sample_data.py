#!/usr/bin/env python3
"""
Populate database with sample data for testing.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, date, timedelta
import random
from backend.app.models.database import (
    Base, engine, SessionLocal,
    Driver, Vehicle, Device, Trip, RiskScore, Premium, User
)
from backend.app.utils.auth import get_password_hash

def create_sample_drivers(session, num_drivers=10):
    """Create sample drivers."""
    print(f"Creating {num_drivers} sample drivers...")

    drivers = []
    for i in range(num_drivers):
        driver_id = f"DRV-{i+1:04d}"

        driver = Driver(
            driver_id=driver_id,
            first_name=f"Driver{i+1}",
            last_name=f"Test{i+1}",
            email=f"driver{i+1}@test.com",
            phone=f"555-{random.randint(1000, 9999)}",
            date_of_birth=date(1980 + random.randint(0, 30), random.randint(1, 12), random.randint(1, 28)),
            license_number=f"DL{random.randint(10000000, 99999999)}",
            license_state=random.choice(["CA", "NY", "TX", "FL"]),
            years_licensed=random.randint(1, 30),
            gender=random.choice(["M", "F"]),
            marital_status=random.choice(["Single", "Married"]),
            address=f"{random.randint(100, 9999)} Main St",
            city="Test City",
            state=random.choice(["CA", "NY", "TX", "FL"]),
            zip_code=f"{random.randint(10000, 99999)}"
        )

        drivers.append(driver)

    session.add_all(drivers)
    session.commit()

    return drivers


def create_sample_vehicles(session, drivers):
    """Create sample vehicles for drivers."""
    print("Creating sample vehicles...")

    makes = ["Toyota", "Honda", "Ford", "Chevrolet", "Tesla"]
    models = ["Sedan", "SUV", "Truck", "Coupe"]

    vehicles = []
    for driver in drivers:
        vehicle = Vehicle(
            vehicle_id=f"VEH-{driver.driver_id[4:]}",
            driver_id=driver.driver_id,
            make=random.choice(makes),
            model=random.choice(models),
            year=random.randint(2015, 2024),
            vin=f"VIN{random.randint(10000000000000000, 99999999999999999)}",
            vehicle_type=random.choice(["sedan", "suv", "truck", "coupe"]),
            safety_rating=random.randint(3, 5)
        )
        vehicles.append(vehicle)

    session.add_all(vehicles)
    session.commit()

    return vehicles


def create_sample_devices(session, drivers, vehicles):
    """Create sample telematics devices."""
    print("Creating sample devices...")

    devices = []
    for driver, vehicle in zip(drivers, vehicles):
        device = Device(
            device_id=f"DEV-{driver.driver_id[4:]}",
            driver_id=driver.driver_id,
            vehicle_id=vehicle.vehicle_id,
            device_type="OBD-II",
            manufacturer="TestManufacturer",
            firmware_version=f"v{random.randint(1, 3)}.{random.randint(0, 9)}",
            installed_date=date.today() - timedelta(days=random.randint(30, 365)),
            is_active=True,
            last_heartbeat=datetime.now() - timedelta(hours=random.randint(0, 24))
        )
        devices.append(device)

    session.add_all(devices)
    session.commit()

    return devices


def create_sample_risk_scores(session, drivers):
    """Create sample risk scores."""
    print("Creating sample risk scores...")

    risk_scores = []
    for driver in drivers:
        # Generate risk score based on profile
        score = random.uniform(20, 80)

        risk_score = RiskScore(
            driver_id=driver.driver_id,
            risk_score=score,
            risk_category="average" if 40 <= score <= 60 else "good" if score < 40 else "below_average",
            confidence=random.uniform(0.7, 0.95),
            model_version="v1.0",
            features={
                "avg_speed": random.uniform(30, 50),
                "harsh_braking_per_100mi": random.uniform(1, 8),
                "speeding_incidents_per_100mi": random.uniform(2, 12)
            },
            shap_values={
                "harsh_braking_per_100mi": random.uniform(-5, 5),
                "speeding_incidents_per_100mi": random.uniform(-5, 5)
            }
        )
        risk_scores.append(risk_score)

    session.add_all(risk_scores)
    session.commit()

    return risk_scores


def create_sample_premiums(session, drivers, risk_scores):
    """Create sample premiums."""
    print("Creating sample premiums...")

    premiums = []
    for driver, risk_score in zip(drivers, risk_scores):
        base_premium = 1200.0
        risk_multiplier = 0.7 if risk_score.risk_score < 40 else 1.2 if risk_score.risk_score > 60 else 1.0

        final_premium = base_premium * risk_multiplier

        premium = Premium(
            driver_id=driver.driver_id,
            policy_id=f"POL-{driver.driver_id[4:]}",
            base_premium=base_premium,
            risk_multiplier=risk_multiplier,
            usage_multiplier=1.0,
            discount_factor=0.98,
            final_premium=final_premium,
            monthly_premium=final_premium / 12,
            effective_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
            status="active"
        )
        premiums.append(premium)

    session.add_all(premiums)
    session.commit()

    return premiums


def create_sample_users(session, drivers):
    """Create sample user accounts."""
    print("Creating sample users...")

    users = []

    # Create demo user
    demo_user = User(
        driver_id=drivers[0].driver_id,
        username="demo",
        email="demo@test.com",
        hashed_password=get_password_hash("demo123"),
        is_active=True,
        is_admin=False
    )
    users.append(demo_user)

    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_admin=True
    )
    users.append(admin_user)

    session.add_all(users)
    session.commit()

    return users


def main():
    """Main function."""
    print("=" * 50)
    print("Populating Sample Data")
    print("=" * 50)

    # Create tables
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)

    # Create session
    session = SessionLocal()

    try:
        # Create sample data
        drivers = create_sample_drivers(session, num_drivers=10)
        vehicles = create_sample_vehicles(session, drivers)
        devices = create_sample_devices(session, drivers, vehicles)
        risk_scores = create_sample_risk_scores(session, drivers)
        premiums = create_sample_premiums(session, drivers, risk_scores)
        users = create_sample_users(session, drivers)

        print("\n" + "=" * 50)
        print("Sample Data Created Successfully!")
        print("=" * 50)
        print(f"\nCreated:")
        print(f"  - {len(drivers)} drivers")
        print(f"  - {len(vehicles)} vehicles")
        print(f"  - {len(devices)} devices")
        print(f"  - {len(risk_scores)} risk scores")
        print(f"  - {len(premiums)} premiums")
        print(f"  - {len(users)} user accounts")
        print(f"\nDemo credentials:")
        print(f"  Username: demo")
        print(f"  Password: demo123")
        print(f"\nAdmin credentials:")
        print(f"  Username: admin")
        print(f"  Password: admin123")

    except Exception as e:
        print(f"\nError: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
