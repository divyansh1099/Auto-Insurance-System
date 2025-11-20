#!/usr/bin/env python3
"""
Batch Risk Scoring Script

Processes multiple drivers for risk score calculation.
Designed to be run as a cron job for nightly updates.

Usage:
    python bin/batch_risk_scoring.py --all
    python bin/batch_risk_scoring.py --driver-ids DRV-0001,DRV-0002,DRV-0003
    python bin/batch_risk_scoring.py --batch-size 100
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, Driver, RiskScore
from app.services.ml_risk_scoring import calculate_ml_risk_score_batch
from app.services.risk_scoring import save_risk_score


def get_all_driver_ids(db: Session) -> list:
    """Get all active driver IDs from database."""
    drivers = db.query(Driver.driver_id).all()
    return [d.driver_id for d in drivers]


def process_batch(driver_ids: list, db: Session, period_days: int = 30):
    """Process a batch of drivers."""
    print(f"\n📊 Processing batch of {len(driver_ids)} drivers...")
    
    try:
        # Calculate risk scores in batch
        results = calculate_ml_risk_score_batch(
            driver_ids=driver_ids,
            db=db,
            period_days=period_days
        )
        
        # Save results to database
        saved_count = 0
        error_count = 0
        
        for driver_id, risk_data in results.items():
            if 'error' in risk_data:
                print(f"  ❌ {driver_id}: {risk_data['error']}")
                error_count += 1
                continue
            
            try:
                save_risk_score(driver_id, risk_data, db)
                saved_count += 1
                print(f"  ✅ {driver_id}: Risk Score = {risk_data['risk_score']:.2f}")
            except Exception as e:
                print(f"  ❌ {driver_id}: Error saving - {str(e)}")
                error_count += 1
        
        print(f"\n✅ Batch complete: {saved_count} saved, {error_count} errors")
        return saved_count, error_count
        
    except Exception as e:
        print(f"❌ Batch processing failed: {str(e)}")
        return 0, len(driver_ids)


def main():
    parser = argparse.ArgumentParser(description='Batch Risk Scoring')
    parser.add_argument('--all', action='store_true', help='Process all drivers')
    parser.add_argument('--driver-ids', type=str, help='Comma-separated list of driver IDs')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size (default: 100)')
    parser.add_argument('--period-days', type=int, default=30, help='Period in days (default: 30)')
    
    args = parser.parse_args()
    
    print("🚀 Batch Risk Scoring Script")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db = SessionLocal()
    
    try:
        # Determine which drivers to process
        if args.all:
            driver_ids = get_all_driver_ids(db)
            print(f"\n📋 Processing ALL drivers: {len(driver_ids)} total")
        elif args.driver_ids:
            driver_ids = [d.strip() for d in args.driver_ids.split(',')]
            print(f"\n📋 Processing specified drivers: {len(driver_ids)} total")
        else:
            print("❌ Error: Must specify --all or --driver-ids")
            sys.exit(1)
        
        if not driver_ids:
            print("❌ No drivers found to process")
            sys.exit(1)
        
        # Process in batches
        total_saved = 0
        total_errors = 0
        batch_size = args.batch_size
        
        for i in range(0, len(driver_ids), batch_size):
            batch = driver_ids[i:i + batch_size]
            print(f"\n--- Batch {i // batch_size + 1} ({i + 1}-{min(i + batch_size, len(driver_ids))} of {len(driver_ids)}) ---")
            
            saved, errors = process_batch(batch, db, args.period_days)
            total_saved += saved
            total_errors += errors
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"Total Drivers Processed: {len(driver_ids)}")
        print(f"Successfully Saved: {total_saved}")
        print(f"Errors: {total_errors}")
        print(f"Success Rate: {(total_saved / len(driver_ids) * 100):.1f}%")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        sys.exit(0 if total_errors == 0 else 1)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
