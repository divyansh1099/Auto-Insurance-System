"""
Authentication and authorization utilities.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.database import get_db, User
from app.models.schemas import TokenData

settings = get_settings()

# Password hashing - use bcrypt directly to avoid passlib compatibility issues
# Using bcrypt directly instead of passlib due to version compatibility
pwd_context = None  # Will use bcrypt directly

# HTTP Bearer security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    if not plain_password or not hashed_password:
        return False
    
    try:
        if pwd_context:
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception:
                pass
        
        # Fallback to bcrypt directly
        # Ensure hashed_password is bytes if it's a string
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
            
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_bytes)
    except (ValueError, TypeError, AttributeError) as e:
        # Log error in production but don't expose details
        # Invalid hash format or other errors
        return False


def get_password_hash(password: str) -> str:
    """Hash a password."""
    if pwd_context:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass
    # Fallback to bcrypt directly
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        driver_id: str = payload.get("driver_id")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(username=username, driver_id=driver_id)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    token = credentials.credentials
    token_data = decode_access_token(token)

    user = db.query(User).filter(User.username == token_data.username).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user.
    
    This function prevents timing attacks by always performing password verification
    even if the user doesn't exist, using a dummy hash comparison.
    """
    user = db.query(User).filter(User.username == username).first()

    # Always perform password verification to prevent timing attacks
    # If user doesn't exist, verify against a dummy hash to maintain constant time
    if not user:
        # Use a dummy bcrypt hash to maintain similar timing
        dummy_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "dummy" hash
        verify_password(password, dummy_hash)
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
