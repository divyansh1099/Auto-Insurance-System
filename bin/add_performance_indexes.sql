-- Performance Indexes Migration
-- This migration adds critical indexes to improve query performance
-- Recommended by RECOMMENDATIONS.md section 2 (Backend Performance > Database Optimization)

-- Create indexes on telematics_events table for high-volume queries
-- Index on (driver_id, timestamp) for queries filtering by driver and time range
CREATE INDEX IF NOT EXISTS idx_telematics_events_driver_timestamp 
ON telematics_events(driver_id, timestamp DESC);

-- Index on (trip_id) for joining with trips
CREATE INDEX IF NOT EXISTS idx_telematics_events_trip_id 
ON telematics_events(trip_id);

-- Create indexes on trips table for common query patterns
-- Composite index on (driver_id, start_time) for driver trip history queries
CREATE INDEX IF NOT EXISTS idx_trips_driver_start_time 
ON trips(driver_id, start_time DESC);

-- Index on start_time for time-based filtering and analytics
CREATE INDEX IF NOT EXISTS idx_trips_start_time 
ON trips(start_time DESC);

-- Index on risk_level for filtering by risk category
CREATE INDEX IF NOT EXISTS idx_trips_risk_level 
ON trips(risk_level);

-- Composite index on (start_time, risk_level) for admin dashboard queries
CREATE INDEX IF NOT EXISTS idx_trips_start_time_risk_level 
ON trips(start_time DESC, risk_level);

-- Create indexes on risk_scores table
-- Composite index on (driver_id, calculation_date) for latest risk score queries
CREATE INDEX IF NOT EXISTS idx_risk_scores_driver_date 
ON risk_scores(driver_id, calculation_date DESC);

-- Index on calculation_date for time-based analytics
CREATE INDEX IF NOT EXISTS idx_risk_scores_calculation_date 
ON risk_scores(calculation_date DESC);

-- Create indexes on premiums table
-- Index on (driver_id, status) for active premium lookups
CREATE INDEX IF NOT EXISTS idx_premiums_driver_status 
ON premiums(driver_id, status);

-- Index on status for filtering active policies
CREATE INDEX IF NOT EXISTS idx_premiums_status 
ON premiums(status);

-- Composite index on (status, created_at) for recent active policies
CREATE INDEX IF NOT EXISTS idx_premiums_status_created 
ON premiums(status, created_at DESC);

-- Print success message
DO $$
BEGIN
    RAISE NOTICE 'Performance indexes created successfully!';
    RAISE NOTICE 'Added indexes on:';
    RAISE NOTICE '  - telematics_events(driver_id, timestamp)';
    RAISE NOTICE '  - telematics_events(trip_id)';
    RAISE NOTICE '  - trips(driver_id, start_time)';
    RAISE NOTICE '  - trips(start_time)';
    RAISE NOTICE '  - trips(risk_level)';
    RAISE NOTICE '  - trips(start_time, risk_level)';
    RAISE NOTICE '  - risk_scores(driver_id, calculation_date)';
    RAISE NOTICE '  - risk_scores(calculation_date)';
    RAISE NOTICE '  - premiums(driver_id, status)';
    RAISE NOTICE '  - premiums(status)';
    RAISE NOTICE '  - premiums(status, created_at)';
END $$;
