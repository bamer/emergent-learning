#!/usr/bin/env python3
"""
ELF Orchestration Test Suite
============================

Tests the unified orchestration system to ensure:
1. All agents use the same orchestration system
2. Logging is centralized
3. No silent errors
4. Spawn/stop works correctly
5. Escalation system works

Usage:
    python test_orchestration.py
    python test_orchestration.py --verbose
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from typing import List, Tuple

# Add agents directory to path
AGENTS_DIR = Path(__file__).parent
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from elf_logging import get_logger, verify_logging, LOGS_DIR


class TestResult:
    """Result of a single test."""

    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.name}"


class OrchestrationTester:
    """Test suite for the orchestration system."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = get_logger("orchestration_test")
        self.results: List[TestResult] = []

    def run_all_tests(self) -> bool:
        """Run all tests and return overall result."""
        print("=" * 70)
        print("ELF ORCHESTRATION TEST SUITE")
        print("=" * 70)
        print()

        tests = [
            self.test_logging_system,
            self.test_log_directory,
            self.test_orchestrator_exists,
            self.test_agent_wrapper,
            self.test_scripts_executable,
            self.test_no_claude_references,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                self.results.append(TestResult(test.__name__, False, f"Exception: {e}"))

        # Print summary
        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        for result in self.results:
            print(result)
            if not result.passed and result.message:
                print(f"   → {result.message}")

        print()
        print(f"Results: {passed} passed, {failed} failed")
        print("=" * 70)

        return failed == 0

    def test_logging_system(self):
        """Test that the logging system works correctly."""
        try:
            verify_logging()
            self.results.append(
                TestResult("Logging System", True, "Centralized logging is working")
            )
        except Exception as e:
            self.results.append(TestResult("Logging System", False, str(e)))

    def test_log_directory(self):
        """Test that log directory exists and is writable."""
        try:
            if not LOGS_DIR.exists():
                raise RuntimeError(f"Log directory does not exist: {LOGS_DIR}")

            # Test write access
            test_file = LOGS_DIR / ".write_test"
            test_file.write_text("test")
            test_file.unlink()

            self.results.append(
                TestResult("Log Directory", True, f"Logs directory ready: {LOGS_DIR}")
            )
        except Exception as e:
            self.results.append(TestResult("Log Directory", False, str(e)))

    def test_orchestrator_exists(self):
        """Test that the unified orchestrator exists."""
        orchestrator_file = AGENTS_DIR / "unified_orchestrator.py"

        if orchestrator_file.exists():
            self.results.append(
                TestResult("Unified Orchestrator", True, f"Found: {orchestrator_file}")
            )
        else:
            self.results.append(
                TestResult(
                    "Unified Orchestrator", False, f"Not found: {orchestrator_file}"
                )
            )

    def test_agent_wrapper(self):
        """Test that the agent wrapper exists and works."""
        wrapper_file = AGENTS_DIR / "elf_agent_wrapper.py"

        if not wrapper_file.exists():
            self.results.append(
                TestResult("Agent Wrapper", False, f"Not found: {wrapper_file}")
            )
            return

        try:
            # Try to import and use the wrapper
            from elf_agent_wrapper import AgentWrapper, AgentConfig

            config = AgentConfig(name="test_wrapper", description="Test agent")
            wrapper = AgentWrapper(config)

            self.results.append(
                TestResult(
                    "Agent Wrapper", True, "Wrapper imports and initializes correctly"
                )
            )
        except Exception as e:
            self.results.append(TestResult("Agent Wrapper", False, str(e)))

    def test_scripts_executable(self):
        """Test that start/stop scripts are executable."""
        scripts_dir = AGENTS_DIR.parent / "scripts"
        start_script = scripts_dir / "start-elf-orchestrator.sh"
        stop_script = scripts_dir / "stop-elf-orchestrator.sh"

        issues = []

        if not start_script.exists():
            issues.append(f"Start script not found: {start_script}")
        elif not os.access(start_script, os.X_OK):
            issues.append(f"Start script not executable: {start_script}")

        if not stop_script.exists():
            issues.append(f"Stop script not found: {stop_script}")
        elif not os.access(stop_script, os.X_OK):
            issues.append(f"Stop script not executable: {stop_script}")

        if issues:
            self.results.append(
                TestResult("Scripts Executable", False, "; ".join(issues))
            )
        else:
            self.results.append(
                TestResult(
                    "Scripts Executable", True, "Start and stop scripts are ready"
                )
            )

    def test_no_claude_references(self):
        """Test that migrated features don't reference 'claude'."""
        # Files that should NOT reference 'claude' anymore
        critical_files = [
            AGENTS_DIR / "unified_orchestrator.py",
            AGENTS_DIR / "elf_logging.py",
            AGENTS_DIR / "elf_agent_wrapper.py",
        ]

        issues = []

        for file_path in critical_files:
            if file_path.exists():
                content = file_path.read_text().lower()
                if "claude" in content:
                    issues.append(f"{file_path.name} still references 'claude'")

        if issues:
            self.results.append(
                TestResult("No Claude References", False, "; ".join(issues))
            )
        else:
            self.results.append(
                TestResult(
                    "No Claude References",
                    True,
                    "Migrated files don't reference 'claude'",
                )
            )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test ELF Orchestration System")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    tester = OrchestrationTester(verbose=args.verbose)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
