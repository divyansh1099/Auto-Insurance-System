#!/bin/bash
# Cleanup Script for Auto-Insurance-System
# Removes unnecessary temporary files and caches

echo "======================================================================"
echo "Auto-Insurance-System Cleanup Script"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cleanup_count=0

# 1. Remove Python cache files
echo "🧹 Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type f -name "*.pyd" -delete 2>/dev/null
echo -e "${GREEN}✓ Python cache files removed${NC}"
((cleanup_count++))

# 2. Remove test artifacts
echo ""
echo "🧹 Cleaning test artifacts..."
rm -f /tmp/test_run_timestamp.pkl 2>/dev/null
rm -f tests/*.pyc 2>/dev/null
rm -rf tests/__pycache__ 2>/dev/null
rm -rf .pytest_cache 2>/dev/null
echo -e "${GREEN}✓ Test artifacts removed${NC}"
((cleanup_count++))

# 3. Remove OS-specific files
echo ""
echo "🧹 Cleaning OS-specific files..."
find . -name ".DS_Store" -delete 2>/dev/null
find . -name "Thumbs.db" -delete 2>/dev/null
find . -name "*.swp" -delete 2>/dev/null
find . -name "*.swo" -delete 2>/dev/null
find . -name "*~" -delete 2>/dev/null
echo -e "${GREEN}✓ OS-specific files removed${NC}"
((cleanup_count++))

# 4. Remove backup files
echo ""
echo "🧹 Cleaning backup files..."
find . -name "*.bak" -delete 2>/dev/null
find . -name "*.tmp" -delete 2>/dev/null
find . -name "*.orig" -delete 2>/dev/null
echo -e "${GREEN}✓ Backup files removed${NC}"
((cleanup_count++))

# 5. Remove log files (keep directory structure)
echo ""
echo "🧹 Cleaning log files..."
find . -name "*.log" -type f -delete 2>/dev/null
echo -e "${GREEN}✓ Log files removed${NC}"
((cleanup_count++))

# 6. Remove empty directories
echo ""
echo "🧹 Removing empty directories..."
find . -type d -empty -delete 2>/dev/null
echo -e "${GREEN}✓ Empty directories removed${NC}"
((cleanup_count++))

echo ""
echo "======================================================================"
echo -e "${GREEN}✅ Cleanup Complete!${NC}"
echo "======================================================================"
echo ""
echo "Cleaned up $cleanup_count categories of files"
echo ""

# Show disk space saved (approximation)
echo "💾 Disk space status:"
du -sh . 2>/dev/null | awk '{print "   Total project size: " $1}'
echo ""

# Documentation consolidation suggestions
echo "======================================================================"
echo "📚 Documentation Consolidation Suggestions"
echo "======================================================================"
echo ""
echo -e "${YELLOW}Consider consolidating these documentation files:${NC}"
echo ""
echo "Testing Documentation (5 files - can be reduced to 2-3):"
echo "  • TESTING_PLAN.md (14K) - Keep (comprehensive plan)"
echo "  • TESTING_QUICKSTART.md (8.2K) - Keep (quick reference)"
echo "  • TESTING_GUIDE.md (9.2K) - Merge into TESTING_PLAN.md"
echo "  • TESTING_TROUBLESHOOTING.md (11K) - Keep (troubleshooting)"
echo "  • TEST_OPTIMIZATIONS.md (14K) - Merge into TESTING_PLAN.md"
echo ""
echo "Architecture Documentation (3 files - can be reduced to 1):"
echo "  • ARCHITECTURE_IMPROVEMENTS.md (36K) - Keep as master doc"
echo "  • PERFORMANCE_IMPROVEMENTS_GUIDE.md (13K) - Merge into above"
echo "  • REFACTORING_PLAN.md (8.1K) - Merge into above"
echo ""
echo "Phase 1 Documentation (3 files - can be reduced to 1):"
echo "  • PHASE1_IMPROVEMENTS_SUMMARY.md (11K) - Keep as master"
echo "  • BUG_FIXES_ANALYSIS.md (15K) - Merge into above"
echo "  • APPLY_DATABASE_INDEXES.md (4.8K) - Keep separate (operational)"
echo ""
echo "Potential consolidation:"
echo "  12 markdown files → 7 files (save ~40K, improve maintainability)"
echo ""
echo "To consolidate, run:"
echo "  bash cleanup_docs.sh"
echo ""
