# Testing Troubleshooting Guide

Based on real issues encountered during testing setup. Use this guide to fix specific problems.

---

## ❌ Issue 1: Backend Not Running (Connection Reset)

### Symptoms:
```
❌ Cannot connect to API: Connection refused
❌ Cannot connect to API: ('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer'))
```

### Root Cause:
Backend container crashed on startup due to missing dependencies or other errors.

### Solution:

**Step 1**: Check backend status
```bash
docker compose ps backend
```

If status is "Exited" or not "Up", check logs:

**Step 2**: Check backend logs
```bash
docker compose logs backend --tail=50
```

**Common errors and fixes:**

#### Error: `ModuleNotFoundError: No module named 'slowapi'`

**Fix:**
```bash
# Install missing dependency
docker compose exec backend pip install slowapi

# Restart backend
docker compose restart backend

# Verify it's running
docker compose ps backend
```

#### Error: `ModuleNotFoundError: No module named 'X'`

**Fix:**
```bash
# Install missing package
docker compose exec backend pip install <package-name>

# Restart backend
docker compose restart backend
```

#### Error: Database connection issues

**Fix:**
```bash
# Restart PostgreSQL
docker compose restart postgres

# Wait 30 seconds
sleep 30

# Restart backend
docker compose restart backend
```

---

## ❌ Issue 2: Missing Test Dependencies (Host Machine)

### Symptoms:
```
❌ API tests FAILED (Duration: 0.2s)
ModuleNotFoundError: No module named 'requests'
ModuleNotFoundError: No module named 'psycopg2'
```

### Root Cause:
Test scripts run on YOUR HOST MACHINE, not inside Docker containers. Your machine is missing required Python packages.

### Solution:

**Important**: These packages must be installed on your LOCAL machine (not in Docker):

```bash
# Option 1: Using requirements file (recommended)
pip install -r requirements-test.txt

# Option 2: Manual installation
pip install requests psycopg2-binary
```

**Verify installation:**
```bash
python -c "import requests; print('requests OK')"
python -c "import psycopg2; print('psycopg2 OK')"
```

---

## ❌ Issue 3: Database Role Not Found

### Symptoms:
```
❌ Cannot connect to database: role "insurance_user" does not exist
❌ DATABASE tests FAILED
```

### Root Cause:
You have LOCAL PostgreSQL running and tests are connecting to it instead of Docker PostgreSQL. Your local PostgreSQL doesn't have the `insurance_user` role.

### Solution:

**Option A: Stop Local PostgreSQL (Recommended)**

```bash
# On macOS
brew services stop postgresql

# On Linux (systemd)
sudo systemctl stop postgresql

# On Linux (older init)
sudo service postgresql stop

# Verify it's stopped
lsof -i :5432
# Should return nothing
```

Then run tests again - they'll connect to Docker PostgreSQL on port 5432.

**Option B: Use Different Port for Docker PostgreSQL**

Edit `docker-compose.yml`:
```yaml
services:
  postgres:
    ports:
      - "5433:5432"  # Change from 5432:5432
```

Update test configurations in `tests/*.py`:
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,  # Change from 5432
    'database': 'telematics_db',
    'user': 'insurance_user',
    'password': 'insurance_pass'
}
```

**Option C: Create Role in Local PostgreSQL**

```bash
# Connect to local PostgreSQL
psql -U postgres

# Create role and database
CREATE USER insurance_user WITH PASSWORD 'insurance_pass';
CREATE DATABASE telematics_db OWNER insurance_user;
GRANT ALL PRIVILEGES ON DATABASE telematics_db TO insurance_user;
\q
```

⚠️ **Warning**: This creates the database in your LOCAL PostgreSQL, not Docker. May cause confusion.

---

## ❌ Issue 4: Connection to Wrong Database

### Symptoms:
```
⚠️  May be connecting to LOCAL PostgreSQL instead of Docker!
```

### Root Cause:
Both local and Docker PostgreSQL running on same port (5432).

### How to Verify:

```bash
# Check if local PostgreSQL is running
lsof -i :5432

# Should show only Docker container, not local PostgreSQL
```

### Solution:

See **Issue 3** above - stop local PostgreSQL.

---

## ❌ Issue 5: Backend Returns 500 Errors

### Symptoms:
```
❌ GET /admin/dashboard/summary: Unexpected status code: 500
```

### Root Cause:
Backend internal errors (database connection issues, missing migrations, etc.)

### Solution:

**Step 1**: Check backend logs
```bash
docker compose logs backend --tail=100
```

**Step 2**: Common fixes

#### Database not initialized:
```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Or initialize with sample data
docker compose exec backend python scripts/init_db.py
```

#### Missing database tables:
```bash
# Check tables exist
docker compose exec postgres psql -U insurance_user -d telematics_db -c "\dt"

# Should show: drivers, users, trips, premiums, risk_scores, etc.
```

#### Redis connection issues:
```bash
# Restart Redis
docker compose restart redis

