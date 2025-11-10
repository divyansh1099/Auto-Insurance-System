# Telematics-Based Auto Insurance System

A production-ready telematics-based automobile insurance system that enables usage-based insurance (UBI) pricing models through real-time driving behavior analysis. The system uses machine learning to assess driver risk and dynamically adjust insurance premiums based on actual driving patterns.

## 🏗️ Project Structure

```
.
├── src/                    # Source code
│   ├── backend/           # FastAPI backend application
│   │   ├── app/
│   │   │   ├── routers/   # API endpoints (11 routers)
│   │   │   ├── services/  # Business logic & ML integration
│   │   │   ├── models/    # Database models & schemas
│   │   │   └── utils/     # Utilities (auth, metrics, etc.)
│   │   ├── scripts/       # Database scripts & utilities
│   │   └── schemas/      # Avro schemas for Kafka
│   ├── frontend/          # React frontend application
│   │   └── src/
│   │       ├── pages/     # 14 React pages/components
│   │       ├── components/# Reusable UI components
│   │       └── services/  # API client services
│   ├── simulator/         # Telematics data simulator
│   │   └── telematics_simulator.py
│   └── ml/                # Machine learning models
│       ├── train_model.py      # XGBoost model training
│       └── feature_engineering.py  # Feature extraction
├── bin/                   # Executables and run scripts
├── data/                  # Runtime data (gitignored)
│   ├── kafka/            # Kafka data
│   ├── postgres/         # PostgreSQL data
│   └── redis/            # Redis data
└── docker-compose.yml     # Docker orchestration

```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (required)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend development)

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd "Auto Insurance System"
   ```

2. **Start all services**

   ```bash
   chmod +x bin/setup.sh
   ./bin/setup.sh
   docker compose up -d
   ```

3. **Create demo users**

   ```bash
   docker compose exec backend python /app/scripts/create_demo_users.py
   ```

4. **Access the application**
   - **API Documentation:** http://localhost:8000/docs
   - **Dashboard:** http://localhost:3000
   - **Default Login:** `admin` / `admin123`
   - **Demo Driver:** `driver0002` / `password0002`

## 📋 Features

### Core Functionality

- ✅ **Real-time Telematics Data Ingestion**

  - Kafka-based event streaming
  - Avro schema validation via Schema Registry
  - Background consumer processing
  - Redis pub/sub for real-time updates

- ✅ **Machine Learning Risk Scoring**

  - XGBoost-based risk prediction model
  - Feature engineering from telematics events
  - SHAP explanations for model interpretability
  - Real-time risk score calculation

- ✅ **Dynamic Pricing Engine**

  - ML-based premium calculation
  - Strict discount system (max 45% discount)
  - Risk-based pricing adjustments
  - Traditional vs. telematics premium comparison

- ✅ **Interactive Dashboard**

  - Real-time driving behavior monitoring
  - Risk profile visualization
  - Trip history and analytics
  - Policy details and pricing

- ✅ **Admin Panel**

  - Driver management (CRUD operations)
  - Policy administration
  - User management
  - Analytics and reporting
  - Risk distribution analysis

- ✅ **Rewards & Gamification**

  - Points-based reward system
  - Achievement tracking
  - Safety milestones

- ✅ **Data Generation & Simulation**
  - Physics-based telematics data generator
  - Realistic driving behavior simulation
  - Batch and continuous generation modes
  - Multiple driver profiles (Safe, Average, Risky)

### Technology Stack

#### Backend

- **Framework:** FastAPI 0.109.0
- **Database:** PostgreSQL 15 (SQLAlchemy 2.0.25)
- **Cache/Feature Store:** Redis 7-alpine
- **Message Queue:** Apache Kafka 7.5.0 (Confluent)
- **Schema Registry:** Confluent Schema Registry 7.5.0
- **Authentication:** JWT (python-jose), bcrypt
- **ML Libraries:** XGBoost 2.0.3, scikit-learn 1.4.0, SHAP 0.44.1
- **Monitoring:** Prometheus metrics, structured logging (structlog)

#### Frontend

- **Framework:** React 18.2.0
- **Build Tool:** Vite 5.0.8
- **Styling:** Tailwind CSS 3.3.6
- **Routing:** React Router DOM 6.20.0
- **Data Fetching:** React Query 3.39.3, Axios 1.6.2
- **Charts:** Recharts 2.10.3
- **UI Components:** Headless UI, Heroicons

#### Infrastructure

- **Containerization:** Docker & Docker Compose
- **Orchestration:** Docker Compose (8 services)
- **Data Serialization:** Avro (via Schema Registry)

#### ML Stack

- **Model:** XGBoost Gradient Boosting
- **Feature Engineering:** Custom telematics feature extraction
- **Model Tracking:** MLflow 2.9.2 (optional)
- **Visualization:** Matplotlib, Seaborn

## 🏛️ Architecture

### Services (Docker Compose)

1. **Zookeeper** - Kafka coordination
2. **Kafka** - Event streaming platform
3. **Schema Registry** - Avro schema management
4. **PostgreSQL** - Primary database
5. **Redis** - Caching and feature store
6. **Backend** - FastAPI application
7. **Frontend** - React dashboard
8. **Simulator** - Telematics data generator

### Data Flow

```
Telematics Devices/Simulator
    ↓
Kafka (telematics-events topic)
    ↓
Kafka Consumer (Background)
    ↓
Event Processing & Validation
    ↓
PostgreSQL (Storage)
    ↓
