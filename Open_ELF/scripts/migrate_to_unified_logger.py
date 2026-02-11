#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO 
# /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Script de migration pour mettre à jour tous les fichiers vers le logger unifié ELF.

Usage:
    python migrate_to_unified_logger.py

Ce script met à jour tous les fichiers Python pour utiliser elf_logging au lieu de logging standard.
"""

import re
import sys
from pathlib import Path

# Liste des fichiers à mettre à jour (priorité haute puis moyenne)
HIGH_PRIORITY_FILES = [
    "/home/bamer/.opencode/emergent-learning/Open_ELF/agents/agent_manager.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/agents/sentinel_monitor.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/event_bridge.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/unified_orchestrator.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/sentinel/elf_sentinel.py",
]

MEDIUM_PRIORITY_FILES = [
    "/home/bamer/.opencode/emergent-learning/Open_ELF/agents/alert_agent.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/agents/escalation_protocol.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/agents/pattern_response_handler.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/core/central_orchestrator.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/mission-engine/mission_engine.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/mission-engine/mission_live_handler.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/query/agent_config.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/query/fraud_detector.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/query/launch_agents.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/query/migrations.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/scripts/record-heuristic.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/timeline_dashboard/timeline_api.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/utils/event_logger.py",
]

DASHBOARD_FILES = [
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/main.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/admin.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/agents.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/auth.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/fraud.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/heuristics.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/live.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/monitoring.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/orchestrator.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/persistence.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/semantic.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/sessions.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/workflows.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/session_index.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/utils/auto_capture.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/utils/broadcast.py",
    "/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/utils/database.py",
]


def get_module_name(file_path: str) -> str:
    """Extract module name from file path."""
    path = Path(file_path)
    return path.stem


def migrate_file(file_path: str, dry_run: bool = False) -> bool:
    """
    Migrate a single file to use unified logging.

    Args:
        file_path: Path to the Python file
        dry_run: If True, only print what would be changed

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        module_name = get_module_name(file_path)

        # Check if file already uses elf_logging
        if "from Open_ELF.utils.elf_logging import" in content or "elf_logging.get_logger" in content:
            print(f"  ✓ Already uses unified logger: {file_path}")
            return True

        # Check if file uses basic logging
        if "import logging" not in content:
            print(f"  ℹ No logging import found: {file_path}")
            return True

        # Pattern 1: Replace basic logging setup
        # Remove: import logging
        # Remove: logging.basicConfig(...)
        # Add: from Open_ELF.utils.elf_logging import get_logger
        # Add: logger = get_logger("module_name")

        # Remove import logging
        content = re.sub(r"^import logging\s*$", "", content, flags=re.MULTILINE)
        content = re.sub(r"^from logging import.*$", "", content, flags=re.MULTILINE)

        # Remove logging.basicConfig block
        content = re.sub(r"logging\.basicConfig\([^)]+\)\s*\n?", "", content)

        # Add unified logger import and setup after other imports
        # Find a good place to insert (after sys.path imports or at top)
        lines = content.split("\n")
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_idx = i + 1

        # Insert unified logger setup
        logger_setup = f'''
# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_critical, log_error, log_warning, log_info
    logger = get_logger("{module_name}")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("{module_name}")
'''

        lines.insert(import_idx, logger_setup)
        content = "\n".join(lines)

        # Clean up multiple blank lines
        content = re.sub(r"\n{3,}", "\n\n", content)

        if content != original_content:
            if dry_run:
                print(f"  Would update: {file_path}")
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  ✓ Updated: {file_path}")
            return True
        else:
            print(f"  ℹ No changes needed: {file_path}")
            return True

    except Exception as e:
        print(f"  ✗ Error updating {file_path}: {e}")
        return False


def main():
    """Main migration function."""
    print("=" * 70)
    print("ELF Unified Logger Migration Tool")
    print("=" * 70)
    print()

    # Test mode
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🧪 DRY RUN MODE - No files will be modified")
        print()

    all_files = HIGH_PRIORITY_FILES + MEDIUM_PRIORITY_FILES + DASHBOARD_FILES

    print(f"Found {len(all_files)} files to process")
    print()

    success_count = 0
    fail_count = 0

    # Process high priority files first
    print("Processing HIGH priority files...")
    for file_path in HIGH_PRIORITY_FILES:
        if Path(file_path).exists():
            if migrate_file(file_path, dry_run):
                success_count += 1
            else:
                fail_count += 1
        else:
            print(f"  ✗ File not found: {file_path}")
            fail_count += 1

    print()
    print("Processing MEDIUM priority files...")
    for file_path in MEDIUM_PRIORITY_FILES:
        if Path(file_path).exists():
            if migrate_file(file_path, dry_run):
                success_count += 1
            else:
                fail_count += 1
        else:
            print(f"  ℹ File not found (optional): {file_path}")

    print()
    print("Processing DASHBOARD files...")
    for file_path in DASHBOARD_FILES:
        if Path(file_path).exists():
            if migrate_file(file_path, dry_run):
                success_count += 1
            else:
                fail_count += 1
        else:
            print(f"  ℹ File not found (optional): {file_path}")

    print()
    print("=" * 70)
    print(f"Migration complete!")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    print("=" * 70)

    if dry_run:
        print()
        print("💡 Run without --dry-run to apply changes")


if __name__ == "__main__":
    main()
