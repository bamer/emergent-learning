#!/usr/bin/env python3
"""
Open_ELF Migration Tool
=======================

Helps migrate existing code to use the new core modules
and eliminate code duplication.

Features:
- Analyzes Python files for duplicate patterns
- Identifies components using custom implementations vs core modules
- Provides automated migration suggestions
- Ensures safe transition without breaking existing functionality
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set
import sys

# Core module imports
CORE_MODULES = {
    "database": "from core.database import get_connection, execute_query, execute_transaction",
    "logging": "from core.openelf_logging import setup_logger, get_logger",
    "config": "from core.config import get_config, set_config",
    "utils": "from lib.utils import resolve_path, validate_file, format_timestamp",
}

# Patterns to identify
PATTERNS = {
    "sqlite_connection": [
        r"sqlite3\.connect",
        r"sqlite3\.Connection",
        r"\.db\b",
        r"\.sqlite\b",
    ],
    "logging_setup": [
        r"logging\.basicConfig",
        r"logging\.getLogger",
        r"logger\s*=\s*logging\.getLogger",
        r"logging\.FileHandler",
        r"logging\.StreamHandler",
    ],
    "file_operations": [
        r"open\(.*\.read\(\)",
        r"open\(.*\.write\(\)",
        r"Path\(.*\.exists\(\)",
        r"os\.path\.exists",
        r"os\.path\.join",
    ],
    "config_access": [
        r"json\.load",
        r"json\.dump",
        r"yaml\.load",
        r"yaml\.dump",
        r"config\.json",
        r"\.env",
    ],
}


def analyze_file(file_path: Path) -> Dict[str, List[str]]:
    """Analyze a Python file for patterns."""

    findings = {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for existing core module imports
        imports = []
        for module in CORE_MODULES.keys():
            if f"import {module}" in content or f"from {module}" in content:
                imports.append(module)

        # Check for patterns
        for pattern_name, patterns in PATTERNS.items():
            matches = []
            for pattern in patterns:
                matches.extend(re.findall(pattern, content))

            if matches:
                findings[pattern_name] = matches

        # Check for duplicate imports
        if imports:
            findings["already_using_core"] = imports

    except Exception as e:
        findings["error"] = [f"Could not analyze file: {e}"]

    return findings


def suggest_migration(
    file_path: Path, findings: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """Suggest migration actions based on findings."""

    suggestions = {}

    if "sqlite_connection" in findings:
        suggestions["database"] = [
            "Replace sqlite3.connect() with core.database.get_connection()",
            "Use execute_query() and execute_transaction() for database operations",
            "Remove manual connection management",
        ]

    if "logging_setup" in findings:
        suggestions["logging"] = [
            "Replace logging.basicConfig() with core.openelf_logging.setup_logger()",
            "Use get_logger() instead of logging.getLogger()",
            "Consolidate logging configuration",
        ]

    if "file_operations" in findings:
        suggestions["utils"] = [
            "Use lib.utils.resolve_path() for path resolution",
            "Use lib.utils.validate_file() for file validation",
            "Consolidate file operations",
        ]

    if "config_access" in findings:
        suggestions["config"] = [
            "Use core.config.get_config() for configuration access",
            "Replace manual JSON/YAML parsing with config module",
            "Centralize configuration management",
        ]

    return suggestions


def generate_migration_patch(file_path: Path, findings: Dict[str, List[str]]) -> str:
    """Generate a migration patch for the file."""

    suggestions = suggest_migration(file_path, findings)
    patch_lines = []

    if suggestions:
        patch_lines.append(f"# Migration suggestions for {file_path.name}")
        patch_lines.append("")

        for module, actions in suggestions.items():
            patch_lines.append(f"# {module.upper()} MODULE")
            for action in actions:
                patch_lines.append(f"# - {action}")
            patch_lines.append("")

        # Add import suggestions
        modules_needed = list(suggestions.keys())
        if modules_needed:
            patch_lines.append("# Suggested imports:")
            for module in modules_needed:
                patch_lines.append(CORE_MODULES[module])
            patch_lines.append("")

    return "\n".join(patch_lines)


def scan_directory(directory: Path) -> Dict[str, Dict]:
    """Scan a directory for migration opportunities."""

    results = {}

    for py_file in directory.rglob("*.py"):
        # Skip core modules themselves
        if "core" in str(py_file) or "lib" in str(py_file):
            continue

        findings = analyze_file(py_file)
        if findings:
            results[str(py_file)] = {
                "findings": findings,
                "suggestions": suggest_migration(py_file, findings),
                "patch": generate_migration_patch(py_file, findings),
            }

    return results


def generate_migration_report(results: Dict[str, Dict]) -> str:
    """Generate a comprehensive migration report."""

    report_lines = ["Open_ELF Migration Report", "=" * 60, ""]

    # Summary statistics
    total_files = len(results)
    modules_needed = set()

    for file_path, data in results.items():
        modules_needed.update(data["suggestions"].keys())

    report_lines.extend(
        [
            f"Files analyzed: {total_files}",
            f"Core modules needed: {', '.join(sorted(modules_needed))}",
            "",
        ]
    )

    # Detailed findings
    for file_path, data in results.items():
        report_lines.extend([f"\nFile: {file_path}", "-" * 40])

        findings = data["findings"]
        suggestions = data["suggestions"]

        if findings:
            for finding_type, matches in findings.items():
                if finding_type != "already_using_core":
                    report_lines.append(f"Pattern: {finding_type}")
                    report_lines.append(f"  Matches: {len(matches)}")

        if suggestions:
            report_lines.append("Suggested migrations:")
            for module, actions in suggestions.items():
                report_lines.append(f"  {module}: {len(actions)} actions")

        if "already_using_core" in findings:
            report_lines.append(
                f"Already using: {', '.join(findings['already_using_core'])}"
            )

    # Migration patches
    report_lines.extend(["", "=" * 60, "MIGRATION PATCHES", "=" * 60, ""])

    for file_path, data in results.items():
        if data["patch"]:
            report_lines.append(data["patch"])
            report_lines.append("")

    return "\n".join(report_lines)


def main():
    """Main function to run migration analysis."""

    print("Open_ELF Migration Tool")
    print("=" * 60)

    # Scan orchestrator directory
    orchestrator_dir = Path(
        "/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator"
    )
    print(f"Scanning orchestrator directory: {orchestrator_dir}")

    orchestrator_results = scan_directory(orchestrator_dir)

    # Scan dashboard directory
    dashboard_dir = Path(
        "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app"
    )
    print(f"Scanning dashboard directory: {dashboard_dir}")

    dashboard_results = scan_directory(dashboard_dir)

    # Combine results
    all_results = {**orchestrator_results, **dashboard_results}

    # Generate report
    report = generate_migration_report(all_results)

    # Save report
    report_file = Path(
        "/home/bamer/.opencode/emergent-learning/Open_ELF/migration-report.md"
    )
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ Migration analysis complete!")
    print(f"📊 Files analyzed: {len(all_results)}")
    print(f"📄 Report saved to: {report_file}")

    # Show quick summary
    modules_needed = set()
    for data in all_results.values():
        modules_needed.update(data["suggestions"].keys())

    if modules_needed:
        print(f"🔧 Core modules needed: {', '.join(sorted(modules_needed))}")
    else:
        print("🎉 No migration needed - files already use core modules!")


if __name__ == "__main__":
    main()
