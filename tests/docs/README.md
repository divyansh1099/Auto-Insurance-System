# Testing Documentation

This directory contains all testing-related documentation for the Auto-Insurance-System.

## Quick Reference

- **TESTING_QUICKSTART.md** - Fast setup guide (5-10 minutes)
- **TESTING_TROUBLESHOOTING.md** - Common issues and solutions

## Comprehensive Guides

- **TESTING_PLAN.md** - Complete test strategy and plan
- **TESTING_GUIDE.md** - Detailed testing procedures
- **TEST_OPTIMIZATIONS.md** - Performance and optimization analysis

## Test Execution

```bash
# Run all tests from project root
python run_all_tests.py

# Run individual test suites
python tests/security_test.py
python tests/test_api_integration.py
python tests/check_db_consistency.py
python tests/test_performance.py
```

## Test Suites

1. **security_test.py** - Security vulnerability testing (11 tests)
2. **test_api_integration.py** - API endpoint testing (16 tests)
3. **check_db_consistency.py** - Database integrity checks (14 tests)
4. **test_performance.py** - Performance benchmarks (9 tests)

**Total**: 50 comprehensive tests

## Current Status

✅ **49/50 tests passing (98%)**
- Security: 11/11 (100%)
- API: 16/16 (100%)
- Database: 14/14 (100%)
- Performance: 8/9 (89%) - 1 info warning

## Need Help?

1. Start with TESTING_QUICKSTART.md
2. Check TESTING_TROUBLESHOOTING.md for common issues
3. Read TESTING_PLAN.md for complete details
