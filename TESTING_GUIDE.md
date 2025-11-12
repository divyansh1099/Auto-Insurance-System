# Comprehensive Testing Guide

This guide explains how to run the comprehensive testing suite for the Auto-Insurance-System before proceeding to Phase 2.

## Overview

The testing suite includes 4 major test categories:

1. **Security Vulnerability Testing** - SQL injection, XSS, auth bypass, input validation
2. **API Integration Testing** - All endpoints, CRUD operations, edge cases
3. **Database Consistency Checks** - Referential integrity, data validation, indexes
4. **Performance Benchmarking** - Response times, cache hit rates, concurrent load

## Prerequisites

### 1. System Requirements

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL client (psql)
- Backend service running
- Test data loaded in database

### 2. Start the System

```bash
# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# Expected output: backend, postgres, redis, kafka should be "Up"
```

### 3. Verify Backend is Accessible

```bash
# Check health
curl http://localhost:8000/health

# Check metrics endpoint
curl http://localhost:8000/metrics
```

### 4. Install Python Dependencies

```bash
# Install testing libraries
pip install requests psycopg2-binary
```

## Running Tests

### Option 1: Run All Tests (Recommended)

Run the complete comprehensive testing suite:

```bash
python run_all_tests.py
```

This will:
- Run all 4 test suites in sequence
- Generate individual test reports
- Generate a comprehensive consolidated report
- Display final results and recommendations

**Duration**: 15-20 minutes

### Option 2: Run Individual Test Suites

Run specific test categories:

```bash
# Security tests only
python run_all_tests.py --only-security

# API tests only
python run_all_tests.py --only-api

# Database checks only
python run_all_tests.py --only-database

# Performance benchmarks only
python run_all_tests.py --only-performance
```

### Option 3: Skip Specific Tests

Skip certain test categories:

```bash
# Run all except security tests
python run_all_tests.py --skip-security

# Run all except performance tests (faster)
python run_all_tests.py --skip-performance
```

### Option 4: Run Individual Scripts Directly

For more control, run test scripts individually:

```bash
# Security vulnerability testing
python tests/security_test.py

# API integration testing
python tests/test_api_integration.py

# Database consistency checks
python tests/check_db_consistency.py

# Performance benchmarking
python tests/test_performance.py
```

## Understanding Test Results

### Success Criteria

All tests must meet these criteria to proceed to Phase 2:

#### Security (CRITICAL)
- ✅ Zero SQL injection vulnerabilities
- ✅ Zero authentication bypass vulnerabilities
- ✅ Zero XSS vulnerabilities
- ✅ Rate limiting functional
- ✅ No sensitive data leaks

#### API Reliability (CRITICAL)
- ✅ 100% of valid requests succeed
- ✅ All invalid requests return proper error codes
- ✅ All endpoints have input validation

#### Database Integrity (CRITICAL)
- ✅ No orphaned records
- ✅ All foreign keys valid
- ✅ Phase 1 indexes exist

#### Performance (HIGH PRIORITY)
- ✅ Dashboard < 500ms (cached)
- ✅ Cache hit rate > 60%
- ✅ No N+1 query problems

### Exit Codes

- **0**: All tests passed ✅
- **1**: One or more tests failed ❌

## Test Reports

After running tests, the following reports are generated:

### Individual Reports

1. **SECURITY_TEST_REPORT.md** - Security vulnerability findings
2. **API_TEST_REPORT.md** - API endpoint test results
3. **DB_CONSISTENCY_REPORT.md** - Database integrity findings
4. **PERFORMANCE_TEST_REPORT.md** - Performance benchmark results

### Consolidated Report

**COMPREHENSIVE_TEST_REPORT.md** - Summary of all tests with actionable recommendations

## Common Issues & Solutions

### Issue 1: Backend Not Accessible

```
❌ Cannot connect to API: Connection refused
```

**Solution**:
```bash
# Check if backend is running
docker compose ps backend

# If not running, start it
docker compose up -d backend

# Check logs
docker compose logs backend -f
```

### Issue 2: Authentication Failed

```
❌ Authentication failed: 401
```

**Solution**:
```bash
# Create admin user if it doesn't exist
docker compose exec backend python -c "
from app.models.database import SessionLocal
from app.models.database import User
from app.utils.auth import get_password_hash

db = SessionLocal()
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

### Issue 3: Database Connection Failed

```
❌ Cannot connect to database: Connection refused
```

**Solution**:
```bash
# Check if postgres is running
docker compose ps postgres

