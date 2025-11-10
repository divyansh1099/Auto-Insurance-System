================================================================================
TELEMATICS-BASED AUTO INSURANCE SYSTEM
================================================================================

Repository Link:
----------------
https://github.com/divyansh1099/auto-insurance-system

================================================================================
SETUP INSTRUCTIONS
================================================================================

Prerequisites:
--------------
- Docker Desktop (version 20.10 or higher)
- Docker Compose (version 2.0 or higher, or use 'docker compose' command)
- At least 8GB RAM available for Docker
- At least 10GB free disk space

Step 1: Clone the Repository
-----------------------------
git clone [YOUR_REPO_URL]
cd "Auto Insurance System"

Step 2: Run Setup Script
-------------------------
chmod +x bin/setup.sh
./bin/setup.sh

This script will:
- Check Docker installation
- Create necessary data directories
- Build and start all Docker containers (8 services)
- Wait for services to initialize (approximately 30 seconds)

Step 3: Create Demo Users
--------------------------
docker compose exec backend python /app/scripts/create_demo_users.py

This creates:
- Admin user: username='admin', password='admin123'
- Demo driver users (driver0001, driver0002, etc.)

Step 4: Train ML Model (Optional but Recommended)
-------------------------------------------------
docker compose exec backend python /app/ml/train_model.py --n-drivers 500

This trains the XGBoost risk scoring model with synthetic data.
Model will be saved to: models/risk_scoring_model.pkl

Note: If model file doesn't exist, the system will use rule-based fallback.

Step 5: Verify Services are Running
------------------------------------
docker compose ps

All services should show "Up" status:
- zookeeper
- kafka
- schema-registry
- postgres
- redis
- backend
- frontend
- simulator

Access Points:
--------------
- Frontend Dashboard: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- API ReDoc: http://localhost:8000/redoc
- Prometheus Metrics: http://localhost:8000/metrics

================================================================================
RUN INSTRUCTIONS
================================================================================

Basic Usage:
------------
1. Access the dashboard at http://localhost:3000
2. Login with credentials:
   - Admin: username='admin', password='admin123'
   - Driver: username='driver0002', password='password0002'

Generate Telematics Data:
--------------------------
Option 1: Batch Generation (Recommended for initial setup)
docker compose exec simulator python telematics_simulator.py

This generates data for 10 drivers over 1 day (default).

Option 2: Continuous Real-Time Generation
docker compose exec simulator sh -c "CONTINUOUS_MODE=true NUM_DRIVERS=5 python telematics_simulator.py"

This continuously generates events in real-time.

Option 3: Custom Parameters
docker compose exec simulator sh -c "NUM_DRIVERS=20 SIMULATION_DAYS=7 python telematics_simulator.py"

View Real-Time Demo:
--------------------
./bin/live_demo.sh

This script:
- Starts the telematics simulator
- Generates realistic driving data
- Shows event counts and recent events
- Provides instructions for viewing in dashboard

Test API Endpoints:
-------------------
./bin/test_api.sh

This script tests:
- Health check endpoint
- Authentication
- Driver endpoints
- Risk scoring endpoints
- Pricing endpoints
- Admin endpoints
- Error handling

Stop Services:
--------------
docker compose down

Stop and Remove Data (Clean Reset):
------------------------------------
docker compose down -v

WARNING: This deletes all data including database, Kafka topics, and Redis cache.

================================================================================
EVALUATION INSTRUCTIONS
================================================================================

1. Model Performance Evaluation
--------------------------------
After training the model, evaluation metrics are printed:
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R² (Coefficient of Determination)
- Explained Variance
- Bucket Classification Accuracy

To view model performance:
docker compose exec backend python /app/ml/train_model.py --n-drivers 500

Expected output includes:
  Model Performance:
    RMSE: [value]
    MAE: [value]
    R²: [value]
    Explained Variance: [value]
    Bucket Classification Accuracy: [value]

