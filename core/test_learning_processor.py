#!/usr/bin/env python3
"""
Tests for improved LearningProcessor.

Tests key improvements:
1. Shared pattern imports from learning_patterns.py
2. Database connection management
3. Refactored _extract_file_paths
4. Error context and anti-pattern extraction
"""

import sys
import json
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import unified ELF logger
try:
    from Open_ELF.utils.elf_logging import (
        get_logger,
        log_info,
        log_error,
        log_warning,
        log_debug,
    )

    logger = get_logger("test_learning_processor")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

try:
    from learning_processor import LearningProcessor, ToolEvent
    from learning_patterns import match_error_pattern, match_anti_pattern
except ImportError as e:
    logger.error(f"Import error: {e}", exc_info=True)
    sys.exit(1)


def test_shared_patterns():
    """Test that shared patterns are imported correctly."""
    logger.info("\n=== Test 1: Shared Pattern Imports ===")

    # Test error pattern matching
    error_text = "sqlite3.OperationalError: database is locked"
    matches = match_error_pattern(error_text)
    logger.info(f"Error matches for '{error_text[:40]}...': {len(matches)}")

    for domain, pattern, heuristic in matches:
        logger.debug(f"  [{domain}] {heuristic[:50]}...")

    assert len(matches) > 0, "Should match database lock error"
    logger.info("✓ Shared error patterns work correctly")

    # Test anti-pattern matching
    code_text = "result = eval(user_input)"
    matches = match_anti_pattern(code_text)
    logger.info(f"Anti-pattern matches for '{code_text[:30]}...': {len(matches)}")

    for domain, pattern, heuristic in matches:
        logger.debug(f"  [{domain}] {heuristic[:50]}...")

    assert len(matches) > 0, "Should match eval anti-pattern"
    print("✓ Shared anti-patterns work correctly")


def test_file_path_extraction():
    """Test refactored _extract_file_paths."""
    print("\n=== Test 2: File Path Extraction ===")

    processor = LearningProcessor()

    # Test Read tool
    tool_input = {"file_path": "/path/to/file.txt"}
    paths = processor._extract_file_paths("Read", tool_input)
    print(f"Read tool paths: {paths}")
    assert paths == ["/path/to/file.txt"], "Should extract file_path"
    print("✓ Read tool extraction works")

    # Test Edit tool with nested input
    tool_input = {
        "input": {"file_path": "/path/to/file.txt", " filePath": "/path/to/other.txt"}
    }
    paths = processor._extract_file_paths("Edit", tool_input)
    print(f"Edit tool (nested) paths: {paths}")
    assert "/path/to/file.txt" in paths, "Should extract from nested input"
    print("✓ Edit tool nested extraction works")

    # Test Bash tool
    tool_input = {"command": "cat /path/to/file.py | grep foo"}
    paths = processor._extract_file_paths("Bash", tool_input)
    print(f"Bash tool paths: {paths}")
    assert "/path/to/file.py" in paths, "Should extract from bash command"
    print("✓ Bash tool extraction works")


def test_error_context_extraction():
    """Test error context learning extraction."""
    print("\n=== Test 3: Error Context Extraction ===")

    processor = LearningProcessor()

    # Test various error types
    test_cases = [
        {
            "error": "FileNotFoundError: config.yaml not found",
            "expected_domain": "filesystem",
        },
        {
            "error": "sqlite3.OperationalError: database is locked",
            "expected_domain": "database",
        },
        {
            "error": "ConnectionRefusedError: Cannot connect to localhost",
            "expected_domain": "network",
        },
    ]

    for test in test_cases:
        learnings = processor._extract_error_context_learnings(
            test["error"], "TestTool"
        )
        print(f"Error: '{test['error'][:40]}...' -> {len(learnings)} learnings")

        if learnings:
            for learning in learnings:
                print(f"  [{learning['domain']}] {learning['rule'][:50]}...")
            assert learning["domain"] == test["expected_domain"], (
                f"Wrong domain: {learning['domain']} != {test['expected_domain']}"
            )

        assert len(learnings) > 0, (
            f"Should extract learning from {test['expected_domain']} error"
        )

    print("✓ Error context extraction works for all test cases")


def test_anti_pattern_extraction():
    """Test anti-pattern learning extraction."""
    print("\n=== Test 4: Anti-Pattern Extraction ===")

    processor = LearningProcessor()

    # Test various anti-patterns
    test_cases = [
        {
            "code": "result = eval(user_input)",
            "expected_domain": "security",
            "expected_keyword": "never",
        },
        {
            "code": "f = open('file.txt', 'r')",
            "expected_domain": "performance",
            "expected_keyword": "context",
        },
        {
            "code": "password = 'secret123'",
            "expected_domain": "security",
            "expected_keyword": "environment",
        },
    ]

    for test in test_cases:
        learnings = processor._extract_anti_pattern_learnings(test["code"])
        print(f"Code: '{test['code'][:30]}...' -> {len(learnings)} learnings")

        if learnings:
            for learning in learnings:
                print(f"  [{learning['domain']}] {learning['rule'][:50]}...")
                assert learning["domain"] == test["expected_domain"]
                assert test["expected_keyword"].lower() in learning["rule"].lower()

        assert len(learnings) > 0, (
            f"Should extract learning from {test['expected_domain']} anti-pattern"
        )

    print("✓ Anti-pattern extraction works for all test cases")


def test_deduplication():
    """Test that duplicate learnings are removed."""
    print("\n=== Test 5: Deduplication ===")

    processor = LearningProcessor()

    # Test with duplicate patterns
    code = """
    # First instance
    result = eval(input())
    # Second instance (same pattern, different line)
    output = eval(data)
    """

    learnings = processor._extract_anti_pattern_learnings(code)
    print(f"Code with 2 eval() calls -> {len(learnings)} leanings")

    # Should only return one learning (deduplicated)
    assert len(learnings) == 1, "Should deduplicate identical anti-patterns"

    print("✓ Deduplication works correctly")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Testing Improved LearningProcessor")
    print("=" * 70)

    try:
        test_shared_patterns()
        test_file_path_extraction()
        test_error_context_extraction()
        test_anti_pattern_extraction()
        test_deduplication()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)

    except AssertionError as e:
        import traceback

        print(f"\n❌ TEST FAILED: {e}")
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
