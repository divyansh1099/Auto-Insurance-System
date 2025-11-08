# Telematics-Based Auto Insurance System

A production-ready telematics-based automobile insurance system that enables usage-based insurance (UBI) pricing models through real-time driving behavior analysis.

## 🏗️ Project Structure

```
.
├── src/                    # Source code
│   ├── backend/           # FastAPI backend application
│   ├── frontend/          # React frontend application
│   ├── simulator/         # Telematics data simulator
│   ├── ml/                # Machine learning models and training
│   └── schemas/           # Avro schemas for data serialization
├── models/                # AI model weights (or pointers to downloads)
├── docs/                  # Documentation, design docs, diagrams
├── bin/                   # Executables and run scripts
├── data/                  # Sample data (anonymized)
│   └── sample/           # Small sample datasets
└── docker-compose.yml     # Docker orchestration

```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

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
   - API Documentation: http://localhost:8000/docs
   - Dashboard: http://localhost:3000
   - Login: `admin` / `admin123`

## 📋 Features

### Core Functionality
- ✅ Real-time telematics data ingestion via Kafka
- ✅ ML-based risk scoring (XGBoost)
- ✅ Dynamic pricing engine
- ✅ Interactive dashboard
- ✅ Admin panel with CRUD operations
- ✅ RESTful API with JWT authentication

### Technology Stack
- **Backend:** FastAPI, PostgreSQL, Redis, Kafka
- **Frontend:** React, Vite, Tailwind CSS
- **ML:** XGBoost, scikit-learn, SHAP
- **Infrastructure:** Docker, Docker Compose, Terraform (AWS)

## 📚 Documentation

See `/docs` directory for:
- `README.md` - Main documentation
- `QUICKSTART.md` - Quick start guide
- `ADMIN_PANEL.md` - Admin panel documentation
- `PROJECT_ANALYSIS.md` - Comprehensive project analysis
- `terraform/` - AWS deployment documentation

## 🔧 Development

### Backend
```bash
cd src/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd src/frontend
npm install
npm run dev
```

### ML Training
```bash
cd src/ml
python train_model.py --n-drivers 500
```

## 📊 API Endpoints

- `GET /health` - Health check
- `POST /api/v1/auth/login` - Authentication
- `GET /api/v1/risk/{driver_id}/score` - Risk score
- `GET /api/v1/pricing/{driver_id}/current` - Premium
- `GET /api/v1/admin/dashboard/stats` - Admin stats

Full API documentation: http://localhost:8000/docs

## 🧪 Testing

```bash
# Run tests
docker compose exec backend pytest

# Check services
docker compose ps

# View logs
docker compose logs -f backend
```

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Contact

For questions or support, please open an issue.

