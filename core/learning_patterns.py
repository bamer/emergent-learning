"""
Shared learning patterns for the ELF auto-learning system.

This module contains all error patterns and anti-patterns used by:
- learning_processor.py
- post_tool_learning.py

Centralizing these patterns ensures:
1. Single source of truth
2. Easy maintenance
3. Consistency across all learning extraction points
"""

import re

# ============================================================================
# ERROR PATTERNS FOR AUTO-LEARNING (MECHANISM 2)
# ============================================================================
# Maps specific error patterns to preventive heuristics
# When an error matches a pattern, the corresponding heuristic is extracted

ERROR_PATTERN_HEURISTICS = {
    "database": [
        (
            r"IntegrityError|UNIQUE constraint.*failed",
            "Always check for unique constraints before INSERT",
        ),
        (
            r"sqlite3\.OperationalError.*locked",
            "Database locked - use proper connection management and timeouts",
        ),
        (r"no such table", "Always verify table exists before querying"),
        (
            r"foreign key constraint",
            "Check foreign key relationships before database operations",
        ),
        (
            r"OperationalError.*database is locked",
            "Use connection pooling or retry logic for database locks",
        ),
    ],
    "filesystem": [
        (r"FileNotFoundError", "Check file exists before accessing"),
        (
            r"Permission denied",
            "Verify file/directory permissions before write operations",
        ),
        (
            r"NotADirectoryError|Is.*is a directory",
            "Use path.is_dir()/is_file() to check path type",
        ),
        (r"No space left on device", "Check disk space before write operations"),
        (r"[Oo]SError.*File exists", "Check file existence before exclusive creation"),
    ],
    "network": [
        (r"ConnectionRefusedError", "Service unavailable - check if server is running"),
        (r"TimeoutError|timed out", "Add proper timeout handling for network requests"),
        (r"HTTP 4\d\d", "Client error - check request parameters"),
        (
            r"HTTP 5\d\d",
            "Server error - implement retry logic with exponential backoff",
        ),
        (r"urllib\.error\.URLError", "Handle network errors gracefully with retries"),
    ],
    "json": [
        (r"JSONDecodeError|Expecting.*delimiter", "Validate JSON before parsing"),
        (r"json\.loads.*failed", "Check JSON structure and encoding"),
    ],
    "python": [
        (r"ModuleNotFoundError", "Install missing dependencies or check import path"),
        (r"ImportError.*No module named", "Verify module name and installation"),
        (
            r"AttributeError.*has no attribute",
            "Check object type before accessing attribute",
        ),
        (
            r"TypeError.*not supported between",
            "Check data types before operations",
        ),
        (r"NameError.*is not defined", "Verify variable scope and initialization"),
    ],
    "asyncio": [
        (
            r"RuntimeError.*event loop is closed",
            "Check event loop state before scheduling tasks",
        ),
        (r"asyncio\.CancelledError", "Handle task cancellation gracefully"),
        (r"Future.*already awaited", "Use proper await patterns, avoid double-await"),
        (
            r"RuntimeWarning.*coroutine.*never awaited",
            "Ensure coroutines are properly awaited",
        ),
    ],
    "react": [
        (
            r"RenderError.*cyclic dependency",
            "Check for circular component dependencies",
        ),
        (
            r"Cannot read.*of (undefined|null)",
            "Add proper null checks before property access",
        ),
        (r"Warning.*deprecated", "Replace deprecated APIs with modern alternatives"),
        (r"Warning.*key prop missing", "Always provide unique keys for list items"),
        (
            r"Maximum.*update.*depth exceeded",
            "Check for infinite loops in component renders",
        ),
    ],
}


# ============================================================================
# ANTI-PATTERN MAPPINGS (MECHANISM 3)
# ============================================================================
# Maps code anti-patterns to best practice heuristics
# When an anti-pattern is detected, the corresponding best practice is extracted

