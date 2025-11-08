# Quick Reference Card

## 🚀 Start/Stop Commands

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# Check status
docker compose ps

# View logs
docker compose logs -f backend
```

## 🌐 Access Points

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:3000
- **Health Check:** http://localhost:8000/health

## 📊 Sample Data (10 Records Each)

- Drivers: DRV-0001 to DRV-0010
- Vehicles: VEH-0001 to VEH-0010
- Risk Scores: 20-80 range
- Premiums: $840-$1,440/year

## 🔍 Quick Database Queries

```bash
# View drivers
docker compose exec postgres psql -U insurance_user -d telematics_db -c "SELECT driver_id, first_name, email FROM drivers;"

# Check counts
docker compose exec postgres psql -U insurance_user -d telematics_db -c "SELECT
  (SELECT COUNT(*) FROM drivers) as drivers,
  (SELECT COUNT(*) FROM risk_scores) as risk_scores,
  (SELECT COUNT(*) FROM premiums) as premiums;"
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `PROGRESS.md` | Full detailed progress report |
| `QUICKSTART.md` | Setup instructions |
| `docker-compose.yml` | Service configuration |
| `backend/app/main.py` | API entry point |
| `simulator/telematics_simulator.py` | Data generator |

## 🎯 What Works Now (75% Complete)

✅ Infrastructure (all services running)
✅ Database schema + sample data
✅ Backend API (90% endpoints)
✅ Telematics simulator (100%)
✅ ML risk scoring model (ready)
✅ Dynamic pricing engine (working)
⚠️ Frontend (structure only)
⚠️ Kafka streaming (not wired)
⚠️ User auth (partial)

## 🔧 Next: Build Data Ingestion

**Component #2: Kafka Streaming**
- Wire simulator → Kafka → Database
- Real-time event processing
- ~4-6 hours estimated

## 🆘 Emergency Reset

```bash
docker compose down -v
rm -rf data/*
./setup.sh
```

---
**See PROGRESS.md for full details**