# Verify Redis is accessible
docker compose exec backend python -c "
from app.services.redis_client import get_redis_client
redis = get_redis_client()
print('Redis OK' if redis else 'Redis FAIL')
"
```

---

## ❌ Issue 6: Performance Tests Failing

### Symptoms:
```
❌ Dashboard Summary Response Time: Avg: 1.2s (Target: <0.5s)
❌ Cache Hit Rate: 15% (Target: >60%)
```

### Root Cause:
- First request after restart (cold cache)
- Heavy database load
- Missing indexes

### Solution:

**Step 1**: Warm up the cache
```bash
# Make several requests to warm cache
for i in {1..10}; do
  curl -s -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/admin/dashboard/summary > /dev/null
  sleep 0.5
done
```

**Step 2**: Verify indexes exist
```bash
docker compose exec postgres psql -U insurance_user -d telematics_db -c "
SELECT COUNT(*) FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'idx_%';
"
# Should return 20+
```

If missing indexes:
```bash
# Run Phase 1 migration
docker compose exec postgres psql -U insurance_user -d telematics_db \
  -f /path/to/001_add_performance_indexes.sql
```

**Step 3**: Restart backend to clear any issues
```bash
docker compose restart backend
sleep 30
```

**Step 4**: Run performance tests again
```bash
python run_all_tests.py --only-performance
```

---

## ❌ Issue 7: Admin User Authentication Failed

### Symptoms:
```
❌ Admin authentication failed: 401
```

### Root Cause:
Admin user doesn't exist or password is incorrect.

### Solution:

**Step 1**: Check if admin user exists
```bash
docker compose exec backend python -c "
from app.models.database import SessionLocal, User
db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    print(f'Admin exists: {admin.username}, is_admin: {admin.is_admin}')
else:
    print('Admin user NOT found')
"
```

**Step 2**: Create or reset admin user
```bash
docker compose exec backend python -c "
from app.models.database import SessionLocal, User
from app.utils.auth import get_password_hash

db = SessionLocal()

# Delete existing admin if any
existing = db.query(User).filter(User.username == 'admin').first()
if existing:
    db.delete(existing)
    db.commit()
    print('Deleted existing admin')

# Create new admin
admin = User(
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('admin123'),
    is_admin=True,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created: username=admin, password=admin123')
"
```

**Step 3**: Test authentication
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin&password=admin123"

# Should return: {"access_token":"...","token_type":"bearer"}
```

---

## ✅ Complete Reset (Nuclear Option)

If nothing else works, completely reset the environment:

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: deletes all data)
docker compose down -v

# Remove images
docker compose down --rmi all

# Start fresh
docker compose up -d

# Wait for services to initialize
sleep 60

# Run setup script
bash setup_test_environment.sh

# Verify environment
python check_environment.py

# Run tests
python run_all_tests.py
```

---

## 🔍 Diagnostic Commands

Use these to diagnose issues:

```bash
# Check all services status
docker compose ps

# View logs for specific service
docker compose logs backend --tail=100
docker compose logs postgres --tail=50
docker compose logs redis --tail=50

# Check backend health
curl http://localhost:8000/health

# Check metrics endpoint
curl http://localhost:8000/metrics | head -20

# Check database connection
docker compose exec postgres psql -U insurance_user -d telematics_db -c "SELECT version();"

# Check which process is using port 5432
lsof -i :5432

# Check which process is using port 8000
lsof -i :8000

# Test backend from inside container
docker compose exec backend python -c "
from app.models.database import SessionLocal
db = SessionLocal()
print('Database connection OK')
"

# Check Redis connection
docker compose exec backend python -c "
from app.services.redis_client import get_redis_client
redis = get_redis_client()
print('Redis connection OK' if redis else 'Redis FAIL')
"
```

---

## 📞 Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Backend not running | `docker compose logs backend` → fix error → `docker compose restart backend` |
| Missing test deps | `pip install -r requirements-test.txt` |
| Database role error | Stop local PostgreSQL: `brew services stop postgresql` |
| Connection reset | Backend crashed - check logs and fix |
| Performance slow | Warm cache, verify indexes, restart backend |
| Admin auth failed | Recreate admin user with script above |
| Port conflict | Stop local PostgreSQL or use different port |

---

## 🆘 Still Stuck?

1. **Check logs**: `docker compose logs -f`
2. **Restart everything**: `docker compose restart`
3. **Reset environment**: `docker compose down -v && docker compose up -d`
4. **Run environment check**: `python check_environment.py`
5. **Review this guide carefully** - solution is likely here!

---

## ✅ Success Checklist

Before running tests, verify:

- [ ] Docker services running: `docker compose ps`
- [ ] Backend accessible: `curl http://localhost:8000/health`
- [ ] Database connectable (from Docker): `docker compose exec postgres psql -U insurance_user -d telematics_db -c "\dt"`
- [ ] Admin user exists: (use check script above)
- [ ] Test dependencies installed: `pip list | grep -E "requests|psycopg2"`
- [ ] No local PostgreSQL conflict: `lsof -i :5432` (should only show Docker)
- [ ] Backend has no errors: `docker compose logs backend --tail=20`

If all checkboxes pass, tests should run successfully!
