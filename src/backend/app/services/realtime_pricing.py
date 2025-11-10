"""
Real-Time Dynamic Pricing Service

Updates insurance premiums based on real-time driving behavior.
"""

from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.database import Premium, Driver
from app.routers.pricing import calculate_risk_multiplier, calculate_usage_multiplier

logger = structlog.get_logger()


class RealTimePricingEngine:
    """Calculates dynamic pricing based on real-time behavior."""

    def __init__(self):
        self.base_premium = 100.0  # Base monthly premium

    def calculate_realtime_premium(
        self,
        driver_id: str,
        risk_score: float,
        behavior_metrics: Dict,
        db: Session
    ) -> Dict:
        """
        Calculate premium based on real-time risk score and behavior.
        
        Args:
            driver_id: Driver ID
            risk_score: Current risk score (0-100)
            behavior_metrics: Real-time behavior metrics
            db: Database session
            
        Returns:
            Premium calculation details
        """
        # Get driver's current premium
        driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
        if not driver:
            return {}

        # Get current premium
        current_premium = db.query(Premium).filter(
            Premium.driver_id == driver_id,
            Premium.status == 'active'
        ).first()

        base_premium = current_premium.monthly_premium if current_premium else self.base_premium

        # Calculate risk multiplier from real-time risk score
        risk_multiplier = calculate_risk_multiplier(risk_score)

        # Calculate usage multiplier from behavior metrics
        avg_speed = behavior_metrics.get('avg_speed', 0)
        total_events = behavior_metrics.get('total_events', 0)
        
        # Estimate annual mileage from recent behavior
        # Rough estimate: avg_speed * hours_driven
        # For real-time, use events as proxy (each event ~10 seconds)
        hours_driven = (total_events * 10) / 3600
        estimated_annual_mileage = (avg_speed * hours_driven * 365) if hours_driven > 0 else 12000
        
        usage_multiplier = calculate_usage_multiplier(estimated_annual_mileage)

        # Calculate behavior penalty/bonus
        behavior_adjustment = self._calculate_behavior_adjustment(behavior_metrics)

        # Calculate final premium
        adjusted_premium = base_premium * risk_multiplier * usage_multiplier * behavior_adjustment

        # Calculate savings vs traditional
        traditional_premium = base_premium * 1.2  # 20% markup for traditional
        savings = traditional_premium - adjusted_premium
        discount_percent = (savings / traditional_premium * 100) if traditional_premium > 0 else 0

        return {
            'driver_id': driver_id,
            'base_premium': round(base_premium, 2),
            'risk_multiplier': round(risk_multiplier, 3),
            'usage_multiplier': round(usage_multiplier, 3),
            'behavior_adjustment': round(behavior_adjustment, 3),
            'adjusted_premium': round(adjusted_premium, 2),
            'traditional_premium': round(traditional_premium, 2),
            'savings': round(savings, 2),
            'discount_percent': round(discount_percent, 2),
            'risk_score': round(risk_score, 2),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _calculate_behavior_adjustment(self, behavior_metrics: Dict) -> float:
        """
        Calculate premium adjustment based on real-time behavior.
        
        Returns:
            Multiplier (1.0 = no change, <1.0 = discount, >1.0 = surcharge)
        """
        adjustment = 1.0

        # Harsh braking penalty
        harsh_braking_count = behavior_metrics.get('harsh_braking_count', 0)
        if harsh_braking_count > 0:
            adjustment += harsh_braking_count * 0.02  # 2% per harsh brake

        # Speeding penalty
        speeding_count = behavior_metrics.get('speeding_count', 0)
        if speeding_count > 0:
            adjustment += speeding_count * 0.03  # 3% per speeding event

        # Phone usage penalty
        phone_usage_count = behavior_metrics.get('phone_usage_count', 0)
        if phone_usage_count > 0:
            adjustment += phone_usage_count * 0.05  # 5% per phone usage

        # Speed consistency bonus
        current_speed = behavior_metrics.get('current_speed', 0)
        avg_speed = behavior_metrics.get('avg_speed', 0)
        if avg_speed > 0:
            speed_variance = abs(current_speed - avg_speed) / avg_speed
            if speed_variance < 0.1:  # Consistent speed
                adjustment -= 0.02  # 2% discount

        # Safe driving bonus (no events)
        total_events = behavior_metrics.get('total_events', 0)
        if total_events > 10:
            event_rate = (
                harsh_braking_count + speeding_count + phone_usage_count
            ) / total_events
            if event_rate < 0.05:  # Less than 5% risky events
                adjustment -= 0.05  # 5% discount

        # Clamp between 0.5 and 2.0
        return max(0.5, min(2.0, adjustment))


# Global pricing engine instance
_pricing_engine_instance: Optional[RealTimePricingEngine] = None


def get_pricing_engine() -> RealTimePricingEngine:
    """Get or create pricing engine instance."""
    global _pricing_engine_instance
    if _pricing_engine_instance is None:
        _pricing_engine_instance = RealTimePricingEngine()
    return _pricing_engine_instance


def calculate_realtime_premium(
    driver_id: str,
    risk_score: float,
    behavior_metrics: Dict,
    db: Session
) -> Dict:
    """Convenience function to calculate real-time premium."""
    engine = get_pricing_engine()
    return engine.calculate_realtime_premium(driver_id, risk_score, behavior_metrics, db)

