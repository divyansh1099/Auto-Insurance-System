# Quick Start Guide

This guide will help you get the Telematics Insurance System running in under 10 minutes.

## Prerequisites

- Docker Desktop installed and running
- At least 8GB RAM available
- 10GB free disk space

## Step 1: Initial Setup (2 minutes)

```bash
# Make setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This will:
- Create necessary directories
- Generate .env file from template
- Build and start all Docker containers
- Initialize the database

## Step 2: Populate Sample Data (1 minute)

```bash
# Install Python dependencies in backend container
docker-compose exec backend pip install -r requirements.txt

# Populate database with sample data
docker-compose exec backend python /app/../scripts/populate_sample_data.py
```

This creates:
- 10 sample drivers with different risk profiles
- Vehicle and device information
- Sample risk scores and premiums
- Demo user accounts

## Step 3: Train the ML Model (2 minutes)

```bash
# Train the risk scoring model
docker-compose exec backend python /app/../ml/train_model.py --n-drivers 500
```

This will:
- Generate synthetic training data
- Train an XGBoost model
- Save the model to /models directory
- Display model performance metrics

## Step 4: Run the Data Simulator (optional)

```bash
# Generate realistic telematics data
docker-compose exec simulator python telematics_simulator.py
```

This creates realistic driving events for testing.

## Step 5: Access the Application

### Dashboard
Open http://localhost:3000 in your browser

**Demo Login:**
- Username: `demo`
- Password: `demo123`

**Admin Login:**
- Username: `admin`
- Password: `admin123`

### API Documentation
Visit http://localhost:8000/docs for interactive API documentation

## Verify Everything is Working

1. **Check Services**
   ```bash
   docker-compose ps
   ```
   All services should show "Up" status

2. **View Logs**
   ```bash
   # All services
   docker-compose logs -f

   # Specific service
   docker-compose logs -f backend
   ```

3. **Test API**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy","version":"1.0.0"}`

4. **Check Database**
   ```bash
   docker-compose exec postgres psql -U insurance_user -d telematics_db -c "SELECT COUNT(*) FROM drivers;"
   ```
   Should show 10 drivers

## Common Commands

### Start/Stop Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart backend
```

### View Logs
```bash
# Tail logs from all services
docker-compose logs -f

# View backend logs
docker-compose logs -f backend

# View simulator logs
docker-compose logs -f simulator
```

### Database Access
```bash
# PostgreSQL
docker-compose exec postgres psql -U insurance_user -d telematics_db

# Redis
docker-compose exec redis redis-cli
```

### Rebuild After Code Changes
```bash
# Rebuild a specific service
docker-compose build backend

# Rebuild and restart
docker-compose up -d --build backend
```

## Troubleshooting

### Services Won't Start
```bash
# Check Docker is running
docker info

# View detailed logs
docker-compose logs

# Restart all services
docker-compose down
docker-compose up -d
```

### Database Connection Errors
```bash
# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready -U insurance_user

# Recreate database
docker-compose down -v
docker-compose up -d
```

### Port Conflicts
If ports are already in use, edit `docker-compose.yml` to use different ports:
- Backend API: Change `8000:8000` to `8001:8000`
- Frontend: Change `3000:3000` to `3001:3000`
- PostgreSQL: Change `5432:5432` to `5433:5432`

### Clear All Data and Start Fresh
```bash
# Stop and remove everything
docker-compose down -v

# Remove data directories
rm -rf data/*

# Start again
./setup.sh
```

## Next Steps

1. **Explore the Dashboard**
   - View risk scores
   - Check premium calculations
   - Review driving statistics

2. **Test the API**
   - Use the interactive docs at http://localhost:8000/docs
   - Try different endpoints
   - Test authentication

3. **Customize the System**
   - Modify driver profiles in the simulator
   - Adjust risk scoring weights
   - Customize premium calculation logic

4. **Add More Data**
   - Run the simulator with more drivers
   - Generate historical trip data
   - Create custom test scenarios

## Architecture Overview

```
┌─────────────────┐
│   React         │  http://localhost:3000
│   Dashboard     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  http://localhost:8000
│   Backend       │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Postgres│ │ Redis  │ │ Kafka  │ │  ML    │
│  DB    │ │ Cache  │ │ Stream │ │ Model  │
└────────┘ └────────┘ └────────┘ └────────┘
```

## Support

- Documentation: See README.md
- Issues: Check docker-compose logs
- API Reference: http://localhost:8000/docs

## Clean Shutdown

```bash
# Stop services but keep data
docker-compose down

# Stop services and remove volumes (deletes all data)
docker-compose down -v
```

---

**Congratulations!** You now have a fully functional telematics-based insurance system running locally. 🎉
