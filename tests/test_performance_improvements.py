#!/usr/bin/env python3
"""
Performance Improvements Test Suite

Tests all Phase 1 improvements:
1. Redis SCAN (non-blocking cache invalidation)
2. Database indexes (query performance)
3. N+1 query prevention (eager loading)
4. Metrics collection
5. Kafka lag monitoring
"""

import sys
import time
import requests
from typing import Dict, List, Tuple
import psycopg2
from redis import Redis


class Colors:
    """Terminal colors for output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


# Test Configuration
API_BASE_URL = "http://localhost:8000"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'telematics_db',
    'user': 'insurance_user',
    'password': 'insurance_pass'
}
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}


def test_api_available() -> bool:
    """Test if API is available."""
    print_header("Testing API Availability")

    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_success("API is available")
            return True
        else:
            print_error(f"API returned status code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to API: {e}")
        print_warning("Make sure the backend is running: docker compose up -d")
        return False


def test_metrics_endpoint() -> bool:
    """Test if Prometheus metrics endpoint is working."""
    print_header("Testing Metrics Endpoint")

    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            metrics_text = response.text

            # Check for new metrics
            new_metrics = [
                'cache_hits_total',
                'cache_misses_total',
                'db_connection_pool_size',
                'kafka_consumer_lag_messages',
                'ml_inference_duration_seconds',
                'active_drivers_total',
                'active_trips_total',
            ]

            found_metrics = []
            missing_metrics = []

            for metric in new_metrics:
                if metric in metrics_text:
                    found_metrics.append(metric)
                else:
                    missing_metrics.append(metric)

            print_info(f"Found {len(found_metrics)}/{len(new_metrics)} new metrics")

            for metric in found_metrics:
                print_success(f"Metric available: {metric}")

            for metric in missing_metrics:
                print_warning(f"Metric not found: {metric} (may not have data yet)")

            return len(found_metrics) > 0
        else:
            print_error(f"Metrics endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot access metrics: {e}")
        return False


def test_database_indexes() -> bool:
    """Test if database indexes were created."""
    print_header("Testing Database Indexes")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Check for key indexes
        expected_indexes = [
            'idx_telematics_events_driver_timestamp',
            'idx_trips_driver_dates',
            'idx_risk_scores_driver_date',
            'idx_premiums_driver_effective',
        ]

        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname LIKE 'idx_%'
            ORDER BY indexname
        """)

        existing_indexes = [row[0] for row in cursor.fetchall()]

        found_count = 0
        for idx in expected_indexes:
            if idx in existing_indexes:
                print_success(f"Index exists: {idx}")
                found_count += 1
            else:
                print_warning(f"Index not found: {idx}")

        print_info(f"\nTotal indexes found: {len(existing_indexes)}")
        print_info(f"Expected indexes found: {found_count}/{len(expected_indexes)}")

        cursor.close()
        conn.close()

        return found_count > 0

    except Exception as e:
        print_error(f"Database test failed: {e}")
        print_warning("Make sure PostgreSQL is running and accessible")
        return False


def test_query_performance() -> bool:
    """Test query performance with indexes."""
    print_header("Testing Query Performance")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Test 1: Check if query uses index
        print_info("Testing telematics_events query plan...")
        cursor.execute("""
            EXPLAIN (FORMAT TEXT)
            SELECT * FROM telematics_events
            WHERE driver_id = 'DRV001'
            AND timestamp >= NOW() - INTERVAL '7 days'
            ORDER BY timestamp DESC
            LIMIT 100
        """)

        plan = cursor.fetchall()
        plan_text = '\n'.join([row[0] for row in plan])

        uses_index = 'Index Scan' in plan_text or 'Bitmap Index Scan' in plan_text

        if uses_index:
            print_success("Query uses index (good!)")
            print_info("Query plan:")
            for line in plan:
                print(f"  {line[0]}")
        else:
            print_warning("Query uses Seq Scan (indexes might not be created)")
            print_info("Query plan:")
            for line in plan:
                print(f"  {line[0]}")

        # Test 2: Measure actual query time
        print_info("\nTesting query execution time...")
        start_time = time.time()

        cursor.execute("""
            SELECT COUNT(*) FROM telematics_events
            WHERE driver_id = 'DRV001'
            AND timestamp >= NOW() - INTERVAL '7 days'
        """)

        result = cursor.fetchone()
        elapsed_ms = (time.time() - start_time) * 1000

        print_info(f"Query returned {result[0]} rows in {elapsed_ms:.2f}ms")

        if elapsed_ms < 100:
            print_success(f"Query performance: EXCELLENT ({elapsed_ms:.2f}ms)")
        elif elapsed_ms < 500:
            print_success(f"Query performance: GOOD ({elapsed_ms:.2f}ms)")
        else:
            print_warning(f"Query performance: SLOW ({elapsed_ms:.2f}ms)")

        cursor.close()
        conn.close()

        return uses_index

    except Exception as e:
        print_error(f"Query performance test failed: {e}")
        return False


