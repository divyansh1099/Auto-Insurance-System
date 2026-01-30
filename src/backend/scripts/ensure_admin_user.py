"""
Ensure admin user exists with correct credentials.
Run: docker compose exec backend python /app/scripts/ensure_admin_user.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, User
from app.utils.auth import get_password_hash

def ensure_admin_user():
    """Ensure admin user exists with correct password."""
    db: Session = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if admin_user:
            # Update password hash to ensure it's correct
            admin_user.hashed_password = get_password_hash("admin123")
            admin_user.is_active = True
            admin_user.is_admin = True
            admin_user.email = admin_user.email or "admin@example.com"
            db.commit()
            print("✅ Admin user updated with correct password")
        else:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True,
                driver_id=None  # Admin doesn't need driver_id
            )
            db.add(admin_user)
            db.commit()
            print("✅ Admin user created")
        
        # Verify the user
        admin_user = db.query(User).filter(User.username == "admin").first()
        print(f"\nAdmin user details:")
        print(f"  Username: {admin_user.username}")
        print(f"  Email: {admin_user.email}")
        print(f"  Is Admin: {admin_user.is_admin}")
        print(f"  Is Active: {admin_user.is_active}")
        print(f"  Driver ID: {admin_user.driver_id}")
        print(f"\n✅ Login credentials:")
        print(f"  Username: admin")
        print(f"  Password: admin123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error ensuring admin user: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ensure_admin_user()





