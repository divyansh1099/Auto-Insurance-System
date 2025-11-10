"""
Drive Simulator endpoints for calculating risk scores based on trip parameters.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.database import get_db, User
from app.utils.auth import get_current_user

router = APIRouter()


class TripParameters(BaseModel):
    """Trip parameters for simulator."""
    distance_miles: float = Field(..., ge=0, description="Distance in miles")
    duration_minutes: float = Field(..., ge=0, description="Duration in minutes")
    average_speed_mph: float = Field(..., ge=0, description="Average speed in mph")
    max_speed_mph: float = Field(..., ge=0, description="Maximum speed in mph")
    time_of_day: str = Field(..., description="Time of day: morning, afternoon, evening, late_night")
    weather: str = Field(..., description="Weather condition: clear, rain, storm, snow")
    hard_braking_count: int = Field(0, ge=0, description="Number of hard braking events")
    rapid_acceleration_count: int = Field(0, ge=0, description="Number of rapid acceleration events")
    sharp_turn_count: int = Field(0, ge=0, description="Number of sharp turn events")
    speeding_incidents: int = Field(0, ge=0, description="Number of speeding incidents")


class SimulatorScoreResponse(BaseModel):
    """Response with calculated score and breakdown."""
    risk_score: float = Field(..., description="Overall risk score (0-100)")
    safety_score: float = Field(..., description="Safety score (0-100, higher is better)")
    trip_score: float = Field(..., description="Trip score (0-100, higher is better)")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    score_breakdown: dict = Field(..., description="Detailed breakdown of score components")
    recommendations: list[str] = Field(..., description="Recommendations for improvement")


def calculate_simulator_score(params: TripParameters) -> SimulatorScoreResponse:
    """
    Calculate risk score based on trip parameters.
    
    Scoring factors:
    - Speed violations (max speed, speeding incidents)
    - Safety events (hard braking, rapid acceleration, sharp turns)
    - Time of day (late night is riskier)
    - Weather conditions (storm is riskier)
    - Distance and duration (longer trips with events are riskier)
    """
    score_components = {}
    risk_points = 0.0
    max_points = 100.0
    
    # 1. Speed Analysis (30 points max)
    speed_score = 30.0
    
    # Max speed penalty (15 points)
    if params.max_speed_mph > 80:
        speed_penalty = min(15, (params.max_speed_mph - 80) * 0.5)
        speed_score -= speed_penalty
        score_components["max_speed"] = {
            "penalty": speed_penalty,
            "reason": f"Excessive max speed ({params.max_speed_mph} mph)"
        }
    elif params.max_speed_mph > 70:
        speed_penalty = min(10, (params.max_speed_mph - 70) * 0.3)
        speed_score -= speed_penalty
        score_components["max_speed"] = {
            "penalty": speed_penalty,
            "reason": f"High max speed ({params.max_speed_mph} mph)"
        }
    else:
        score_components["max_speed"] = {"penalty": 0, "reason": "Acceptable max speed"}
    
    # Speeding incidents penalty (15 points)
    if params.speeding_incidents > 0:
        speeding_penalty = min(15, params.speeding_incidents * 3)
        speed_score -= speeding_penalty
        score_components["speeding_incidents"] = {
            "penalty": speeding_penalty,
            "reason": f"{params.speeding_incidents} speeding incident(s)"
        }
    else:
        score_components["speeding_incidents"] = {"penalty": 0, "reason": "No speeding incidents"}
    
    speed_score = max(0, speed_score)
    risk_points += (30 - speed_score)
    score_components["speed_score"] = speed_score
    
    # 2. Safety Events Analysis (40 points max)
    safety_score = 40.0
    
    # Hard braking penalty (10 points max)
    if params.hard_braking_count > 0:
        braking_penalty = min(10, params.hard_braking_count * 2)
        safety_score -= braking_penalty
        score_components["hard_braking"] = {
            "penalty": braking_penalty,
            "count": params.hard_braking_count,
            "reason": f"{params.hard_braking_count} hard braking event(s)"
        }
    else:
        score_components["hard_braking"] = {"penalty": 0, "count": 0, "reason": "No hard braking"}
    
    # Rapid acceleration penalty (10 points max)
    if params.rapid_acceleration_count > 0:
        accel_penalty = min(10, params.rapid_acceleration_count * 2)
        safety_score -= accel_penalty
        score_components["rapid_acceleration"] = {
            "penalty": accel_penalty,
            "count": params.rapid_acceleration_count,
            "reason": f"{params.rapid_acceleration_count} rapid acceleration event(s)"
        }
    else:
        score_components["rapid_acceleration"] = {"penalty": 0, "count": 0, "reason": "No rapid acceleration"}
    
    # Sharp turn penalty (10 points max)
    if params.sharp_turn_count > 0:
        turn_penalty = min(10, params.sharp_turn_count * 2)
        safety_score -= turn_penalty
        score_components["sharp_turns"] = {
            "penalty": turn_penalty,
            "count": params.sharp_turn_count,
            "reason": f"{params.sharp_turn_count} sharp turn event(s)"
        }
    else:
        score_components["sharp_turns"] = {"penalty": 0, "count": 0, "reason": "No sharp turns"}
    
    # Total safety events penalty (10 points max)
    total_events = params.hard_braking_count + params.rapid_acceleration_count + params.sharp_turn_count
    if total_events > 5:
        event_penalty = min(10, (total_events - 5) * 1)
        safety_score -= event_penalty
        score_components["total_events"] = {
            "penalty": event_penalty,
            "count": total_events,
            "reason": f"High number of safety events ({total_events})"
        }
    
    safety_score = max(0, safety_score)
    risk_points += (40 - safety_score)
    score_components["safety_score"] = safety_score
    
    # 3. Time of Day Analysis (10 points max)
    time_score = 10.0
    if params.time_of_day == "late_night":
        time_penalty = 5
        time_score -= time_penalty
        score_components["time_of_day"] = {
            "penalty": time_penalty,
            "reason": "Late night driving is riskier"
        }
    elif params.time_of_day == "evening":
        time_penalty = 2
        time_score -= time_penalty
        score_components["time_of_day"] = {
            "penalty": time_penalty,
            "reason": "Evening driving has moderate risk"
        }
    else:
        score_components["time_of_day"] = {"penalty": 0, "reason": "Daytime driving"}
    
    time_score = max(0, time_score)
    risk_points += (10 - time_score)
    score_components["time_score"] = time_score
    
    # 4. Weather Analysis (10 points max)
    weather_score = 10.0
    if params.weather == "storm":
        weather_penalty = 8
        weather_score -= weather_penalty
        score_components["weather"] = {
            "penalty": weather_penalty,
            "reason": "Storm conditions significantly increase risk"
        }
    elif params.weather == "snow":
        weather_penalty = 6
        weather_score -= weather_penalty
        score_components["weather"] = {
            "penalty": weather_penalty,
            "reason": "Snow conditions increase risk"
        }
    elif params.weather == "rain":
        weather_penalty = 3
        weather_score -= weather_penalty
        score_components["weather"] = {
            "penalty": weather_penalty,
            "reason": "Rain conditions slightly increase risk"
        }
    else:
        score_components["weather"] = {"penalty": 0, "reason": "Clear weather conditions"}
    
    weather_score = max(0, weather_score)
    risk_points += (10 - weather_score)
    score_components["weather_score"] = weather_score
    
    # 5. Trip Efficiency Analysis (10 points max)
    efficiency_score = 10.0
    
    # Average speed vs max speed ratio
    if params.duration_minutes > 0:
        avg_speed_calc = params.distance_miles / (params.duration_minutes / 60)
        speed_variance = abs(params.max_speed_mph - avg_speed_calc)
        
        if speed_variance > 30:
            efficiency_penalty = min(5, (speed_variance - 30) * 0.1)
            efficiency_score -= efficiency_penalty
            score_components["speed_consistency"] = {
                "penalty": efficiency_penalty,
                "reason": "Large variance between average and max speed"
            }
        else:
            score_components["speed_consistency"] = {"penalty": 0, "reason": "Consistent speed"}
    
    # Long trips with many events
    if params.distance_miles > 100 and total_events > 3:
        efficiency_penalty = min(5, (params.distance_miles - 100) * 0.02)
        efficiency_score -= efficiency_penalty
        score_components["trip_length"] = {
            "penalty": efficiency_penalty,
            "reason": "Long trip with multiple safety events"
        }
    
    efficiency_score = max(0, efficiency_score)
    risk_points += (10 - efficiency_score)
    score_components["efficiency_score"] = efficiency_score
    
    # Calculate final scores
    risk_score = min(100, risk_points)  # Risk score (0-100, higher is riskier)
    safety_score_final = max(0, 100 - risk_score)  # Safety score (0-100, higher is better)
    
    # Calculate trip_score (same as safety_score for consistency)
    trip_score = safety_score_final
    
    # Determine risk_level
    if trip_score >= 80:
        risk_level = "low"
    elif trip_score >= 60:
        risk_level = "medium"
    else:
        risk_level = "high"
    
    # Generate recommendations
    recommendations = []
    if params.max_speed_mph > 75:
        recommendations.append("Reduce maximum speed to stay within safe limits")
    if params.speeding_incidents > 0:
        recommendations.append("Avoid speeding to improve your safety score")
    if params.hard_braking_count > 2:
        recommendations.append("Practice smoother braking to reduce hard braking events")
    if params.rapid_acceleration_count > 2:
        recommendations.append("Accelerate more gradually to improve safety")
    if params.sharp_turn_count > 2:
        recommendations.append("Take turns more gradually to reduce risk")
    if params.time_of_day == "late_night":
        recommendations.append("Consider driving during daylight hours when possible")
    if params.weather == "storm":
        recommendations.append("Avoid driving in storm conditions if possible")
    if total_events > 5:
        recommendations.append("Focus on smoother driving to reduce safety events")
    
    if not recommendations:
        recommendations.append("Great driving! Keep up the safe driving habits")
    
    return SimulatorScoreResponse(
        risk_score=round(risk_score, 2),
        safety_score=round(safety_score_final, 2),
        trip_score=round(trip_score, 2),
        risk_level=risk_level,
        score_breakdown=score_components,
        recommendations=recommendations
    )


@router.post("/calculate-score", response_model=SimulatorScoreResponse)
async def calculate_score(
    params: TripParameters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate risk score based on trip parameters.
    
    This endpoint allows users to simulate different driving scenarios
    and see how they would affect their risk score.
    """
    return calculate_simulator_score(params)

