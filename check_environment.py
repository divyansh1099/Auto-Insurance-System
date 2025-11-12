#!/usr/bin/env python3
"""
Environment Pre-Flight Check

Verifies that the system is ready to run comprehensive tests:
- Docker services are running
- Backend is accessible
- Database is accessible
- Admin user exists

Run this BEFORE running the test suite.

Usage:
    python check_environment.py
"""
import subprocess
import requests
import psycopg2
import sys
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'telematics_db',
    'user': 'insurance_user',
    'password': 'insurance_pass'
}


class EnvironmentChecker:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0

    def print_header(self, text):
        """Print section header"""
        print("\n" + "="*80)
        print(text)
        print("="*80 + "\n")

    def check_docker_installed(self):
        """Check if Docker is installed"""
        print("1️⃣  Checking Docker installation...")
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   ✅ Docker installed: {result.stdout.strip()}")
                self.checks_passed += 1
                return True
            else:
                print("   ❌ Docker not found")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"   ❌ Docker not found: {e}")
            print("   💡 Install Docker: https://docs.docker.com/get-docker/")
            self.checks_failed += 1
            return False

    def check_docker_compose_installed(self):
        """Check if Docker Compose is installed"""
        print("\n2️⃣  Checking Docker Compose installation...")
        try:
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   ✅ Docker Compose installed: {result.stdout.strip()}")
                self.checks_passed += 1
                return True
            else:
                print("   ❌ Docker Compose not found")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"   ❌ Docker Compose not found: {e}")
            self.checks_failed += 1
            return False

    def check_docker_services_running(self):
        """Check if Docker services are running"""
        print("\n3️⃣  Checking Docker services...")
        try:
            result = subprocess.run(['docker', 'compose', 'ps'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output = result.stdout

                # Check for required services
                required_services = ['backend', 'postgres', 'redis']
                services_status = {}

                for service in required_services:
                    if service in output and 'Up' in output:
                        services_status[service] = True
                    else:
                        services_status[service] = False

                all_running = all(services_status.values())

                if all_running:
                    print("   ✅ All required services are running:")
                    for service in required_services:
                        print(f"      • {service}: Up")
                    self.checks_passed += 1
                    return True
                else:
                    print("   ⚠️  Some services are not running:")
                    for service, running in services_status.items():
                        status = "Up" if running else "Down"
                        icon = "✅" if running else "❌"
                        print(f"      {icon} {service}: {status}")
                    print("\n   💡 Start services: docker compose up -d")
                    self.checks_failed += 1
                    return False
            else:
                print("   ❌ Could not check Docker services")
                print("   💡 Make sure you're in the project directory")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"   ❌ Could not check Docker services: {e}")
            self.checks_failed += 1
            return False

    def check_backend_accessible(self):
        """Check if backend API is accessible"""
        print("\n4️⃣  Checking Backend API...")
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Backend is accessible at {API_BASE_URL}")
                print(f"      Health check: {response.json()}")
                self.checks_passed += 1
                return True
            else:
                print(f"   ❌ Backend returned status code: {response.status_code}")
                print("   💡 Check backend logs: docker compose logs backend")
                self.checks_failed += 1
                return False
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to backend at {API_BASE_URL}")
            print("   💡 Is backend running? Check: docker compose ps backend")
            self.checks_failed += 1
            return False
        except Exception as e:
            print(f"   ❌ Error connecting to backend: {e}")
            self.checks_failed += 1
            return False

    def check_metrics_endpoint(self):
        """Check if Prometheus metrics endpoint is accessible"""
        print("\n5️⃣  Checking Metrics endpoint...")
        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
            if response.status_code == 200:
                metrics_count = len([line for line in response.text.split('\n') if line and not line.startswith('#')])
                print(f"   ✅ Metrics endpoint accessible ({metrics_count} metrics)")
                self.checks_passed += 1
                return True
            else:
                print(f"   ⚠️  Metrics endpoint returned: {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"   ⚠️  Metrics endpoint not accessible: {e}")
            self.checks_failed += 1
            return False

    def check_database_connection(self):
        """Check if database is accessible"""
        print("\n6️⃣  Checking Database connection...")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            print(f"   ✅ Database connection successful")
            print(f"      PostgreSQL: {version.split(',')[0]}")
            self.checks_passed += 1
            return True
        except psycopg2.OperationalError as e:
            if "role" in str(e) and "does not exist" in str(e):
                print(f"   ❌ Database role does not exist: {DB_CONFIG['user']}")
                print("\n   💡 Create database role:")
                print("      docker compose exec postgres psql -U postgres -c \"CREATE USER insurance_user WITH PASSWORD 'insurance_pass';\"")
                print("      docker compose exec postgres psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE telematics_db TO insurance_user;\"")
            elif "database" in str(e) and "does not exist" in str(e):
                print(f"   ❌ Database does not exist: {DB_CONFIG['database']}")
                print("\n   💡 Create database:")
                print("      docker compose exec postgres psql -U postgres -c \"CREATE DATABASE telematics_db OWNER insurance_user;\"")
            else:
                print(f"   ❌ Database connection failed: {e}")
                print("\n   💡 Check PostgreSQL logs: docker compose logs postgres")
            self.checks_failed += 1
            return False
        except Exception as e:
            print(f"   ❌ Database connection error: {e}")
            self.checks_failed += 1
            return False

    def check_database_tables(self):
        """Check if database tables exist"""
        print("\n7️⃣  Checking Database tables...")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Check for key tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('drivers', 'users', 'trips', 'premiums', 'risk_scores')
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            required_tables = ['drivers', 'users', 'trips', 'premiums', 'risk_scores']
            missing_tables = [t for t in required_tables if t not in tables]

            if not missing_tables:
                print(f"   ✅ All required tables exist ({len(tables)} tables)")
                for table in tables:
                    print(f"      • {table}")
                self.checks_passed += 1
                return True
            else:
                print(f"   ⚠️  Missing tables: {', '.join(missing_tables)}")
                print("   💡 Run migrations or initialize database")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"   ⚠️  Could not check tables: {e}")
            self.checks_failed += 1
            return False

    def check_admin_user(self):
        """Check if admin user exists"""
        print("\n8️⃣  Checking Admin user...")
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/auth/token",
                data={"username": "admin", "password": "admin123"},
                timeout=5
            )

            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    print("   ✅ Admin user exists and authentication works")
                    print(f"      Token: {token[:20]}...")
                    self.checks_passed += 1
                    return True
            else:
                print(f"   ❌ Admin authentication failed: {response.status_code}")
                if response.status_code == 401:
                    print("   💡 Admin user may not exist or password is wrong")
                    print("\n   Create admin user:")
                    print("      docker compose exec backend python -c \"")
                    print("      from app.models.database import SessionLocal, User")
                    print("      from app.utils.auth import get_password_hash")
                    print("      db = SessionLocal()")
                    print("      admin = User(username='admin', email='admin@example.com',")
                    print("                   hashed_password=get_password_hash('admin123'),")
                    print("                   is_admin=True, is_active=True)")
                    print("      db.add(admin)")
                    print("      db.commit()")
                    print("      \"")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"   ❌ Could not check admin user: {e}")
            self.checks_failed += 1
            return False

    def check_test_dependencies(self):
        """Check if required Python packages are installed"""
        print("\n9️⃣  Checking Python test dependencies...")
        required_packages = ['requests', 'psycopg2']
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package} installed")
            except ImportError:
                print(f"   ❌ {package} not installed")
                missing_packages.append(package)

        if not missing_packages:
            self.checks_passed += 1
            return True
        else:
            print(f"\n   💡 Install missing packages ON YOUR HOST MACHINE:")
            print("      pip install -r requirements-test.txt")
            print("      # OR manually:")
            print("      pip install requests psycopg2-binary")
            self.checks_failed += 1
            return False

    def check_database_port_conflict(self):
        """Check if connecting to Docker PostgreSQL or local PostgreSQL"""
        print("\n🔟  Checking database port configuration...")
        try:
            # Try to connect and check PostgreSQL version string
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Check if we're in Docker container by looking at data directory
            cursor.execute("SHOW data_directory;")
            data_dir = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            # Docker PostgreSQL typically has data in /var/lib/postgresql/data
            if '/var/lib/postgresql/data' in data_dir or '/docker' in data_dir:
                print(f"   ✅ Connected to Docker PostgreSQL")
                print(f"      Data directory: {data_dir}")
                self.checks_passed += 1
                return True
            else:
                print(f"   ⚠️  May be connecting to LOCAL PostgreSQL instead of Docker!")
                print(f"      Data directory: {data_dir}")
                print("\n   💡 If you have local PostgreSQL running:")
                print("      1. Stop local PostgreSQL: sudo systemctl stop postgresql")
                print("      2. Or use different port in docker-compose.yml")
                print("      3. Docker PostgreSQL should be on port 5432")
                self.checks_failed += 1
                return False
        except Exception as e:
            # Can't determine - might be okay
            print(f"   ⚠️  Cannot verify database source: {e}")
            return True

    def generate_report(self):
        """Generate environment check report"""
        self.print_header("ENVIRONMENT CHECK REPORT")

        total_checks = self.checks_passed + self.checks_failed
        pass_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0

        print(f"Total Checks: {total_checks}")
        print(f"Passed: {self.checks_passed} ({pass_rate:.1f}%)")
        print(f"Failed: {self.checks_failed}")
        print()

        if self.checks_failed == 0:
            print("✅ Environment is ready for testing!")
            print("\nYou can now run:")
            print("  python run_all_tests.py")
            return True
        else:
            print("⚠️  Environment needs attention before running tests")
            print("\nFix the issues above, then run this check again:")
            print("  python check_environment.py")
            return False

    def run_all_checks(self):
        """Run all environment checks"""
        self.print_header("ENVIRONMENT PRE-FLIGHT CHECK")
        print("Checking if system is ready for comprehensive testing...\n")

        # Run all checks
        self.check_docker_installed()
        self.check_docker_compose_installed()
        self.check_docker_services_running()
        self.check_backend_accessible()
        self.check_metrics_endpoint()
        self.check_database_connection()
        self.check_database_tables()
        self.check_admin_user()
        self.check_test_dependencies()
        self.check_database_port_conflict()

        # Generate report
        success = self.generate_report()

        return success


if __name__ == "__main__":
    checker = EnvironmentChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)
