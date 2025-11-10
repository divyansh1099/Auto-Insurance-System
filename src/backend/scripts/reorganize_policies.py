#!/usr/bin/env python3
"""
Reorganize policies: Reduce to 3 policies and assign drivers based on their properties.
Policy assignment logic:
- PHYD (Pay-How-You-Drive): Low risk drivers (risk_score < 40)
- PAYD (Pay-As-You-Drive): Moderate risk, high mileage drivers (risk_score 40-60, high miles)
- Hybrid: High risk or low mileage drivers (risk_score > 60 or very low miles)
"""

import sys
import os
from datetime import datetime, date, timedelta
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.database import (
    SessionLocal, Driver, Premium, RiskScore, Trip
)
from sqlalchemy import func

def get_driver_profile(session, driver_id):
    """Get driver's risk score and driving statistics."""
    # Get latest risk score
    latest_risk = session.query(RiskScore).filter(
        RiskScore.driver_id == driver_id
    ).order_by(RiskScore.calculation_date.desc()).first()
    
    risk_score = latest_risk.risk_score if latest_risk else 50.0
    
    # Get total miles driven
    total_miles = session.query(func.sum(Trip.distance_miles)).filter(
        Trip.driver_id == driver_id
    ).scalar() or 0.0
    
    # Get total trips
    total_trips = session.query(func.count(Trip.trip_id)).filter(
        Trip.driver_id == driver_id
    ).scalar() or 0
    
    return {
        'risk_score': risk_score,
        'total_miles': total_miles,
        'total_trips': total_trips
    }

def assign_policy_type(risk_score, total_miles, driver_index, total_drivers):
    """Assign policy type based on driver characteristics.
    Distributes drivers across 3 policy types to ensure variety."""
    # Sort drivers by risk score and miles to create 3 groups
    # Group 1 (PHYD): Lowest risk drivers (best drivers)
    # Group 2 (PAYD): Moderate risk, moderate-high mileage
    # Group 3 (Hybrid): Higher risk or very low/high mileage
    
    # Distribute drivers into 3 groups based on their index
    # This ensures we get a mix across all 3 policy types
    if driver_index < total_drivers * 0.4:  # First 40% - best drivers
        return 'PHYD'
    elif driver_index < total_drivers * 0.7:  # Next 30% - moderate drivers
        return 'PAYD'
    else:  # Last 30% - varied drivers
        return 'Hybrid'

def create_policy_premium(session, driver_id, policy_type, risk_score, total_miles):
    """Create or update premium with policy details."""
    # Base premium varies by policy type
    base_premiums = {
        'PHYD': 1200,    # Lower base for good drivers
        'PAYD': 1400,    # Moderate base
        'Hybrid': 1600   # Higher base for risky drivers
    }
    base_premium = base_premiums.get(policy_type, 1400)
    
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
    
    # Usage multiplier (based on miles)
    if total_miles < 1000:
        usage_multiplier = 0.9  # Low usage discount
    elif total_miles > 5000:
        usage_multiplier = 1.1  # High usage surcharge
    else:
        usage_multiplier = 1.0
    
    # Discount factor (safe driving discount)
    if risk_score < 30:
        discount_factor = 0.90  # 10% discount
    elif risk_score < 50:
        discount_factor = 0.95  # 5% discount
    else:
        discount_factor = 1.0
    
    final_premium = base_premium * risk_multiplier * usage_multiplier * discount_factor
    monthly_premium = final_premium / 12
    
    # Coverage details based on policy type
    coverage_types = {
        'PHYD': 'Comprehensive',
        'PAYD': 'Full Coverage',
        'Hybrid': 'Liability'
    }
    
    coverage_limits = {
        'PHYD': 500000,  # Higher coverage for good drivers
        'PAYD': 250000,
        'Hybrid': 100000
    }
    
    deductibles = {
        'PHYD': 500,    # Lower deductible for good drivers
        'PAYD': 1000,
        'Hybrid': 2000  # Higher deductible for risky drivers
    }
    
    # Get or create premium
    existing = session.query(Premium).filter(
        Premium.driver_id == driver_id,
        Premium.status == 'active'
    ).first()
    
    if existing:
        # Update existing premium
        existing.policy_type = policy_type
        existing.coverage_type = coverage_types[policy_type]
        existing.coverage_limit = coverage_limits[policy_type]
        existing.deductible = deductibles[policy_type]
        existing.base_premium = base_premium
        existing.risk_multiplier = risk_multiplier
        existing.usage_multiplier = usage_multiplier
        existing.discount_factor = discount_factor
        existing.final_premium = final_premium
        existing.monthly_premium = monthly_premium
        existing.policy_last_updated = datetime.utcnow()
        if policy_type == 'PAYD':
            existing.total_miles_allowed = random.choice([8000, 10000, 12000])
        session.commit()
        return existing
    else:
        # Create new premium
        premium = Premium(
            driver_id=driver_id,
            policy_id=f"POL-{driver_id[4:]}",
            base_premium=base_premium,
            risk_multiplier=risk_multiplier,
            usage_multiplier=usage_multiplier,
            discount_factor=discount_factor,
            final_premium=final_premium,
            monthly_premium=monthly_premium,
            effective_date=date.today() - timedelta(days=random.randint(30, 180)),
            expiration_date=date.today() + timedelta(days=random.randint(180, 365)),
            status='active',
            policy_type=policy_type,
            coverage_type=coverage_types[policy_type],
            coverage_limit=coverage_limits[policy_type],
            deductible=deductibles[policy_type],
            policy_last_updated=datetime.utcnow()
        )
        
        if policy_type == 'PAYD':
            premium.total_miles_allowed = random.choice([8000, 10000, 12000])
        
        session.add(premium)
        session.commit()
        session.refresh(premium)
        return premium

