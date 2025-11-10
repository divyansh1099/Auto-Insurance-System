"""
Rewards and achievements endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db, User, Trip
from app.models.schemas import (
    RewardsSummaryResponse,
    MilestoneResponse,
    AchievementResponse,
    PointsRuleResponse
)
from app.utils.auth import get_current_user

router = APIRouter()


# Default milestones (if table doesn't exist)
DEFAULT_MILESTONES = [
    {"milestone_id": 1, "points_threshold": 100, "reward_name": "100 Points", "reward_description": "5% Extra Discount", "status": "pending"},
    {"milestone_id": 2, "points_threshold": 250, "reward_name": "250 Points", "reward_description": "Free Roadside Assistance", "status": "pending"},
    {"milestone_id": 3, "points_threshold": 500, "reward_name": "500 Points", "reward_description": "10% Extra Discount", "status": "pending"},
    {"milestone_id": 4, "points_threshold": 1000, "reward_name": "1000 Points", "reward_description": "Premium Upgrade", "status": "pending"},
]

# Default achievements (if table doesn't exist)
DEFAULT_ACHIEVEMENTS = [
    {"achievement_id": "a1", "achievement_name": "Safe Week", "achievement_description": "7 consecutive days with no safety events", "status": "pending"},
    {"achievement_id": "a2", "achievement_name": "Speed Demon Reformed", "achievement_description": "No speeding incidents in 30 days", "status": "pending"},
    {"achievement_id": "a3", "achievement_name": "Smooth Operator", "achievement_description": "50 trips with perfect acceleration/braking", "status": "pending"},
    {"achievement_id": "a4", "achievement_name": "Century Club", "achievement_description": "Complete 100 trips", "status": "pending"},
    {"achievement_id": "a5", "achievement_name": "Perfect Score", "achievement_description": "Achieve a trip score of 100", "status": "pending"},
]

# Default points rules
DEFAULT_POINTS_RULES = [
    {"rule_id": 1, "rule_name": "Excellent Trips", "rule_description": "Earn 10 points for trips scored 80+", "min_score": 80, "max_score": 100, "points_awarded": 10},
    {"rule_id": 2, "rule_name": "Good Trips", "rule_description": "Earn 5 points for trips scored 60-79", "min_score": 60, "max_score": 79, "points_awarded": 5},
]


def calculate_reward_points(driver_id: str, db: Session) -> int:
    """Calculate current reward points for a driver."""
    # Get trips for this driver
    trips = (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id)
        .all()
    )
    
    total_points = 0
    
    for trip in trips:
        # Calculate trip score if not exists
        trip_score = trip.trip_score
        if trip_score is None:
            trip_score = max(0, min(100, 100 - (
                (trip.harsh_braking_count or 0) * 5 +
                (trip.rapid_accel_count or 0) * 3 +
                (trip.speeding_count or 0) * 8 +
                (trip.harsh_corner_count or 0) * 4
            )))
        
        # Award points based on trip score
        if trip_score >= 80:
            total_points += 10  # Excellent trip
        elif trip_score >= 60:
            total_points += 5   # Good trip
    
    return total_points


@router.get("/{driver_id}/summary", response_model=RewardsSummaryResponse)
async def get_rewards_summary(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get rewards summary for Rewards page."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's rewards"
        )
    
    # Calculate current points
    current_points = calculate_reward_points(driver_id, db)
    
    # Find next milestone
    next_milestone = None
    for milestone in DEFAULT_MILESTONES:
        if current_points < milestone["points_threshold"]:
            next_milestone = {
                "points_threshold": milestone["points_threshold"],
                "reward_description": milestone["reward_description"],
                "points_needed": milestone["points_threshold"] - current_points,
                "progress_percentage": (current_points / milestone["points_threshold"]) * 100
            }
            break
    
    # If all milestones achieved, use last one
    if not next_milestone:
        last_milestone = DEFAULT_MILESTONES[-1]
        next_milestone = {
            "points_threshold": last_milestone["points_threshold"],
            "reward_description": last_milestone["reward_description"],
            "points_needed": 0,
            "progress_percentage": 100.0
        }
    
    return RewardsSummaryResponse(
        current_points=current_points,
        next_milestone=next_milestone
    )


@router.get("/{driver_id}/milestones", response_model=List[MilestoneResponse])
async def get_milestones(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get reward milestones for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's milestones"
        )
    
    # Calculate current points
    current_points = calculate_reward_points(driver_id, db)
    
    # Determine status for each milestone
    milestones = []
    for milestone in DEFAULT_MILESTONES:
        status = "unlocked" if current_points >= milestone["points_threshold"] else "pending"
        milestones.append(MilestoneResponse(
            milestone_id=milestone["milestone_id"],
            points_threshold=milestone["points_threshold"],
            reward_name=milestone["reward_name"],
            reward_description=milestone["reward_description"],
            status=status
        ))
    
    return milestones


@router.get("/{driver_id}/achievements", response_model=List[AchievementResponse])
async def get_achievements(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get achievements for a driver."""
    # Check permissions
    if not current_user.is_admin and current_user.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this driver's achievements"
        )
    
    # Get trips for this driver
    trips = (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id)
        .order_by(Trip.start_time.desc())
        .all()
    )
    
    # Check achievement criteria
    achievements = []
    
    # Safe Week: 7 consecutive days with no safety events
    safe_week_achieved = False
    if len(trips) >= 7:
        # Check last 7 trips for no safety events
        recent_trips = trips[:7]
        safe_week_achieved = all(
            (trip.harsh_braking_count or 0) == 0 and
            (trip.rapid_accel_count or 0) == 0 and
            (trip.speeding_count or 0) == 0 and
            (trip.harsh_corner_count or 0) == 0
            for trip in recent_trips
        )
    
    # Speed Demon Reformed: No speeding in last 30 days
    no_speeding_30_days = False
    if len(trips) > 0:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        recent_trips_30d = [t for t in trips if t.start_time >= cutoff_date]
        no_speeding_30_days = all((trip.speeding_count or 0) == 0 for trip in recent_trips_30d)
    
    # Smooth Operator: 50 trips with perfect acceleration/braking
    perfect_trips = sum(
        1 for trip in trips
        if (trip.harsh_braking_count or 0) == 0 and (trip.rapid_accel_count or 0) == 0
    )
    smooth_operator_achieved = perfect_trips >= 50
    
    # Century Club: 100 trips
    century_club_achieved = len(trips) >= 100
    
    # Perfect Score: Trip score of 100
    perfect_score_achieved = any(
        (trip.trip_score or 0) == 100 or
        ((trip.harsh_braking_count or 0) == 0 and
         (trip.rapid_accel_count or 0) == 0 and
         (trip.speeding_count or 0) == 0 and
         (trip.harsh_corner_count or 0) == 0)
        for trip in trips
    )
    
    # Map achievements
    achievement_statuses = {
        "a1": "achieved" if safe_week_achieved else "pending",
        "a2": "achieved" if no_speeding_30_days else "pending",
        "a3": "achieved" if smooth_operator_achieved else "pending",
        "a4": "achieved" if century_club_achieved else "pending",
        "a5": "achieved" if perfect_score_achieved else "pending",
    }
    
    for achievement in DEFAULT_ACHIEVEMENTS:
        achievements.append(AchievementResponse(
            achievement_id=achievement["achievement_id"],
            achievement_name=achievement["achievement_name"],
            achievement_description=achievement["achievement_description"],
            status=achievement_statuses.get(achievement["achievement_id"], "pending")
        ))
    
    return achievements


@router.get("/rules", response_model=List[PointsRuleResponse])
async def get_points_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get points earning rules."""
    # Return default rules (could be from database in future)
    return [
        PointsRuleResponse(**rule) for rule in DEFAULT_POINTS_RULES
    ]


@router.post("/{driver_id}/award-points")
async def award_points(
    driver_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Award points to a driver (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can award points"
        )
    
    # In a real implementation, this would update a rewards/points table
    # For now, points are calculated from trips
    return {
        "message": "Points are automatically calculated from trip scores",
        "driver_id": driver_id
    }

