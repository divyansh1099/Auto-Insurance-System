# Telematics-Based Auto Insurance System

A production-ready telematics-based automobile insurance system that enables usage-based insurance (UBI) pricing models through real-time driving behavior analysis.

## Overview

This system collects real-time driving behavior data, processes it through distributed streaming pipelines, calculates personalized risk scores using machine learning, and provides dynamic insurance pricing.

### Key Features

- **Real-time Data Processing**: Kafka + Spark Streaming for processing telematics events
- **ML-Based Risk Scoring**: XGBoost model for personalized risk assessment
- **Dynamic Pricing**: Usage-based insurance premium calculation
- **Interactive Dashboard**: React-based UI with driving behavior insights
- **Scalable Architecture**: Distributed system design supporting thousands of drivers

## Architecture

```
Telematics Simulator → Kafka → Spark Streaming → Feature Store (Redis)
                                      ↓
                                Data Lake (S3)
                                      ↓
                              ML Risk Scoring Model
                                      ↓
                                FastAPI Backend
                                      ↓
                                React Dashboard
```

## Technology Stack

- **Data Ingestion**: Apache Kafka, Confluent Schema Registry
- **Stream Processing**: Apache Spark Structured Streaming
- **Storage**: PostgreSQL, Redis, S3/MinIO
- **Machine Learning**: XGBoost, scikit-learn, MLflow
- **API**: FastAPI, Pydantic
- **Frontend**: React, Recharts, Tailwind CSS
- **Infrastructure**: Docker, Docker Compose

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend development)
- 8GB RAM minimum (16GB recommended)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Auto Insurance System"
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Verify services are running**
   ```bash
   docker-compose ps
   ```

5. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Dashboard: http://localhost:3000
   - Kafka UI: http://localhost:9092

## Project Structure

```
.
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py      # Application entry point
│   │   ├── config.py    # Configuration management
│   │   ├── models/      # Database & Pydantic models
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── ml/          # ML model integration
│   │   └── utils/       # Utilities
│   ├── requirements.txt
│   └── Dockerfile
├── streaming/            # Spark Streaming jobs
├── simulator/            # Telematics data simulator
├── ml/                   # ML training pipeline
├── frontend/             # React dashboard
├── schemas/              # Avro schemas
└── docker-compose.yml    # Service orchestration
```

## Development

### Running Individual Components

**Backend API:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**Data Simulator:**
```bash
cd simulator
python telematics_simulator.py
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/refresh` - Refresh token

### Drivers
- `GET /api/v1/drivers/{id}` - Get driver profile
- `GET /api/v1/drivers/{id}/trips` - Get trip history
- `GET /api/v1/drivers/{id}/statistics` - Driving statistics

### Risk Scoring
- `GET /api/v1/risk/{driver_id}/score` - Current risk score
- `GET /api/v1/risk/{driver_id}/breakdown` - Score breakdown
- `GET /api/v1/risk/{driver_id}/history` - Historical scores

### Pricing
- `GET /api/v1/pricing/{driver_id}/current` - Current premium
- `GET /api/v1/pricing/{driver_id}/breakdown` - Premium breakdown
- `POST /api/v1/pricing/{driver_id}/simulate` - What-if scenarios

## Data Flow

1. **Data Generation**: Simulator generates realistic telematics events
2. **Ingestion**: Events published to Kafka topics
3. **Stream Processing**: Spark Streaming processes events in real-time
4. **Feature Engineering**: Calculate risk metrics and store in Redis
5. **ML Scoring**: XGBoost model calculates risk scores
6. **Pricing**: Dynamic premium calculation based on risk
7. **Visualization**: React dashboard displays insights

## Machine Learning

### Risk Scoring Model

The system uses XGBoost for risk scoring based on:
- Driving behavior (speed, braking, acceleration)
- Time patterns (night driving, rush hour)
- Location risk factors
- Historical claims data

**Model Performance:**
- R² Score: >0.70
- RMSE: <10 (on 0-100 scale)
- Feature importance via SHAP values

### Training the Model

```bash
cd ml
python train_model.py --data-path ../data/training --output-path ./models
```

## Monitoring

- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Dashboards (port 3001)
- **Kafka UI**: Topic monitoring

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## License

MIT License

## Contact

For questions or support, please open an issue.
