-- Migration: Add Missing Columns for Enhanced Features
-- Description: Adds columns required for Policy Management, Trips Page, and Risk Profile features
-- Date: 2024-11-09
-- Safe to run multiple times (uses IF NOT EXISTS)

-- ============================================================================
-- PREMIUMS TABLE ENHANCEMENTS
-- ============================================================================

-- Add policy_type column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'premiums' AND column_name = 'policy_type'
    ) THEN
        ALTER TABLE premiums ADD COLUMN policy_type VARCHAR(20) DEFAULT 'PHYD';
        RAISE NOTICE 'Added policy_type column to premiums table';
    ELSE
        RAISE NOTICE 'policy_type column already exists in premiums table';
    END IF;
END $$;

-- Add coverage_type column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'premiums' AND column_name = 'coverage_type'
    ) THEN
        ALTER TABLE premiums ADD COLUMN coverage_type VARCHAR(50) DEFAULT 'Comprehensive';
        RAISE NOTICE 'Added coverage_type column to premiums table';
    ELSE
        RAISE NOTICE 'coverage_type column already exists in premiums table';
    END IF;
END $$;

-- Add coverage_limit column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'premiums' AND column_name = 'coverage_limit'
    ) THEN
        ALTER TABLE premiums ADD COLUMN coverage_limit NUMERIC(12, 2) DEFAULT 100000.00;
        RAISE NOTICE 'Added coverage_limit column to premiums table';
    ELSE
        RAISE NOTICE 'coverage_limit column already exists in premiums table';
    END IF;
END $$;

-- Add total_miles_allowed column (if not exists) - nullable for PAYD policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'premiums' AND column_name = 'total_miles_allowed'
    ) THEN
        ALTER TABLE premiums ADD COLUMN total_miles_allowed NUMERIC(10, 2);
        RAISE NOTICE 'Added total_miles_allowed column to premiums table';
    ELSE
        RAISE NOTICE 'total_miles_allowed column already exists in premiums table';
    END IF;
END $$;

-- Add deductible column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'premiums' AND column_name = 'deductible'
    ) THEN
        ALTER TABLE premiums ADD COLUMN deductible NUMERIC(10, 2) DEFAULT 1000.00;
        RAISE NOTICE 'Added deductible column to premiums table';
    ELSE
        RAISE NOTICE 'deductible column already exists in premiums table';
    END IF;
END $$;

-- Add policy_last_updated column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'premiums' AND column_name = 'policy_last_updated'
    ) THEN
        ALTER TABLE premiums ADD COLUMN policy_last_updated TIMESTAMP;
        RAISE NOTICE 'Added policy_last_updated column to premiums table';
    ELSE
        RAISE NOTICE 'policy_last_updated column already exists in premiums table';
    END IF;
END $$;

-- Update existing records: Set policy_type to PHYD if NULL
UPDATE premiums 
SET policy_type = 'PHYD' 
WHERE policy_type IS NULL;

-- Update existing records: Set coverage_type to Comprehensive if NULL
UPDATE premiums 
SET coverage_type = 'Comprehensive' 
WHERE coverage_type IS NULL;

-- Update existing records: Set coverage_limit to 100000 if NULL
UPDATE premiums 
SET coverage_limit = 100000.00 
WHERE coverage_limit IS NULL;

-- Update existing records: Set deductible to 1000 if NULL
UPDATE premiums 
SET deductible = 1000.00 
WHERE deductible IS NULL;

-- ============================================================================
-- TRIPS TABLE ENHANCEMENTS
-- ============================================================================

-- Add origin_city column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trips' AND column_name = 'origin_city'
    ) THEN
        ALTER TABLE trips ADD COLUMN origin_city VARCHAR(100);
        RAISE NOTICE 'Added origin_city column to trips table';
    ELSE
        RAISE NOTICE 'origin_city column already exists in trips table';
    END IF;
END $$;

-- Add origin_state column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trips' AND column_name = 'origin_state'
    ) THEN
        ALTER TABLE trips ADD COLUMN origin_state VARCHAR(50);
        RAISE NOTICE 'Added origin_state column to trips table';
    ELSE
        RAISE NOTICE 'origin_state column already exists in trips table';
    END IF;
END $$;

-- Add destination_city column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trips' AND column_name = 'destination_city'
    ) THEN
        ALTER TABLE trips ADD COLUMN destination_city VARCHAR(100);
        RAISE NOTICE 'Added destination_city column to trips table';
    ELSE
        RAISE NOTICE 'destination_city column already exists in trips table';
    END IF;
END $$;

-- Add destination_state column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trips' AND column_name = 'destination_state'
    ) THEN
        ALTER TABLE trips ADD COLUMN destination_state VARCHAR(50);
        RAISE NOTICE 'Added destination_state column to trips table';
    ELSE
        RAISE NOTICE 'destination_state column already exists in trips table';
    END IF;
END $$;

-- Add trip_score column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trips' AND column_name = 'trip_score'
    ) THEN
        ALTER TABLE trips ADD COLUMN trip_score INTEGER 
            CHECK (trip_score IS NULL OR (trip_score >= 0 AND trip_score <= 100));
        RAISE NOTICE 'Added trip_score column to trips table';
    ELSE
        RAISE NOTICE 'trip_score column already exists in trips table';
    END IF;
END $$;

