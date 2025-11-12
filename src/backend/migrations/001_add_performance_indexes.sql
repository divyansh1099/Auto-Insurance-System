-- Migration: 001_add_performance_indexes.sql
-- Purpose: Add strategic indexes for improved query performance
-- Date: 2025-11-12
-- Estimated Impact: 50-70% faster queries on filtered results

-- ============================================================================
-- TELEMATICS EVENTS INDEXES
-- ============================================================================

-- Composite index for driver + timestamp queries (most common)
-- Used by: trip queries, event lookups by driver and time range
CREATE INDEX IF NOT EXISTS idx_telematics_events_driver_timestamp
    ON telematics_events(driver_id, timestamp DESC);

-- Index for event type filtering (harsh braking, speeding, etc.)
-- Used by: risk scoring, analytics on specific event types
CREATE INDEX IF NOT EXISTS idx_telematics_events_event_type
    ON telematics_events(event_type)
    WHERE event_type IN ('harsh_braking', 'harsh_acceleration', 'speeding', 'phone_usage');

-- Index for trip-based queries
-- Used by: aggregating events by trip
CREATE INDEX IF NOT EXISTS idx_telematics_events_trip_id
    ON telematics_events(trip_id, timestamp DESC)
    WHERE trip_id IS NOT NULL;

-- Index for device queries
-- Used by: device health monitoring, device-specific analytics
CREATE INDEX IF NOT EXISTS idx_telematics_events_device_timestamp
    ON telematics_events(device_id, timestamp DESC);

-- Composite index for geospatial queries (optional, enable if using location queries)
-- CREATE INDEX IF NOT EXISTS idx_telematics_events_location
--     ON telematics_events(latitude, longitude)
--     WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- ============================================================================
-- TRIPS INDEXES
-- ============================================================================

-- Composite index for driver + date range queries
-- Used by: driver trip history, trip analytics
CREATE INDEX IF NOT EXISTS idx_trips_driver_dates
    ON trips(driver_id, start_time DESC, end_time DESC);

-- Index for active trips (trips without end_time)
-- Used by: real-time trip tracking, live driving sessions
CREATE INDEX IF NOT EXISTS idx_trips_active
    ON trips(driver_id, start_time DESC)
    WHERE end_time IS NULL;

-- Index for trip type filtering
-- Used by: analytics by trip type (commute, leisure, business)
CREATE INDEX IF NOT EXISTS idx_trips_type
    ON trips(trip_type)
    WHERE trip_type IS NOT NULL;

-- Index for high-risk trips
-- Used by: risk analytics, identifying problematic trips
CREATE INDEX IF NOT EXISTS idx_trips_risk_level
    ON trips(driver_id, risk_level)
    WHERE risk_level IN ('high', 'medium');

-- Index for trip score queries
-- Used by: finding best/worst trips, reward calculations
CREATE INDEX IF NOT EXISTS idx_trips_score
    ON trips(driver_id, trip_score DESC)
    WHERE trip_score IS NOT NULL;

-- ============================================================================
-- RISK SCORES INDEXES
-- ============================================================================

-- Composite index for driver + most recent risk score
-- Used by: dashboard, pricing calculations
CREATE INDEX IF NOT EXISTS idx_risk_scores_driver_date
    ON risk_scores(driver_id, calculation_date DESC);

-- Index for risk category filtering
-- Used by: admin analytics, high-risk driver identification
CREATE INDEX IF NOT EXISTS idx_risk_scores_category
    ON risk_scores(risk_category, risk_score DESC);

-- Index for risk score range queries
-- Used by: finding drivers within specific risk ranges
CREATE INDEX IF NOT EXISTS idx_risk_scores_score_range
    ON risk_scores(risk_score)
    WHERE risk_score IS NOT NULL;

-- ============================================================================
-- PREMIUMS INDEXES
-- ============================================================================

-- Composite index for driver + effective date
-- Used by: current premium lookups, premium history
CREATE INDEX IF NOT EXISTS idx_premiums_driver_effective
    ON premiums(driver_id, effective_date DESC);

-- Index for active policies
-- Used by: finding current policies
CREATE INDEX IF NOT EXISTS idx_premiums_active
    ON premiums(driver_id, status, effective_date DESC)
    WHERE status = 'active';

-- Index for policy lookups
-- Used by: policy number searches
CREATE INDEX IF NOT EXISTS idx_premiums_policy_id
    ON premiums(policy_id)
    WHERE policy_id IS NOT NULL;

-- ============================================================================
-- DRIVER STATISTICS INDEXES
-- ============================================================================

-- Composite index for driver + period queries
-- Used by: statistics lookups by time period
CREATE INDEX IF NOT EXISTS idx_driver_stats_driver_period
    ON driver_statistics(driver_id, period_start DESC, period_end DESC);

-- ============================================================================
-- DEVICES INDEXES
-- ============================================================================

-- Index for active devices
-- Used by: device management, active device queries
CREATE INDEX IF NOT EXISTS idx_devices_active
    ON devices(driver_id, is_active)
    WHERE is_active = TRUE;

-- Index for device health monitoring
-- Used by: identifying devices with stale heartbeats
CREATE INDEX IF NOT EXISTS idx_devices_heartbeat
    ON devices(last_heartbeat DESC)
    WHERE is_active = TRUE;

-- ============================================================================
-- USERS INDEXES
-- ============================================================================

-- Index for username lookups (likely already exists, but ensure it's there)
CREATE INDEX IF NOT EXISTS idx_users_username
    ON users(username);

-- Index for email lookups
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);

-- Index for active users
CREATE INDEX IF NOT EXISTS idx_users_active
    ON users(is_active)
    WHERE is_active = TRUE;

-- Index for admin users
CREATE INDEX IF NOT EXISTS idx_users_admin
    ON users(is_admin)
    WHERE is_admin = TRUE;

-- ============================================================================
-- ANALYZE TABLES
-- ============================================================================
-- Update table statistics for query planner optimization

ANALYZE telematics_events;
ANALYZE trips;
ANALYZE risk_scores;
ANALYZE premiums;
ANALYZE driver_statistics;
ANALYZE devices;
ANALYZE drivers;
ANALYZE vehicles;
ANALYZE users;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these queries to verify index creation:

-- List all indexes
-- SELECT tablename, indexname, indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
-- ORDER BY tablename, indexname;

-- Check index usage statistics
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan as index_scans,
--     idx_tup_read as tuples_read,
--     idx_tup_fetch as tuples_fetched
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public'
-- ORDER BY idx_scan DESC;

-- Check table sizes
-- SELECT
--     schemaname,
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
--     pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS index_size
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================================
-- ROLLBACK (IF NEEDED)
-- ============================================================================
-- To rollback this migration, drop the indexes:
-- DROP INDEX IF EXISTS idx_telematics_events_driver_timestamp;
-- DROP INDEX IF EXISTS idx_telematics_events_event_type;
-- ... (continue for all indexes)
