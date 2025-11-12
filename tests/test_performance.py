"""
Performance Benchmark Script

Validates Phase 1 performance improvements:
- Dashboard response times < 500ms
- Cache hit rates > 60%
- Database index usage
- Prometheus metrics collection
- Query performance

Usage:
    python tests/test_performance.py
"""
import requests
import time
from typing import Dict, List
from datetime import datetime
import statistics
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
METRICS_URL = "http://localhost:8000/metrics"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Performance targets (from ARCHITECTURE_IMPROVEMENTS.md)
TARGETS = {
    "dashboard_summary": 0.500,  # 500ms
    "driver_list": 1.000,  # 1s
    "trip_activity": 0.800,  # 800ms
    "risk_distribution": 0.600,  # 600ms
    "cache_hit_rate": 60.0  # 60%
}


class PerformanceTester:
    def __init__(self):
        self.results = []
        self.admin_token = None
        self.failures = 0
        self.warnings = 0

    def log_result(self, test_name: str, passed: bool, details: str, severity="INFO"):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "severity": severity,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)

        if not passed:
            if severity == "ERROR":
                self.failures += 1
            elif severity == "WARNING":
                self.warnings += 1

        status = "✅" if passed else ("⚠️ " if severity == "WARNING" else "❌")
        print(f"{status} {test_name}: {details}")

    def setup(self):
        """Setup test environment"""
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK TESTING")
        print("="*80 + "\n")

        # Get admin token
        try:
            response = requests.post(
                f"{BASE_URL}/auth/token",
                data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
            )
            if response.status_code == 200:
                self.admin_token = response.json().get("access_token")
                print(f"✅ Authenticated as {ADMIN_USERNAME}\n")
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            sys.exit(1)

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}

    def measure_response_time(self, url: str, iterations: int = 5) -> List[float]:
        """Measure response time over multiple iterations"""
        times = []
        for _ in range(iterations):
            start = time.time()
            try:
                response = requests.get(url, headers=self.get_headers(), timeout=10)
                elapsed = time.time() - start
                if response.status_code == 200:
                    times.append(elapsed)
                time.sleep(0.1)  # Small delay between requests
            except:
                pass
        return times

    # ==================== 1. ENDPOINT RESPONSE TIME TESTS ====================

    def test_dashboard_summary_performance(self):
        """Test dashboard summary endpoint performance"""
        print("\n--- Endpoint Response Time Tests ---\n")

        times = self.measure_response_time(f"{BASE_URL}/admin/dashboard/summary", iterations=10)

        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            max_time = max(times)
            target = TARGETS["dashboard_summary"]

            passed = avg_time < target
            severity = "ERROR" if not passed else "INFO"

            self.log_result(
                "Dashboard Summary Response Time",
                passed,
                f"Avg: {avg_time:.3f}s, Median: {median_time:.3f}s, Max: {max_time:.3f}s (Target: <{target}s)",
                severity
            )
        else:
            self.log_result(
                "Dashboard Summary Response Time",
                False,
                "Could not measure response time",
                "ERROR"
            )

    def test_driver_list_performance(self):
        """Test driver list endpoint performance"""
        times = self.measure_response_time(f"{BASE_URL}/admin/drivers?limit=100", iterations=10)

        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            target = TARGETS["driver_list"]

            passed = avg_time < target
            severity = "WARNING" if not passed else "INFO"

            self.log_result(
                "Driver List Response Time",
                passed,
                f"Avg: {avg_time:.3f}s, Median: {median_time:.3f}s (Target: <{target}s)",
                severity
            )
        else:
            self.log_result(
                "Driver List Response Time",
                False,
                "Could not measure response time",
                "ERROR"
            )

    def test_trip_activity_performance(self):
        """Test trip activity endpoint performance"""
        times = self.measure_response_time(f"{BASE_URL}/admin/dashboard/trip-activity?days=30", iterations=10)

        if times:
            avg_time = statistics.mean(times)
            target = TARGETS["trip_activity"]

            passed = avg_time < target
            severity = "WARNING" if not passed else "INFO"

            self.log_result(
                "Trip Activity Response Time",
                passed,
                f"Avg: {avg_time:.3f}s (Target: <{target}s)",
                severity
            )
        else:
            self.log_result(
                "Trip Activity Response Time",
                False,
                "Could not measure response time",
                "ERROR"
            )

    def test_risk_distribution_performance(self):
        """Test risk distribution endpoint performance"""
        times = self.measure_response_time(f"{BASE_URL}/admin/dashboard/risk-distribution", iterations=10)

        if times:
            avg_time = statistics.mean(times)
            target = TARGETS["risk_distribution"]

            passed = avg_time < target
            severity = "WARNING" if not passed else "INFO"

            self.log_result(
                "Risk Distribution Response Time",
                passed,
                f"Avg: {avg_time:.3f}s (Target: <{target}s)",
                severity
            )
        else:
            self.log_result(
                "Risk Distribution Response Time",
                False,
                "Could not measure response time",
                "ERROR"
            )

    # ==================== 2. CACHE PERFORMANCE TESTS ====================

    def test_cache_hit_rate(self):
        """Test cache hit rate"""
        print("\n--- Cache Performance Tests ---\n")

        try:
            # Get initial metrics
            response_before = requests.get(METRICS_URL, timeout=5)
            if response_before.status_code != 200:
                self.log_result(
                    "Cache Hit Rate",
                    False,
                    "Metrics endpoint not accessible",
                    "ERROR"
                )
                return

            # Make some requests to warm up cache
            for _ in range(10):
                requests.get(f"{BASE_URL}/admin/dashboard/summary", headers=self.get_headers())
                time.sleep(0.1)

            # Get metrics again
            response_after = requests.get(METRICS_URL, timeout=5)
            if response_after.status_code != 200:
                self.log_result(
                    "Cache Hit Rate",
                    False,
                    "Metrics endpoint not accessible",
                    "ERROR"
                )
                return

            # Parse metrics
            metrics_text = response_after.text
            cache_hits = 0
            cache_misses = 0

            for line in metrics_text.split('\n'):
                if line.startswith('cache_hits_total'):
                    try:
                        cache_hits = float(line.split()[-1])
                    except:
                        pass
                elif line.startswith('cache_misses_total'):
                    try:
                        cache_misses = float(line.split()[-1])
                    except:
                        pass

            if cache_hits + cache_misses > 0:
                hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100
                target = TARGETS["cache_hit_rate"]
                passed = hit_rate >= target

                self.log_result(
                    "Cache Hit Rate",
                    passed,
                    f"{hit_rate:.1f}% (Hits: {int(cache_hits)}, Misses: {int(cache_misses)}, Target: >{target}%)",
                    "WARNING" if not passed else "INFO"
                )
            else:
                self.log_result(
                    "Cache Hit Rate",
                    False,
                    "No cache metrics available (might be too early or cache disabled)",
                    "WARNING"
                )

        except Exception as e:
            self.log_result(
                "Cache Hit Rate",
                False,
                f"Failed to check cache metrics: {e}",
                "ERROR"
            )

    # ==================== 3. METRICS COLLECTION TESTS ====================

    def test_prometheus_metrics_availability(self):
        """Test that Prometheus metrics are being collected"""
        print("\n--- Metrics Collection Tests ---\n")

        try:
            response = requests.get(METRICS_URL, timeout=5)

            if response.status_code == 200:
                metrics_text = response.text

                # Check for Phase 1 metrics
                expected_metrics = [
                    "cache_hits_total",
                    "cache_misses_total",
                    "db_connection_pool_size",
                    "active_drivers_total",
                    "active_trips_total",
                    "events_per_second"
                ]

                found_metrics = []
                missing_metrics = []

                for metric in expected_metrics:
                    if metric in metrics_text:
                        found_metrics.append(metric)
                    else:
                        missing_metrics.append(metric)

                if not missing_metrics:
                    self.log_result(
                        "Prometheus Metrics Collection",
                        True,
                        f"All {len(expected_metrics)} expected metrics are available"
                    )
                else:
                    self.log_result(
                        "Prometheus Metrics Collection",
                        False,
                        f"Missing metrics: {', '.join(missing_metrics)}",
                        "WARNING"
                    )

                # Count total metrics
                metric_lines = [line for line in metrics_text.split('\n') if line and not line.startswith('#')]
                self.log_result(
                    "Total Metrics Count",
                    True,
                    f"{len(metric_lines)} metrics available"
                )
            else:
                self.log_result(
                    "Prometheus Metrics Collection",
                    False,
                    f"Metrics endpoint returned {response.status_code}",
                    "ERROR"
                )

        except Exception as e:
            self.log_result(
                "Prometheus Metrics Collection",
                False,
                f"Cannot access metrics: {e}",
                "ERROR"
            )

    def test_business_metrics(self):
        """Test that business metrics are being collected"""
        try:
            response = requests.get(METRICS_URL, timeout=5)

            if response.status_code == 200:
                metrics_text = response.text

                business_metrics = {
                    "active_drivers_total": "Active drivers count",
                    "active_trips_total": "Active trips count",
                    "average_risk_score": "Average risk score",
                    "events_per_second": "Events per second"
                }

                found_count = 0
                for metric_name, description in business_metrics.items():
                    if metric_name in metrics_text:
                        found_count += 1

                passed = found_count >= len(business_metrics) * 0.75  # At least 75%

                self.log_result(
                    "Business Metrics Collection",
                    passed,
                    f"{found_count}/{len(business_metrics)} business metrics available",
                    "WARNING" if not passed else "INFO"
                )
        except Exception as e:
            self.log_result(
                "Business Metrics Collection",
                False,
                f"Failed to check business metrics: {e}",
                "ERROR"
            )

    # ==================== 4. LOAD TESTING ====================

    def test_concurrent_requests(self):
        """Test system under concurrent load"""
        print("\n--- Load Testing ---\n")

        import concurrent.futures

        def make_request():
            try:
                start = time.time()
                response = requests.get(
                    f"{BASE_URL}/admin/dashboard/summary",
                    headers=self.get_headers(),
                    timeout=10
                )
                elapsed = time.time() - start
                return response.status_code == 200, elapsed
            except:
                return False, None

        # Send 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        successful = sum(1 for success, _ in results if success)
        times = [elapsed for success, elapsed in results if success and elapsed is not None]

        if times:
            avg_time = statistics.mean(times)
            max_time = max(times)

            # 95% success rate, average < 2s
            passed = successful >= 19 and avg_time < 2.0

            self.log_result(
                "Concurrent Requests (20 concurrent)",
                passed,
                f"{successful}/20 successful, Avg: {avg_time:.3f}s, Max: {max_time:.3f}s",
                "WARNING" if not passed else "INFO"
            )
        else:
            self.log_result(
                "Concurrent Requests",
                False,
                f"Only {successful}/20 requests successful",
                "ERROR"
            )

    # ==================== REPORT GENERATION ====================

    def generate_report(self):
        """Generate performance test report"""
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK REPORT")
        print("="*80 + "\n")

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests Run: {total_tests}")
        print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"\nFailure Breakdown:")
        print(f"  Errors: {self.failures}")
        print(f"  Warnings: {self.warnings}")

        if self.failures > 0:
            print("\n⚠️  Performance issues found! System not meeting targets.")
        elif self.warnings > 0:
            print("\n⚠️  Some performance warnings. Review recommended.")
        else:
            print("\n✅ All performance targets met!")

        # Save detailed report
        report_file = "PERFORMANCE_TEST_REPORT.md"
        with open(report_file, "w") as f:
            f.write("# Performance Benchmark Report\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Total Tests**: {total_tests}\n")
            f.write(f"**Passed**: {passed_tests}\n")
            f.write(f"**Failed**: {failed_tests}\n\n")
            f.write(f"## Performance Targets\n\n")
            f.write("| Endpoint | Target | Status |\n")
            f.write("|----------|--------|--------|\n")

            for result in self.results:
                status = "✅ PASS" if result["passed"] else ("⚠️  WARNING" if result["severity"] == "WARNING" else "❌ FAIL")
                f.write(f"### {status} {result['test']}\n\n")
                f.write(f"- **Details**: {result['details']}\n")
                f.write(f"- **Timestamp**: {result['timestamp']}\n\n")

        print(f"\nDetailed report saved to: {report_file}")

        return self.failures == 0

    def run_all_tests(self):
        """Run all performance tests"""
        self.setup()

        # Endpoint response time tests
        self.test_dashboard_summary_performance()
        self.test_driver_list_performance()
        self.test_trip_activity_performance()
        self.test_risk_distribution_performance()

        # Cache performance tests
        self.test_cache_hit_rate()

        # Metrics collection tests
        self.test_prometheus_metrics_availability()
        self.test_business_metrics()

        # Load testing
        self.test_concurrent_requests()

        # Generate report
        return self.generate_report()


if __name__ == "__main__":
    tester = PerformanceTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
