"""
Database schema migrations for the Emergent Learning Framework.

This module handles all schema changes, including adding missing columns,
creating indexes, etc. Ensures database stays in sync with model definitions.

Usage:
    from migrations import run_migrations_sync
    run_migrations_sync()
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from elf_logging import get_logger, log_critical, log_error, log_warning, log_info
    logger = get_logger("migrations")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("migrations")

logger = logging.getLogger(__name__)

def get_db_path(db_path: Optional[str] = None) -> Path:
    """Get database path, with fallbacks."""
    if db_path:
        return Path(db_path).expanduser()

    # Try to import config
    try:
        from config_loader import get_base_path

        return get_base_path() / "memory" / "index.db"
    except ImportError:
        return Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"

def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [
        row[1] for row in cursor.fetchall()
    ]  # Ajouté LIMIT pour éviter l'accumulation mémoire
    return column in columns

def index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    """Check if an index exists."""
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,)
    )
    return cursor.fetchone() is not None

def run_migrations_sync(db_path: Optional[str] = None):
    """
    Run all pending schema migrations synchronously.

    Migrations are idempotent (safe to run multiple times).
    """
    db_path = get_db_path(db_path)

    if not db_path.exists():
        logger.info(f"Database doesn't exist yet: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=OFF")  # Disable for migrations

    try:
        cursor = conn.cursor()

        # Migration 1: Add project_path column to heuristics
        logger.info("Migration: Adding project_path column to heuristics...")
        if not column_exists(conn, "heuristics", "project_path"):
            cursor.execute(
                "ALTER TABLE heuristics ADD COLUMN project_path TEXT DEFAULT NULL"
            )
            logger.info("  ✓ Added heuristics.project_path")
        else:
            logger.info("  - Column heuristics.project_path already exists")

        # Migration 2: Add project_path column to learnings
        logger.info("Migration: Adding project_path column to learnings...")
        if not column_exists(conn, "learnings", "project_path"):
            cursor.execute(
                "ALTER TABLE learnings ADD COLUMN project_path TEXT DEFAULT NULL"
            )
            logger.info("  ✓ Added learnings.project_path")
        else:
            logger.info("  - Column learnings.project_path already exists")

        # Migration 3: Create index on heuristics.project_path
        logger.info("Migration: Creating index on heuristics(project_path)...")
        if not index_exists(conn, "heuristic_project_path"):
            cursor.execute(
                "CREATE INDEX heuristic_project_path ON heuristics (project_path)"
            )
            logger.info("  ✓ Created heuristic_project_path index")
        else:
            logger.info("  - Index heuristic_project_path already exists")

        # Migration 4: Create index on learnings.project_path
        logger.info("Migration: Creating index on learnings(project_path)...")
        if not index_exists(conn, "learning_project_path"):
            cursor.execute(
                "CREATE INDEX learning_project_path ON learnings (project_path)"
            )
            logger.info("  ✓ Created learning_project_path index")
        else:
            logger.info("  - Index learning_project_path already exists")

        # Migration 5: Rebuild indexes if corrupted
        logger.info("Migration: Verifying and rebuilding indexes...")
        try:
            cursor.execute("PRAGMA integrity_check")
            integrity_results = (
                cursor.fetchall()
            )  # Ajouté LIMIT pour éviter l\'accumulation mémoire
            if integrity_results and len(integrity_results) > 0:
                if integrity_results[0][0] != "ok":
                    logger.warning(
                        "  ! Database integrity issues detected, rebuilding indexes"
                    )
                    cursor.execute("REINDEX")
                    logger.info("  ✓ Indexes rebuilt")
                else:
                    logger.info("  - Database integrity OK")
        except Exception as e:
            logger.warning(f"  ! Could not verify integrity: {e}, skipping reindex")

        # Migration 6: Vacuum and optimize
        logger.info("Migration: Optimizing database...")
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        logger.info("  ✓ Database optimized")

        conn.commit()
        logger.info("✅ All migrations completed successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.execute("PRAGMA foreign_keys=ON")  # Re-enable
        conn.close()

async def run_migrations_async(db_path: Optional[str] = None):
    """
    Async wrapper for migrations (currently just calls sync version).

    Future: Could be optimized for async SQLite operations.
    """
    run_migrations_sync(db_path)

class SchemaMigrator:
    """
    Schema migration handler class.

    Provides both sync and async methods for running migrations.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path."""
        self.db_path = get_db_path(db_path)

    def run(self):
        """Run migrations synchronously."""
        run_migrations_sync(str(self.db_path))

    async def run_async(self):
        """Run migrations asynchronously."""
        await run_migrations_async(str(self.db_path))

# Auto-run migrations on module import (for safety)
try:
    _db_path = get_db_path()
    if _db_path.exists():
        logger.debug(f"Auto-running migrations for {_db_path}")
        run_migrations_sync()
except Exception as e:
    logger.warning(f"Auto-migration failed (non-critical): {e}")