def main():
    session = SessionLocal()
    try:
        print("🔄 Reorganizing policies...")
        print("=" * 60)
        
        # Get all drivers
        drivers = session.query(Driver).order_by(Driver.driver_id).all()
        
        # Group drivers by assigned policy type
        policy_assignments = {
            'PHYD': [],
            'PAYD': [],
            'Hybrid': []
        }
        
        # Sort drivers by risk score and miles for better distribution
        driver_profiles = []
        for driver in drivers:
            profile = get_driver_profile(session, driver.driver_id)
            driver_profiles.append({
                'driver': driver,
                'profile': profile
            })
        
        # Sort by risk score (ascending), then by miles (descending)
        driver_profiles.sort(key=lambda x: (x['profile']['risk_score'], -x['profile']['total_miles']))
        
        print("\n📊 Analyzing drivers and assigning policies:")
        print("-" * 60)
        
        for idx, driver_info in enumerate(driver_profiles):
            driver = driver_info['driver']
            profile = driver_info['profile']
            policy_type = assign_policy_type(profile['risk_score'], profile['total_miles'], idx, len(driver_profiles))
            
            policy_assignments[policy_type].append({
                'driver_id': driver.driver_id,
                'name': f'{driver.first_name} {driver.last_name}',
                'risk_score': profile['risk_score'],
                'total_miles': profile['total_miles'],
                'policy_type': policy_type
            })
            
            print(f"  {driver.driver_id}: {driver.first_name} {driver.last_name}")
            print(f"    Risk Score: {profile['risk_score']:.1f}, Miles: {profile['total_miles']:.0f}")
            print(f"    → Assigned: {policy_type}")
        
        print("\n" + "=" * 60)
        print("📋 Policy Distribution:")
        print(f"  PHYD: {len(policy_assignments['PHYD'])} drivers")
        print(f"  PAYD: {len(policy_assignments['PAYD'])} drivers")
        print(f"  Hybrid: {len(policy_assignments['Hybrid'])} drivers")
        print("=" * 60)
        
        # Deactivate all existing policies first
        print("\n🔄 Deactivating all existing policies...")
        session.query(Premium).filter(Premium.status == 'active').update({'status': 'inactive'})
        session.commit()
        
        # Create/update premiums for each driver, but only keep 3 active policies total
        # Keep one policy per policy type (the first driver in each group)
        print("\n💰 Creating/updating premiums (keeping only 3 active)...")
        print("-" * 60)
        
        active_policy_count = 0
        for policy_type, drivers_list in policy_assignments.items():
            if not drivers_list:
                continue
                
            print(f"\n{policy_type} Policy:")
            for idx, driver_info in enumerate(drivers_list):
                profile = get_driver_profile(session, driver_info['driver_id'])
                
                # Only keep first driver's policy active for each type (3 total)
                should_be_active = (idx == 0) and (active_policy_count < 3)
                
                premium = create_policy_premium(
                    session,
                    driver_info['driver_id'],
                    policy_type,
                    profile['risk_score'],
                    profile['total_miles']
                )
                
                # Set status based on whether this is one of the 3 active policies
                if should_be_active:
                    premium.status = 'active'
                    active_policy_count += 1
                    print(f"  ✅ {driver_info['driver_id']}: ${premium.monthly_premium:.2f}/month (ACTIVE)")
                else:
                    premium.status = 'inactive'
                    print(f"  ⏸️  {driver_info['driver_id']}: ${premium.monthly_premium:.2f}/month (inactive)")
                
                print(f"    Coverage: {premium.coverage_type}, Limit: ${premium.coverage_limit:,.0f}")
                print(f"    Deductible: ${premium.deductible:,.0f}")
                if premium.total_miles_allowed:
                    print(f"    Miles Allowed: {premium.total_miles_allowed:,.0f}")
                
                session.commit()
        
        # Verify final state
        print("\n" + "=" * 60)
        print("✅ Verification:")
        print("-" * 60)
        
        policy_counts = session.query(
            Premium.policy_type,
            func.count(Premium.premium_id).label('count')
        ).filter(Premium.status == 'active').group_by(Premium.policy_type).all()
        
        total_policies = 0
        for pt, count in policy_counts:
            print(f"  {pt}: {count} policies")
            total_policies += count
        
        print(f"\n  Total active policies: {total_policies}")
        print("=" * 60)
        print("\n✅ Policy reorganization complete!")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()

