#!/bin/bash
# Open_ELF Validation Script
# Tests that all critical components are working

set -e

ELF_ROOT="/home/bamer/.opencode/emergent-learning/Open_ELF"
FAILED=0

echo "=========================================="
echo "🔍 Open_ELF Validation Tests"
echo "=========================================="
echo ""

# Test 1: Directory structure
echo "📁 Test 1: Directory Structure"
for dir in agents config coordinator dashboard-app database docs golden-rules memory orchestrator query scripts skills workflows; do
    if [ -d "$ELF_ROOT/$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ MISSING"
        FAILED=$((FAILED + 1))
    fi
done
echo ""

# Test 2: Critical scripts
echo "🔧 Test 2: Critical Scripts"
for script in record-failure.sh record-heuristic.py record-success.sh self-test.sh learning-metrics.sh; do
    if [ -f "$ELF_ROOT/scripts/$script" ]; then
        echo "  ✅ $script"
    else
        echo "  ❌ $script MISSING"
        FAILED=$((FAILED + 1))
    fi
done
echo ""

# Test 3: Query system
echo "🗄️  Test 3: Query System"
if python3 "$ELF_ROOT/query/query.py" --context > /dev/null 2>&1; then
    echo "  ✅ Query system responds"
else
    echo "  ❌ Query system failed"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: Memory system
echo "🧠 Test 4: Memory System"
if [ -f "$ELF_ROOT/memory/elf_memory.db" ] || [ -f "$ELF_ROOT/memory/building.db" ]; then
    echo "  ✅ Memory databases present"
else
    echo "  ⚠️  Memory databases not found (will be created on first use)"
fi
echo ""

# Test 5: Skills
echo "🎓 Test 5: Skills"
SKILL_COUNT=$(find "$ELF_ROOT/skills" -name "SKILL.md" 2>/dev/null | wc -l)
if [ "$SKILL_COUNT" -gt 0 ]; then
    echo "  ✅ $SKILL_COUNT skills found"
else
    echo "  ⚠️  No skills found"
fi
echo ""

# Test 6: Orchestrator
echo "🎼 Test 6: Orchestrator"
if [ -f "$ELF_ROOT/orchestrator/orchestrator.py" ]; then
    echo "  ✅ Orchestrator present"
else
    echo "  ❌ Orchestrator missing"
    FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ All tests passed! Open_ELF is ready."
    exit 0
else
    echo "❌ $FAILED test(s) failed. Please review."
    exit 1
fi
