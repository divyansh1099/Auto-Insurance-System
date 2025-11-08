-- Telematics Insurance Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drivers table
CREATE TABLE IF NOT EXISTS drivers (
    driver_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    license_number VARCHAR(50) UNIQUE,
    license_state VARCHAR(2),
    years_licensed INTEGER,
    gender VARCHAR(10),
    marital_status VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id VARCHAR(50) PRIMARY KEY,
    driver_id VARCHAR(50) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    make VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    vin VARCHAR(17) UNIQUE,
    vehicle_type VARCHAR(50),
    safety_rating INTEGER CHECK (safety_rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(50) PRIMARY KEY,
    driver_id VARCHAR(50) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    vehicle_id VARCHAR(50) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    device_type VARCHAR(50),
    manufacturer VARCHAR(100),
    firmware_version VARCHAR(20),
    installed_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trips table
CREATE TABLE IF NOT EXISTS trips (
    trip_id VARCHAR(50) PRIMARY KEY,
    driver_id VARCHAR(50) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    device_id VARCHAR(50) REFERENCES devices(device_id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes NUMERIC(10, 2),
    distance_miles NUMERIC(10, 2),
    start_latitude NUMERIC(10, 6),
    start_longitude NUMERIC(10, 6),
    end_latitude NUMERIC(10, 6),
    end_longitude NUMERIC(10, 6),
    avg_speed NUMERIC(6, 2),
    max_speed NUMERIC(6, 2),
    harsh_braking_count INTEGER DEFAULT 0,
    rapid_accel_count INTEGER DEFAULT 0,
    speeding_count INTEGER DEFAULT 0,
    harsh_corner_count INTEGER DEFAULT 0,
    phone_usage_detected BOOLEAN DEFAULT FALSE,
    trip_type VARCHAR(20), -- commute, leisure, business
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telematics Events (partitioned by date for performance)
CREATE TABLE IF NOT EXISTS telematics_events (
    event_id VARCHAR(50),
    device_id VARCHAR(50) REFERENCES devices(device_id),
    driver_id VARCHAR(50) REFERENCES drivers(driver_id),
    trip_id VARCHAR(50) REFERENCES trips(trip_id),
    timestamp TIMESTAMP NOT NULL,
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    speed NUMERIC(6, 2),
    acceleration NUMERIC(6, 3),
    braking_force NUMERIC(6, 3),
    heading NUMERIC(6, 2),
    altitude NUMERIC(8, 2),
    gps_accuracy NUMERIC(6, 2),
    event_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create partitions for events (monthly)
CREATE TABLE IF NOT EXISTS telematics_events_2024_11 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
CREATE TABLE IF NOT EXISTS telematics_events_2024_12 PARTITION OF telematics_events
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
CREATE TABLE IF NOT EXISTS telematics_events_2025_01 PARTITION OF telematics_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Risk Scores table
CREATE TABLE IF NOT EXISTS risk_scores (
    score_id SERIAL PRIMARY KEY,
    driver_id VARCHAR(50) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    risk_score NUMERIC(5, 2) CHECK (risk_score BETWEEN 0 AND 100),
    risk_category VARCHAR(20), -- excellent, good, average, below_average, high_risk
    confidence NUMERIC(5, 2),
    model_version VARCHAR(20),
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    features JSONB, -- Store feature values used for scoring
    shap_values JSONB, -- Store SHAP explanation values
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Premiums table
CREATE TABLE IF NOT EXISTS premiums (
    premium_id SERIAL PRIMARY KEY,
    driver_id VARCHAR(50) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    policy_id VARCHAR(50),
    base_premium NUMERIC(10, 2),
    risk_multiplier NUMERIC(5, 2),
    usage_multiplier NUMERIC(5, 2),
    discount_factor NUMERIC(5, 2),
    final_premium NUMERIC(10, 2),
    monthly_premium NUMERIC(10, 2),
    effective_date DATE,
    expiration_date DATE,
    status VARCHAR(20), -- active, pending, expired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Driver Statistics (aggregated)
CREATE TABLE IF NOT EXISTS driver_statistics (
    stat_id SERIAL PRIMARY KEY,
    driver_id VARCHAR(50) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    period_start DATE,
    period_end DATE,
    total_miles NUMERIC(10, 2),
    total_trips INTEGER,
    avg_speed NUMERIC(6, 2),
    max_speed NUMERIC(6, 2),
    harsh_braking_rate NUMERIC(8, 4), -- per 100 miles
    rapid_accel_rate NUMERIC(8, 4),
    speeding_rate NUMERIC(8, 4),
    night_driving_pct NUMERIC(5, 2),
    rush_hour_pct NUMERIC(5, 2),
    weekend_driving_pct NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(driver_id, period_start, period_end)
);

-- Historical Claims (for ML training)
CREATE TABLE IF NOT EXISTS claims (
    claim_id VARCHAR(50) PRIMARY KEY,
    driver_id VARCHAR(50) REFERENCES drivers(driver_id),
    policy_id VARCHAR(50),
    claim_date DATE,
    claim_type VARCHAR(50), -- collision, comprehensive, liability
    claim_amount NUMERIC(10, 2),
    at_fault BOOLEAN,
    description TEXT,
    status VARCHAR(20), -- open, closed, denied
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Authentication
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    driver_id VARCHAR(50) UNIQUE REFERENCES drivers(driver_id),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_trips_driver_id ON trips(driver_id);
CREATE INDEX idx_trips_start_time ON trips(start_time);
CREATE INDEX idx_events_driver_id ON telematics_events(driver_id);
CREATE INDEX idx_events_timestamp ON telematics_events(timestamp);
CREATE INDEX idx_events_trip_id ON telematics_events(trip_id);
CREATE INDEX idx_risk_scores_driver_id ON risk_scores(driver_id);
CREATE INDEX idx_risk_scores_date ON risk_scores(calculation_date);
CREATE INDEX idx_premiums_driver_id ON premiums(driver_id);
CREATE INDEX idx_driver_stats_driver_id ON driver_statistics(driver_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to relevant tables
CREATE TRIGGER update_drivers_updated_at BEFORE UPDATE ON drivers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON vehicles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_premiums_updated_at BEFORE UPDATE ON premiums
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
