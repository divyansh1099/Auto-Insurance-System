"""
Rate limiting utilities using slowapi.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

def get_rate_limiter():
    """Get the rate limiter instance."""
    return limiter


def get_client_ip(request: Request) -> str:
    """Get client IP address for rate limiting."""
    # Check for forwarded IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to remote address
    return get_remote_address(request)

# Export RateLimitExceeded for exception handler
__all__ = ["limiter", "RateLimitExceeded", "get_rate_limiter", "get_client_ip"]

