#!/bin/bash
set -e

TESTS_PASSED=0

pass() {
    echo -e "✓ PASS: $*"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "✗ FAIL: $*"
    ((TESTS_FAILED++))
}

echo "Test 1: Direct call"
pass "Direct test"
echo "Passed: $TESTS_PASSED"

echo "Test 2: Function call"
test_func() {
    pass "Function test"
}

test_func
echo "Passed: $TESTS_PASSED"
