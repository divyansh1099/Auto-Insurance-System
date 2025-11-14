#!/bin/bash
# Data Restoration Script
# This script restores the admin user and sample data to the database

set -e

echo "🔄 Starting data restoration..."

# Database connection details
DB_CONTAINER="postgres"
DB_NAME="telematics_db"
DB_USER="insurance_user"

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until docker exec $DB_CONTAINER pg_isready -U $DB_USER -d $DB_NAME > /dev/null 2>&1; do
  echo "   Database is unavailable - sleeping"
  sleep 2
done
echo "✅ Database is ready!"

# Create admin user
echo "👤 Creating admin user..."
docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME <<'EOF'
-- Create admin user (password: admin123)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (username, email, password_hash, is_active, is_admin, created_at)
VALUES (
    'admin',
    'admin@insurance.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNv0C8J9Fi', -- admin123
    TRUE,
    TRUE,
    CURRENT_TIMESTAMP
)
ON CONFLICT (username) DO NOTHING;

-- Create regular test user (password: user123)
INSERT INTO users (driver_id, username, email, password_hash, is_active, is_admin, created_at)
VALUES (
    'DRV-0001',
    'user1',
    'user1@insurance.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- user123
    TRUE,
    FALSE,
    CURRENT_TIMESTAMP
)
ON CONFLICT (username) DO NOTHING;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Admin user created successfully"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo "   Email: admin@insurance.com"
else
    echo "❌ Failed to create admin user"
    exit 1
fi

# Check if sample data already exists
DRIVER_COUNT=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM drivers;" 2>/dev/null | xargs)

if [ "$DRIVER_COUNT" -gt 0 ]; then
    echo "ℹ️  Sample data already exists ($DRIVER_COUNT drivers found)"
    echo "   Skipping sample data insertion"
else
    echo "📊 Inserting sample data..."

    # Insert sample drivers
    docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME <<'EOF'
-- Insert sample drivers
INSERT INTO drivers (driver_id, first_name, last_name, email, phone, date_of_birth, license_number, license_state, years_licensed, gender, marital_status, address, city, state, zip_code, created_at)
VALUES
    ('DRV-0001', 'John', 'Doe', 'john.doe@email.com', '555-0101', '1985-03-15', 'D1234567', 'CA', 15, 'Male', 'Married', '123 Main St', 'Los Angeles', 'CA', '90001', CURRENT_TIMESTAMP),
    ('DRV-0002', 'Jane', 'Smith', 'jane.smith@email.com', '555-0102', '1990-07-22', 'D2345678', 'CA', 10, 'Female', 'Single', '456 Oak Ave', 'San Francisco', 'CA', '94102', CURRENT_TIMESTAMP),
    ('DRV-0003', 'Bob', 'Johnson', 'bob.johnson@email.com', '555-0103', '1978-11-30', 'D3456789', 'CA', 20, 'Male', 'Married', '789 Pine Rd', 'San Diego', 'CA', '92101', CURRENT_TIMESTAMP),
    ('DRV-0004', 'Alice', 'Williams', 'alice.williams@email.com', '555-0104', '1995-05-18', 'D4567890', 'CA', 5, 'Female', 'Single', '321 Elm St', 'Sacramento', 'CA', '95814', CURRENT_TIMESTAMP),
    ('DRV-0005', 'Charlie', 'Brown', 'charlie.brown@email.com', '555-0105', '1982-09-25', 'D5678901', 'CA', 18, 'Male', 'Married', '654 Maple Dr', 'San Jose', 'CA', '95113', CURRENT_TIMESTAMP),
    ('DRV-0006', 'Diana', 'Davis', 'diana.davis@email.com', '555-0106', '1988-12-08', 'D6789012', 'CA', 12, 'Female', 'Divorced', '987 Cedar Ln', 'Oakland', 'CA', '94612', CURRENT_TIMESTAMP),
    ('DRV-0007', 'Eve', 'Martinez', 'eve.martinez@email.com', '555-0107', '1992-04-14', 'D7890123', 'CA', 8, 'Female', 'Single', '147 Birch Ct', 'Fresno', 'CA', '93721', CURRENT_TIMESTAMP)
ON CONFLICT (driver_id) DO NOTHING;

