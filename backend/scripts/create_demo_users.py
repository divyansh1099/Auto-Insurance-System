"""
Create demo users for testing.

Run: docker compose exec backend python /app/scripts/create_demo_users.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, User, Driver
from app.utils.auth import get_password_hash

def create_demo_users():
    """Create demo users."""
    db: Session = SessionLocal()
    
    try:
        # Demo users data
        demo_users = [
            {
                "username": "demo1",
                "email": "demo1@example.com",
                "password": "demo123",
                "driver_id": "DRV-0001"
            },
            {
                "username": "demo2",
                "email": "demo2@example.com",
                "password": "demo123",
                "driver_id": "DRV-0002"
            },
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "driver_id": None,  # Admin doesn't need driver_id
                "is_admin": True
            }
        ]
        
        created_count = 0
        
        for user_data in demo_users:
            # Check if user exists by username
            existing_user = db.query(User).filter(
                User.username == user_data["username"]
            ).first()
            
            if existing_user:
                print(f"User {user_data['username']} already exists, skipping...")
                continue
            
            # Check if driver_id is already used by another user (skip if driver_id is None)
            if user_data.get("driver_id"):
                existing_driver_user = db.query(User).filter(
                    User.driver_id == user_data["driver_id"]
                ).first()
                
                if existing_driver_user and existing_driver_user.username != user_data["username"]:
                    print(f"Driver {user_data['driver_id']} already has user {existing_driver_user.username}, skipping {user_data['username']}...")
                    continue
            
            # Check if driver exists (skip for admin users without driver_id)
            if user_data.get("driver_id"):
                driver = db.query(Driver).filter(
                    Driver.driver_id == user_data["driver_id"]
                ).first()
                
                if not driver:
                    print(f"Driver {user_data['driver_id']} not found, skipping user {user_data['username']}...")
                    continue
            
            # Create user
            hashed_password = get_password_hash(user_data["password"])
            
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hashed_password,
                driver_id=user_data["driver_id"],
                is_active=True,
                is_admin=user_data.get("is_admin", False)
            )
            
            try:
                db.add(new_user)
                db.commit()  # Commit individually to catch unique constraint errors
                created_count += 1
                print(f"Created user: {user_data['username']} (driver: {user_data['driver_id']})")
            except Exception as e:
                db.rollback()
                if "UniqueViolation" in str(e) or "duplicate key" in str(e).lower():
                    print(f"User {user_data['username']} or driver {user_data['driver_id']} already exists, skipping...")
                else:
                    raise
        print(f"\n✅ Created {created_count} demo users")
        print("\nLogin credentials:")
        print("  demo1 / demo123")
        print("  demo2 / demo123")
        print("  admin / admin123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating users: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_demo_users()

