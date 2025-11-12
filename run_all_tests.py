#!/usr/bin/env python3
"""
Master Test Runner

Runs all comprehensive tests in sequence:
1. Security vulnerability testing
2. API integration testing
3. Database consistency checks
4. Performance benchmarking

Generates a consolidated final report with all findings.

Usage:
    python run_all_tests.py

    Or with specific tests:
    python run_all_tests.py --skip-security
    python run_all_tests.py --only-api
"""
import subprocess
import sys
import time
from datetime import datetime
import argparse
import os
import pickle
from pathlib import Path

# Test scripts
TEST_SCRIPTS = {
    "security": "tests/security_test.py",
    "api": "tests/test_api_integration.py",
    "database": "tests/check_db_consistency.py",
    "performance": "tests/test_performance.py"
}

# Rate limit configuration
RATE_LIMIT_FILE = "/tmp/test_run_timestamp.pkl"
RATE_LIMIT_COOLDOWN = 60  # seconds - matches 5/minute auth rate limit


class MasterTestRunner:
    def __init__(self, skip_tests=None, only_tests=None):
        self.skip_tests = skip_tests or []
        self.only_tests = only_tests
        self.results = {}
        self.start_time = None
        self.end_time = None

    def check_rate_limit_cooldown(self):
        """Check if enough time has passed since last test run to avoid rate limiting"""
        if os.path.exists(RATE_LIMIT_FILE):
            try:
                with open(RATE_LIMIT_FILE, 'rb') as f:
                    last_run_time = pickle.load(f)

                time_since_last_run = time.time() - last_run_time

                if time_since_last_run < RATE_LIMIT_COOLDOWN:
                    wait_time = RATE_LIMIT_COOLDOWN - time_since_last_run
                    print(f"\n⚠️  Rate Limit Cooldown Required")
                    print(f"   Last test run: {int(time_since_last_run)}s ago")
                    print(f"   Auth rate limit: 5 requests/minute")
                    print(f"   Waiting {int(wait_time)}s to avoid rate limiting...")
                    print(f"   (or press Ctrl+C to cancel)\n")

                    # Countdown timer
                    for remaining in range(int(wait_time), 0, -1):
                        print(f"\r   ⏱️  {remaining}s remaining...", end='', flush=True)
                        time.sleep(1)
                    print("\r   ✅ Cooldown complete!             \n")
            except Exception as e:
                # If there's any issue reading the file, just continue
                pass

        # Update last run time
        try:
            with open(RATE_LIMIT_FILE, 'wb') as f:
                pickle.dump(time.time(), f)
        except Exception:
            pass  # Non-critical if we can't write the timestamp

    def print_header(self, text):
        """Print section header"""
        print("\n" + "="*80)
        print(text)
        print("="*80 + "\n")

    def run_test(self, test_name: str, script_path: str) -> bool:
        """Run a single test script"""
        # Check if test should be skipped
        if test_name in self.skip_tests:
            print(f"⏭️  Skipping {test_name} test (--skip-{test_name} specified)")
            self.results[test_name] = {"status": "skipped", "duration": 0}
            return True

        # Check if only specific tests should run
        if self.only_tests and test_name not in self.only_tests:
            print(f"⏭️  Skipping {test_name} test (not in --only-* list)")
            self.results[test_name] = {"status": "skipped", "duration": 0}
            return True

        self.print_header(f"Running {test_name.upper()} Tests")

        # Check if script exists
        if not os.path.exists(script_path):
            print(f"❌ Test script not found: {script_path}")
            self.results[test_name] = {"status": "error", "duration": 0, "message": "Script not found"}
            return False

        start = time.time()
        try:
            # Run the test script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=False,  # Show output in real-time
                text=True
            )

            duration = time.time() - start

            if result.returncode == 0:
                self.results[test_name] = {"status": "passed", "duration": duration}
                print(f"\n✅ {test_name.upper()} tests PASSED (Duration: {duration:.1f}s)")
                return True
            else:
                self.results[test_name] = {"status": "failed", "duration": duration}
                print(f"\n❌ {test_name.upper()} tests FAILED (Duration: {duration:.1f}s)")
                return False

        except Exception as e:
            duration = time.time() - start
            self.results[test_name] = {"status": "error", "duration": duration, "message": str(e)}
            print(f"\n❌ {test_name.upper()} tests ERROR: {e}")
            return False

    def run_all_tests(self):
        """Run all test suites"""
        # Check rate limit cooldown first
        self.check_rate_limit_cooldown()

        self.print_header("COMPREHENSIVE TESTING SUITE")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Scripts: {len([t for t in TEST_SCRIPTS if t not in self.skip_tests])}")
        print(f"\nℹ️  Note: Tests use auth endpoint with 5 req/min rate limit")
        print(f"   Automatic cooldown prevents rate limit errors\n")

        self.start_time = time.time()

        # Run each test suite
        test_results = []

        for test_name, script_path in TEST_SCRIPTS.items():
            success = self.run_test(test_name, script_path)
            test_results.append((test_name, success))
            # Wait between test suites to avoid rate limiting
            # Rate limit: 5 requests/minute = 1 request every 12 seconds
            # Wait 20 seconds to be safe (allows for auth + retries)
            if test_name != list(TEST_SCRIPTS.keys())[-1]:  # Don't wait after last test
                print(f"\n⏱️  Waiting 20 seconds before next test suite (rate limit: 5/min)...")
                time.sleep(20)

        self.end_time = time.time()

        # Generate final report
        self.generate_final_report(test_results)

    def generate_final_report(self, test_results):
        """Generate consolidated final report"""
        self.print_header("FINAL COMPREHENSIVE TESTING REPORT")

        total_duration = self.end_time - self.start_time

        # Count results
        passed = sum(1 for _, success in test_results if success)
        failed = sum(1 for _, success in test_results if not success)
        skipped = sum(1 for r in self.results.values() if r["status"] == "skipped")
        total = len(test_results)

        print(f"Total Test Suites: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"Skipped: {skipped}")
        print(f"Total Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        print()

        # Print individual test results
        print("Individual Test Results:")
        print("-" * 80)
        for test_name, success in test_results:
            result = self.results[test_name]
            status_icon = "✅" if success else ("⏭️ " if result["status"] == "skipped" else "❌")
            duration_str = f"{result['duration']:.1f}s" if result['duration'] > 0 else "N/A"
            print(f"{status_icon} {test_name.upper():15} - {result['status']:10} (Duration: {duration_str})")

        print()

        # Overall status
        if failed > 0:
            print("⚠️  TESTING FAILED - Issues detected that need attention!")
            print("\nRecommendations:")
            for test_name, success in test_results:
                if not success and self.results[test_name]["status"] != "skipped":
                    print(f"  - Review {test_name.upper()}_TEST_REPORT.md for details")

            sys.exit(1)
        elif skipped > 0:
            print("⚠️  Some tests were skipped. Run all tests for complete validation.")
        else:
            print("✅ ALL TESTS PASSED - System ready for Phase 2!")

        # Save consolidated report
        self.save_consolidated_report(test_results, total_duration)

    def save_consolidated_report(self, test_results, total_duration):
        """Save consolidated testing report"""
        report_file = "COMPREHENSIVE_TEST_REPORT.md"

        with open(report_file, "w") as f:
            f.write("# Comprehensive Testing Report\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n")
            f.write(f"**Duration**: {total_duration:.1f}s ({total_duration/60:.1f} minutes)\n\n")

            # Summary
            passed = sum(1 for _, success in test_results if success)
            failed = sum(1 for _, success in test_results if not success)
            skipped = sum(1 for r in self.results.values() if r["status"] == "skipped")
            total = len(test_results)

            f.write("## Summary\n\n")
            f.write(f"- **Total Test Suites**: {total}\n")
            f.write(f"- **Passed**: {passed} ({passed/total*100:.1f}%)\n")
            f.write(f"- **Failed**: {failed}\n")
            f.write(f"- **Skipped**: {skipped}\n\n")

            # Detailed results
            f.write("## Test Suite Results\n\n")
            f.write("| Test Suite | Status | Duration | Report |\n")
            f.write("|------------|--------|----------|--------|\n")

            for test_name, success in test_results:
                result = self.results[test_name]
                status_icon = "✅" if success else ("⏭️" if result["status"] == "skipped" else "❌")
                duration = f"{result['duration']:.1f}s" if result['duration'] > 0 else "N/A"

                report_name = {
                    "security": "SECURITY_TEST_REPORT.md",
                    "api": "API_TEST_REPORT.md",
                    "database": "DB_CONSISTENCY_REPORT.md",
                    "performance": "PERFORMANCE_TEST_REPORT.md"
                }.get(test_name, "")

                f.write(f"| {test_name.title()} | {status_icon} {result['status'].title()} | {duration} | {report_name} |\n")

            f.write("\n## Overall Assessment\n\n")

            if failed > 0:
                f.write("⚠️ **Status**: FAILED\n\n")
                f.write("Issues were detected during testing. Please review individual test reports for details:\n\n")
                for test_name, success in test_results:
                    if not success and self.results[test_name]["status"] != "skipped":
                        report_name = {
                            "security": "SECURITY_TEST_REPORT.md",
                            "api": "API_TEST_REPORT.md",
                            "database": "DB_CONSISTENCY_REPORT.md",
                            "performance": "PERFORMANCE_TEST_REPORT.md"
                        }.get(test_name, "")
                        f.write(f"- [ ] Fix issues in **{test_name}** - see `{report_name}`\n")

                f.write("\n### Action Items\n\n")
                f.write("1. Review all failed test reports\n")
                f.write("2. Fix critical security vulnerabilities first\n")
                f.write("3. Address data integrity issues\n")
                f.write("4. Optimize performance bottlenecks\n")
                f.write("5. Re-run tests after fixes\n")
            else:
                f.write("✅ **Status**: PASSED\n\n")
                f.write("All tests passed successfully! The system is ready for Phase 2 implementation.\n\n")
                f.write("### Next Steps\n\n")
                f.write("1. Proceed with Phase 2 - Cache Improvements\n")
                f.write("2. Continue monitoring performance metrics\n")
                f.write("3. Schedule regular testing cadence\n")

            # Individual report links
            f.write("\n## Individual Test Reports\n\n")
            f.write("For detailed findings, see:\n\n")
            f.write("- [Security Test Report](SECURITY_TEST_REPORT.md)\n")
            f.write("- [API Integration Test Report](API_TEST_REPORT.md)\n")
            f.write("- [Database Consistency Report](DB_CONSISTENCY_REPORT.md)\n")
            f.write("- [Performance Benchmark Report](PERFORMANCE_TEST_REPORT.md)\n")

        print(f"\n📄 Consolidated report saved to: {report_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run comprehensive testing suite")
    parser.add_argument("--skip-security", action="store_true", help="Skip security tests")
    parser.add_argument("--skip-api", action="store_true", help="Skip API integration tests")
    parser.add_argument("--skip-database", action="store_true", help="Skip database consistency checks")
    parser.add_argument("--skip-performance", action="store_true", help="Skip performance benchmarks")
    parser.add_argument("--only-security", action="store_true", help="Run only security tests")
    parser.add_argument("--only-api", action="store_true", help="Run only API tests")
    parser.add_argument("--only-database", action="store_true", help="Run only database checks")
    parser.add_argument("--only-performance", action="store_true", help="Run only performance tests")

    args = parser.parse_args()

    # Determine which tests to skip
    skip_tests = []
    if args.skip_security:
        skip_tests.append("security")
    if args.skip_api:
        skip_tests.append("api")
    if args.skip_database:
        skip_tests.append("database")
    if args.skip_performance:
        skip_tests.append("performance")

    # Determine if only specific tests should run
    only_tests = []
    if args.only_security:
        only_tests.append("security")
    if args.only_api:
        only_tests.append("api")
    if args.only_database:
        only_tests.append("database")
    if args.only_performance:
        only_tests.append("performance")

    # Run tests
    runner = MasterTestRunner(skip_tests=skip_tests, only_tests=only_tests if only_tests else None)
    runner.run_all_tests()


if __name__ == "__main__":
    main()
