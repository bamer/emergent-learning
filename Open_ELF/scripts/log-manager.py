#!/usr/bin/env python3
"""
Open_ELF Log Manager
Consolidates and manages log files to eliminate duplication
"""

import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

LOGS_DIR = Path("/home/bamer/OPC_ELF/Open_ELF/logs")


def analyze_log_files() -> Dict[str, List[Path]]:
    """Analyze log files and group them by type."""

    if not LOGS_DIR.exists():
        print(f"Logs directory not found: {LOGS_DIR}")
        return {}

    log_files = list(LOGS_DIR.glob("*.log"))
    log_files.extend(list(LOGS_DIR.glob("*.gz")))

    categories = {
        "self_test": [],
        "orchestrator": [],
        "dashboard": [],
        "generic": [],
        "empty": [],
        "duplicate": [],
    }

    for log_file in log_files:
        # Check file size
        if log_file.stat().st_size == 0:
            categories["empty"].append(log_file)
            continue

        # Categorize by filename pattern
        filename = log_file.name

        if "self-test" in filename.lower():
            categories["self_test"].append(log_file)
        elif "orchestrator" in filename.lower():
            categories["orchestrator"].append(log_file)
        elif any(x in filename.lower() for x in ["dashboard", "backend", "frontend"]):
            categories["dashboard"].append(log_file)
        else:
            categories["generic"].append(log_file)

    return categories


def identify_duplicates(log_files: List[Path]) -> List[List[Path]]:
    """Identify duplicate log files."""

    # Group by size first (quick heuristic)
    size_groups = {}
    for log_file in log_files:
        size = log_file.stat().st_size
        if size not in size_groups:
            size_groups[size] = []
        size_groups[size].append(log_file)

    # Check files with same size for content similarity
    duplicates = []
    for size, files in size_groups.items():
        if len(files) > 1:
            # For now, assume files with same size and similar names are duplicates
            # This is a simplification - could be improved with content comparison
            name_groups = {}
            for file in files:
                # Extract base name without timestamps
                base_name = re.sub(r"-\d{8}-\d{6}", "", file.stem)
                base_name = re.sub(r"_\d{8}_\d{6}", "", base_name)
                base_name = re.sub(r"\d{8}", "", base_name)

                if base_name not in name_groups:
                    name_groups[base_name] = []
                name_groups[base_name].append(file)

            for group in name_groups.values():
                if len(group) > 1:
                    duplicates.append(group)

    return duplicates


def consolidate_self_test_logs(self_test_files: List[Path]) -> Path:
    """Consolidate self-test logs into a single daily file."""

    if not self_test_files:
        return None

    # Get today's date for consolidation
    today = datetime.now().strftime("%Y%m%d")
    consolidated_file = LOGS_DIR / f"self-test-{today}.log"

    # Sort files by modification time
    sorted_files = sorted(self_test_files, key=lambda x: x.stat().st_mtime)

    with open(consolidated_file, "w", encoding="utf-8") as outfile:
        outfile.write(
            f"# Consolidated self-test logs - {datetime.now().isoformat()}\n\n"
        )

        for log_file in sorted_files:
            outfile.write(f"# File: {log_file.name}\n")
            try:
                with open(log_file, "r", encoding="utf-8") as infile:
                    content = infile.read().strip()
                    if content:
                        outfile.write(content)
                        outfile.write("\n\n")
            except Exception as e:
                outfile.write(f"# Error reading {log_file.name}: {e}\n\n")

    # Remove original files
    for log_file in self_test_files:
        if log_file != consolidated_file:
            log_file.unlink()

    return consolidated_file


def clean_empty_files(empty_files: List[Path]):
    """Remove empty log files."""

    for empty_file in empty_files:
        try:
            empty_file.unlink()
            print(f"Removed empty file: {empty_file.name}")
        except Exception as e:
            print(f"Error removing {empty_file.name}: {e}")


def implement_log_rotation():
    """Implement basic log rotation for large files."""

    max_size = 5 * 1024 * 1024  # 5MB
    max_age = timedelta(days=7)  # Keep logs for 7 days

    for log_file in LOGS_DIR.glob("*.log"):
        if log_file.stat().st_size > max_size:
            # Rotate large files
            rotated_name = (
                f"{log_file.stem}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
            rotated_file = log_file.with_name(rotated_name)
            log_file.rename(rotated_file)
            print(f"Rotated large file: {log_file.name} -> {rotated_file.name}")

        # Remove old files
        file_age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
        if file_age > max_age:
            log_file.unlink()
            print(f"Removed old file: {log_file.name}")


def main():
    """Main function to consolidate and manage logs."""

    print("=== Open_ELF Log Manager ===\n")

    # Analyze current log files
    categories = analyze_log_files()

    print("Log file analysis:")
    for category, files in categories.items():
        print(f"  {category}: {len(files)} files")

    # Clean empty files
    if categories["empty"]:
        print(f"\nCleaning {len(categories['empty'])} empty files...")
        clean_empty_files(categories["empty"])

    # Consolidate self-test logs
    if categories["self_test"]:
        print(f"\nConsolidating {len(categories['self_test'])} self-test logs...")
        consolidated = consolidate_self_test_logs(categories["self_test"])
        if consolidated:
            print(f"Created consolidated file: {consolidated.name}")

    # Implement rotation
    print("\nImplementing log rotation...")
    implement_log_rotation()

    # Final analysis
    categories_after = analyze_log_files()

    print("\n=== Summary ===")
    for category in categories:
        before = len(categories[category])
        after = len(categories_after.get(category, []))
        reduction = before - after
        if reduction > 0:
            print(f"{category}: Reduced from {before} to {after} files (-{reduction})")
        else:
            print(f"{category}: {after} files")

    print("\n✅ Log management completed successfully!")


if __name__ == "__main__":
    main()