Redis (Pub/Sub for real-time updates)
    ↓
Frontend (WebSocket/SSE)
```

### API Architecture

- **11 API Routers:**
  - `auth` - Authentication & authorization
  - `drivers` - Driver management
  - `telematics` - Event ingestion
  - `risk` - Risk scoring
  - `pricing` - Premium calculation
  - `admin` - Admin operations
  - `analytics` - Analytics & reporting
  - `rewards` - Rewards system
  - `realtime` - Real-time updates
  - `data_generator` - Data generation
  - `simulator` - Simulator control

## 📊 Frontend Pages

1. **Login** - User authentication
2. **Dashboard** - Driver overview & metrics
3. **Driving Behavior** - Risk profile & trends
4. **Trips** - Trip history & statistics
5. **Pricing** - Policy details & premium info
6. **Rewards** - Points & achievements
7. **Live Driving** - Real-time monitoring
8. **Profile** - User profile management
9. **Drive Simulator** - Manual trip simulation
10. **Insurance Advisor** - Premium recommendations
11. **Admin Dashboard** - System overview
12. **Admin Drivers** - Driver management
13. **Admin Policies** - Policy administration
14. **Admin Users** - User management

## 🔧 Development

### Backend Development

```bash
cd src/backend
pip install -r requirements.txt

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
alembic upgrade head

# Run tests
pytest
```

### Frontend Development

```bash
cd src/frontend
npm install

# Development server
npm run dev

# Production build
npm run build
```

### ML Model Training

```bash
cd src/ml
pip install -r requirements.txt

# Train model with default settings
python train_model.py

# Train with custom parameters
python train_model.py --n-drivers 500 --tune

# Output: models/risk_scoring_model.pkl
```

### Running the Simulator

```bash
# Generate data for 10 drivers over 7 days
docker compose exec simulator python telematics_simulator.py

# Continuous mode (real-time generation)
docker compose exec simulator sh -c "CONTINUOUS_MODE=true NUM_DRIVERS=5 python telematics_simulator.py"

# Or use the live demo script
./bin/live_demo.sh
```

## 📡 API Endpoints

### Authentication

- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### Drivers

- `GET /api/v1/drivers/{driver_id}` - Get driver details
- `GET /api/v1/drivers/{driver_id}/trips` - Get trip history
- `GET /api/v1/drivers/{driver_id}/trips/summary` - Trip statistics

### Risk Scoring

- `GET /api/v1/risk/{driver_id}/score` - Get risk score
- `GET /api/v1/risk/{driver_id}/risk-profile-summary` - Risk profile
- `GET /api/v1/risk/{driver_id}/trend` - Risk trend over time

### Pricing

- `GET /api/v1/pricing/{driver_id}/current` - Current premium
- `GET /api/v1/pricing/{driver_id}/policy-details` - Policy details
- `GET /api/v1/pricing/{driver_id}/comparison` - Traditional vs. telematics
- `POST /api/v1/pricing/{driver_id}/recalculate-premium` - Recalculate premium

### Admin

- `GET /api/v1/admin/dashboard/stats` - Dashboard statistics
- `GET /api/v1/admin/drivers` - List all drivers
- `GET /api/v1/admin/policies` - List all policies
- `GET /api/v1/admin/users` - List all users

### Telematics

- `POST /api/v1/telematics/events` - Ingest telematics event
- `POST /api/v1/telematics/events/batch` - Batch event ingestion

### Real-time

- `GET /api/v1/realtime/{driver_id}/events` - Real-time event stream

**Full API Documentation:** http://localhost:8000/docs (Interactive Swagger UI)

## 🧪 Testing

```bash
# Run all tests
docker compose exec backend pytest

# Run with coverage
docker compose exec backend pytest --cov=app

# Check service status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f kafka

# Test API endpoints
./bin/test_api.sh
```

## 📈 ML Model Details

### Risk Scoring Model

- **Algorithm:** XGBoost Gradient Boosting
- **Features:** 30+ telematics-derived features
  - Speed patterns (avg, max, std deviation)
  - Acceleration/deceleration metrics
  - Time-based patterns (hour, day of week)
  - Trip characteristics (distance, duration)
  - Risk event frequencies
- **Output:** Risk score (0-100 scale)
- **Training:** Synthetic data generation (configurable)
- **Evaluation Metrics:** RMSE, MAE, R², Explained Variance
- **Interpretability:** SHAP values for feature importance

### Discount System

- **Maximum Discount:** 45%
- **Rules:**
  - Only trips with ZERO risk factors count toward discount
  - Any trip with risk factors (harsh braking, speeding, etc.) is excluded
  - Each risky trip incurs -5 point penalty
  - Discounts are hard to achieve (requires many clean trips)

## 🔐 Security

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (Admin, Driver)
- CORS configuration
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM

## 📝 Environment Variables

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/dbname

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
SCHEMA_REGISTRY_URL=http://schema-registry:8081

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
```

## 🐛 Troubleshooting

### Services not starting

```bash
# Check logs
docker compose logs

# Restart services
docker compose restart

# Rebuild containers
docker compose up -d --build
```

### Database connection issues

```bash
# Check PostgreSQL status
docker compose exec postgres pg_isready -U insurance_user

# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d
```

### Kafka issues

```bash
# Check Kafka topics
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check consumer groups
docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list
```

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Prometheus Metrics:** http://localhost:8000/metrics

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Support

For questions, issues, or support, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI, React, XGBoost, and Kafka**
