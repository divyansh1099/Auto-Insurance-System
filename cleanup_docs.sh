#!/bin/bash
# Documentation Consolidation Script
# Consolidates redundant documentation files

echo "======================================================================"
echo "Documentation Consolidation Script"
echo "======================================================================"
echo ""
echo "⚠️  WARNING: This will merge and remove documentation files."
echo "   A backup will be created before consolidation."
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Create backup directory
BACKUP_DIR="docs_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 Creating backup in $BACKUP_DIR..."
cp *.md "$BACKUP_DIR/" 2>/dev/null
echo "✓ Backup created"
echo ""

# 1. Consolidate Testing Documentation
echo "📝 Consolidating testing documentation..."
cat > TESTING_COMPREHENSIVE.md <<'EOF'
# Comprehensive Testing Documentation

This document consolidates all testing information for the Auto-Insurance-System Phase 1.

**Last Updated**: $(date +%Y-%m-%d)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Testing Plan](#testing-plan)
3. [Test Optimizations](#test-optimizations)
4. [Troubleshooting](#troubleshooting)

---

EOF

# Append relevant sections from each file
echo "## Quick Start" >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md
tail -n +5 TESTING_QUICKSTART.md >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md
echo "---" >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md

echo "## Testing Plan" >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md
tail -n +5 TESTING_PLAN.md >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md
echo "---" >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md

echo "## Test Optimizations" >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md
tail -n +5 TEST_OPTIMIZATIONS.md >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md
echo "---" >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md

echo "## Troubleshooting" >> TESTING_COMPREHENSIVE.md
echo "" >> TESTING_COMPREHENSIVE.md
tail -n +5 TESTING_TROUBLESHOOTING.md >> TESTING_COMPREHENSIVE.md

echo "✓ Created TESTING_COMPREHENSIVE.md"

# Remove consolidated files
rm -f TESTING_QUICKSTART.md TESTING_PLAN.md TEST_OPTIMIZATIONS.md
echo "✓ Removed: TESTING_QUICKSTART.md, TESTING_PLAN.md, TEST_OPTIMIZATIONS.md"
echo "✓ Kept: TESTING_GUIDE.md (for reference), TESTING_TROUBLESHOOTING.md (standalone)"
echo ""

# 2. Consolidate Architecture Documentation
echo "📝 Consolidating architecture documentation..."
cat > ARCHITECTURE_COMPLETE.md <<'EOF'
# Complete Architecture Documentation

This document consolidates all architecture improvements for the Auto-Insurance-System.

**Last Updated**: $(date +%Y-%m-%d)

---

## Table of Contents

1. [Architecture Improvements](#architecture-improvements)
2. [Performance Improvements](#performance-improvements)
3. [Refactoring Plan](#refactoring-plan)

---

EOF

echo "## Architecture Improvements" >> ARCHITECTURE_COMPLETE.md
echo "" >> ARCHITECTURE_COMPLETE.md
tail -n +5 ARCHITECTURE_IMPROVEMENTS.md >> ARCHITECTURE_COMPLETE.md
echo "" >> ARCHITECTURE_COMPLETE.md
echo "---" >> ARCHITECTURE_COMPLETE.md
echo "" >> ARCHITECTURE_COMPLETE.md

echo "## Performance Improvements" >> ARCHITECTURE_COMPLETE.md
echo "" >> ARCHITECTURE_COMPLETE.md
tail -n +5 PERFORMANCE_IMPROVEMENTS_GUIDE.md >> ARCHITECTURE_COMPLETE.md
echo "" >> ARCHITECTURE_COMPLETE.md
echo "---" >> ARCHITECTURE_COMPLETE.md
echo "" >> ARCHITECTURE_COMPLETE.md

echo "## Refactoring Plan" >> ARCHITECTURE_COMPLETE.md
echo "" >> ARCHITECTURE_COMPLETE.md
tail -n +5 REFACTORING_PLAN.md >> ARCHITECTURE_COMPLETE.md

echo "✓ Created ARCHITECTURE_COMPLETE.md"

# Remove consolidated files
rm -f ARCHITECTURE_IMPROVEMENTS.md PERFORMANCE_IMPROVEMENTS_GUIDE.md REFACTORING_PLAN.md
echo "✓ Removed: ARCHITECTURE_IMPROVEMENTS.md, PERFORMANCE_IMPROVEMENTS_GUIDE.md, REFACTORING_PLAN.md"
echo ""

# 3. Consolidate Phase 1 Documentation
echo "📝 Consolidating Phase 1 documentation..."
cat > PHASE1_COMPLETE.md <<'EOF'
# Phase 1 Complete Documentation

This document consolidates all Phase 1 improvements and bug fixes.

**Last Updated**: $(date +%Y-%m-%d)

---

## Table of Contents

1. [Phase 1 Summary](#phase-1-summary)
2. [Bug Fixes Analysis](#bug-fixes-analysis)

---

EOF

echo "## Phase 1 Summary" >> PHASE1_COMPLETE.md
echo "" >> PHASE1_COMPLETE.md
tail -n +5 PHASE1_IMPROVEMENTS_SUMMARY.md >> PHASE1_COMPLETE.md
echo "" >> PHASE1_COMPLETE.md
echo "---" >> PHASE1_COMPLETE.md
echo "" >> PHASE1_COMPLETE.md

echo "## Bug Fixes Analysis" >> PHASE1_COMPLETE.md
echo "" >> PHASE1_COMPLETE.md
tail -n +5 BUG_FIXES_ANALYSIS.md >> PHASE1_COMPLETE.md

echo "✓ Created PHASE1_COMPLETE.md"

# Remove consolidated files
rm -f PHASE1_IMPROVEMENTS_SUMMARY.md BUG_FIXES_ANALYSIS.md
echo "✓ Removed: PHASE1_IMPROVEMENTS_SUMMARY.md, BUG_FIXES_ANALYSIS.md"
echo "✓ Kept: APPLY_DATABASE_INDEXES.md (operational guide)"
echo ""

# Summary
echo "======================================================================"
echo "✅ Documentation Consolidation Complete!"
echo "======================================================================"
echo ""
echo "Results:"
echo "  • Created 3 consolidated documentation files"
echo "  • Removed 8 redundant files"
echo "  • Backup available in: $BACKUP_DIR/"
echo ""
echo "Remaining documentation files:"
ls -1h *.md | awk '{print "  • " $0}'
echo ""
echo "To restore from backup:"
echo "  cp $BACKUP_DIR/*.md ."
echo ""