-- Add risk_level column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trips' AND column_name = 'risk_level'
    ) THEN
        ALTER TABLE trips ADD COLUMN risk_level VARCHAR(20) 
            CHECK (risk_level IS NULL OR risk_level IN ('low', 'medium', 'high'));
        RAISE NOTICE 'Added risk_level column to trips table';
    ELSE
        RAISE NOTICE 'risk_level column already exists in trips table';
    END IF;
END $$;

-- ============================================================================
-- RISK_SCORES TABLE ENHANCEMENTS (Optional - for Risk Profile features)
-- ============================================================================

-- Add behavior_score column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'behavior_score'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN behavior_score NUMERIC(5, 2) 
            CHECK (behavior_score IS NULL OR (behavior_score >= 0 AND behavior_score <= 100));
        RAISE NOTICE 'Added behavior_score column to risk_scores table';
    ELSE
        RAISE NOTICE 'behavior_score column already exists in risk_scores table';
    END IF;
END $$;

-- Add mileage_score column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'mileage_score'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN mileage_score NUMERIC(5, 2) 
            CHECK (mileage_score IS NULL OR (mileage_score >= 0 AND mileage_score <= 100));
        RAISE NOTICE 'Added mileage_score column to risk_scores table';
    ELSE
        RAISE NOTICE 'mileage_score column already exists in risk_scores table';
    END IF;
END $$;

-- Add time_pattern_score column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'time_pattern_score'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN time_pattern_score NUMERIC(5, 2) 
            CHECK (time_pattern_score IS NULL OR (time_pattern_score >= 0 AND time_pattern_score <= 100));
        RAISE NOTICE 'Added time_pattern_score column to risk_scores table';
    ELSE
        RAISE NOTICE 'time_pattern_score column already exists in risk_scores table';
    END IF;
END $$;

-- Add location_score column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'location_score'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN location_score NUMERIC(5, 2) 
            CHECK (location_score IS NULL OR (location_score >= 0 AND location_score <= 100));
        RAISE NOTICE 'Added location_score column to risk_scores table';
    ELSE
        RAISE NOTICE 'location_score column already exists in risk_scores table';
    END IF;
END $$;

-- Add detailed risk factor columns (if not exists)
DO $$
BEGIN
    -- speeding_frequency
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'speeding_frequency'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN speeding_frequency NUMERIC(6, 2) DEFAULT 0;
    END IF;
    
    -- acceleration_pattern
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'acceleration_pattern'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN acceleration_pattern NUMERIC(6, 2) DEFAULT 0;
    END IF;
    
    -- high_risk_area_exposure
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'high_risk_area_exposure'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN high_risk_area_exposure NUMERIC(6, 2) DEFAULT 0;
    END IF;
    
    -- weather_risk_exposure
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'weather_risk_exposure'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN weather_risk_exposure NUMERIC(6, 2) DEFAULT 0;
    END IF;
    
    -- hard_braking_frequency
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'hard_braking_frequency'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN hard_braking_frequency NUMERIC(6, 2) DEFAULT 0;
    END IF;
    
    -- night_driving_percentage
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'night_driving_percentage'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN night_driving_percentage NUMERIC(6, 2) DEFAULT 0;
    END IF;
    
    -- phone_usage_incidents
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'phone_usage_incidents'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN phone_usage_incidents INTEGER DEFAULT 0;
    END IF;
    
    RAISE NOTICE 'Added detailed risk factor columns to risk_scores table';
END $$;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Indexes for premiums table
CREATE INDEX IF NOT EXISTS idx_premiums_policy_type ON premiums(policy_type);
CREATE INDEX IF NOT EXISTS idx_premiums_status ON premiums(status);
CREATE INDEX IF NOT EXISTS idx_premiums_driver_id ON premiums(driver_id);
CREATE INDEX IF NOT EXISTS idx_premiums_driver_status ON premiums(driver_id, status);

-- Indexes for trips table
CREATE INDEX IF NOT EXISTS idx_trips_driver_id ON trips(driver_id);
CREATE INDEX IF NOT EXISTS idx_trips_start_time ON trips(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_trips_risk_level ON trips(risk_level);
CREATE INDEX IF NOT EXISTS idx_trips_origin_city ON trips(origin_city);
CREATE INDEX IF NOT EXISTS idx_trips_destination_city ON trips(destination_city);
CREATE INDEX IF NOT EXISTS idx_trips_trip_score ON trips(trip_score);

-- Composite index for common query pattern: driver_id + start_time DESC
-- This significantly speeds up paginated queries filtered by driver
CREATE INDEX IF NOT EXISTS idx_trips_driver_start_time ON trips(driver_id, start_time DESC);

-- Composite index for risk level filtering with driver
CREATE INDEX IF NOT EXISTS idx_trips_driver_risk_level ON trips(driver_id, risk_level) WHERE risk_level IS NOT NULL;

-- Indexes for risk_scores table
CREATE INDEX IF NOT EXISTS idx_risk_scores_driver_id ON risk_scores(driver_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_calculation_date ON risk_scores(calculation_date DESC);
CREATE INDEX IF NOT EXISTS idx_risk_scores_driver_date ON risk_scores(driver_id, calculation_date DESC);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed successfully!';
    RAISE NOTICE 'Added columns to premiums, trips, and risk_scores tables';
    RAISE NOTICE 'Created indexes for better query performance';
END $$;

