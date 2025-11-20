-- =====================================================
-- Table Partitioning Migration for telematics_events
-- =====================================================
-- 
-- This script converts the telematics_events table to use
-- range partitioning by month for better query performance
-- and easier data management.
--
-- IMPORTANT: Run this during a maintenance window
-- Estimated time: Depends on data volume (5-30 minutes for 1M+ rows)
--
-- =====================================================

BEGIN;

-- Step 1: Rename existing table
ALTER TABLE telematics_events RENAME TO telematics_events_old;

-- Step 2: Create new partitioned table
CREATE TABLE telematics_events (
    event_id VARCHAR(50) NOT NULL,
    device_id VARCHAR(50),
    driver_id VARCHAR(50) NOT NULL,
    trip_id VARCHAR(50),
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    speed FLOAT,
    acceleration FLOAT,
    braking_force FLOAT,
    heading FLOAT,
    altitude FLOAT,
    gps_accuracy FLOAT,
    event_type VARCHAR(20),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    PRIMARY KEY (event_id, timestamp),
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
) PARTITION BY RANGE (timestamp);

-- Step 3: Create partitions for past months (last 12 months)
-- Adjust the dates based on your data range

-- 2024 partitions
CREATE TABLE telematics_events_2024_01 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE telematics_events_2024_02 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE telematics_events_2024_03 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE telematics_events_2024_04 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE telematics_events_2024_05 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE telematics_events_2024_06 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE telematics_events_2024_07 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE telematics_events_2024_08 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE telematics_events_2024_09 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE telematics_events_2024_10 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE telematics_events_2024_11 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE telematics_events_2024_12 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- 2025 partitions
CREATE TABLE telematics_events_2025_01 PARTITION OF telematics_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE telematics_events_2025_02 PARTITION OF telematics_events
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE telematics_events_2025_03 PARTITION OF telematics_events
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

-- Future partitions (next 3 months)
CREATE TABLE telematics_events_2025_04 PARTITION OF telematics_events
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');

CREATE TABLE telematics_events_2025_05 PARTITION OF telematics_events
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');

CREATE TABLE telematics_events_2025_06 PARTITION OF telematics_events
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

-- Step 4: Copy data from old table to new partitioned table
-- This may take a while depending on data volume
INSERT INTO telematics_events 
SELECT * FROM telematics_events_old;

-- Step 5: Create indexes on partitioned table
-- Note: Indexes are created on the parent table and automatically applied to all partitions

CREATE INDEX idx_telematics_events_driver_timestamp 
    ON telematics_events(driver_id, timestamp DESC);

CREATE INDEX idx_telematics_events_trip 
    ON telematics_events(trip_id);

CREATE INDEX idx_telematics_events_device 
    ON telematics_events(device_id);

CREATE INDEX idx_telematics_events_event_type 
    ON telematics_events(event_type);

-- Step 6: Verify data migration
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM telematics_events_old;
    SELECT COUNT(*) INTO new_count FROM telematics_events;
    
    IF old_count != new_count THEN
        RAISE EXCEPTION 'Data migration failed: old table has % rows, new table has % rows', old_count, new_count;
    ELSE
        RAISE NOTICE 'Data migration successful: % rows migrated', new_count;
    END IF;
END $$;

-- Step 7: Drop old table (UNCOMMENT AFTER VERIFICATION)
-- DROP TABLE telematics_events_old;

COMMIT;

-- =====================================================
-- Post-Migration: Create function for automatic partition creation
-- =====================================================

CREATE OR REPLACE FUNCTION create_telematics_partition_if_not_exists(partition_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Calculate partition boundaries
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';
    
    -- Generate partition name
    partition_name := 'telematics_events_' || TO_CHAR(start_date, 'YYYY_MM');
    
    -- Check if partition exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        -- Create partition
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF telematics_events FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            start_date,
            end_date
        );
        
        RAISE NOTICE 'Created partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Usage Examples
-- =====================================================

-- Create partition for a specific month:
-- SELECT create_telematics_partition_if_not_exists('2025-07-01');

-- Create partitions for next 6 months:
-- SELECT create_telematics_partition_if_not_exists(CURRENT_DATE + (n || ' months')::INTERVAL)
-- FROM generate_series(1, 6) AS n;

-- List all partitions:
-- SELECT 
--     schemaname,
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
-- FROM pg_tables
-- WHERE tablename LIKE 'telematics_events_%'
-- ORDER BY tablename;

-- =====================================================
-- Rollback Plan (if needed)
-- =====================================================

-- If something goes wrong, you can rollback:
-- BEGIN;
-- DROP TABLE IF EXISTS telematics_events CASCADE;
-- ALTER TABLE telematics_events_old RENAME TO telematics_events;
-- COMMIT;
