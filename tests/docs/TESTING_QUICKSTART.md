# Testing Quick Start Guide

## ⚠️ IMPORTANT: Run Tests on Your Local Machine

The comprehensive testing suite requires a **running backend with Docker services**. These tests **must be run on your local machine** where Docker is installed, not in the Claude Code environment.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Setup Test Environment

On your **local machine**, navigate to the project directory and run:

```bash
# Automated setup (recommended)
bash setup_test_environment.sh
```

This script will:
- ✅ Start Docker services (backend, postgres, redis, kafka)
- ✅ Create database role and database if needed
- ✅ Create admin user for testing
- ✅ Install Python test dependencies
- ✅ Verify backend is accessible

**Duration**: 1-2 minutes

---

### Step 2: Verify Environment

Check that everything is ready:

```bash
python check_environment.py
```

**Expected output**:
```
================================================================================
ENVIRONMENT CHECK REPORT
================================================================================

Total Checks: 9
Passed: 9 (100%)
Failed: 0

✅ Environment is ready for testing!

You can now run:
  python run_all_tests.py
```

If any checks fail, the script will tell you exactly what to fix.

---

### Step 3: Run Tests

Once environment checks pass, run the comprehensive test suite:

```bash
# Run all tests (recommended first time)
python run_all_tests.py
```

**Duration**: 15-20 minutes

---

## 🔧 Manual Setup (if automated script fails)

If the automated setup script doesn't work, follow these manual steps:

### 1. Start Docker Services

```bash
docker compose up -d
```

### 2. Wait for Services to Initialize

```bash
# Wait 30 seconds for PostgreSQL to be ready
sleep 30
```

### 3. Create Database Role (if needed)

```bash
docker compose exec postgres psql -U postgres -c \
  "CREATE USER insurance_user WITH PASSWORD 'insurance_pass';"
```

### 4. Create Database (if needed)

```bash
docker compose exec postgres psql -U postgres -c \
  "CREATE DATABASE telematics_db OWNER insurance_user;"
```

### 5. Grant Privileges

```bash
docker compose exec postgres psql -U postgres -c \
  "GRANT ALL PRIVILEGES ON DATABASE telematics_db TO insurance_user;"

docker compose exec postgres psql -U postgres -d telematics_db -c \
  "GRANT ALL ON SCHEMA public TO insurance_user;"
```

### 6. Create Admin User

```bash
docker compose exec backend python -c "
from app.models.database import SessionLocal
from app.models.database import User
from app.utils.auth import get_password_hash

db = SessionLocal()

# Check if admin exists
admin = db.query(User).filter(User.username == 'admin').first()

if not admin:
    admin = User(
        username='admin',
        email='admin@example.com',
        hashed_password=get_password_hash('admin123'),
        is_admin=True,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print('Admin user created')
else:
    print('Admin user already exists')
"
```

### 7. Install Python Dependencies

```bash
pip install requests psycopg2-binary
```

### 8. Verify Backend is Running

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

---

## 📊 Understanding Test Results

### All Tests Pass ✅

```
================================================================================
FINAL COMPREHENSIVE TESTING REPORT
================================================================================
Total Test Suites: 4
Passed: 4 (100%)
Failed: 0

✅ ALL TESTS PASSED - System ready for Phase 2!
```

**Next step**: Proceed to Phase 2 - Cache Improvements

### Some Tests Fail ❌

```
Total Test Suites: 4
Passed: 2 (50%)
Failed: 2

⚠️  TESTING FAILED - Issues detected that need attention!

Recommendations:
  - Review SECURITY_TEST_REPORT.md for details
  - Review PERFORMANCE_TEST_REPORT.md for details
```

**Next steps**:
1. Review the specific test report files
2. Fix the issues identified
3. Re-run tests: `python run_all_tests.py`
4. Repeat until all tests pass

---

## 🐛 Common Issues & Solutions

### Issue: "Cannot connect to API"

```
❌ Cannot connect to API: Connection refused
```

