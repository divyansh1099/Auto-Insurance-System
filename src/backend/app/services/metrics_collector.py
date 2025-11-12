"""
Metrics Collector Service

Periodically collects business metrics and system health metrics for Prometheus.
This runs as a background task and updates Gauge metrics.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.models.database import (
    SessionLocal,
    Driver,
    Trip,
    RiskScore,
    Premium,
    TelematicsEvent,
    engine
)
from app.utils.metrics import (
    active_drivers_total,
    active_trips_total,
    events_per_second,
    average_risk_score,
    high_risk_drivers_total,
    medium_risk_drivers_total,
    low_risk_drivers_total,
    active_policies_total,
    total_premiums_monthly,
    average_premium_monthly,
    db_connection_pool_size,
    db_connection_pool_checked_out,
    db_connection_pool_overflow,
    db_connection_pool_checked_in,
)

logger = structlog.get_logger()


class MetricsCollector:
    """Background metrics collector for business and system metrics."""

    def __init__(self, collection_interval: int = 30):
        """
        Initialize metrics collector.

        Args:
            collection_interval: How often to collect metrics (seconds)
        """
        self.collection_interval = collection_interval
        self.running = False

    async def start(self):
        """Start the metrics collection background task."""
        self.running = True
        logger.info("metrics_collector_started", interval=self.collection_interval)

        while self.running:
            try:
                await self._collect_all_metrics()
            except Exception as e:
                logger.error("metrics_collection_error", error=str(e), exc_info=True)

            await asyncio.sleep(self.collection_interval)

    def stop(self):
        """Stop the metrics collection background task."""
        self.running = False
        logger.info("metrics_collector_stopped")

    async def _collect_all_metrics(self):
        """Collect all metrics."""
        db = SessionLocal()
        try:
            # Collect metrics in parallel for better performance
            await asyncio.gather(
                self._collect_driver_metrics(db),
                self._collect_trip_metrics(db),
                self._collect_risk_metrics(db),
                self._collect_premium_metrics(db),
                self._collect_event_metrics(db),
                self._collect_db_pool_metrics(),
                return_exceptions=True
            )

            logger.debug("metrics_collected_successfully")

        except Exception as e:
            logger.error("metrics_collection_failed", error=str(e))
        finally:
            db.close()

    async def _collect_driver_metrics(self, db: Session):
        """Collect driver-related metrics."""
        try:
            # Count active drivers
            active_count = db.query(Driver).count()
            active_drivers_total.set(active_count)

            logger.debug("driver_metrics_collected", active_drivers=active_count)

        except Exception as e:
            logger.error("driver_metrics_error", error=str(e))

    async def _collect_trip_metrics(self, db: Session):
        """Collect trip-related metrics."""
        try:
            # Count active trips (trips without end_time)
            active_trip_count = db.query(Trip).filter(
                Trip.end_time.is_(None)
            ).count()
            active_trips_total.set(active_trip_count)

            logger.debug("trip_metrics_collected", active_trips=active_trip_count)

        except Exception as e:
            logger.error("trip_metrics_error", error=str(e))

    async def _collect_risk_metrics(self, db: Session):
        """Collect risk scoring metrics."""
        try:
            # Get latest risk scores for each driver (subquery approach)
            from sqlalchemy import and_

            # Count drivers by risk category
            # Note: This assumes you have a risk_category field or we derive it from risk_score
            high_risk = db.query(RiskScore).filter(
                RiskScore.risk_score >= 70
            ).distinct(RiskScore.driver_id).count()

            medium_risk = db.query(RiskScore).filter(
                and_(
                    RiskScore.risk_score >= 40,
                    RiskScore.risk_score < 70
                )
            ).distinct(RiskScore.driver_id).count()

            low_risk = db.query(RiskScore).filter(
                RiskScore.risk_score < 40
            ).distinct(RiskScore.driver_id).count()

            high_risk_drivers_total.set(high_risk)
            medium_risk_drivers_total.set(medium_risk)
            low_risk_drivers_total.set(low_risk)

            # Calculate average risk score
            avg_risk = db.query(func.avg(RiskScore.risk_score)).scalar()
            if avg_risk:
                average_risk_score.set(float(avg_risk))

            logger.debug("risk_metrics_collected",
                        high_risk=high_risk,
                        medium_risk=medium_risk,
                        low_risk=low_risk,
                        avg_risk=avg_risk)

        except Exception as e:
            logger.error("risk_metrics_error", error=str(e))

    async def _collect_premium_metrics(self, db: Session):
        """Collect premium and policy metrics."""
        try:
            # Count active policies
            active_policy_count = db.query(Premium).filter(
                Premium.status == 'active'
            ).count()
            active_policies_total.set(active_policy_count)

            # Calculate total and average monthly premiums
            premium_stats = db.query(
                func.sum(Premium.monthly_premium),
                func.avg(Premium.monthly_premium)
            ).filter(
                Premium.status == 'active'
            ).first()

            total_premium = premium_stats[0] if premium_stats[0] else 0
            avg_premium = premium_stats[1] if premium_stats[1] else 0

            total_premiums_monthly.set(float(total_premium))
            average_premium_monthly.set(float(avg_premium))

            logger.debug("premium_metrics_collected",
                        active_policies=active_policy_count,
                        total_premium=total_premium,
                        avg_premium=avg_premium)

        except Exception as e:
            logger.error("premium_metrics_error", error=str(e))

    async def _collect_event_metrics(self, db: Session):
        """Collect telematics event metrics."""
        try:
            # Calculate events per second (events in last minute / 60)
            one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
            event_count = db.query(TelematicsEvent).filter(
                TelematicsEvent.timestamp >= one_minute_ago
            ).count()

            eps = event_count / 60.0
            events_per_second.set(eps)

            logger.debug("event_metrics_collected", events_per_second=eps)

        except Exception as e:
            logger.error("event_metrics_error", error=str(e))

    async def _collect_db_pool_metrics(self):
        """Collect database connection pool metrics."""
        try:
            pool = engine.pool

            # Get pool statistics
            db_connection_pool_size.set(pool.size())
            db_connection_pool_checked_out.set(pool.checkedout())
            db_connection_pool_overflow.set(pool.overflow())

            # checked_in = size - checked_out (approximation)
            checked_in = max(0, pool.size() - pool.checkedout())
            db_connection_pool_checked_in.set(checked_in)

            logger.debug("db_pool_metrics_collected",
                        pool_size=pool.size(),
                        checked_out=pool.checkedout(),
                        overflow=pool.overflow(),
                        checked_in=checked_in)

        except Exception as e:
            logger.error("db_pool_metrics_error", error=str(e))


# Global metrics collector instance
_metrics_collector_instance: MetricsCollector = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance."""
    global _metrics_collector_instance
    if _metrics_collector_instance is None:
        _metrics_collector_instance = MetricsCollector(collection_interval=30)
    return _metrics_collector_instance


async def start_metrics_collector():
    """Start the background metrics collector."""
    collector = get_metrics_collector()
    await collector.start()


def stop_metrics_collector():
    """Stop the background metrics collector."""
    collector = get_metrics_collector()
    collector.stop()