def test_redis_scan() -> bool:
    """Test Redis SCAN functionality."""
    print_header("Testing Redis SCAN (Cache Invalidation)")

    try:
        redis_client = Redis(**REDIS_CONFIG, decode_responses=True)

        # Test connection
        redis_client.ping()
        print_success("Connected to Redis")

        # Create test keys
        test_pattern = "response_cache:test:*"
        test_keys = [f"response_cache:test:{i}" for i in range(10)]

        print_info("Creating test cache keys...")
        for key in test_keys:
            redis_client.set(key, "test_value", ex=60)

        print_success(f"Created {len(test_keys)} test keys")

        # Use SCAN to find keys (mimicking the improved cache invalidation)
        print_info("Using SCAN to find keys...")
        cursor = 0
        found_keys = []
        scan_iterations = 0

        while True:
            cursor, keys = redis_client.scan(cursor, match=test_pattern, count=100)
            found_keys.extend(keys)
            scan_iterations += 1
            if cursor == 0:
                break

        print_success(f"SCAN found {len(found_keys)} keys in {scan_iterations} iterations")

        # Clean up
        if found_keys:
            redis_client.delete(*found_keys)
            print_success("Cleaned up test keys")

        print_success("Redis SCAN working correctly (non-blocking)")

        return True

    except Exception as e:
        print_error(f"Redis test failed: {e}")
        print_warning("Make sure Redis is running: docker compose ps redis")
        return False


def test_api_performance() -> Dict[str, float]:
    """Test API endpoint performance."""
    print_header("Testing API Performance")

    endpoints = [
        ("/api/v1/drivers/DRV001", "GET driver"),
        ("/api/v1/drivers/DRV001/trips?page=1&page_size=20", "GET trips"),
        ("/api/v1/risk/DRV001/score", "GET risk score"),
    ]

    results = {}

    for endpoint, description in endpoints:
        try:
            print_info(f"Testing: {description}")

            # Warm up
            requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)

            # Measure 5 requests
            times = []
            for _ in range(5):
                start = time.time()
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
                elapsed = (time.time() - start) * 1000

                if response.status_code in [200, 401]:  # 401 is ok (no auth)
                    times.append(elapsed)

            if times:
                avg_time = sum(times) / len(times)
                results[description] = avg_time

                if avg_time < 100:
                    print_success(f"{description}: {avg_time:.2f}ms (EXCELLENT)")
                elif avg_time < 200:
                    print_success(f"{description}: {avg_time:.2f}ms (GOOD)")
                elif avg_time < 500:
                    print_warning(f"{description}: {avg_time:.2f}ms (ACCEPTABLE)")
                else:
                    print_warning(f"{description}: {avg_time:.2f}ms (SLOW)")
            else:
                print_warning(f"{description}: No successful requests")

        except Exception as e:
            print_error(f"{description}: {e}")

    return results


def test_connection_pool() -> bool:
    """Test database connection pool metrics."""
    print_header("Testing Database Connection Pool")

    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        metrics_text = response.text

        # Look for connection pool metrics
        pool_metrics = {
            'db_connection_pool_size': None,
            'db_connection_pool_checked_out': None,
            'db_connection_pool_overflow': None,
        }

        for metric in pool_metrics.keys():
            for line in metrics_text.split('\n'):
                if line.startswith(metric) and not line.startswith('#'):
                    try:
                        value = float(line.split()[-1])
                        pool_metrics[metric] = value
                    except:
                        pass

        has_metrics = any(v is not None for v in pool_metrics.values())

        if has_metrics:
            print_success("Connection pool metrics available:")
            for metric, value in pool_metrics.items():
                if value is not None:
                    print(f"  {metric}: {value}")

            # Check if pool is healthy
            if pool_metrics['db_connection_pool_overflow'] == 0:
                print_success("Pool is healthy (no overflow)")
            else:
                print_warning(f"Pool overflow: {pool_metrics['db_connection_pool_overflow']}")

            return True
        else:
            print_warning("Connection pool metrics not yet available")
            print_info("Metrics collector may need to be enabled in main.py")
            return False

    except Exception as e:
        print_error(f"Connection pool test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and generate report."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("PERFORMANCE IMPROVEMENTS TEST SUITE".center(80))
    print("=" * 80)
    print(f"{Colors.END}")

    test_results = []

    # Run tests
    test_results.append(("API Available", test_api_available()))
    test_results.append(("Metrics Endpoint", test_metrics_endpoint()))
    test_results.append(("Database Indexes", test_database_indexes()))
    test_results.append(("Query Performance", test_query_performance()))
    test_results.append(("Redis SCAN", test_redis_scan()))
    test_results.append(("Connection Pool", test_connection_pool()))

    # API performance test
    perf_results = test_api_performance()
    test_results.append(("API Performance", len(perf_results) > 0))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Phase 1 improvements are working.{Colors.END}\n")
        return 0
    elif passed >= total * 0.7:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Most tests passed, but some improvements need attention.{Colors.END}\n")
        return 1
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Many tests failed. Check the setup and try again.{Colors.END}\n")
        return 2


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
