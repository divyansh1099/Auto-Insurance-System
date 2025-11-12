"""
Request validation middleware

Provides additional security validations:
- Request body size limits
- Request timeout handling
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog

logger = structlog.get_logger()

# Max request body size: 1MB (prevents DoS via large payloads)
MAX_REQUEST_SIZE = 1 * 1024 * 1024  # 1MB in bytes


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""

    def __init__(self, app, max_size: int = MAX_REQUEST_SIZE):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        """Check request size before processing."""
        # Get content length from headers
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                logger.warning(
                    "request_too_large",
                    content_length=content_length,
                    max_size=self.max_size,
                    path=request.url.path
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "detail": f"Request body too large. Maximum size is {self.max_size / 1024 / 1024}MB"
                    }
                )

        response = await call_next(request)
        return response