2. System Performance Evaluation
---------------------------------
Check system metrics:
curl http://localhost:8000/metrics

Key metrics to monitor:
- http_requests_total: Total API requests
- risk_score_calculations_total: Number of risk scores calculated
- kafka_messages_consumed_total: Messages processed from Kafka
- events_processed_total: Telematics events processed

3. Risk Scoring Evaluation
---------------------------
Test risk scoring for a driver:
curl -X GET "http://localhost:8000/api/v1/risk/DRV-0001/score" \
  -H "Authorization: Bearer [TOKEN]"

Get token by logging in:
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

4. Pricing Engine Evaluation
-----------------------------
Test premium calculation:
curl -X GET "http://localhost:8000/api/v1/pricing/DRV-0001/current" \
  -H "Authorization: Bearer [TOKEN]"

Compare traditional vs telematics pricing:
curl -X GET "http://localhost:8000/api/v1/pricing/DRV-0001/comparison" \
  -H "Authorization: Bearer [TOKEN]"

5. Data Processing Evaluation
------------------------------
Check events in database:
docker compose exec backend python -c "
from app.models.database import SessionLocal, TelematicsEvent
db = SessionLocal()
count = db.query(TelematicsEvent).count()
print(f'Total events: {count}')
"

Check trips detected:
docker compose exec backend python -c "
from app.models.database import SessionLocal, Trip
db = SessionLocal()
count = db.query(Trip).count()
print(f'Total trips: {count}')
"

6. Real-Time Processing Evaluation
-----------------------------------
Monitor real-time event processing:
- Open dashboard at http://localhost:3000
- Navigate to "Live Driving" page
- Start continuous data generation
- Observe real-time updates of:
  * Risk scores
  * Safety scores
  * Behavior metrics
  * Premium adjustments

7. End-to-End Evaluation
------------------------
Run comprehensive test:
./bin/test_api.sh

This evaluates:
- API functionality
- Authentication and authorization
- Data ingestion
- Risk scoring
- Pricing calculation
- Error handling

================================================================================
NOTES ON MODELS, DATA, AND EXTERNAL SERVICES
================================================================================

Machine Learning Model:
-----------------------
- Algorithm: XGBoost Gradient Boosting Regressor
- Model Type: Regression (predicts risk score 0-100)
- Training Data: Synthetic data generated with diverse driver profiles
  * Safe drivers (40% of data)
  * Average drivers (45% of data)
  * Risky drivers (15% of data)
- Features: 30+ telematics-derived features including:
  * Speed patterns (average, max, variance, speeding incidents)
  * Acceleration/deceleration metrics (harsh braking, rapid acceleration)
  * Time-based patterns (night driving %, rush hour %, weekend %)
  * Trip characteristics (distance, duration, consistency)
  * Risk event frequencies (phone usage, harsh cornering)
- Model Location: models/risk_scoring_model.pkl
- Fallback: If model file not found, system uses rule-based scoring
- Interpretability: SHAP values for feature importance analysis
- Model Version: v1.0

Data Sources:
-------------
1. Telematics Simulator:
   - Generates realistic GPS, accelerometer, and vehicle data
   - Simulates three driver profiles: Safe, Average, Risky
   - Physics-based movement simulation
   - Configurable parameters (number of drivers, duration, continuous mode)
   - Output: Avro-serialized events published to Kafka

2. Database:
   - PostgreSQL 15: Primary data store
   - Tables: drivers, devices, telematics_events, trips, risk_scores, premiums, users
   - Initialization: src/backend/init.sql

3. Cache/Feature Store:
   - Redis 7: Caching and real-time feature store
   - Used for: Risk score caching, real-time updates, pub/sub messaging

4. Message Queue:
   - Apache Kafka 7.5.0: Event streaming platform
   - Topic: telematics-events (3 partitions)
   - Schema Registry: Confluent Schema Registry for Avro schema validation

