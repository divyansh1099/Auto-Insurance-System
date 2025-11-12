-- Migration: 002_partition_telematics_events.sql
-- Purpose: Implement table partitioning for telematics_events by timestamp
-- Date: 2025-11-12
-- Estimated Impact: 5-10x faster queries, easier maintenance and archival
-- WARNING: This is a major schema change. Test thoroughly before production!

-- ============================================================================
-- STEP 1: CREATE PARTITIONED TABLE
-- ============================================================================

-- Create the new partitioned table structure
CREATE TABLE IF NOT EXISTS telematics_events_partitioned (
    event_id VARCHAR(50) NOT NULL,
    device_id VARCHAR(50),
    driver_id VARCHAR(50) NOT NULL,
    trip_id VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    speed FLOAT,
    acceleration FLOAT,
    braking_force FLOAT,
    heading FLOAT,
    altitude FLOAT,
    gps_accuracy FLOAT,
    event_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Composite primary key including partition key
    PRIMARY KEY (event_id, timestamp),

    -- Foreign keys
    CONSTRAINT fk_telematics_device FOREIGN KEY (device_id) REFERENCES devices(device_id),
    CONSTRAINT fk_telematics_driver FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    CONSTRAINT fk_telematics_trip FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
) PARTITION BY RANGE (timestamp);

-- ============================================================================
-- STEP 2: CREATE INITIAL PARTITIONS
-- ============================================================================

-- Create partitions for recent months (adjust dates as needed)
-- Each partition covers one month

-- November 2025
CREATE TABLE IF NOT EXISTS telematics_events_2025_11 PARTITION OF telematics_events_partitioned
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- December 2025
CREATE TABLE IF NOT EXISTS telematics_events_2025_12 PARTITION OF telematics_events_partitioned
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- January 2026
CREATE TABLE IF NOT EXISTS telematics_events_2026_01 PARTITION OF telematics_events_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- February 2026
CREATE TABLE IF NOT EXISTS telematics_events_2026_02 PARTITION OF telematics_events_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- March 2026
CREATE TABLE IF NOT EXISTS telematics_events_2026_03 PARTITION OF telematics_events_partitioned
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- April 2026
CREATE TABLE IF NOT EXISTS telematics_events_2026_04 PARTITION OF telematics_events_partitioned
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

-- ============================================================================
-- STEP 3: CREATE INDEXES ON PARTITIONED TABLE
-- ============================================================================

-- Indexes will be automatically created on each partition
CREATE INDEX IF NOT EXISTS idx_telematics_part_driver_timestamp
    ON telematics_events_partitioned(driver_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_telematics_part_event_type
    ON telematics_events_partitioned(event_type)
    WHERE event_type IN ('harsh_braking', 'harsh_acceleration', 'speeding', 'phone_usage');

CREATE INDEX IF NOT EXISTS idx_telematics_part_trip_id
    ON telematics_events_partitioned(trip_id, timestamp DESC)
    WHERE trip_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_telematics_part_device_timestamp
    ON telematics_events_partitioned(device_id, timestamp DESC);

-- ============================================================================
-- STEP 4: AUTOMATED PARTITION MANAGEMENT FUNCTION
-- ============================================================================

-- Function to automatically create next month's partition
CREATE OR REPLACE FUNCTION create_next_month_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    -- Calculate next month
    partition_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
    partition_name := 'telematics_events_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date := partition_date::TEXT;
    end_date := (partition_date + INTERVAL '1 month')::TEXT;

    -- Check if partition already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF telematics_events_partitioned
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        RAISE NOTICE 'Created partition: %', partition_name;
    ELSE
        RAISE NOTICE 'Partition already exists: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to drop old partitions (for archival)
CREATE OR REPLACE FUNCTION drop_old_partitions(months_to_keep INTEGER DEFAULT 12)
RETURNS void AS $$
DECLARE
    partition_record RECORD;
    cutoff_date DATE;
BEGIN
    cutoff_date := DATE_TRUNC('month', CURRENT_DATE - (months_to_keep || ' months')::INTERVAL);

    FOR partition_record IN
        SELECT
            schemaname,
            tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE 'telematics_events_20%'
    LOOP
        -- Extract year and month from partition name
        DECLARE
            partition_date DATE;
            year_str TEXT;
            month_str TEXT;
        BEGIN
            year_str := SUBSTRING(partition_record.tablename FROM 21 FOR 4);
            month_str := SUBSTRING(partition_record.tablename FROM 26 FOR 2);
            partition_date := TO_DATE(year_str || '-' || month_str || '-01', 'YYYY-MM-DD');

            IF partition_date < cutoff_date THEN
                EXECUTE format('DROP TABLE IF EXISTS %I', partition_record.tablename);
                RAISE NOTICE 'Dropped old partition: %', partition_record.tablename;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Error processing partition %: %', partition_record.tablename, SQLERRM;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 5: MIGRATION INSTRUCTIONS
-- ============================================================================

/*
IMPORTANT: This migration requires downtime for data migration!

To migrate existing data from telematics_events to telematics_events_partitioned:

1. BACKUP YOUR DATA:
   pg_dump -h localhost -U insurance_user -t telematics_events insurance_db > telematics_events_backup.sql

2. During maintenance window:
   a. Stop the application
   b. Rename old table:
      ALTER TABLE telematics_events RENAME TO telematics_events_old;

   c. Rename partitioned table:
      ALTER TABLE telematics_events_partitioned RENAME TO telematics_events;

   d. Migrate data (in batches to avoid long locks):
      INSERT INTO telematics_events
      SELECT * FROM telematics_events_old
      WHERE timestamp >= '2025-11-01'  -- Only migrate recent data
      ON CONFLICT DO NOTHING;

   e. Verify data:
      SELECT COUNT(*) FROM telematics_events;
      SELECT COUNT(*) FROM telematics_events_old;

   f. Drop old table (only after verification!):
      DROP TABLE telematics_events_old;

3. Set up cron job for automatic partition creation:
   -- Run this monthly:
   SELECT create_next_month_partition();

4. Set up cron job for old partition archival (optional):
   -- Run this monthly to drop partitions older than 12 months:
   SELECT drop_old_partitions(12);

ALTERNATIVE: Zero-downtime migration using logical replication (advanced)
See PostgreSQL documentation for pg_logical replication setup.
*/

-- ============================================================================
-- STEP 6: HELPER QUERIES
-- ============================================================================

-- View all partitions
/*
SELECT
    parent.relname AS parent_table,
    child.relname AS partition_name,
    pg_get_expr(child.relpartbound, child.oid) AS partition_bounds,
    pg_size_pretty(pg_total_relation_size(child.oid)) AS size
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
WHERE parent.relname = 'telematics_events'
ORDER BY child.relname;
*/

-- Check partition sizes
/*
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE 'telematics_events_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
*/

-- Test query performance (should use partition pruning)
/*
EXPLAIN ANALYZE
SELECT * FROM telematics_events_partitioned
WHERE driver_id = 'DRV001'
AND timestamp >= '2025-11-01'
AND timestamp < '2025-12-01';
*/

-- ============================================================================
-- ROLLBACK (IF NEEDED)
-- ============================================================================
/*
-- If migration fails, rollback:
DROP TABLE IF EXISTS telematics_events_partitioned CASCADE;
DROP FUNCTION IF EXISTS create_next_month_partition();
DROP FUNCTION IF EXISTS drop_old_partitions(INTEGER);

-- If old table was renamed:
ALTER TABLE telematics_events_old RENAME TO telematics_events;
*/
