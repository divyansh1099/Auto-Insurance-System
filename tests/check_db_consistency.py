"""
Database Consistency Checker

Checks for:
- Referential integrity (orphaned records)
- Data validation (invalid values)
- Index existence (Phase 1 indexes)
- Constraint violations
- Data anomalies

Usage:
    python tests/check_db_consistency.py
"""
import psycopg2
from typing import List, Dict, Tuple
from datetime import datetime
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'telematics_db',
    'user': 'insurance_user',
    'password': 'insurance_pass'
}


class DatabaseConsistencyChecker:
    def __init__(self):
        self.results = []
        self.critical_issues = 0
        self.warnings = 0
        self.conn = None

    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✅ Connected to database\n")
            return True
        except Exception as e:
            print(f"❌ Cannot connect to database: {e}")
            return False

    def execute_query(self, query: str) -> List[Tuple]:
        """Execute query and return results"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []

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
            if severity == "CRITICAL":
                self.critical_issues += 1
            elif severity == "WARNING":
                self.warnings += 1

        status = "✅" if passed else ("⚠️ " if severity == "WARNING" else "❌")
        print(f"{status} {test_name}: {details}")

    # ==================== 1. REFERENTIAL INTEGRITY CHECKS ====================

    def check_orphaned_trips(self):
        """Check for trips without valid drivers"""
        print("\n--- Referential Integrity Checks ---\n")

        query = """
        SELECT COUNT(*)
        FROM trips
        WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
        """

        results = self.execute_query(query)
        if results:
            orphaned_count = results[0][0]
            passed = orphaned_count == 0

            self.log_result(
                "Orphaned Trips Check",
                passed,
                f"Found {orphaned_count} orphaned trips" if not passed else "No orphaned trips",
                "CRITICAL" if not passed else "INFO"
            )

    def check_orphaned_vehicles(self):
        """Check for vehicles without valid drivers"""
        query = """
        SELECT COUNT(*)
        FROM vehicles
        WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
        """

        results = self.execute_query(query)
        if results:
            orphaned_count = results[0][0]
            passed = orphaned_count == 0

            self.log_result(
                "Orphaned Vehicles Check",
                passed,
                f"Found {orphaned_count} orphaned vehicles" if not passed else "No orphaned vehicles",
                "CRITICAL" if not passed else "INFO"
            )

    def check_orphaned_devices(self):
        """Check for devices without valid drivers"""
        query = """
        SELECT COUNT(*)
        FROM devices
        WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
        """

        results = self.execute_query(query)
        if results:
            orphaned_count = results[0][0]
            passed = orphaned_count == 0

            self.log_result(
                "Orphaned Devices Check",
                passed,
                f"Found {orphaned_count} orphaned devices" if not passed else "No orphaned devices",
                "CRITICAL" if not passed else "INFO"
            )

    def check_orphaned_users(self):
        """Check for users without valid drivers (if driver_id is set)"""
        query = """
        SELECT COUNT(*)
        FROM users
        WHERE driver_id IS NOT NULL
        AND driver_id NOT IN (SELECT driver_id FROM drivers);
        """

        results = self.execute_query(query)
        if results:
            orphaned_count = results[0][0]
            passed = orphaned_count == 0

            self.log_result(
                "Orphaned Users Check",
                passed,
                f"Found {orphaned_count} users with invalid driver_id" if not passed else "All users have valid driver_id",
                "CRITICAL" if not passed else "INFO"
            )

    def check_orphaned_premiums(self):
        """Check for premiums without valid drivers"""
        query = """
        SELECT COUNT(*)
        FROM premiums
        WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
        """

        results = self.execute_query(query)
        if results:
            orphaned_count = results[0][0]
            passed = orphaned_count == 0

            self.log_result(
                "Orphaned Premiums Check",
                passed,
                f"Found {orphaned_count} orphaned premiums" if not passed else "No orphaned premiums",
                "CRITICAL" if not passed else "INFO"
            )

    def check_orphaned_risk_scores(self):
        """Check for risk scores without valid drivers"""
        query = """
        SELECT COUNT(*)
        FROM risk_scores
        WHERE driver_id NOT IN (SELECT driver_id FROM drivers);
        """

        results = self.execute_query(query)
        if results:
            orphaned_count = results[0][0]
            passed = orphaned_count == 0

            self.log_result(
                "Orphaned Risk Scores Check",
                passed,
                f"Found {orphaned_count} orphaned risk scores" if not passed else "No orphaned risk scores",
                "CRITICAL" if not passed else "INFO"
            )

    # ==================== 2. DATA VALIDATION CHECKS ====================

    def check_invalid_emails(self):
        """Check for invalid email addresses"""
        print("\n--- Data Validation Checks ---\n")

        query = """
        SELECT COUNT(*)
        FROM drivers
        WHERE email IS NOT NULL
        AND email NOT LIKE '%@%';
        """

        results = self.execute_query(query)
        if results:
            invalid_count = results[0][0]
            passed = invalid_count == 0

            self.log_result(
                "Invalid Email Addresses",
                passed,
                f"Found {invalid_count} invalid emails" if not passed else "All emails are valid",
                "WARNING" if not passed else "INFO"
            )

    def check_negative_distances(self):
        """Check for negative trip distances"""
        query = """
        SELECT COUNT(*)
        FROM trips
        WHERE distance_miles < 0;
        """

        results = self.execute_query(query)
        if results:
            invalid_count = results[0][0]
            passed = invalid_count == 0

            self.log_result(
                "Negative Trip Distances",
                passed,
                f"Found {invalid_count} trips with negative distance" if not passed else "All distances are valid",
                "CRITICAL" if not passed else "INFO"
            )

    def check_invalid_trip_times(self):
        """Check for trips where start_time > end_time"""
        query = """
        SELECT COUNT(*)
        FROM trips
        WHERE end_time IS NOT NULL
        AND start_time > end_time;
        """

        results = self.execute_query(query)
        if results:
            invalid_count = results[0][0]
            passed = invalid_count == 0

            self.log_result(
                "Invalid Trip Times",
                passed,
                f"Found {invalid_count} trips with start_time > end_time" if not passed else "All trip times are valid",
                "CRITICAL" if not passed else "INFO"
            )

    def check_invalid_risk_scores(self):
        """Check for risk scores outside 0-100 range"""
        query = """
        SELECT COUNT(*)
        FROM risk_scores
        WHERE risk_score < 0 OR risk_score > 100;
        """

        results = self.execute_query(query)
        if results:
            invalid_count = results[0][0]
            passed = invalid_count == 0

            self.log_result(
                "Invalid Risk Scores",
                passed,
                f"Found {invalid_count} risk scores outside 0-100 range" if not passed else "All risk scores are valid",
                "CRITICAL" if not passed else "INFO"
            )

    def check_negative_premiums(self):
        """Check for negative premium amounts"""
        query = """
        SELECT COUNT(*)
        FROM premiums
        WHERE base_premium < 0 OR final_premium < 0 OR monthly_premium < 0;
        """

        results = self.execute_query(query)
        if results:
            invalid_count = results[0][0]
            passed = invalid_count == 0

            self.log_result(
                "Negative Premium Amounts",
                passed,
                f"Found {invalid_count} premiums with negative amounts" if not passed else "All premium amounts are valid",
                "CRITICAL" if not passed else "INFO"
            )

    def check_future_dates(self):
        """Check for records with future dates (beyond current date)"""
        query = """
        SELECT
            (SELECT COUNT(*) FROM trips WHERE start_time > NOW()) as future_trips,
            (SELECT COUNT(*) FROM risk_scores WHERE calculation_date > CURRENT_DATE) as future_risk_scores,
            (SELECT COUNT(*) FROM premiums WHERE effective_date > CURRENT_DATE) as future_premiums;
        """

        results = self.execute_query(query)
        if results:
            future_trips, future_risk_scores, future_premiums = results[0]
            total_future = future_trips + future_risk_scores + future_premiums
            passed = total_future == 0

            details = []
            if future_trips > 0:
                details.append(f"{future_trips} future trips")
            if future_risk_scores > 0:
                details.append(f"{future_risk_scores} future risk scores")
            if future_premiums > 0:
                details.append(f"{future_premiums} future premiums")

            self.log_result(
                "Future Dates Check",
                passed,
                f"Found: {', '.join(details)}" if not passed else "No future dates detected",
                "WARNING" if not passed else "INFO"
            )

    # ==================== 3. INDEX VERIFICATION ====================

    def check_phase1_indexes(self):
        """Verify Phase 1 performance indexes exist"""
        print("\n--- Index Verification ---\n")

        expected_indexes = [
            'idx_telematics_events_driver_timestamp',
            'idx_telematics_events_event_type',
            'idx_telematics_events_timestamp',
            'idx_trips_driver_dates',
            'idx_trips_driver_id',
            'idx_trips_start_time',
            'idx_risk_scores_driver_date',
            'idx_risk_scores_driver_id',
            'idx_risk_scores_calculation_date',
            'idx_premiums_driver_effective',
            'idx_premiums_driver_id',
            'idx_premiums_status',
            'idx_devices_driver_id',
            'idx_devices_status',
            'idx_vehicles_driver_id',
            'idx_users_driver_id',
            'idx_users_username',
            'idx_users_email',
            'idx_driver_statistics_driver_date',
            'idx_driver_statistics_driver_id'
        ]

        query = """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_%'
        ORDER BY indexname;
        """

        results = self.execute_query(query)
        existing_indexes = [row[0] for row in results] if results else []

        missing_indexes = [idx for idx in expected_indexes if idx not in existing_indexes]

        if missing_indexes:
            self.log_result(
                "Phase 1 Indexes",
                False,
                f"Missing {len(missing_indexes)} indexes: {', '.join(missing_indexes[:5])}{'...' if len(missing_indexes) > 5 else ''}",
                "WARNING"
            )
        else:
            self.log_result(
                "Phase 1 Indexes",
                True,
                f"All {len(expected_indexes)} expected indexes exist",
                "INFO"
            )

        # List any extra indexes
        extra_indexes = [idx for idx in existing_indexes if idx not in expected_indexes and idx.startswith('idx_')]
        if extra_indexes:
            self.log_result(
                "Additional Indexes",
                True,
                f"Found {len(extra_indexes)} additional custom indexes",
                "INFO"
            )

    # ==================== 4. TABLE STATISTICS ====================

    def check_table_statistics(self):
        """Get table row counts and sizes"""
        print("\n--- Table Statistics ---\n")

        query = """
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            n_live_tup AS row_count
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """

        results = self.execute_query(query)
        if results:
            print("\nTable Sizes:")
            for schema, table, size, row_count in results[:10]:  # Top 10 tables
                print(f"  {table}: {row_count:,} rows, {size}")

            # Check for empty critical tables
            critical_tables = ['drivers', 'users']
            for schema, table, size, row_count in results:
                if table in critical_tables and row_count == 0:
                    self.log_result(
                        f"Empty Table: {table}",
                        False,
                        f"Critical table {table} is empty!",
                        "WARNING"
                    )

    # ==================== REPORT GENERATION ====================

    def generate_report(self):
        """Generate database consistency report"""
        print("\n" + "="*80)
        print("DATABASE CONSISTENCY REPORT")
        print("="*80 + "\n")

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests

        print(f"Total Checks Run: {total_tests}")
        print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"\nIssue Breakdown:")
        print(f"  Critical: {self.critical_issues}")
        print(f"  Warnings: {self.warnings}")

        if self.critical_issues > 0:
            print("\n⚠️  CRITICAL DATA INTEGRITY ISSUES FOUND! Database needs attention.")
        elif self.warnings > 0:
            print("\n⚠️  Warnings found. Review recommended.")
        else:
            print("\n✅ Database is consistent!")

        # Save detailed report
        report_file = "DB_CONSISTENCY_REPORT.md"
        with open(report_file, "w") as f:
            f.write("# Database Consistency Report\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Total Checks**: {total_tests}\n")
            f.write(f"**Passed**: {passed_tests}\n")
            f.write(f"**Failed**: {failed_tests}\n\n")
            f.write(f"## Issue Summary\n\n")
            f.write(f"- Critical Issues: {self.critical_issues}\n")
            f.write(f"- Warnings: {self.warnings}\n\n")
            f.write(f"## Detailed Results\n\n")

            for result in self.results:
                status = "✅ PASS" if result["passed"] else ("⚠️  WARNING" if result["severity"] == "WARNING" else "❌ FAIL")
                f.write(f"### {status} {result['test']}\n\n")
                f.write(f"- **Severity**: {result['severity']}\n")
                f.write(f"- **Details**: {result['details']}\n")
                f.write(f"- **Timestamp**: {result['timestamp']}\n\n")

        print(f"\nDetailed report saved to: {report_file}")

        return self.critical_issues == 0

    def run_all_checks(self):
        """Run all database consistency checks"""
        print("\n" + "="*80)
        print("DATABASE CONSISTENCY CHECKER")
        print("="*80 + "\n")

        if not self.connect():
            return False

        try:
            # Referential integrity checks
            self.check_orphaned_trips()
            self.check_orphaned_vehicles()
            self.check_orphaned_devices()
            self.check_orphaned_users()
            self.check_orphaned_premiums()
            self.check_orphaned_risk_scores()

            # Data validation checks
            self.check_invalid_emails()
            self.check_negative_distances()
            self.check_invalid_trip_times()
            self.check_invalid_risk_scores()
            self.check_negative_premiums()
            self.check_future_dates()

            # Index verification
            self.check_phase1_indexes()

            # Table statistics
            self.check_table_statistics()

            # Generate report
            return self.generate_report()

        finally:
            if self.conn:
                self.conn.close()
                print("\n✅ Database connection closed")


if __name__ == "__main__":
    checker = DatabaseConsistencyChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)