ANTI_PATTERN_HEURISTICS = {
    "security": [
        (
            r"eval\s*\(",
            "Never use eval() - use safe alternatives like literal_eval or JSON parsing",
        ),
        (
            r"exec\s*\(",
            "Never use exec() - dangerous code injection risk",
        ),
        (
            r"shell\s*=\s*True",
            "Avoid shell=True in subprocess - use list of args instead",
        ),
        (
            r'password\s*=\s*[\'"\']',
            "Never hardcode passwords - use environment variables",
        ),
        (
            r'api_key\s*=\s*[\'"\']',
            "Never hardcode API keys - use secrets management",
        ),
        (
            r'token\s*=\s*[\'"\']',
            "Never hardcode tokens - use secrets management",
        ),
    ],
    "performance": [
        (
            r"open\(.*(?:(?!with|close).)*",
            "Always use context managers (with statements) for file operations",
        ),
        (r"while\s+True:", "Infinite loops should have exit conditions"),
        (
            r"recursion.*depth",
            re.IGNORECASE,
            "For deep recursion, consider iterative alternatives or increase recursion limit",
        ),
        (
            r"list\((?!.*items\(\))",
            "Consider using itertools for large list comprehensions",
        ),
    ],
    "testing": [
        (
            r"assert.*==",
            re.IGNORECASE,
            "For floats, use assertAlmost... instead of ==",
        ),
        (
            r"time\.sleep\(.*test",
            re.IGNORECASE,
            "Avoid time.sleep() in tests - use mocks instead",
        ),
        (
            r"open\(.*test",
            re.IGNORECASE,
            "Use tempfile or fixtures in tests instead of real files",
        ),
    ],
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def match_error_pattern(error_text: str) -> list:
    """
    Match error text against all error patterns.

    Returns:
        List of (domain, pattern, heuristic_text) tuples that matched
    """
    matches = []

    for domain, patterns in ERROR_PATTERN_HEURISTICS.items():
        for pattern_entry in patterns:
            # Handle both tuple (pattern, heuristic) and tuple (pattern, heuristic, flags) formats
            if len(pattern_entry) == 3:
                pattern, heuristic_text, flags = pattern_entry
                match = re.search(pattern, error_text, flags)
            else:  # len == 2
                pattern, heuristic_text = pattern_entry
                match = re.search(pattern, error_text)

            if match:
                matches.append((domain, pattern, heuristic_text))

    return matches


def match_anti_pattern(code_text: str) -> list:
    """
    Match code text against all anti-patterns.

    Returns:
        List of (domain, pattern, heuristic_text) tuples that matched
    """
    matches = []

    for domain, patterns in ANTI_PATTERN_HEURISTICS.items():
        for pattern_entry in patterns:
            # Handle both tuple (pattern, heuristic) and tuple (pattern, heuristic, flags) formats
            if len(pattern_entry) == 3:
                pattern, heuristic_text, flags = pattern_entry
                match = re.search(pattern, code_text, flags)
            else:  # len == 2
                pattern, heuristic_text = pattern_entry
                match = re.search(pattern, code_text)

            if match:
                matches.append((domain, pattern, heuristic_text))

    return matches


def match_anti_pattern(code_text: str) -> list:
    """
    Match code text against all anti-patterns.

    Returns:
        List of (domain, pattern, heuristic_text) tuples that matched
    """
    matches = []

    for domain, patterns in ANTI_PATTERN_HEURISTICS.items():
        for pattern_entry in patterns:
            # Handle both tuple and list formats (can have flags)
            if isinstance(pattern_entry, tuple):
                if len(pattern_entry) == 3:
                    # Check if the third element is a flag object or a string
                    pattern, heuristic_text, flags = pattern_entry
                    if isinstance(flags, str):
                        # Skip string-based flags (like 're.IGNORECASE')
                        match = None
                    elif flags:
                        match = re.search(pattern, code_text, flags)
                    else:
                        match = re.search(pattern, code_text)
                else:
                    pattern, heuristic_text = pattern_entry
                    match = re.search(pattern, code_text)

                if match:
                    matches.append((domain, pattern, heuristic_text))

    return matches
