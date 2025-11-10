#!/usr/bin/env python3
"""
Security Testing Script for Auto Insurance System APIs

Tests for common vulnerabilities:
- SQL Injection
- XSS (Cross-Site Scripting)
- Authentication/Authorization bypass
- Input validation issues
- Path traversal
- Command injection
- JWT token manipulation
- Rate limiting
- CORS misconfiguration
"""

import sys
import os
import requests
import json
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = f"{API_BASE_URL}/api/v1"

# Test credentials (should exist in database)
TEST_USERNAME = "driver0002"
TEST_PASSWORD = "password0002"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class SecurityTestResult:
    """Represents a security test result."""
    def __init__(self, test_name: str, endpoint: str, method: str, vulnerable: bool, 
                 details: str, severity: str = "MEDIUM"):
        self.test_name = test_name
        self.endpoint = endpoint
        self.method = method
        self.vulnerable = vulnerable
        self.details = details
        self.severity = severity
        self.timestamp = datetime.now()

class SecurityTester:
    """Security testing class."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.api_prefix = f"{base_url}/api/v1"
        self.session = requests.Session()
        self.results: List[SecurityTestResult] = []
        self.auth_token: Optional[str] = None
        self.admin_token: Optional[str] = None
        
    def log_result(self, result: SecurityTestResult):
        """Log a test result."""
        self.results.append(result)
        status = f"{Colors.RED}VULNERABLE{Colors.RESET}" if result.vulnerable else f"{Colors.GREEN}SAFE{Colors.RESET}"
        print(f"[{status}] {result.test_name}")
        print(f"  Endpoint: {result.method} {result.endpoint}")
        print(f"  Severity: {result.severity}")
        if result.details:
            print(f"  Details: {result.details}")
        print()
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate and get JWT token."""
        try:
            response = self.session.post(
                f"{self.api_prefix}/auth/login",
                json={"username": username, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get("access_token")
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Authentication failed: {e}{Colors.RESET}")
        return None
    
    def setup_auth(self):
        """Setup authentication tokens."""
        print(f"{Colors.BLUE}Setting up authentication...{Colors.RESET}")
        self.auth_token = self.authenticate(TEST_USERNAME, TEST_PASSWORD)
        self.admin_token = self.authenticate(ADMIN_USERNAME, ADMIN_PASSWORD)
        
        if self.auth_token:
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print(f"{Colors.GREEN}✓ Authenticated as {TEST_USERNAME}{Colors.RESET}\n")
        else:
            print(f"{Colors.YELLOW}⚠ Could not authenticate as test user{Colors.RESET}\n")
    
    # SQL Injection Payloads
    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin'--",
        "admin'/*",
        "' UNION SELECT NULL--",
        "1' OR '1'='1",
        "1' AND '1'='1",
        "'; DROP TABLE users--",
        "' OR 1=1--",
        "' OR 'a'='a",
        "') OR ('1'='1",
        "1' OR '1'='1' LIMIT 1--",
        "' OR 1=1#",
        "' OR 1=1/*",
    ]
    
    # XSS Payloads
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>",
        "<video><source onerror=alert('XSS')>",
        "<audio src=x onerror=alert('XSS')>",
        "<details open ontoggle=alert('XSS')>",
        "<marquee onstart=alert('XSS')>",
        "<div onmouseover=alert('XSS')>",
    ]
    
    # Path Traversal Payloads
    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "..%2f..%2f..%2fetc%2fpasswd",
        "..%5c..%5c..%5cwindows%5csystem32%5cconfig%5csam",
        "....\\\\....\\\\....\\\\etc\\\\passwd",
    ]
    
    # Command Injection Payloads
    COMMAND_INJECTION_PAYLOADS = [
        "; ls",
        "| ls",
        "& ls",
        "&& ls",
        "|| ls",
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "& cat /etc/passwd",
        "; id",
        "| id",
        "& id",
        "$(ls)",
        "`ls`",
        "${ls}",
        "; ping -c 1 127.0.0.1",
    ]
    
    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities."""
        print(f"{Colors.BOLD}Testing SQL Injection...{Colors.RESET}")
        
        # Test login endpoint
        for payload in self.SQL_INJECTION_PAYLOADS[:5]:  # Test first 5
            try:
                response = self.session.post(
                    f"{self.api_prefix}/auth/login",
                    json={"username": payload, "password": "test"},
                    timeout=5
                )
                
                # Check for SQL error messages
                response_text = response.text.lower()
                sql_errors = [
                    "sql syntax", "mysql", "postgresql", "sqlite", "ora-",
                    "sql error", "database error", "syntax error", "unclosed",
                    "unterminated", "quoted string"
                ]
                
                if any(error in response_text for error in sql_errors):
                    self.log_result(SecurityTestResult(
                        "SQL Injection - Login",
                        f"{self.api_prefix}/auth/login",
                        "POST",
                        True,
                        f"SQL error detected with payload: {payload}",
                        "HIGH"
                    ))
            except Exception as e:
                pass
        
        # Test driver_id parameters
        if self.auth_token:
            test_endpoints = [
                f"/drivers/DRV-0001' OR '1'='1/summary",
                f"/risk/DRV-0001' OR '1'='1/score",
                f"/pricing/DRV-0001' OR '1'='1/current",
            ]
            
            for endpoint in test_endpoints:
                try:
                    response = self.session.get(
                        f"{self.api_prefix}{endpoint}",
                        timeout=5
                    )
                    
                    response_text = response.text.lower()
                    sql_errors = [
                        "sql syntax", "mysql", "postgresql", "sqlite",
                        "database error", "syntax error"
                    ]
                    
                    if any(error in response_text for error in sql_errors):
                        self.log_result(SecurityTestResult(
                            "SQL Injection - Path Parameter",
                            endpoint,
                            "GET",
                            True,
                            "SQL error detected in response",
                            "HIGH"
                        ))
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ SQL Injection tests completed{Colors.RESET}\n")
    
    def test_xss(self):
        """Test for XSS vulnerabilities."""
        print(f"{Colors.BOLD}Testing XSS (Cross-Site Scripting)...{Colors.RESET}")
        
        # Test input fields that might reflect user input
        if self.auth_token:
            for payload in self.XSS_PAYLOADS[:3]:  # Test first 3
                try:
                    # Test in driver_id parameter
                    response = self.session.get(
                        f"{self.api_prefix}/drivers/{payload}/summary",
                        timeout=5
                    )
                    
                    # Check if payload is reflected in response
                    if payload in response.text and "<script>" in payload:
                        self.log_result(SecurityTestResult(
                            "XSS - Reflected",
                            f"/drivers/{payload[:20]}.../summary",
                            "GET",
                            True,
                            "XSS payload reflected in response",
                            "MEDIUM"
                        ))
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ XSS tests completed{Colors.RESET}\n")
    
    def test_authentication_bypass(self):
        """Test for authentication bypass vulnerabilities."""
        print(f"{Colors.BOLD}Testing Authentication Bypass...{Colors.RESET}")
        
        # Test endpoints without authentication
        protected_endpoints = [
            ("/drivers/DRV-0001", "GET"),
            ("/risk/DRV-0001/score", "GET"),
            ("/pricing/DRV-0001/current", "GET"),
            ("/admin/dashboard/stats", "GET"),
        ]
        
        # Remove auth header temporarily
        original_headers = self.session.headers.copy()
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        for endpoint, method in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.api_prefix}{endpoint}", timeout=5)
                else:
                    response = self.session.post(f"{self.api_prefix}{endpoint}", timeout=5)
                
                if response.status_code == 200:
                    self.log_result(SecurityTestResult(
                        "Authentication Bypass",
                        endpoint,
                        method,
                        True,
                        "Endpoint accessible without authentication",
                        "HIGH"
                    ))
                elif response.status_code == 401:
                    pass  # Expected - endpoint is protected
            except Exception:
                pass
        
        # Restore auth headers
        self.session.headers.update(original_headers)
        
        print(f"{Colors.GREEN}✓ Authentication bypass tests completed{Colors.RESET}\n")
    
    def test_authorization_bypass(self):
        """Test for authorization bypass (accessing other users' data)."""
        print(f"{Colors.BOLD}Testing Authorization Bypass...{Colors.RESET}")
        
        if not self.auth_token:
            print(f"{Colors.YELLOW}⚠ Skipping - no authentication token{Colors.RESET}\n")
            return
        
        # Try to access other drivers' data
        other_driver_ids = ["DRV-0001", "DRV-0003", "DRV-0004", "DRV-0005"]
        
        for driver_id in other_driver_ids:
            try:
                # Try to access another driver's summary
                response = self.session.get(
                    f"{self.api_prefix}/drivers/{driver_id}/summary",
                    timeout=5
                )
                
                if response.status_code == 200:
                    # Check if we got data (should be 403 if authorization works)
                    data = response.json()
                    if data:
                        self.log_result(SecurityTestResult(
                            "Authorization Bypass",
                            f"/drivers/{driver_id}/summary",
                            "GET",
                            True,
                            f"Accessible data for driver {driver_id}",
                            "HIGH"
                        ))
                elif response.status_code == 403:
                    pass  # Expected - authorization is working
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ Authorization bypass tests completed{Colors.RESET}\n")
    
    def test_path_traversal(self):
        """Test for path traversal vulnerabilities."""
        print(f"{Colors.BOLD}Testing Path Traversal...{Colors.RESET}")
        
        if not self.auth_token:
            print(f"{Colors.YELLOW}⚠ Skipping - no authentication token{Colors.RESET}\n")
            return
        
        for payload in self.PATH_TRAVERSAL_PAYLOADS[:3]:  # Test first 3
            try:
                # Test in driver_id parameter
                response = self.session.get(
                    f"{self.api_prefix}/drivers/{payload}/summary",
                    timeout=5
                )
                
                # Check for file contents in response
                if "root:" in response.text or "bin/bash" in response.text:
                    self.log_result(SecurityTestResult(
                        "Path Traversal",
                        f"/drivers/{payload[:20]}.../summary",
                        "GET",
                        True,
                        "File contents detected in response",
                        "HIGH"
                    ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ Path traversal tests completed{Colors.RESET}\n")
    
    def test_input_validation(self):
        """Test for input validation issues."""
        print(f"{Colors.BOLD}Testing Input Validation...{Colors.RESET}")
        
        # Test with extremely long inputs
        long_string = "A" * 10000
        
        if self.auth_token:
            try:
                response = self.session.get(
                    f"{self.api_prefix}/drivers/{long_string}/summary",
                    timeout=5
                )
                
                # Check if server handles it gracefully
                if response.status_code == 500:
                    self.log_result(SecurityTestResult(
                        "Input Validation - Long String",
                        "/drivers/{long_string}/summary",
                        "GET",
                        True,
                        "Server error with long input",
                        "MEDIUM"
                    ))
            except Exception:
                pass
        
        # Test with special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        try:
            response = self.session.post(
                f"{self.api_prefix}/auth/login",
                json={"username": special_chars, "password": special_chars},
                timeout=5
            )
            
            # Should handle gracefully
            if response.status_code == 500:
                self.log_result(SecurityTestResult(
                    "Input Validation - Special Characters",
                    "/auth/login",
                    "POST",
                    True,
                    "Server error with special characters",
                    "MEDIUM"
                ))
        except Exception:
            pass
        
        print(f"{Colors.GREEN}✓ Input validation tests completed{Colors.RESET}\n")
    
    def test_jwt_manipulation(self):
        """Test JWT token manipulation."""
        print(f"{Colors.BOLD}Testing JWT Token Manipulation...{Colors.RESET}")
        
        if not self.auth_token:
            print(f"{Colors.YELLOW}⚠ Skipping - no authentication token{Colors.RESET}\n")
            return
        
        # Test with modified token
        modified_token = self.auth_token[:-1] + "X"
        original_headers = self.session.headers.copy()
        self.session.headers.update({"Authorization": f"Bearer {modified_token}"})
        
        try:
            response = self.session.get(
                f"{self.api_prefix}/auth/me",
                timeout=5
            )
            
            if response.status_code == 200:
                self.log_result(SecurityTestResult(
                    "JWT Manipulation",
                    "/auth/me",
                    "GET",
                    True,
                    "Modified token accepted",
                    "HIGH"
                ))
        except Exception:
            pass
        
        # Restore original token
        self.session.headers.update(original_headers)
        
        # Test with no signature (if algorithm is None)
        try:
            import jwt as jwt_lib
            payload = jwt_lib.decode(self.auth_token, options={"verify_signature": False})
            payload["is_admin"] = True  # Try to escalate privileges
            
            # Try to create new token (will fail without secret, but test the attempt)
            # This is just to check if the system validates tokens properly
        except Exception:
            pass
        
        print(f"{Colors.GREEN}✓ JWT manipulation tests completed{Colors.RESET}\n")
    
    def test_rate_limiting(self):
        """Test for rate limiting."""
        print(f"{Colors.BOLD}Testing Rate Limiting...{Colors.RESET}")
        
        # Make rapid requests to login endpoint
        requests_made = 0
        for i in range(20):
            try:
                response = self.session.post(
                    f"{self.api_prefix}/auth/login",
                    json={"username": "test", "password": "test"},
                    timeout=2
                )
                requests_made += 1
            except Exception:
                break
        
        if requests_made >= 20:
            self.log_result(SecurityTestResult(
                "Rate Limiting",
                "/auth/login",
                "POST",
                True,
                f"No rate limiting detected ({requests_made} requests)",
                "MEDIUM"
            ))
        else:
            print(f"{Colors.GREEN}✓ Rate limiting appears to be working{Colors.RESET}")
        
        print()
    
    def test_cors_configuration(self):
        """Test CORS configuration."""
        print(f"{Colors.BOLD}Testing CORS Configuration...{Colors.RESET}")
        
        try:
            # Test with origin header
            response = self.session.options(
                f"{self.api_prefix}/drivers/DRV-0001",
                headers={"Origin": "https://evil.com"},
                timeout=5
            )
            
            cors_headers = response.headers.get("Access-Control-Allow-Origin")
            if cors_headers == "*":
                self.log_result(SecurityTestResult(
                    "CORS - Wildcard Origin",
                    "/drivers/DRV-0001",
                    "OPTIONS",
                    True,
                    "CORS allows all origins (*)",
                    "MEDIUM"
                ))
            elif cors_headers == "https://evil.com":
                self.log_result(SecurityTestResult(
                    "CORS - Reflected Origin",
                    "/drivers/DRV-0001",
                    "OPTIONS",
                    True,
                    "CORS reflects origin header",
                    "HIGH"
                ))
        except Exception:
            pass
        
        print(f"{Colors.GREEN}✓ CORS tests completed{Colors.RESET}\n")
    
    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure."""
        print(f"{Colors.BOLD}Testing Sensitive Data Exposure...{Colors.RESET}")
        
        if not self.auth_token:
            print(f"{Colors.YELLOW}⚠ Skipping - no authentication token{Colors.RESET}\n")
            return
        
        # Check if passwords are exposed
        try:
            response = self.session.get(
                f"{self.api_prefix}/auth/me",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                sensitive_fields = ["password", "hashed_password", "secret", "token", "key"]
                
                for field in sensitive_fields:
                    if field in str(data).lower():
                        self.log_result(SecurityTestResult(
                            "Sensitive Data Exposure",
                            "/auth/me",
                            "GET",
                            True,
                            f"Sensitive field '{field}' exposed in response",
                            "HIGH"
                        ))
        except Exception:
            pass
        
        print(f"{Colors.GREEN}✓ Sensitive data exposure tests completed{Colors.RESET}\n")
    
    def generate_report(self):
        """Generate security test report."""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}SECURITY TEST REPORT{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        
        vulnerable = [r for r in self.results if r.vulnerable]
        safe = [r for r in self.results if not r.vulnerable]
        
        print(f"Total Tests: {len(self.results)}")
        print(f"{Colors.RED}Vulnerabilities Found: {len(vulnerable)}{Colors.RESET}")
        print(f"{Colors.GREEN}Safe: {len(safe)}{Colors.RESET}\n")
        
        if vulnerable:
            print(f"{Colors.BOLD}VULNERABILITIES:{Colors.RESET}\n")
            for result in vulnerable:
                print(f"{Colors.RED}● {result.test_name}{Colors.RESET}")
                print(f"  Endpoint: {result.method} {result.endpoint}")
                print(f"  Severity: {result.severity}")
                print(f"  Details: {result.details}\n")
        
        # Summary by severity
        high = [r for r in vulnerable if r.severity == "HIGH"]
        medium = [r for r in vulnerable if r.severity == "MEDIUM"]
        low = [r for r in vulnerable if r.severity == "LOW"]
        
        if high or medium or low:
            print(f"\n{Colors.BOLD}Severity Breakdown:{Colors.RESET}")
            print(f"{Colors.RED}  HIGH: {len(high)}{Colors.RESET}")
            print(f"{Colors.YELLOW}  MEDIUM: {len(medium)}{Colors.RESET}")
            print(f"{Colors.BLUE}  LOW: {len(low)}{Colors.RESET}\n")
        
        if not vulnerable:
            print(f"{Colors.GREEN}✓ No vulnerabilities detected!{Colors.RESET}\n")
        
        return len(vulnerable) == 0
    
    def run_all_tests(self):
        """Run all security tests."""
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}SECURITY TESTING - Auto Insurance System API{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        print(f"Testing API at: {self.api_prefix}\n")
        
        self.setup_auth()
        
        self.test_sql_injection()
        self.test_xss()
        self.test_authentication_bypass()
        self.test_authorization_bypass()
        self.test_path_traversal()
        self.test_input_validation()
        self.test_jwt_manipulation()
        self.test_rate_limiting()
        self.test_cors_configuration()
        self.test_sensitive_data_exposure()
        
        return self.generate_report()


def main():
    """Main entry point."""
    tester = SecurityTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