-- Insert sample vehicles
INSERT INTO vehicles (vehicle_id, driver_id, make, model, year, vin, vehicle_type, safety_rating, created_at)
VALUES
    ('VEH-0001', 'DRV-0001', 'Toyota', 'Camry', 2020, '1HGBH41JXMN109186', 'Sedan', 5, CURRENT_TIMESTAMP),
    ('VEH-0002', 'DRV-0002', 'Honda', 'Civic', 2021, '2HGFC2F59MH123456', 'Sedan', 5, CURRENT_TIMESTAMP),
    ('VEH-0003', 'DRV-0003', 'Ford', 'F-150', 2019, '1FTFW1EF8KFC12345', 'Truck', 4, CURRENT_TIMESTAMP),
    ('VEH-0004', 'DRV-0004', 'Tesla', 'Model 3', 2022, '5YJ3E1EA8MF123456', 'Electric', 5, CURRENT_TIMESTAMP),
    ('VEH-0005', 'DRV-0005', 'Chevrolet', 'Silverado', 2020, '1GCUYEED6LZ123456', 'Truck', 4, CURRENT_TIMESTAMP),
    ('VEH-0006', 'DRV-0006', 'BMW', '3 Series', 2021, 'WBA8B9G51MNU12345', 'Sedan', 5, CURRENT_TIMESTAMP),
    ('VEH-0007', 'DRV-0007', 'Mazda', 'CX-5', 2020, 'JM3KFBDM8M0123456', 'SUV', 5, CURRENT_TIMESTAMP)
ON CONFLICT (vehicle_id) DO NOTHING;

