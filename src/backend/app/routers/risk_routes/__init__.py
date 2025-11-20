"""
Risk Routes Package

Modular risk scoring endpoints organized by functionality:
- scoring: Risk score calculation
- analysis: Breakdown, history, trends
- recommendations: Risk recommendations and insights
"""

from fastapi import APIRouter
from app.routers.risk_routes import scoring, analysis, recommendations

# Create main risk router
router = APIRouter()

# Include sub-routers
router.include_router(scoring.router, tags=["Risk Scoring"])
router.include_router(analysis.router, tags=["Risk Analysis"])
router.include_router(recommendations.router, tags=["Risk Recommendations"])

__all__ = ["router"]