# Verify database exists
docker compose exec postgres psql -U insurance_user -d telematics_db -c "\dt"
```

### Issue 4: Missing Indexes

```
⚠️  Missing 5 indexes: idx_telematics_events_driver_timestamp...
```

**Solution**:
```bash
# Run Phase 1 migration
docker compose exec postgres psql -U insurance_user -d telematics_db \
  -f /app/migrations/001_add_performance_indexes.sql
```

### Issue 5: Performance Tests Failing

```
❌ Dashboard Summary Response Time: Avg: 1.2s (Target: <0.5s)
```

**Possible causes**:
- Cache not warmed up (run tests again)
- Heavy database load (restart database)
- Indexes missing (run migrations)
- No test data (load sample data)

**Solution**:
```bash
# Restart backend to clear state
docker compose restart backend

# Wait 30 seconds for metrics collector to start
sleep 30

# Run performance tests again
python run_all_tests.py --only-performance
```

## Test Configuration

### Modifying Test Parameters

Edit configuration at the top of each test script:

**tests/security_test.py**:
```python
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
```

**tests/check_db_consistency.py**:
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'telematics_db',
    'user': 'insurance_user',
    'password': 'insurance_pass'
}
```

### Adjusting Performance Targets

Edit targets in **tests/test_performance.py**:

```python
TARGETS = {
    "dashboard_summary": 0.500,  # 500ms
    "driver_list": 1.000,  # 1s
    "trip_activity": 0.800,  # 800ms
    "risk_distribution": 0.600,  # 600ms
    "cache_hit_rate": 60.0  # 60%
}
```

## Continuous Testing

### Automated Testing Schedule

Run tests regularly to catch regressions:

```bash
# Daily quick check (skip performance tests for speed)
0 2 * * * cd /path/to/Auto-Insurance-System && python run_all_tests.py --skip-performance

# Weekly comprehensive test
0 3 * * 0 cd /path/to/Auto-Insurance-System && python run_all_tests.py
```

### Pre-Deployment Testing

Always run full test suite before deploying changes:

```bash
#!/bin/bash
# pre-deploy.sh

echo "Running comprehensive tests..."
python run_all_tests.py

if [ $? -eq 0 ]; then
    echo "✅ All tests passed. Ready to deploy."
    exit 0
else
    echo "❌ Tests failed. Fix issues before deploying."
    exit 1
fi
```

## Next Steps After Testing

### If All Tests Pass ✅

1. Review COMPREHENSIVE_TEST_REPORT.md for metrics
2. Proceed to Phase 2 - Cache Improvements
3. Maintain testing discipline for future changes

### If Tests Fail ❌

1. Review individual test reports for details
2. Fix critical issues first (security, data integrity)
3. Address performance issues
4. Re-run tests until all pass
5. Do NOT proceed to Phase 2 until tests pass

## Getting Help

If you encounter issues not covered in this guide:

1. Check Docker logs: `docker compose logs -f`
2. Review test output carefully
3. Check database connectivity: `docker compose exec postgres psql -U insurance_user -d telematics_db`
4. Verify all services are healthy: `docker compose ps`
5. Restart services if needed: `docker compose restart`

## Test Coverage Summary

### Security Tests (11 tests)
- SQL injection in search parameters
- SQL injection in filter parameters
- Access without authentication token
- Non-admin accessing admin endpoints
- JWT token tampering
- XSS in driver creation
- Oversized input handling
- Invalid data type handling
- Rate limiting
- Error message disclosure
- Password hash exposure

### API Tests (15+ tests)
- Dashboard stats, summary, trip activity, risk distribution
- Driver list, get, pagination, search
- User list, password security
- Policy summary, list
- Vehicle list
- Trip list
- Event stats

### Database Checks (17 tests)
- Orphaned trips, vehicles, devices, users, premiums, risk scores
- Invalid emails, negative distances, invalid trip times
- Invalid risk scores, negative premiums, future dates
- Phase 1 index verification
- Table statistics

### Performance Tests (8 tests)
- Dashboard summary response time
- Driver list response time
- Trip activity response time
- Risk distribution response time
- Cache hit rate
- Prometheus metrics availability
- Business metrics collection
- Concurrent request handling

---

**Total: 50+ comprehensive tests covering security, functionality, data integrity, and performance**
