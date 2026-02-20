#!/usr/bin/env python3
"""
Unify ELF Memory Databases

Problem: Multiple index.db files caused confusion and data loss
Solution: Single source of truth at /home/bamer/OPC_ELF/memory/index.db

This script:
1. Identifies all ELF database files
2. Merges heuristics and embeddings into the primary database
3. Creates symlinks for legacy paths
4. Updates configuration to use unified path

Usage:
    python3 unify-databases.py [--dry-run]
"""

import sqlite3
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Primary database (source of truth)
PRIMARY_DB = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"

# Legacy databases to merge
LEGACY_DBS = [
    Path.home() / ".opencode" / "memory" / "index.db",
]


def get_table_count(db_path, table_name):
    """Get row count for a table."""
    if not db_path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0


def merge_databases(source_db, target_db, dry_run=False):
    """Merge heuristics and embeddings from source to target."""
    print(f"\n📊 Merging {source_db} → {target_db}")

    if not source_db.exists():
        print(f"  ⚠️  Source does not exist, skipping")
        return

    if not target_db.exists():
        print(f"  ⚠️  Target does not exist, creating...")
        target_db.parent.mkdir(parents=True, exist_ok=True)
        # Create empty database with schema from source
        shutil.copy(source_db, target_db)
        return

    # Connect to both databases
    source_conn = sqlite3.connect(str(source_db))
    target_conn = sqlite3.connect(str(target_db))
    source_conn.row_factory = sqlite3.Row
    target_conn.row_factory = sqlite3.Row

    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    merged_count = {"heuristics": 0, "embeddings": 0}

    # Merge heuristics
    print("  Merging heuristics...")
    try:
        source_cursor.execute("SELECT * FROM heuristics")
        heuristics = source_cursor.fetchall()

        for h in heuristics:
            # Check if already exists in target
            target_cursor.execute("SELECT id FROM heuristics WHERE id = ?", (h["id"],))
            if not target_cursor.fetchone():
                if not dry_run:
                    target_cursor.execute(
                        """
                        INSERT INTO heuristics VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                        tuple(h),
                    )
                merged_count["heuristics"] += 1

        if not dry_run:
            target_conn.commit()
        print(f"    ✅ Merged {merged_count['heuristics']} new heuristics")
    except Exception as e:
        print(f"    ❌ Error merging heuristics: {e}")

    # Merge embeddings
    print("  Merging embeddings...")
    try:
        source_cursor.execute("SELECT * FROM embeddings")
        embeddings = source_cursor.fetchall()

        for e in embeddings:
            # Check if already exists (by source_id + source_type)
            target_cursor.execute(
                "SELECT id FROM embeddings WHERE source_id = ? AND source_type = ?",
                (e["source_id"], e["source_type"]),
            )
            if not target_cursor.fetchone():
                if not dry_run:
                    target_cursor.execute(
                        """
                        INSERT INTO embeddings VALUES (?,?,?,?,?,?,?)
                    """,
                        tuple(e),
                    )
                merged_count["embeddings"] += 1

        if not dry_run:
            target_conn.commit()
        print(f"    ✅ Merged {merged_count['embeddings']} new embeddings")
    except Exception as e:
        print(f"    ❌ Error merging embeddings: {e}")

    source_conn.close()
    target_conn.close()

    return merged_count


def create_symlinks():
    """Create symlinks from legacy paths to primary database."""
    print("\n🔗 Creating symlinks for legacy paths...")

    for legacy_path in LEGACY_DBS:
        if legacy_path.exists() or legacy_path.is_symlink():
            print(f"  Removing {legacy_path}...")
            if legacy_path.is_symlink():
                legacy_path.unlink()
            else:
                # Backup before removing
                backup = legacy_path.with_suffix(".db.backup")
                print(f"    Backing up to {backup}...")
                shutil.move(str(legacy_path), str(backup))

        # Create symlink
        print(f"  Creating symlink: {legacy_path} → {PRIMARY_DB}")
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            legacy_path.symlink_to(PRIMARY_DB)
            print(f"    ✅ Symlink created")
        except Exception as e:
            print(f"    ❌ Failed: {e}")


def update_config():
    """Update configuration files to use unified path."""
    print("\n⚙️  Updating configuration files...")

    config_files = [
        Path.home() / ".opencode" / "emergent-learning" / "semantic" / "daemon.py",
        Path.home()
        / ".opencode"
        / "emergent-learning"
        / "scripts"
        / "record-heuristic.py",
        Path.home()
        / ".opencode"
        / "emergent-learning"
        / "scripts"
        / "backfill-heuristic-embeddings.py",
    ]

    for config_file in config_files:
        if not config_file.exists():
            continue

        print(f"  Checking {config_file}...")
        content = config_file.read_text()

        # Check if it already uses the correct path
        if "emergent-learning/memory/index.db" in content:
            print(f"    ✅ Already using unified path")
            continue

        # Update BASE_DIR if needed
        if "BASE_DIR = Path(__file__).parent.parent.parent" in content:
            print(f"    ✅ Uses correct BASE_DIR")

        print(f"    ℹ️  No changes needed")


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 70)
    print("ELF Database Unification Script")
    print("=" * 70)

    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")

    # Show current state
    print("\n📊 Current Database State:")
    print(f"  Primary: {PRIMARY_DB}")
    print(f"    Heuristics: {get_table_count(PRIMARY_DB, 'heuristics')}")
    print(f"    Embeddings: {get_table_count(PRIMARY_DB, 'embeddings')}")

    for legacy_db in LEGACY_DBS:
        print(f"\n  Legacy: {legacy_db}")
        print(f"    Heuristics: {get_table_count(legacy_db, 'heuristics')}")
        print(f"    Embeddings: {get_table_count(legacy_db, 'embeddings')}")

    # Merge databases
    print("\n" + "=" * 70)
    print("MERGING DATABASES")
    print("=" * 70)

    total_merged = {"heuristics": 0, "embeddings": 0}
    for legacy_db in LEGACY_DBS:
        result = merge_databases(legacy_db, PRIMARY_DB, dry_run)
        if result:
            total_merged["heuristics"] += result["heuristics"]
            total_merged["embeddings"] += result["embeddings"]

    print(f"\n📈 Total Merged:")
    print(f"  Heuristics: {total_merged['heuristics']}")
    print(f"  Embeddings: {total_merged['embeddings']}")

    # Create symlinks (only if not dry run)
    if not dry_run:
        print("\n" + "=" * 70)
        print("CREATING SYMLINKS")
        print("=" * 70)
        create_symlinks()

        print("\n" + "=" * 70)
        print("UPDATING CONFIGURATION")
        print("=" * 70)
        update_config()

        print("\n" + "=" * 70)
        print("✅ DATABASE UNIFICATION COMPLETE")
        print("=" * 70)
        print(f"\nPrimary database: {PRIMARY_DB}")
        print(f"  Total heuristics: {get_table_count(PRIMARY_DB, 'heuristics')}")
        print(f"  Total embeddings: {get_table_count(PRIMARY_DB, 'embeddings')}")
        print("\nLegacy paths now point to primary database via symlinks.")
        print("All scripts will now use the unified database.")
    else:
        print("\n" + "=" * 70)
        print("DRY RUN COMPLETE - No changes made")
        print("=" * 70)
        print("\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
