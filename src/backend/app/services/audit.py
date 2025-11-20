from sqlalchemy.orm import Session
from app.models.database import AuditLog
from typing import Optional, Dict, Any

def log_action(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """
    Log an administrative action.
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        action: Action name (e.g., CREATE, UPDATE, DELETE)
        resource_type: Type of resource (e.g., Driver, User)
        resource_id: ID of the resource
        details: Dictionary containing details of the change
        ip_address: IP address of the user
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
