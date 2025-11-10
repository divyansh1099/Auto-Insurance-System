"""
Fix Login Issues - Ensure all required users exist with correct credentials.

Run: docker compose exec backend python /app/scripts/fix_login.py
Or: python src/backend/scripts/fix_login.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, User, Driver
from app.utils.auth import get_password_hash, verify_password

def fix_login():
    """Ensure all required users exist with correct credentials."""
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("Fixing Login Issues")
        print("=" * 60)
        
        # Users to ensure exist
        required_users = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "driver_id": None,
                "is_admin": True,
                "is_active": True
            },
            {
                "username": "demo",
                "email": "demo@example.com",
                "password": "demo123",
                "driver_id": "DRV-0001",  # Link to first driver
                "is_admin": False,
                "is_active": True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for user_data in required_users:
            username = user_data["username"]
            print(f"\n📋 Checking user: {username}")
            
            # Check if user exists
            existing_user = db.query(User).filter(User.username == username).first()
            
            if existing_user:
                print(f"  ✓ User exists")
                
                # Verify password is correct
                password_correct = verify_password(user_data["password"], existing_user.hashed_password)
                
                if not password_correct:
                    print(f"  ⚠ Password incorrect, updating...")
                    existing_user.hashed_password = get_password_hash(user_data["password"])
                    updated_count += 1
                
                # Update other fields
                needs_update = False
                if existing_user.is_active != user_data["is_active"]:
                    existing_user.is_active = user_data["is_active"]
                    needs_update = True
                if existing_user.is_admin != user_data["is_admin"]:
                    existing_user.is_admin = user_data["is_admin"]
                    needs_update = True
                if existing_user.email != user_data["email"]:
                    existing_user.email = user_data["email"]
                    needs_update = True
                if existing_user.driver_id != user_data["driver_id"]:
                    existing_user.driver_id = user_data["driver_id"]
                    needs_update = True
                
                if needs_update or not password_correct:
                    db.commit()
                    print(f"  ✅ User updated")
                else:
                    print(f"  ✅ User already correct")
            else:
                # Check if driver exists and doesn't already have a user
                driver_id = user_data.get("driver_id")
                if driver_id:
                    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
                    if not driver:
                        print(f"  ⚠ Driver {driver_id} not found, creating user without driver_id...")
                        driver_id = None
                    else:
                        # Check if this driver already has a user
                        existing_driver_user = db.query(User).filter(User.driver_id == driver_id).first()
                        if existing_driver_user:
                            print(f"  ⚠ Driver {driver_id} already has user {existing_driver_user.username}, creating user without driver_id...")
                            driver_id = None
                
                # Create new user
                print(f"  ➕ Creating new user...")
                hashed_password = get_password_hash(user_data["password"])
                
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    driver_id=driver_id,
                    is_active=user_data["is_active"],
                    is_admin=user_data["is_admin"]
                )
                
                db.add(new_user)
                db.commit()
                created_count += 1
                print(f"  ✅ User created")
        
        # List all users
        print("\n" + "=" * 60)
        print("Current Users in Database:")
        print("=" * 60)
        all_users = db.query(User).all()
        for user in all_users:
            status = "ACTIVE" if user.is_active else "INACTIVE"
            admin = "ADMIN" if user.is_admin else "USER"
            print(f"  {user.username:15} | {status:8} | {admin:5} | Driver: {user.driver_id or 'N/A'}")
        
        print("\n" + "=" * 60)
        print("Login Credentials:")
        print("=" * 60)
        print("\nAdmin Account:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nDemo Account:")
        print("  Username: demo")
        print("  Password: demo123")
        print("\n" + "=" * 60)
        print(f"✅ Fixed login issues!")
        print(f"   Created: {created_count} users")
        print(f"   Updated: {updated_count} users")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error fixing login: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_login()

