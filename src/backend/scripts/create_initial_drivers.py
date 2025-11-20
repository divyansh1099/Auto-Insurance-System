
import sys
import os
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.database import SessionLocal, Driver

def main():
    session = SessionLocal()
    try:
        print("Creating initial drivers...")
        for i in range(1, 11):
            driver_id = f"DRV-{i:04d}"
            existing = session.query(Driver).filter(Driver.driver_id == driver_id).first()
            if not existing:
                driver = Driver(
                    driver_id=driver_id,
                    email=f"driver{i}@example.com",
                    first_name=f"Driver{i}",
                    last_name="Test",
                    created_at=date.today()
                )
                session.add(driver)
                print(f"Created {driver_id}")
            else:
                print(f"Skipping {driver_id} (already exists)")
        
        session.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
