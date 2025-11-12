# Comprehensive Testing & Security Audit Plan

**Date**: 2025-11-12
**Purpose**: Validate Phase 1 improvements, security hardening, and system reliability before Phase 2
**Estimated Duration**: 8-12 hours

---

## 1. Security Vulnerability Testing

### 1.1 SQL Injection Testing
**Target**: All database query endpoints (drivers, users, policies, trips, events)

**Test Cases**:
- [ ] Search parameters with SQL injection attempts (`' OR '1'='1`, `'; DROP TABLE--`)
- [ ] Query parameters with UNION-based injections
- [ ] Numeric parameters with arithmetic operations
- [ ] Filter parameters with boolean-based blind injection
- [ ] Verify SQLAlchemy ORM prevents raw SQL injection

**Tools**: Manual testing + `sqlmap` (if available)

### 1.2 Authentication & Authorization Testing
**Target**: All admin endpoints, user endpoints

**Test Cases**:
- [ ] Access admin endpoints without token (expect 401)
- [ ] Access admin endpoints with expired token (expect 401)
- [ ] Access admin endpoints with non-admin user token (expect 403)
- [ ] JWT token tampering (modify payload, expect rejection)
- [ ] Password brute-force protection (rate limiting)
- [ ] Session fixation attacks
- [ ] Horizontal privilege escalation (user accessing other user's data)
- [ ] Vertical privilege escalation (user accessing admin data)

### 1.3 Input Validation & XSS Testing
**Target**: All POST/PATCH endpoints accepting user input

**Test Cases**:
- [ ] XSS payloads in text fields (`<script>alert('XSS')</script>`)
- [ ] HTML injection in names, addresses, emails
- [ ] Command injection in search parameters
- [ ] Path traversal in file parameters (if any)
- [ ] Invalid data types (strings where integers expected)
- [ ] Oversized inputs (10MB strings, arrays with 100K items)
- [ ] Unicode/emoji injection
- [ ] NULL byte injection

### 1.4 API Rate Limiting & DoS Protection
**Test Cases**:
- [ ] Verify rate limits are enforced (429 Too Many Requests)
- [ ] Test rate limit bypass attempts (different IPs, headers)
- [ ] Large payload attacks (100MB JSON body)
- [ ] Slowloris-style attacks (slow request sending)
- [ ] Regex DoS in search parameters

### 1.5 Information Disclosure
**Test Cases**:
- [ ] Error messages don't reveal stack traces to users
- [ ] Database errors are generic (no schema info leaked)
- [ ] 404 responses don't reveal system info
- [ ] Password hashes never returned in API responses
- [ ] Sensitive data not logged (passwords, tokens)

---

## 2. API Endpoint Testing

### 2.1 Admin Dashboard Endpoints
```bash
# Base URL: /api/v1/admin/dashboard

GET /stats                      # System-wide statistics
GET /summary                    # 4 summary cards
GET /trip-activity?days=7       # Trip activity chart
GET /risk-distribution          # Risk pie chart
GET /safety-events-breakdown    # Safety events bar chart
GET /policy-type-distribution   # Policy type pie chart
```

**Test Cases for Each**:
- [ ] Success with valid admin token (200 OK)
- [ ] Failure without token (401 Unauthorized)
- [ ] Failure with non-admin token (403 Forbidden)
- [ ] Response schema validation (correct fields, types)
- [ ] Performance < 500ms (with cache)
- [ ] Edge case: empty database returns valid default values

### 2.2 Admin Drivers Endpoints
```bash
# Base URL: /api/v1/admin/drivers

GET /                           # List drivers
GET /{driver_id}                # Get driver (basic)
GET /{driver_id}/details        # Get driver (detailed)
POST /                          # Create driver
PATCH /{driver_id}              # Update driver
DELETE /{driver_id}             # Delete driver
```

**Test Cases**:
- [ ] List: pagination works (skip, limit)
- [ ] List: search filtering works
- [ ] List: returns enriched data (risk scores, policies)
- [ ] Get: 404 for non-existent driver
- [ ] Get: returns correct driver data
- [ ] Create: validates required fields
- [ ] Create: rejects duplicate driver_id
- [ ] Create: validates email format
- [ ] Update: partial updates work (exclude_unset)
- [ ] Update: validates data types
- [ ] Delete: removes driver successfully
- [ ] Delete: cascades or prevents (based on constraints)

### 2.3 Admin Users Endpoints
```bash
# Base URL: /api/v1/admin/users

GET /                           # List users
GET /{user_id}                  # Get user
POST /                          # Create user
PATCH /{user_id}                # Update user
DELETE /{user_id}               # Delete user
```

**Test Cases**:
- [ ] List: search by username/email works
- [ ] Create: password is hashed (never stored plain)
- [ ] Create: duplicate username/email rejected
- [ ] Update: password update hashes new password
- [ ] Delete: cannot delete own account (if admin)
- [ ] Response: hashed_password never exposed in API

### 2.4 Admin Policies Endpoints
```bash
# Base URL: /api/v1/admin/policies

GET /summary                    # Policy summary stats
GET /                           # List policies
```

**Test Cases**:
- [ ] Summary: correct calculations (revenue, savings)
- [ ] List: filtering by policy_type works
- [ ] List: search by driver name/policy_id works
- [ ] List: enriched data includes driver info
- [ ] List: discount percentages calculated correctly
- [ ] Edge case: handles missing policy_type column gracefully

### 2.5 Admin Resources Endpoints
```bash
# Base URL: /api/v1/admin

GET /vehicles                   # List vehicles
GET /vehicles/{id}              # Get vehicle
DELETE /vehicles/{id}           # Delete vehicle
GET /devices                    # List devices
GET /devices/{id}               # Get device
DELETE /devices/{id}            # Delete device
GET /trips                      # List trips
GET /trips/{id}                 # Get trip
DELETE /trips/{id}              # Delete trip
GET /events                     # List events
GET /events/stats               # Event statistics
```

**Test Cases**:
- [ ] All list endpoints: pagination works
- [ ] All list endpoints: driver_id filtering works
- [ ] Events: event_type filtering works
- [ ] Delete operations: verify cascade behavior
- [ ] Stats: correct aggregations

---

## 3. API Failure Scenarios

### 3.1 Invalid Input Testing
**Test Cases**:
- [ ] Negative pagination values (skip=-1, limit=-10)
- [ ] Excessive pagination (limit=999999)
- [ ] Invalid date formats
- [ ] Invalid email formats
- [ ] Missing required fields
- [ ] Extra unexpected fields
- [ ] Wrong data types (string instead of int)
- [ ] Empty strings where values required
- [ ] Null values where not allowed

### 3.2 Database Failure Scenarios
**Test Cases**:
- [ ] Database connection lost during request
- [ ] Transaction rollback on error
- [ ] Deadlock handling
- [ ] Connection pool exhaustion
- [ ] Query timeout handling

### 3.3 External Service Failures
**Test Cases**:
- [ ] Redis unavailable (graceful degradation)
- [ ] Kafka unavailable (queue errors handled)
- [ ] ML service unavailable (default risk scores)

---

## 4. Database Consistency Checks

### 4.1 Referential Integrity
```sql
-- Check orphaned records
SELECT COUNT(*) FROM trips WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
SELECT COUNT(*) FROM vehicles WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
SELECT COUNT(*) FROM devices WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
SELECT COUNT(*) FROM users WHERE driver_id IS NOT NULL AND driver_id NOT IN (SELECT driver_id FROM drivers);
SELECT COUNT(*) FROM premiums WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
SELECT COUNT(*) FROM risk_scores WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
```

### 4.2 Data Validation
```sql
-- Check for invalid data
SELECT COUNT(*) FROM drivers WHERE email NOT LIKE '%@%';
SELECT COUNT(*) FROM trips WHERE distance_miles < 0;
SELECT COUNT(*) FROM trips WHERE start_time > end_time;
SELECT COUNT(*) FROM risk_scores WHERE risk_score < 0 OR risk_score > 100;
SELECT COUNT(*) FROM premiums WHERE base_premium < 0 OR final_premium < 0;
```

### 4.3 Index Verification
```sql
-- Verify all Phase 1 indexes exist
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

---

## 5. Performance Regression Testing

### 5.1 Verify Phase 1 Improvements Are Active

**Metrics Collection**:
- [ ] Check `/metrics` endpoint is accessible
- [ ] Verify Prometheus metrics exist:
  - `cache_hits_total`, `cache_misses_total`
  - `db_connection_pool_size`, `db_connection_pool_checked_out`
  - `kafka_consumer_lag_messages`
  - `active_drivers_total`, `active_trips_total`
  - `events_per_second`, `average_risk_score`

**Query Performance**:
- [ ] Dashboard summary < 500ms
- [ ] Driver list (100 items) < 1s
- [ ] Trip activity (30 days) < 800ms
- [ ] Risk distribution < 600ms

### 5.2 Cache Hit Rate Verification
```bash
# Monitor cache performance
curl -s http://localhost:8000/metrics | grep cache_hits
curl -s http://localhost:8000/metrics | grep cache_misses

# Calculate hit rate (should be > 60% after warm-up)
# Hit Rate = cache_hits / (cache_hits + cache_misses) * 100
```

### 5.3 Database Index Usage
```sql
-- Verify indexes are being used
EXPLAIN ANALYZE
SELECT * FROM telematics_events
WHERE driver_id = 'DRV-0001'
ORDER BY timestamp DESC
LIMIT 100;

-- Should show "Index Scan using idx_telematics_events_driver_timestamp"
```

---

## 6. System Stress Testing

### 6.1 High Load Scenarios

**Test 1: Concurrent API Requests**
```bash
# 100 concurrent requests to dashboard
ab -n 1000 -c 100 -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/dashboard/summary
```

**Expected**:
- [ ] 95% of requests complete successfully
- [ ] No 500 errors
- [ ] Average response time < 2s
- [ ] No database connection pool exhaustion

**Test 2: Large Dataset Queries**
- [ ] Query 10,000+ trips (pagination works)
- [ ] Query 100,000+ events (no timeout)
- [ ] Export large datasets (memory doesn't spike)

**Test 3: Write Heavy Load**
- [ ] Create 100 drivers simultaneously
- [ ] Update 100 policies simultaneously
- [ ] Delete 100 trips simultaneously
- [ ] Verify no deadlocks or race conditions

### 6.2 Memory & Resource Monitoring
```bash
# Monitor during stress tests
docker stats backend

# Check for memory leaks
# Memory usage should stabilize, not grow indefinitely
```

---

## 7. Integration Testing (End-to-End)

### 7.1 Complete Driver Lifecycle
1. [ ] Admin creates new driver
2. [ ] System creates user account for driver
3. [ ] Driver logs in successfully
4. [ ] System records trips for driver
5. [ ] Risk score is calculated
6. [ ] Premium is generated based on risk
7. [ ] Admin views driver dashboard (all data present)
8. [ ] Admin updates driver info
9. [ ] Changes reflect in all related tables

### 7.2 Complete Trip Processing Flow
1. [ ] Telematics event arrives via Kafka
2. [ ] Event is consumed and stored
3. [ ] Trip is created/updated
4. [ ] Safety events are recorded
5. [ ] Risk score is recalculated
6. [ ] Premium is adjusted (if needed)
7. [ ] Dashboard metrics update
8. [ ] Prometheus metrics reflect changes

### 7.3 Cache Invalidation Flow
1. [ ] Request driver list (cache miss)
2. [ ] Request driver list again (cache hit)
3. [ ] Update a driver
4. [ ] Verify cache is invalidated
5. [ ] Request driver list (cache miss, fresh data)
6. [ ] Verify updated data is returned

---

## 8. Testing Tools & Scripts

### 8.1 Security Testing Script
Location: `tests/security_test.py`
- Automated SQL injection testing
- Auth bypass attempts
- XSS payload testing
- Rate limit verification

### 8.2 API Integration Tests
Location: `tests/test_api_integration.py`
- All admin endpoints
- Complete CRUD cycles
- Error scenarios
- Edge cases

### 8.3 Performance Benchmarks
Location: `tests/test_performance.py`
- Baseline measurements
- Compare with Phase 1 improvements
- Regression detection

### 8.4 Database Consistency Checker
Location: `tests/check_db_consistency.py`
- Referential integrity checks
- Data validation
- Index verification

---

## 9. Success Criteria

All tests must pass before proceeding to Phase 2:

### Security (CRITICAL)
- [ ] Zero SQL injection vulnerabilities
- [ ] Zero authentication bypass vulnerabilities
- [ ] Zero XSS vulnerabilities
- [ ] Rate limiting functional
- [ ] No sensitive data leaks

### API Reliability (CRITICAL)
- [ ] 100% of valid requests succeed
- [ ] All invalid requests return proper error codes
- [ ] All endpoints have input validation
- [ ] Error handling doesn't crash system

### Performance (HIGH PRIORITY)
- [ ] Dashboard loads < 500ms (cached)
- [ ] Cache hit rate > 60%
- [ ] Database indexes are used
- [ ] No N+1 query problems
- [ ] Metrics collection working

### System Stability (HIGH PRIORITY)
- [ ] No memory leaks
- [ ] Graceful degradation when services fail
- [ ] Database connections don't leak
- [ ] No deadlocks under load

### Data Integrity (HIGH PRIORITY)
- [ ] No orphaned records
- [ ] All foreign keys valid
- [ ] Data constraints enforced
- [ ] Transactions roll back on error

---

## 10. Testing Timeline

**Day 1 (4 hours)**:
- Security vulnerability testing (1-2)
- API endpoint testing (2.1-2.5)

**Day 2 (4 hours)**:
- API failure scenarios (3)
- Database consistency checks (4)
- Performance regression testing (5)

**Day 3 (2-4 hours)**:
- System stress testing (6)
- Integration testing (7)
- Generate testing report

---

## 11. Reporting

After all tests complete, generate a report with:
- Total tests run
- Pass/fail counts
- Critical vulnerabilities found
- Performance metrics (before/after)
- Recommendations for fixes

**Report Location**: `TESTING_REPORT.md`