-- Insert sample devices
INSERT INTO devices (device_id, driver_id, vehicle_id, device_type, manufacturer, firmware_version, installed_date, is_active, last_heartbeat, created_at)
VALUES
    ('DEV-0001', 'DRV-0001', 'VEH-0001', 'OBD-II', 'SafeDrive Inc', 'v2.1.0', '2023-01-15', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('DEV-0002', 'DRV-0002', 'VEH-0002', 'OBD-II', 'SafeDrive Inc', 'v2.1.0', '2023-02-20', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('DEV-0003', 'DRV-0003', 'VEH-0003', 'OBD-II', 'TelematicsPlus', 'v1.9.2', '2023-03-10', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('DEV-0004', 'DRV-0004', 'VEH-0004', 'OBD-II', 'SafeDrive Inc', 'v2.2.0', '2023-04-05', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('DEV-0005', 'DRV-0005', 'VEH-0005', 'OBD-II', 'TelematicsPlus', 'v2.0.1', '2023-05-12', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('DEV-0006', 'DRV-0006', 'VEH-0006', 'OBD-II', 'SafeDrive Inc', 'v2.1.5', '2023-06-18', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('DEV-0007', 'DRV-0007', 'VEH-0007', 'OBD-II', 'SafeDrive Inc', 'v2.1.0', '2023-07-22', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (device_id) DO NOTHING;

-- Insert sample risk scores
INSERT INTO risk_scores (score_id, driver_id, risk_score, calculation_date, factors_json, created_at)
VALUES
    ('RISK-0001', 'DRV-0001', 35.5, CURRENT_TIMESTAMP - INTERVAL '1 day', '{"harsh_braking": 2, "speeding": 1, "night_driving": 0.5}', CURRENT_TIMESTAMP),
    ('RISK-0002', 'DRV-0002', 28.2, CURRENT_TIMESTAMP - INTERVAL '1 day', '{"harsh_braking": 1, "speeding": 0, "night_driving": 0.2}', CURRENT_TIMESTAMP),
    ('RISK-0003', 'DRV-0003', 52.8, CURRENT_TIMESTAMP - INTERVAL '1 day', '{"harsh_braking": 5, "speeding": 4, "night_driving": 1.8}', CURRENT_TIMESTAMP),
    ('RISK-0004', 'DRV-0004', 22.1, CURRENT_TIMESTAMP - INTERVAL '1 day', '{"harsh_braking": 0, "speeding": 0, "night_driving": 0.1}', CURRENT_TIMESTAMP),
    ('RISK-0005', 'DRV-0005', 45.3, CURRENT_TIMESTAMP - INTERVAL '1 day', '{"harsh_braking": 3, "speeding": 2, "night_driving": 1.3}', CURRENT_TIMESTAMP),
    ('RISK-0006', 'DRV-0006', 38.7, CURRENT_TIMESTAMP - INTERVAL '1 day', '{"harsh_braking": 2, "speeding": 2, "night_driving": 0.7}', CURRENT_TIMESTAMP),
    ('RISK-0007', 'DRV-0007', 31.4, CURRENT_TIMESTAMP - INTERVAL '1 day', '{"harsh_braking": 1, "speeding": 1, "night_driving": 0.4}', CURRENT_TIMESTAMP)
ON CONFLICT (score_id) DO NOTHING;

-- Insert sample premiums
INSERT INTO premiums (premium_id, driver_id, policy_id, base_premium, risk_adjustment, final_premium, monthly_premium, policy_type, status, effective_date, expiration_date, created_at)
VALUES
    (1, 'DRV-0001', 'POL-0001', 1200.00, -15.50, 1184.50, 98.71, 'PHYD', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year', CURRENT_TIMESTAMP),
    (2, 'DRV-0002', 'POL-0002', 1100.00, -28.20, 1071.80, 89.32, 'PHYD', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year', CURRENT_TIMESTAMP),
    (3, 'DRV-0003', 'POL-0003', 1300.00, 52.80, 1352.80, 112.73, 'PHYD', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year', CURRENT_TIMESTAMP),
    (4, 'DRV-0004', 'POL-0004', 1000.00, -22.10, 977.90, 81.49, 'PHYD', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year', CURRENT_TIMESTAMP),
    (5, 'DRV-0005', 'POL-0005', 1250.00, 45.30, 1295.30, 107.94, 'PHYD', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year', CURRENT_TIMESTAMP),
    (6, 'DRV-0006', 'POL-0006', 1150.00, 38.70, 1188.70, 99.06, 'PHYD', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year', CURRENT_TIMESTAMP),
    (7, 'DRV-0007', 'POL-0007', 1050.00, -31.40, 1018.60, 84.88, 'PHYD', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year', CURRENT_TIMESTAMP)
ON CONFLICT (premium_id) DO NOTHING;

-- Insert sample trips (last 7 days)
INSERT INTO trips (trip_id, driver_id, device_id, start_time, end_time, duration_minutes, distance_miles, avg_speed, max_speed, harsh_braking_count, rapid_accel_count, speeding_count, harsh_corner_count, trip_type, created_at)
VALUES
    ('TRIP-0001', 'DRV-0001', 'DEV-0001', CURRENT_TIMESTAMP - INTERVAL '6 days', CURRENT_TIMESTAMP - INTERVAL '6 days' + INTERVAL '25 minutes', 25, 15.3, 35.2, 45.8, 0, 1, 0, 0, 'commute', CURRENT_TIMESTAMP - INTERVAL '6 days'),
    ('TRIP-0002', 'DRV-0002', 'DEV-0002', CURRENT_TIMESTAMP - INTERVAL '5 days', CURRENT_TIMESTAMP - INTERVAL '5 days' + INTERVAL '18 minutes', 18, 12.1, 40.5, 52.3, 1, 0, 1, 0, 'commute', CURRENT_TIMESTAMP - INTERVAL '5 days'),
    ('TRIP-0003', 'DRV-0003', 'DEV-0003', CURRENT_TIMESTAMP - INTERVAL '4 days', CURRENT_TIMESTAMP - INTERVAL '4 days' + INTERVAL '45 minutes', 45, 28.7, 38.5, 68.2, 3, 2, 4, 1, 'leisure', CURRENT_TIMESTAMP - INTERVAL '4 days'),
    ('TRIP-0004', 'DRV-0004', 'DEV-0004', CURRENT_TIMESTAMP - INTERVAL '3 days', CURRENT_TIMESTAMP - INTERVAL '3 days' + INTERVAL '22 minutes', 22, 14.2, 38.9, 48.5, 0, 0, 0, 0, 'commute', CURRENT_TIMESTAMP - INTERVAL '3 days'),
    ('TRIP-0005', 'DRV-0005', 'DEV-0005', CURRENT_TIMESTAMP - INTERVAL '2 days', CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '35 minutes', 35, 22.5, 42.3, 62.1, 2, 1, 2, 1, 'business', CURRENT_TIMESTAMP - INTERVAL '2 days'),
    ('TRIP-0006', 'DRV-0006', 'DEV-0006', CURRENT_TIMESTAMP - INTERVAL '1 day', CURRENT_TIMESTAMP - INTERVAL '1 day' + INTERVAL '28 minutes', 28, 18.9, 40.1, 55.7, 1, 1, 1, 0, 'commute', CURRENT_TIMESTAMP - INTERVAL '1 day'),
    ('TRIP-0007', 'DRV-0007', 'DEV-0007', CURRENT_TIMESTAMP - INTERVAL '12 hours', CURRENT_TIMESTAMP - INTERVAL '12 hours' + INTERVAL '20 minutes', 20, 13.5, 40.5, 50.2, 0, 0, 0, 0, 'leisure', CURRENT_TIMESTAMP - INTERVAL '12 hours')
ON CONFLICT (trip_id) DO NOTHING;
EOF

    if [ $? -eq 0 ]; then
        echo "✅ Sample data inserted successfully"
        echo "   - 7 Drivers"
        echo "   - 7 Vehicles"
        echo "   - 7 Devices"
        echo "   - 7 Risk Scores"
        echo "   - 7 Premiums"
        echo "   - 7 Trips"
    else
        echo "⚠️  Warning: Some sample data may not have been inserted"
    fi
fi

# Verify the data
echo ""
echo "📊 Database Status:"
echo "-------------------"
USER_COUNT=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM users;" | xargs)
DRIVER_COUNT=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM drivers;" | xargs)
VEHICLE_COUNT=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM vehicles;" | xargs)
TRIP_COUNT=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM trips;" | xargs)

echo "Users: $USER_COUNT"
echo "Drivers: $DRIVER_COUNT"
echo "Vehicles: $VEHICLE_COUNT"
echo "Trips: $TRIP_COUNT"

echo ""
echo "✅ Data restoration complete!"
echo ""
echo "🔑 Login Credentials:"
echo "   Admin:"
echo "     Username: admin"
echo "     Password: admin123"
echo ""
echo "   Test User:"
echo "     Username: user1"
echo "     Password: user123"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
