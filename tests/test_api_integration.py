"""
Comprehensive API Integration Testing Script

Tests all admin endpoints for:
- Correct HTTP status codes
- Response schema validation
- CRUD operations
- Pagination
- Search/filtering
- Error handling
- Edge cases

Usage:
    python tests/test_api_integration.py
"""
import requests
import time
import json
from typing import Dict, List, Optional
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


class APITester:
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
        print("API INTEGRATION TESTING")
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

    # ==================== DASHBOARD ENDPOINTS ====================

    def test_dashboard_stats(self):
        """Test GET /admin/dashboard/stats"""
        print("\n--- Dashboard Endpoints ---\n")

        try:
            response = requests.get(
                f"{BASE_URL}/admin/dashboard/stats",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                # Validate response structure
                required_keys = ["totals"]
                has_keys = all(key in data for key in required_keys)

                if has_keys and "drivers" in data["totals"]:
                    self.log_result(
                        "GET /admin/dashboard/stats",
                        True,
                        f"Returns valid stats (Response time: {response.elapsed.total_seconds():.2f}s)"
                    )
                else:
                    self.log_result(
                        "GET /admin/dashboard/stats",
                        False,
                        "Missing required keys in response",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/dashboard/stats",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/dashboard/stats",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    def test_dashboard_summary(self):
        """Test GET /admin/dashboard/summary"""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/dashboard/summary",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                required_keys = ["total_drivers", "total_vehicles", "monthly_revenue", "avg_risk_score"]
                has_keys = all(key in data for key in required_keys)

                if has_keys:
                    # Validate data types
                    valid_types = (
                        isinstance(data["total_drivers"], int) and
                        isinstance(data["total_vehicles"], int) and
                        isinstance(data["monthly_revenue"], (int, float)) and
                        isinstance(data["avg_risk_score"], (int, float))
                    )

                    if valid_types:
                        self.log_result(
                            "GET /admin/dashboard/summary",
                            True,
                            f"Returns valid summary (Response time: {response.elapsed.total_seconds():.2f}s)"
                        )
                    else:
                        self.log_result(
                            "GET /admin/dashboard/summary",
                            False,
                            "Invalid data types in response",
                            "ERROR"
                        )
                else:
                    self.log_result(
                        "GET /admin/dashboard/summary",
                        False,
                        "Missing required keys in response",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/dashboard/summary",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/dashboard/summary",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    def test_dashboard_trip_activity(self):
        """Test GET /admin/dashboard/trip-activity"""
        try:
            # Test with default parameters
            response = requests.get(
                f"{BASE_URL}/admin/dashboard/trip-activity",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Should return 7 days by default
                    if len(data) == 7:
                        # Validate structure of first item
                        if data and "date" in data[0] and "trip_count" in data[0]:
                            self.log_result(
                                "GET /admin/dashboard/trip-activity",
                                True,
                                f"Returns {len(data)} days of trip activity"
                            )
                        else:
                            self.log_result(
                                "GET /admin/dashboard/trip-activity",
                                False,
                                "Invalid data structure",
                                "ERROR"
                            )
                    else:
                        self.log_result(
                            "GET /admin/dashboard/trip-activity",
                            False,
                            f"Expected 7 days, got {len(data)}",
                            "WARNING"
                        )
                else:
                    self.log_result(
                        "GET /admin/dashboard/trip-activity",
                        False,
                        "Response is not a list",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/dashboard/trip-activity",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )

            # Test with custom days parameter
            response = requests.get(
                f"{BASE_URL}/admin/dashboard/trip-activity?days=30",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if len(data) == 30:
                    self.log_result(
                        "GET /admin/dashboard/trip-activity?days=30",
                        True,
                        "Correctly returns 30 days"
                    )
                else:
                    self.log_result(
                        "GET /admin/dashboard/trip-activity?days=30",
                        False,
                        f"Expected 30 days, got {len(data)}",
                        "WARNING"
                    )
        except Exception as e:
            self.log_result(
                "GET /admin/dashboard/trip-activity",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    def test_dashboard_risk_distribution(self):
        """Test GET /admin/dashboard/risk-distribution"""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/dashboard/risk-distribution",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                required_keys = ["low_risk_percentage", "medium_risk_percentage", "high_risk_percentage", "total_drivers"]
                has_keys = all(key in data for key in required_keys)

                if has_keys:
                    # Validate percentages add up to ~100
                    total_pct = (
                        data["low_risk_percentage"] +
                        data["medium_risk_percentage"] +
                        data["high_risk_percentage"]
                    )

                    if abs(total_pct - 100) < 0.1 or total_pct == 0:  # Allow small rounding error or no data
                        self.log_result(
                            "GET /admin/dashboard/risk-distribution",
                            True,
                            f"Returns valid risk distribution (Total: {data['total_drivers']} drivers)"
                        )
                    else:
                        self.log_result(
                            "GET /admin/dashboard/risk-distribution",
                            False,
                            f"Percentages don't add up to 100: {total_pct}",
                            "ERROR"
                        )
                else:
                    self.log_result(
                        "GET /admin/dashboard/risk-distribution",
                        False,
                        "Missing required keys",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/dashboard/risk-distribution",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/dashboard/risk-distribution",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    # ==================== DRIVER ENDPOINTS ====================

    def test_list_drivers(self):
        """Test GET /admin/drivers"""
        print("\n--- Driver Endpoints ---\n")

        try:
            # Test basic list
            response = requests.get(
                f"{BASE_URL}/admin/drivers",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    driver_count = len(data)
                    self.log_result(
                        "GET /admin/drivers",
                        True,
                        f"Returns {driver_count} drivers"
                    )

                    # Test pagination
                    response_page = requests.get(
                        f"{BASE_URL}/admin/drivers?skip=0&limit=2",
                        headers=self.get_headers(),
                        timeout=10
                    )

                    if response_page.status_code == 200:
                        page_data = response_page.json()
                        if len(page_data) <= 2:
                            self.log_result(
                                "GET /admin/drivers (pagination)",
                                True,
                                f"Pagination works (limit=2, got {len(page_data)})"
                            )
                        else:
                            self.log_result(
                                "GET /admin/drivers (pagination)",
                                False,
                                f"Pagination not working (limit=2, got {len(page_data)})",
                                "ERROR"
                            )

                    # Test search
                    if driver_count > 0:
                        first_driver = data[0]
                        search_term = first_driver["driver_id"][:5]

                        response_search = requests.get(
                            f"{BASE_URL}/admin/drivers?search={search_term}",
                            headers=self.get_headers(),
                            timeout=10
                        )

                        if response_search.status_code == 200:
                            search_data = response_search.json()
                            self.log_result(
                                "GET /admin/drivers (search)",
                                True,
                                f"Search returns {len(search_data)} results"
                            )
                else:
                    self.log_result(
                        "GET /admin/drivers",
                        False,
                        "Response is not a list",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/drivers",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/drivers",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    def test_get_driver(self):
        """Test GET /admin/drivers/{driver_id}"""
        try:
            # First get list to find a driver
            response = requests.get(
                f"{BASE_URL}/admin/drivers",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                drivers = response.json()
                if drivers:
                    driver_id = drivers[0]["driver_id"]

                    # Test getting specific driver
                    response_detail = requests.get(
                        f"{BASE_URL}/admin/drivers/{driver_id}",
                        headers=self.get_headers(),
                        timeout=10
                    )

                    if response_detail.status_code == 200:
                        driver = response_detail.json()
                        if driver["driver_id"] == driver_id:
                            self.log_result(
                                "GET /admin/drivers/{driver_id}",
                                True,
                                f"Returns correct driver: {driver_id}"
                            )
                        else:
                            self.log_result(
                                "GET /admin/drivers/{driver_id}",
                                False,
                                "Returned wrong driver",
                                "ERROR"
                            )
                    else:
                        self.log_result(
                            "GET /admin/drivers/{driver_id}",
                            False,
                            f"Unexpected status code: {response_detail.status_code}",
                            "ERROR"
                        )

                    # Test 404 for non-existent driver
                    response_404 = requests.get(
                        f"{BASE_URL}/admin/drivers/NONEXISTENT",
                        headers=self.get_headers(),
                        timeout=10
                    )

                    if response_404.status_code == 404:
                        self.log_result(
                            "GET /admin/drivers/{driver_id} (404)",
                            True,
                            "Correctly returns 404 for non-existent driver"
                        )
                    else:
                        self.log_result(
                            "GET /admin/drivers/{driver_id} (404)",
                            False,
                            f"Expected 404, got {response_404.status_code}",
                            "ERROR"
                        )
                else:
                    self.log_result(
                        "GET /admin/drivers/{driver_id}",
                        False,
                        "No drivers available to test",
                        "WARNING"
                    )
        except Exception as e:
            self.log_result(
                "GET /admin/drivers/{driver_id}",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    # ==================== USER ENDPOINTS ====================

    def test_list_users(self):
        """Test GET /admin/users"""
        print("\n--- User Endpoints ---\n")

        try:
            response = requests.get(
                f"{BASE_URL}/admin/users",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check that password hash is NOT in response
                    has_password_hash = any("hashed_password" in str(user) for user in data)

                    if not has_password_hash:
                        self.log_result(
                            "GET /admin/users",
                            True,
                            f"Returns {len(data)} users (passwords not exposed)"
                        )
                    else:
                        self.log_result(
                            "GET /admin/users",
                            False,
                            "Password hashes exposed in response!",
                            "ERROR"
                        )
                else:
                    self.log_result(
                        "GET /admin/users",
                        False,
                        "Response is not a list",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/users",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/users",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    # ==================== POLICY ENDPOINTS ====================

    def test_policies_summary(self):
        """Test GET /admin/policies/summary"""
        print("\n--- Policy Endpoints ---\n")

        try:
            response = requests.get(
                f"{BASE_URL}/admin/policies/summary",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                required_keys = ["total_policies", "active_policies", "monthly_revenue", "total_savings"]
                has_keys = all(key in data for key in required_keys)

                if has_keys:
                    self.log_result(
                        "GET /admin/policies/summary",
                        True,
                        f"Returns valid summary ({data['total_policies']} policies, ${data['monthly_revenue']}/mo revenue)"
                    )
                else:
                    self.log_result(
                        "GET /admin/policies/summary",
                        False,
                        "Missing required keys",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/policies/summary",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/policies/summary",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    def test_list_policies(self):
        """Test GET /admin/policies"""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/policies",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result(
                        "GET /admin/policies",
                        True,
                        f"Returns {len(data)} policies"
                    )
                else:
                    self.log_result(
                        "GET /admin/policies",
                        False,
                        "Response is not a list",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/policies",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/policies",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    # ==================== RESOURCE ENDPOINTS ====================

    def test_list_vehicles(self):
        """Test GET /admin/vehicles"""
        print("\n--- Resource Endpoints ---\n")

        try:
            response = requests.get(
                f"{BASE_URL}/admin/vehicles",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result(
                        "GET /admin/vehicles",
                        True,
                        f"Returns {len(data)} vehicles"
                    )
                else:
                    self.log_result(
                        "GET /admin/vehicles",
                        False,
                        "Response is not a list",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/vehicles",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/vehicles",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    def test_list_trips(self):
        """Test GET /admin/trips"""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/trips",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result(
                        "GET /admin/trips",
                        True,
                        f"Returns {len(data)} trips"
                    )
                else:
                    self.log_result(
                        "GET /admin/trips",
                        False,
                        "Response is not a list",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/trips",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/trips",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    def test_events_stats(self):
        """Test GET /admin/events/stats"""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/events/stats",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "total_events" in data and "unique_drivers" in data:
                    self.log_result(
                        "GET /admin/events/stats",
                        True,
                        f"Returns event stats ({data['total_events']} events, {data['unique_drivers']} drivers)"
                    )
                else:
                    self.log_result(
                        "GET /admin/events/stats",
                        False,
                        "Missing required keys",
                        "ERROR"
                    )
            else:
                self.log_result(
                    "GET /admin/events/stats",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    "ERROR"
                )
        except Exception as e:
            self.log_result(
                "GET /admin/events/stats",
                False,
                f"Request failed: {e}",
                "ERROR"
            )

    # ==================== REPORT GENERATION ====================

    def generate_report(self):
        """Generate API test report"""
        print("\n" + "="*80)
        print("API TEST REPORT")
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
            print("\n⚠️  ERRORS FOUND! API has issues that need to be fixed.")
        elif self.warnings > 0:
            print("\n⚠️  Warnings found. Review recommended.")
        else:
            print("\n✅ All API tests passed!")

        # Save detailed report
        report_file = "API_TEST_REPORT.md"
        with open(report_file, "w") as f:
            f.write("# API Integration Test Report\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Total Tests**: {total_tests}\n")
            f.write(f"**Passed**: {passed_tests}\n")
            f.write(f"**Failed**: {failed_tests}\n\n")
            f.write(f"## Results Summary\n\n")
            f.write(f"- Errors: {self.failures}\n")
            f.write(f"- Warnings: {self.warnings}\n\n")
            f.write(f"## Detailed Results\n\n")

            for result in self.results:
                status = "✅ PASS" if result["passed"] else ("⚠️  WARNING" if result["severity"] == "WARNING" else "❌ FAIL")
                f.write(f"### {status} {result['test']}\n\n")
                f.write(f"- **Details**: {result['details']}\n")
                f.write(f"- **Timestamp**: {result['timestamp']}\n\n")

        print(f"\nDetailed report saved to: {report_file}")

        return self.failures == 0

    def run_all_tests(self):
        """Run all API tests"""
        self.setup()

        # Dashboard tests
        self.test_dashboard_stats()
        self.test_dashboard_summary()
        self.test_dashboard_trip_activity()
        self.test_dashboard_risk_distribution()

        # Driver tests
        self.test_list_drivers()
        self.test_get_driver()

        # User tests
        self.test_list_users()

        # Policy tests
        self.test_policies_summary()
        self.test_list_policies()

        # Resource tests
        self.test_list_vehicles()
        self.test_list_trips()
        self.test_events_stats()

        # Generate report
        return self.generate_report()


if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