**Solution:**
```bash
# Check if backend is running
docker compose ps backend

# If not running, start it
docker compose up -d backend

# Check logs for errors
docker compose logs backend -f
```

---

### Issue: "role 'insurance_user' does not exist"

```
❌ Database connection failed: role "insurance_user" does not exist
```

**Solution:**
```bash
docker compose exec postgres psql -U postgres -c \
  "CREATE USER insurance_user WITH PASSWORD 'insurance_pass';"
```

---

### Issue: "database 'telematics_db' does not exist"

```
❌ Database connection failed: database "telematics_db" does not exist
```

**Solution:**
```bash
docker compose exec postgres psql -U postgres -c \
  "CREATE DATABASE telematics_db OWNER insurance_user;"
```

---

### Issue: "Authentication failed: 401"

```
❌ Admin authentication failed: 401
```

**Solution:**
```bash
# Create or reset admin user
docker compose exec backend python -c "
from app.models.database import SessionLocal, User
from app.utils.auth import get_password_hash

db = SessionLocal()

# Delete existing admin if any
existing = db.query(User).filter(User.username == 'admin').first()
if existing:
    db.delete(existing)
    db.commit()

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
print('Admin user created')
"
```

---

### Issue: "Missing indexes"

```
⚠️  Only 5 indexes found (expected 20+)
```

**Solution:**
```bash
# Copy migration file to container
docker compose cp src/backend/migrations/001_add_performance_indexes.sql postgres:/tmp/

# Run migration
docker compose exec postgres psql -U insurance_user -d telematics_db \
  -f /tmp/001_add_performance_indexes.sql
```

---

### Issue: Performance tests failing

```
❌ Dashboard Summary Response Time: Avg: 1.2s (Target: <0.5s)
```

**Possible causes:**
- Cache not warmed up yet
- First request after restart
- Heavy database load

**Solution:**
```bash
# Restart backend to clear state
docker compose restart backend

# Wait for services to initialize
sleep 30

# Run performance tests again
python run_all_tests.py --only-performance
```

---

## 🎯 Test Options

### Run All Tests

```bash
python run_all_tests.py
```

### Run Specific Test Category

```bash
# Security only
python run_all_tests.py --only-security

# API only
python run_all_tests.py --only-api

# Database only
python run_all_tests.py --only-database

# Performance only
python run_all_tests.py --only-performance
```

### Skip Specific Tests

```bash
# Skip performance (faster)
python run_all_tests.py --skip-performance

# Skip security
python run_all_tests.py --skip-security
```

---

## 📝 Test Reports

After running tests, check these generated reports:

1. **COMPREHENSIVE_TEST_REPORT.md** - Overall summary
2. **SECURITY_TEST_REPORT.md** - Security findings
3. **API_TEST_REPORT.md** - API test results
4. **DB_CONSISTENCY_REPORT.md** - Database integrity
5. **PERFORMANCE_TEST_REPORT.md** - Performance metrics

---

## ✅ Success Criteria

Before proceeding to Phase 2, ensure:

- ✅ All security tests pass (no vulnerabilities)
- ✅ All API tests pass (all endpoints work)
- ✅ Database consistency checks pass (no data issues)
- ✅ Performance targets met (dashboard < 500ms, cache > 60%)

---

## 🆘 Still Having Issues?

1. **Check Docker services**: `docker compose ps`
2. **View logs**: `docker compose logs -f`
3. **Restart everything**: `docker compose restart`
4. **Check this file**: `TESTING_GUIDE.md` (detailed troubleshooting)

---

## 📞 Quick Reference

| Command | Purpose |
|---------|---------|
| `bash setup_test_environment.sh` | Automated environment setup |
| `python check_environment.py` | Verify environment is ready |
| `python run_all_tests.py` | Run all comprehensive tests |
| `docker compose ps` | Check service status |
| `docker compose logs backend` | View backend logs |
| `docker compose restart` | Restart all services |

---

**Remember**: Tests must run on your **local machine** with Docker, not in Claude Code environment!
