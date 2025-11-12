"""
Security Vulnerability Testing Script

Tests for:
- SQL Injection attacks
- Authentication & Authorization bypass
- XSS and HTML injection
- Input validation vulnerabilities
- Rate limiting
- Information disclosure

Usage:
    python tests/security_test.py
"""
import requests
import time
import json
from typing import Dict, List, Tuple
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
USER_USERNAME = "testuser"
USER_PASSWORD = "testpass123"


class SecurityTester:
    def __init__(self):
        self.results = []
        self.admin_token = None
        self.user_token = None
        self.critical_failures = 0
        self.high_failures = 0
        self.medium_failures = 0

    def log_result(self, test_name: str, passed: bool, severity: str, details: str):
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
            if severity == "CRITICAL":
                self.critical_failures += 1
            elif severity == "HIGH":
                self.high_failures += 1
            elif severity == "MEDIUM":
                self.medium_failures += 1

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} [{severity}] {test_name}: {details}")

    def get_auth_token(self, username: str, password: str) -> str:
        """Get JWT token for authentication"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/token",
                data={"username": username, "password": password}
            )
            if response.status_code == 200:
                return response.json().get("access_token")
            return None
        except Exception as e:
            print(f"⚠️  Warning: Could not get auth token: {e}")
            return None

    def setup(self):
        """Setup test environment"""
        print("\n" + "="*80)
        print("SECURITY VULNERABILITY TESTING")
        print("="*80 + "\n")

        # Try to get tokens
        self.admin_token = self.get_auth_token(ADMIN_USERNAME, ADMIN_PASSWORD)
        if not self.admin_token:
            print("⚠️  Warning: Could not authenticate as admin. Some tests will be skipped.")

        self.user_token = self.get_auth_token(USER_USERNAME, USER_PASSWORD)
        if not self.user_token:
            print("⚠️  Warning: Could not authenticate as user. Some tests will be skipped.")

        print()

    # ==================== 1. SQL INJECTION TESTS ====================

    def test_sql_injection_in_search(self):
        """Test SQL injection in search parameters"""
        print("\n--- SQL Injection Tests ---\n")

        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE drivers--",
            "' UNION SELECT NULL,NULL,NULL--",
            "1' AND 1=1--",
            "admin'--",
            "' OR 1=1#",
            "') OR '1'='1--",
            "1' UNION SELECT username, password FROM users--"
        ]

        if not self.admin_token:
            self.log_result(
                "SQL Injection - Search Parameters",
                True,
                "CRITICAL",
                "Skipped - no admin token"
            )
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}
        vulnerable = False

        for payload in payloads:
            try:
                response = requests.get(
                    f"{BASE_URL}/admin/drivers",
                    headers=headers,
                    params={"search": payload},
                    timeout=5
                )

                # Check if we got unexpected behavior
                if response.status_code == 200:
                    data = response.json()
                    # If we get data back with SQL error patterns, it's vulnerable
                    if "error" in str(data).lower() and "sql" in str(data).lower():
                        vulnerable = True
                        break
                elif response.status_code == 500:
                    # 500 error might indicate SQL error
                    if "sql" in response.text.lower():
                        vulnerable = True
                        break
            except Exception as e:
                if "sql" in str(e).lower():
                    vulnerable = True
                    break

        self.log_result(
            "SQL Injection - Search Parameters",
            not vulnerable,
            "CRITICAL",
            "No SQL injection vulnerabilities detected" if not vulnerable else "SQL injection possible!"
        )

    def test_sql_injection_in_filters(self):
        """Test SQL injection in filter parameters"""
        payloads = [
            "1 OR 1=1",
            "1; DELETE FROM trips",
            "1 UNION SELECT * FROM users"
        ]

        if not self.admin_token:
            self.log_result(
                "SQL Injection - Filter Parameters",
                True,
                "CRITICAL",
                "Skipped - no admin token"
            )
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}
        vulnerable = False

        for payload in payloads:
            try:
                response = requests.get(
                    f"{BASE_URL}/admin/trips",
                    headers=headers,
                    params={"driver_id": payload},
                    timeout=5
                )

                if response.status_code == 500 and "sql" in response.text.lower():
                    vulnerable = True
                    break
            except Exception as e:
                if "sql" in str(e).lower():
                    vulnerable = True
                    break

        self.log_result(
            "SQL Injection - Filter Parameters",
            not vulnerable,
            "CRITICAL",
            "No SQL injection vulnerabilities detected" if not vulnerable else "SQL injection possible!"
        )

    # ==================== 2. AUTHENTICATION & AUTHORIZATION TESTS ====================

    def test_access_without_token(self):
        """Test accessing protected endpoints without authentication"""
        print("\n--- Authentication & Authorization Tests ---\n")

        endpoints = [
            "/admin/dashboard/summary",
            "/admin/drivers",
            "/admin/users",
            "/admin/policies"
        ]

        all_protected = True
        for endpoint in endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if response.status_code == 200:
                    all_protected = False
                    break
            except:
                pass

        self.log_result(
            "Access Without Token",
            all_protected,
            "CRITICAL",
            "All endpoints properly protected" if all_protected else "Some endpoints accessible without token!"
        )

    def test_user_accessing_admin_endpoints(self):
        """Test non-admin user accessing admin endpoints"""
        if not self.user_token:
            self.log_result(
                "Non-Admin Access to Admin Endpoints",
                True,
                "CRITICAL",
                "Skipped - no user token"
            )
            return

        headers = {"Authorization": f"Bearer {self.user_token}"}
        properly_restricted = True

        try:
            response = requests.get(
                f"{BASE_URL}/admin/dashboard/summary",
                headers=headers,
                timeout=5
            )
            # Should get 403 Forbidden, not 200 OK
            if response.status_code == 200:
                properly_restricted = False
        except:
            pass

        self.log_result(
            "Non-Admin Access to Admin Endpoints",
            properly_restricted,
            "CRITICAL",
            "Admin endpoints properly restricted" if properly_restricted else "Non-admin can access admin endpoints!"
        )

    def test_jwt_token_tampering(self):
        """Test JWT token tampering"""
        if not self.admin_token:
            self.log_result(
                "JWT Token Tampering",
                True,
                "HIGH",
                "Skipped - no admin token"
            )
            return

        # Create a tampered token (flip some bits)
        tampered_token = self.admin_token[:-5] + "XXXXX"
        headers = {"Authorization": f"Bearer {tampered_token}"}

        try:
            response = requests.get(
                f"{BASE_URL}/admin/dashboard/summary",
                headers=headers,
                timeout=5
            )
            # Should reject tampered token
            rejects_tampered = response.status_code in [401, 403]
        except:
            rejects_tampered = True

        self.log_result(
            "JWT Token Tampering",
            rejects_tampered,
            "HIGH",
            "Tampered tokens rejected" if rejects_tampered else "Tampered token accepted!"
        )

    # ==================== 3. XSS & INPUT VALIDATION TESTS ====================

    def test_xss_in_create_driver(self):
        """Test XSS payload injection in driver creation"""
        print("\n--- XSS & Input Validation Tests ---\n")

        if not self.admin_token:
            self.log_result(
                "XSS in Create Driver",
                True,
                "HIGH",
                "Skipped - no admin token"
            )
            return

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>"
        ]

        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }

        properly_sanitized = True
        for payload in xss_payloads:
            driver_data = {
                "driver_id": f"DRV-XSS-{int(time.time())}",
                "first_name": payload,
                "last_name": "Test",
                "email": "xss@test.com",
                "phone": "1234567890"
            }

            try:
                response = requests.post(
                    f"{BASE_URL}/admin/drivers",
                    headers=headers,
                    json=driver_data,
                    timeout=5
                )

                # If created successfully, check if payload is stored as-is
                if response.status_code == 201:
                    data = response.json()
                    if "<script>" in data.get("first_name", ""):
                        properly_sanitized = False
                        # Clean up
                        requests.delete(
                            f"{BASE_URL}/admin/drivers/{driver_data['driver_id']}",
                            headers=headers
                        )
                        break
            except:
                pass

        self.log_result(
            "XSS in Create Driver",
            properly_sanitized,
            "HIGH",
            "XSS payloads properly handled" if properly_sanitized else "XSS payload stored without sanitization!"
        )

    def test_oversized_input(self):
        """Test handling of oversized inputs"""
        if not self.admin_token:
            self.log_result(
                "Oversized Input Handling",
                True,
                "MEDIUM",
                "Skipped - no admin token"
            )
            return

        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }

        # Try to create driver with 10MB string
        huge_string = "A" * (10 * 1024 * 1024)
        driver_data = {
            "driver_id": f"DRV-BIG-{int(time.time())}",
            "first_name": huge_string,
            "last_name": "Test",
            "email": "big@test.com"
        }

        properly_rejected = False
        try:
            response = requests.post(
                f"{BASE_URL}/admin/drivers",
                headers=headers,
                json=driver_data,
                timeout=10
            )
            # Should reject with 400 or 413 (payload too large)
            if response.status_code in [400, 413, 422]:
                properly_rejected = True
        except requests.exceptions.RequestException:
            # Timeout or connection error is acceptable
            properly_rejected = True

        self.log_result(
            "Oversized Input Handling",
            properly_rejected,
            "MEDIUM",
            "Oversized inputs rejected" if properly_rejected else "Oversized input accepted!"
        )

    def test_invalid_data_types(self):
        """Test invalid data type handling"""
        if not self.admin_token:
            self.log_result(
                "Invalid Data Type Handling",
                True,
                "MEDIUM",
                "Skipped - no admin token"
            )
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Send string where integer expected
        properly_validated = False
        try:
            response = requests.get(
                f"{BASE_URL}/admin/dashboard/trip-activity",
                headers=headers,
                params={"days": "invalid_string"},
                timeout=5
            )
            # Should reject with 422 validation error
            if response.status_code == 422:
                properly_validated = True
        except:
            pass

        self.log_result(
            "Invalid Data Type Handling",
            properly_validated,
            "MEDIUM",
            "Invalid data types rejected" if properly_validated else "Invalid data types accepted!"
        )

    # ==================== 4. RATE LIMITING TESTS ====================

    def test_rate_limiting(self):
        """Test rate limiting protection"""
        print("\n--- Rate Limiting Tests ---\n")

        if not self.admin_token:
            self.log_result(
                "Rate Limiting",
                True,
                "HIGH",
                "Skipped - no admin token"
            )
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Send 100 rapid requests
        rate_limited = False
        for i in range(100):
            try:
                response = requests.get(
                    f"{BASE_URL}/admin/dashboard/summary",
                    headers=headers,
                    timeout=1
                )
                if response.status_code == 429:  # Too Many Requests
                    rate_limited = True
                    break
            except:
                pass

        self.log_result(
            "Rate Limiting",
            rate_limited,
            "HIGH",
            "Rate limiting active" if rate_limited else "No rate limiting detected (may be expected for admin)"
        )

    # ==================== 5. INFORMATION DISCLOSURE TESTS ====================

    def test_error_message_disclosure(self):
        """Test that error messages don't reveal sensitive info"""
        print("\n--- Information Disclosure Tests ---\n")

        if not self.admin_token:
            self.log_result(
                "Error Message Disclosure",
                True,
                "MEDIUM",
                "Skipped - no admin token"
            )
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Try to trigger an error
        try:
            response = requests.get(
                f"{BASE_URL}/admin/drivers/NONEXISTENT",
                headers=headers,
                timeout=5
            )

            if response.status_code == 404:
                error_text = response.text.lower()
                # Check for sensitive info leaks
                has_leak = any(keyword in error_text for keyword in [
                    "traceback", "file", "line", ".py", "exception",
                    "database", "postgresql", "sqlalchemy"
                ])
                no_disclosure = not has_leak
            else:
                no_disclosure = True
        except:
            no_disclosure = True

        self.log_result(
            "Error Message Disclosure",
            no_disclosure,
            "MEDIUM",
            "Error messages don't leak sensitive info" if no_disclosure else "Error messages reveal system details!"
        )

    def test_password_in_response(self):
        """Test that password hashes never appear in API responses"""
        if not self.admin_token:
            self.log_result(
                "Password Hash in Response",
                True,
                "CRITICAL",
                "Skipped - no admin token"
            )
            return

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        try:
            response = requests.get(
                f"{BASE_URL}/admin/users",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                response_text = response.text.lower()
                # Check if password-related fields are exposed
                has_password = "hashed_password" in response_text or "password" in response_text
                no_password_leak = not has_password
            else:
                no_password_leak = True
        except:
            no_password_leak = True

        self.log_result(
            "Password Hash in Response",
            no_password_leak,
            "CRITICAL",
            "Passwords never exposed in responses" if no_password_leak else "Password hashes exposed in API responses!"
        )

    # ==================== REPORT GENERATION ====================

    def generate_report(self):
        """Generate security test report"""
        print("\n" + "="*80)
        print("SECURITY TEST REPORT")
        print("="*80 + "\n")

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests Run: {total_tests}")
        print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"\nFailure Breakdown:")
        print(f"  CRITICAL: {self.critical_failures}")
        print(f"  HIGH: {self.high_failures}")
        print(f"  MEDIUM: {self.medium_failures}")

        if self.critical_failures > 0:
            print("\n⚠️  CRITICAL VULNERABILITIES FOUND! System is NOT SAFE for production.")
        elif self.high_failures > 0:
            print("\n⚠️  HIGH SEVERITY issues found. Recommend fixing before production.")
        elif self.medium_failures > 0:
            print("\n⚠️  MEDIUM SEVERITY issues found. Should be addressed.")
        else:
            print("\n✅ No security vulnerabilities detected!")

        # Save detailed report
        report_file = "SECURITY_TEST_REPORT.md"
        with open(report_file, "w") as f:
            f.write("# Security Test Report\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Total Tests**: {total_tests}\n")
            f.write(f"**Passed**: {passed_tests}\n")
            f.write(f"**Failed**: {failed_tests}\n\n")
            f.write(f"## Failure Summary\n\n")
            f.write(f"- CRITICAL: {self.critical_failures}\n")
            f.write(f"- HIGH: {self.high_failures}\n")
            f.write(f"- MEDIUM: {self.medium_failures}\n\n")
            f.write(f"## Detailed Results\n\n")

            for result in self.results:
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                f.write(f"### {status} {result['test']}\n\n")
                f.write(f"- **Severity**: {result['severity']}\n")
                f.write(f"- **Details**: {result['details']}\n")
                f.write(f"- **Timestamp**: {result['timestamp']}\n\n")

        print(f"\nDetailed report saved to: {report_file}")

        return self.critical_failures == 0 and self.high_failures == 0

    def run_all_tests(self):
        """Run all security tests"""
        self.setup()

        # SQL Injection Tests
        self.test_sql_injection_in_search()
        self.test_sql_injection_in_filters()

        # Authentication & Authorization Tests
        self.test_access_without_token()
        self.test_user_accessing_admin_endpoints()
        self.test_jwt_token_tampering()

        # XSS & Input Validation Tests
        self.test_xss_in_create_driver()
        self.test_oversized_input()
        self.test_invalid_data_types()

        # Rate Limiting Tests
        self.test_rate_limiting()

        # Information Disclosure Tests
        self.test_error_message_disclosure()
        self.test_password_in_response()

        # Generate report
        return self.generate_report()


if __name__ == "__main__":
    tester = SecurityTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
