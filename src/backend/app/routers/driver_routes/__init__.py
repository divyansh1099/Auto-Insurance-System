from fastapi import APIRouter

from .profile import router as profile_router
from .trips import router as trips_router
from .stats import router as stats_router

# Create a main router that combines all sub-routers
router = APIRouter()

router.include_router(profile_router, tags=["Drivers"])
router.include_router(trips_router, tags=["Driver Trips"])
router.include_router(stats_router, tags=["Driver Statistics"])
