"""
Custom exception classes for better error handling.
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class BaseAPIException(HTTPException):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ValidationError(BaseAPIException):
    """Validation error exception."""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        error_code = f"VALIDATION_ERROR_{field.upper()}" if field else "VALIDATION_ERROR"
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code
        )
        self.field = field


class NotFoundError(BaseAPIException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        detail = f"{resource} not found"
        if resource_id:
            detail += f": {resource_id}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=f"{resource.upper()}_NOT_FOUND"
        )
        self.resource = resource
        self.resource_id = resource_id


class UnauthorizedError(BaseAPIException):
    """Unauthorized access exception."""
    
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(BaseAPIException):
    """Forbidden access exception."""
    
    def __init__(self, detail: str = "You don't have permission to access this resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class ConflictError(BaseAPIException):
    """Resource conflict exception."""
    
    def __init__(self, detail: str, resource: Optional[str] = None):
        error_code = f"{resource.upper()}_CONFLICT" if resource else "CONFLICT"
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code
        )


class DatabaseError(BaseAPIException):
    """Database operation error."""
    
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR"
        )


class ExternalServiceError(BaseAPIException):
    """External service error."""
    
    def __init__(self, service: str, detail: Optional[str] = None):
        detail = detail or f"External service '{service}' is unavailable"
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code=f"{service.upper()}_SERVICE_ERROR"
        )
        self.service = service

