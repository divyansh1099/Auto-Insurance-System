# Phase 2 Optimization Plan - Using Existing Infrastructure

**Status**: Ready to implement
**Infrastructure**: ✅ Already in place (Redis client, cache decorator, metrics)
**Focus**: Apply existing caching layer + query optimization

---

## Current Infrastructure Analysis

### ✅ Already Implemented

1. **Redis Client** (`app/services/redis_client.py`)
   - Connection pooling (max 50 connections)
   - Settings: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`
   - Functions: `cache_risk_score()`, `cache_driver_statistics()`, `get_cached_risk_score()`
   - Metrics integrated: `redis_operations_total`, `redis_operation_duration_seconds`

2. **Cache Decorator** (`app/utils/cache.py`)
   - `@cache_response(ttl=300, key_prefix="cache")` decorator
   - Async-compatible
   - Auto cache key generation from request path + query params
   - Pattern: `response_cache:{md5_hash}`
   - Invalidation: `invalidate_cache_pattern(pattern)` using SCAN

3. **Metrics** (`app/utils/metrics.py`)
   - Prometheus integration already configured
   - Redis operation metrics already tracking

### ❌ Not Yet Applied

1. **No endpoints use `@cache_response` decorator** - Ready to apply!
2. **Cache invalidation not triggered on updates** - Need to add
3. **Cache hit rate not exposed** - Need to add metric
4. **N+1 queries present** - Need to optimize

---

## Step-by-Step Optimization Plan

### Phase 2A: Apply Existing Cache Decorator (Week 1)

#### Day 1-2: Dashboard Endpoints Caching

**File**: `src/backend/app/routers/admin/dashboard.py`

**Add this import**:
```python
from app.utils.cache import cache_response
```

**Apply to these endpoints** (Already tested at 17-30ms, cache will make <5ms):

1. **`/admin/dashboard/stats`** - TTL: 60s
```python
@router.get("/stats")
@cache_response(ttl=60, key_prefix="dashboard_stats")
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing code unchanged
```

2. **`/admin/dashboard/summary`** - TTL: 60s
```python
@router.get("/summary", response_model=AdminDashboardSummary)
@cache_response(ttl=60, key_prefix="dashboard_summary")
async def get_admin_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing code unchanged
```

3. **`/admin/dashboard/trip-activity`** - TTL: 300s (5 min)
```python
@router.get("/trip-activity", response_model=List[DailyTripActivity])
@cache_response(ttl=300, key_prefix="trip_activity")
async def get_trip_activity(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing code unchanged
```

4. **`/admin/dashboard/risk-distribution`** - TTL: 300s
```python
@router.get("/risk-distribution", response_model=List[RiskDistributionResponse])
@cache_response(ttl=300, key_prefix="risk_distribution")
async def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing code unchanged
```

5. **`/admin/dashboard/safety-events`** - TTL: 300s
```python
@router.get("/safety-events", response_model=List[SafetyEventBreakdown])
@cache_response(ttl=300, key_prefix="safety_events")
async def get_safety_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing code unchanged
```

**Expected Impact**:
- Dashboard load time: 17ms → **<5ms** (3-4x improvement)
- Database queries reduced by 60-70%
- Cache hit rate: >80% after warm-up

---

#### Day 3: Driver Endpoints Caching

**File**: `src/backend/app/routers/admin/drivers.py`

**Import**:
```python
from app.utils.cache import cache_response
```

**Apply to**:

1. **List drivers** - TTL: 120s
```python
@router.get("", response_model=List[DriverResponse])
@cache_response(ttl=120, key_prefix="drivers_list")
async def list_drivers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing code
```

2. **Get driver details** - TTL: 180s
```python
@router.get("/{driver_id}", response_model=DriverResponse)
@cache_response(ttl=180, key_prefix="driver_detail")
async def get_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing code
```

---

#### Day 4: Add Cache Invalidation on Updates

**File**: `src/backend/app/routers/admin/drivers.py`

**Import**:
```python
from app.utils.cache import invalidate_cache_pattern
```

**Invalidate on driver update**:
```python
@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    driver_update: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing update logic...

    # AFTER successful update, add:
    # Invalidate driver-specific caches
    invalidate_cache_pattern(f"*driver_detail*{driver_id}*")
    invalidate_cache_pattern("*drivers_list*")
    invalidate_cache_pattern("*dashboard_*")  # Dashboard includes driver counts

    return updated_driver
```

**Invalidate on driver creation**:
```python
@router.post("", response_model=DriverResponse, status_code=201)
async def create_driver(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Existing creation logic...

    # AFTER successful creation, add:
    invalidate_cache_pattern("*drivers_list*")
    invalidate_cache_pattern("*dashboard_*")

    return new_driver
```

---

#### Day 5: Add Cache Hit Rate Metrics

**File**: `src/backend/app/utils/metrics.py`

**Add new metrics**:
```python
# Cache hit/miss metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['endpoint', 'key_prefix']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['endpoint', 'key_prefix']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage',
    ['key_prefix']
)
```

**Update**: `src/backend/app/utils/cache.py`

**Modify the decorator to track metrics**:
```python
def cache_response(ttl: int = 300, key_prefix: str = "cache"):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # ... existing cache key generation ...

            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_response = redis_client.get(full_cache_key)
                    if cached_response:
                        logger.debug("cache_hit", key=full_cache_key)
                        # ADD METRIC:
                        from app.utils.metrics import cache_hits_total
                        cache_hits_total.labels(
                            endpoint=func.__name__,
                            key_prefix=key_prefix
                        ).inc()
                        return json.loads(cached_response)
                    else:
                        # ADD METRIC:
                        from app.utils.metrics import cache_misses_total
                        cache_misses_total.labels(
                            endpoint=func.__name__,
                            key_prefix=key_prefix
                        ).inc()
                except Exception as e:
                    logger.warning("cache_read_error", error=str(e))

            # ... rest of existing code ...
```

**Expose metrics at** `/metrics` (already configured)

**View in Prometheus**:
```promql
# Cache hit rate by endpoint
sum(rate(cache_hits_total[5m])) by (key_prefix) /
(sum(rate(cache_hits_total[5m])) by (key_prefix) + sum(rate(cache_misses_total[5m])) by (key_prefix))
```

---

### Phase 2B: Query Optimization (Week 2)

#### Day 6-7: Eliminate N+1 Queries

**Check for N+1 patterns**:
```bash
# Enable SQL logging temporarily
# In src/backend/app/main.py, add:
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**Common N+1 pattern to fix**:

**File**: `src/backend/app/routers/admin/drivers.py`

**Before** (N+1 query):
```python
@router.get("")
async def list_drivers(...):
    drivers = db.query(Driver).offset(skip).limit(limit).all()
    # Each driver.vehicle access triggers a query!
    return drivers
```

**After** (Optimized with joinedload):
```python
from sqlalchemy.orm import joinedload

@router.get("")
async def list_drivers(...):
    drivers = db.query(Driver)\
        .options(joinedload(Driver.vehicle))\
        .options(joinedload(Driver.risk_scores))\
        .offset(skip)\
        .limit(limit)\
        .all()
    return drivers
```

**Check driver model relationships**:
```bash
# Find what relationships exist
grep -A5 "relationship(" src/backend/app/models/database.py
```

---

#### Day 8: Add Pagination to Large Result Sets

**File**: `src/backend/app/routers/admin/drivers.py`

**Improve pagination**:
```python
@router.get("", response_model=DriverListResponse)
@cache_response(ttl=120, key_prefix="drivers_list")
async def list_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Get total count (cached separately if needed)
    total = db.query(func.count(Driver.driver_id)).scalar()

    # Get paginated results with eager loading
    drivers = db.query(Driver)\
        .options(joinedload(Driver.vehicle))\
        .offset(skip)\
        .limit(limit)\
        .all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "drivers": drivers
    }
```

---

#### Day 9: Optimize Expensive Aggregations

**File**: `src/backend/app/routers/admin/dashboard.py`

**Before** (Multiple separate queries):
```python
async def get_admin_dashboard_summary(...):
    total_drivers = db.query(func.count(Driver.driver_id)).scalar()
    total_trips = db.query(func.count(Trip.trip_id)).scalar()
    # ... etc
```

**After** (Single query with subqueries):
```python
async def get_admin_dashboard_summary(...):
    # Use a single query with multiple aggregations
    summary = db.query(
        func.count(distinct(Driver.driver_id)).label('total_drivers'),
        func.count(distinct(Trip.trip_id)).label('total_trips'),
        func.count(distinct(Vehicle.vehicle_id)).label('total_vehicles'),
        func.avg(RiskScore.risk_score).label('avg_risk_score')
    ).outerjoin(Trip, Driver.driver_id == Trip.driver_id)\
     .outerjoin(Vehicle, Driver.driver_id == Vehicle.driver_id)\
     .outerjoin(RiskScore, Driver.driver_id == RiskScore.driver_id)\
     .first()

    return {
        "total_drivers": summary.total_drivers,
        "total_trips": summary.total_trips,
        # ... etc
    }
```

---

#### Day 10: Testing & Documentation

**Test Plan**:
```bash
# 1. Run existing tests
python run_all_tests.py

# 2. Load test with cache
ab -n 1000 -c 10 http://localhost:8000/api/v1/admin/dashboard/summary

# 3. Check cache hit rate
curl http://localhost:8000/metrics | grep cache_hit

# 4. Verify query count reduction
# Compare SQL logs before/after
```

**Document changes** in Phase 2 completion report

---

## Expected Results

### Performance Targets

| Endpoint | Current | With Cache | Improvement |
|----------|---------|------------|-------------|
| Dashboard Summary | 17ms | **<5ms** | **70% faster** |
| Driver List | 30ms | **<10ms** | **67% faster** |
| Trip Activity | 19ms | **<6ms** | **68% faster** |
| Driver Details | ~40ms | **<12ms** | **70% faster** |

### System Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Cache Hit Rate | N/A | >80% | `cache_hits_total/(cache_hits_total+cache_misses_total)` |
| DB Queries/min | ~100 | <40 | SQL logging + count |
| Redis Ops/sec | ~10 | ~50 | `redis_operations_total` |
| Memory Usage | 200MB | <600MB | Docker stats |

---

## Implementation Checklist

### Week 1: Caching
- [ ] Day 1: Add `@cache_response` to dashboard endpoints (5 endpoints)
- [ ] Day 2: Test dashboard caching, verify metrics
- [ ] Day 3: Add caching to driver endpoints (2 endpoints)
- [ ] Day 4: Add cache invalidation on updates (2 update endpoints)
- [ ] Day 5: Add cache hit rate metrics, verify in Prometheus

### Week 2: Query Optimization
- [ ] Day 6: Enable SQL logging, identify N+1 queries
- [ ] Day 7: Fix N+1 queries with `joinedload()`, `selectinload()`
- [ ] Day 8: Improve pagination, add total counts
- [ ] Day 9: Optimize dashboard aggregations
- [ ] Day 10: Full testing, documentation, completion report

---

## Files to Modify

1. `src/backend/app/routers/admin/dashboard.py` - Add 5 cache decorators
2. `src/backend/app/routers/admin/drivers.py` - Add 2 cache decorators + invalidation
3. `src/backend/app/utils/cache.py` - Add cache hit/miss metrics
4. `src/backend/app/utils/metrics.py` - Define cache metrics
5. `src/backend/app/routers/admin/drivers.py` - Query optimization

**Total**: 5 files to modify (all existing files)

---

## Risks & Mitigations

| Risk | Mitigation | Status |
|------|------------|--------|
| Cache stampede | Use existing connection pool (max 50) | ✅ In place |
| Stale data | TTL values tuned per endpoint (60-300s) | ✅ Planned |
| Memory exhaustion | Redis maxmemory policy (LRU) in docker-compose | ⚠️ Check config |
| Invalidation issues | Use SCAN-based pattern matching | ✅ In place |

---

## How to Start

```bash
# 1. Verify Redis is running
docker compose ps redis

# 2. Check Redis connectivity
docker compose logs redis

# 3. Test existing cache decorator manually
# Add to any endpoint and observe behavior

# 4. Start with Day 1 tasks
# Modify: src/backend/app/routers/admin/dashboard.py
```

---

**Ready to implement?** Start with Day 1: Dashboard endpoints caching.

**Questions?** All infrastructure is already in place - just need to apply the decorators!