External Services:
------------------
1. Docker Hub Images:
   - confluentinc/cp-zookeeper:7.5.0
   - confluentinc/cp-kafka:7.5.0
   - confluentinc/cp-schema-registry:7.5.0
   - postgres:15
   - redis:7-alpine

2. Python Packages (Backend):
   - FastAPI 0.109.0: Web framework
   - SQLAlchemy 2.0.25: ORM
   - XGBoost 2.0.3: ML model
   - scikit-learn 1.4.0: ML utilities
   - SHAP 0.44.1: Model interpretability
   - confluent-kafka: Kafka client
   - python-jose: JWT authentication
   - bcrypt: Password hashing

3. Node.js Packages (Frontend):
   - React 18.2.0: UI framework
   - Vite 5.0.8: Build tool
   - Tailwind CSS 3.3.6: Styling
   - React Query 3.39.3: Data fetching
   - Recharts 2.10.3: Charts

4. No External APIs Required:
   - All services run locally via Docker
   - No internet connection required after initial setup
   - No third-party API keys needed

Data Generation:
----------------
- Synthetic telematics data generated for POC/demonstration
- In production, would integrate with:
  * Hardware telematics devices (OBD-II dongles)
  * Smartphone apps (GPS + accelerometer)
  * Vehicle manufacturer APIs
- Current simulator generates realistic patterns:
  * Speed variations based on road type
  * Acceleration/deceleration events
  * Location-based driving patterns
  * Time-of-day behavior variations

Model Training:
--------------
- Default: 500 drivers, synthetic data
- Hyperparameter tuning: Optional (--tune flag)
- Cross-validation: 5-fold CV for hyperparameter search
- Evaluation: Train/test split (80/20)
- Model persistence: Pickle format (.pkl)

Pricing Model:
--------------
- Base Premium: Varies by policy type (PHYD, PAYD, Hybrid)
- Risk Multiplier: 0.7-1.5 based on risk score (0-100)
- Usage Multiplier: Based on annual mileage
- Discount System: Up to 45% discount for safe driving
  * Only trips with ZERO risk factors count
  * Each risky trip: -5 point penalty
  * Requires many clean trips to achieve discounts

================================================================================
TROUBLESHOOTING
================================================================================

Services Not Starting:
----------------------
docker compose logs [service_name]
docker compose restart [service_name]
docker compose up -d --build

Database Connection Issues:
---------------------------
docker compose exec postgres pg_isready -U insurance_user
docker compose down -v  # WARNING: Deletes all data
docker compose up -d

Kafka Issues:
-------------
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
docker compose logs kafka

Port Conflicts:
---------------
If ports 3000, 8000, 5432, 6379, 9092, 8081, or 2181 are in use:
- Stop conflicting services, or
- Modify ports in docker-compose.yml

Model Not Found:
----------------
If risk scoring fails, train the model:
docker compose exec backend python /app/ml/train_model.py

The system will use rule-based fallback if model is unavailable.

================================================================================
ADDITIONAL INFORMATION
================================================================================

Architecture:
-------------
- Microservices architecture with Docker Compose
- Event-driven processing via Kafka
- Real-time updates via Redis pub/sub
- RESTful API with FastAPI
- React SPA frontend

Security:
---------
- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (Admin, Driver)
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM

Performance:
------------
- Scalable: Kafka handles high-throughput event streaming
- Real-time: Redis enables sub-second updates
- Efficient: ML model cached in memory
- Monitoring: Prometheus metrics available

Features Implemented:
--------------------
- Real-time telematics data ingestion
- ML-based risk scoring (XGBoost)
- Dynamic pricing engine
- Interactive dashboard
- Admin panel
- Rewards & gamification
- Real-time driver feedback
- Trip detection and analysis
- Risk trend visualization
- Premium comparison (traditional vs telematics)

================================================================================
CONTACT & SUPPORT
================================================================================

For issues or questions:
- Check logs: docker compose logs
- Review API docs: http://localhost:8000/docs
- Check service status: docker compose ps

================================================================================
END OF README
================================================================================

