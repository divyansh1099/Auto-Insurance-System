#!/usr/bin/env python3
"""
Create user accounts for all drivers in the database.
Generates login credentials for each driver.
"""

import sys
import os
import csv
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.database import SessionLocal, Driver, User
from app.utils.auth import get_password_hash

def generate_username(driver):
    """Generate username from driver email or driver_id."""
    if driver.email:
        # Use email prefix (before @)
        username = driver.email.split('@')[0]
        # Remove any special characters
        username = ''.join(c for c in username if c.isalnum() or c in '._-')
        return username.lower()
    else:
        # Fallback to driver_id format
        return f"driver{driver.driver_id[4:].lower()}"

def generate_password(driver_id):
    """Generate a default password based on driver_id."""
    # Use driver_id as base: DRV-0001 -> password0001
    driver_num = driver_id[4:] if len(driver_id) > 4 else driver_id
    return f"password{driver_num}"

def create_user_for_driver(session, driver, password=None):
    """Create a user account for a driver."""
    # Check if user already exists
    existing_user = session.query(User).filter(
        User.driver_id == driver.driver_id
    ).first()
    
    if existing_user:
        print(f"  ⚠️  User already exists for {driver.driver_id}: {existing_user.username}")
        return existing_user, False
    
    # Generate username
    username = generate_username(driver)
    
    # Check if username already exists
    username_exists = session.query(User).filter(User.username == username).first()
    if username_exists:
        # Append driver_id suffix
        username = f"{username}{driver.driver_id[4:]}"
    
    # Generate password if not provided
    if password is None:
        password = generate_password(driver.driver_id)
    
    # Create user
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=driver.email,
        hashed_password=hashed_password,
        driver_id=driver.driver_id,
        is_active=True,
        is_admin=False
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user, True

def main():
    """Main function."""
    print("=" * 70)
    print("Creating User Accounts for All Drivers")
    print("=" * 70)
    
    session = SessionLocal()
    credentials = []
    
    try:
        # Get all drivers
        drivers = session.query(Driver).order_by(Driver.driver_id).all()
        print(f"\nFound {len(drivers)} drivers\n")
        
        created_count = 0
        skipped_count = 0
        
        for driver in drivers:
            print(f"Processing {driver.driver_id}: {driver.first_name} {driver.last_name}")
            
            user, was_created = create_user_for_driver(session, driver)
            
            if was_created:
                created_count += 1
                password = generate_password(driver.driver_id)
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
                    'account_created': str(user.created_at) if user.created_at else 'N/A',
                    'last_updated': str(driver.updated_at) if driver.updated_at else 'N/A'
                })
                print(f"  ✅ Created user: {user.username} (password: {password})")
            else:
                skipped_count += 1
                password = generate_password(driver.driver_id)
                # Still add to credentials for reference
                credentials.append({
                    'driver_id': driver.driver_id,
                    'username': user.username,
                    'password': 'EXISTING_USER',
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
                    'account_created': str(user.created_at) if user.created_at else 'N/A',
                    'last_updated': str(driver.updated_at) if driver.updated_at else 'N/A'
                })
        
        # Save credentials to CSV file
        csv_filename = 'driver_credentials.csv'
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', csv_filename)
        
        if credentials:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'driver_id', 'username', 'password', 'email', 'full_name', 'phone',
                    'license_number', 'license_state', 'years_licensed',
                    'address', 'city', 'state', 'zip_code',
                    'date_of_birth', 'gender', 'marital_status',
                    'account_created', 'last_updated'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(credentials)
            
            print(f"\n✅ Credentials saved to: {csv_path}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Total drivers: {len(drivers)}")
        print(f"Users created: {created_count}")
        print(f"Users skipped (already exist): {skipped_count}")
        print(f"\n📄 Credentials file: {csv_filename}")
        print("\n💡 Default password format: password{driver_number}")
        print("   Example: DRV-0001 -> password0001")
        print("   Example: DRV-0042 -> password0042")
        
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

