"""
Admin Router Module

This module provides administrative endpoints organized by domain:
- dashboard: System-wide statistics and analytics
- drivers: Driver management (CRUD operations)
- users: User management (CRUD operations)
- policies: Policy management and summaries
- resources: Vehicle, Device, Trip, and Event management

All endpoints require admin authentication.
"""
from fastapi import APIRouter
from app.routers.admin import dashboard, drivers, users, policies, resources

# Create main admin router
router = APIRouter()

# Include sub-routers with their respective prefixes
router.include_router(dashboard.router, prefix="/dashboard", tags=["Admin Dashboard"])
router.include_router(drivers.router, prefix="/drivers", tags=["Admin Drivers"])
router.include_router(users.router, prefix="/users", tags=["Admin Users"])
router.include_router(policies.router, prefix="/policies", tags=["Admin Policies"])
router.include_router(resources.router, tags=["Admin Resources"])

__all__ = ["router"]
