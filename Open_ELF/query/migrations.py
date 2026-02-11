
# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO 
# /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Database schema migrations for the Emergent Learning Framework.

This module handles all schema changes, including adding missing columns,
creating indexes, etc. Ensures database stays in sync with model definitions.

Usage:
    from migrations import run_migrations_sync
    run_migrations_sync()

IMPORTANT: Migrations are NOT auto-run on module import to avoid polluting
external agent context. They should be triggered explicitly by the orchestrator
or sentinel AI when needed.
"""

import sqlite3
import logging
import hashlib
from pathlib import Path
from typing import Optional, List, Tuple

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_critical, log_error, log_warning, log_info
    logger = get_logger("migrations")
except ImportError:
    logging.basicConfig(level=logging.INFO)
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
    ]
    return column in columns

def index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    """Check if an index exists."""
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,)
    )
    return cursor.fetchone() is not None

def get_schema_version(conn: sqlite3.Connection) -> str:
    """
    Get a hash representing the current schema state.
    This is used to quickly check if migrations are needed.
    """
    cursor = conn.cursor()
    
    # Get all table schemas
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL ORDER BY name")
    table_schemas = [row[0] for row in cursor.fetchall()]
    
    # Get all index definitions
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name")
    index_schemas = [row[0] for row in cursor.fetchall()]
    
    # Combine and hash
    schema_text = '\n'.join(table_schemas + index_schemas)
    return hashlib.sha256(schema_text.encode()).hexdigest()[:16]

def get_expected_schema_version() -> str:
    """
    Get the expected schema version based on current migration definitions.
    This should be updated when migrations change.
    """
    # This is a simplified version - in production, this would be more sophisticated
    # For now, we track based on the columns and indexes we expect
    expected_schema = """
    CREATE TABLE heuristics (id INTEGER PRIMARY KEY, project_path TEXT)
    CREATE INDEX heuristic_project_path ON heuristics(project_path)
    CREATE TABLE learnings (id INTEGER PRIMARY KEY, project_path TEXT)
    CREATE INDEX learning_project_path ON learnings(project_path)
    """
    return hashlib.sha256(expected_schema.encode()).hexdigest()[:16]

def check_integrity(conn: sqlite3.Connection) -> Tuple[bool, List[str]]:
    """
    Check database integrity properly.
    
    PRAGMA integrity_check returns:
    - One row with "ok" if database is valid
    - Multiple rows with error messages if there are issues
    
    Returns: (is_valid, list_of_errors)
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    results = cursor.fetchall()
    
    if not results:
        return False, ["No integrity check results returned"]
    
    # Check all results - integrity_check returns one row per error
    errors = []
    for row in results:
        if row[0] != "ok":
            errors.append(row[0])
    
    if errors:
        return False, errors
    
    return True, []

def run_migrations_sync(db_path: Optional[str] = None, force: bool = False) -> bool:
    """
    Run all pending schema migrations synchronously.

    Migrations are idempotent (safe to run multiple times).
    
    Args:
        db_path: Path to the database file
        force: If True, run migrations even if schema version matches
        
    Returns:
        True if migrations were run, False if skipped (schema up-to-date)
    """
    db_path = get_db_path(db_path)

    if not db_path.exists():
        logger.debug(f"Database doesn't exist yet: {db_path}")
        return False

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=OFF")  # Disable for migrations

    try:
        cursor = conn.cursor()
        
        # Check if migrations are needed using schema version
        if not force:
            try:
                current_version = get_schema_version(conn)
                # We don't compare to expected - we just check if actual schema matches
                # by checking individual components below
                logger.debug(f"Current schema hash: {current_version}")
            except Exception as e:
                logger.debug(f"Could not get schema version: {e}")
        
        migrations_run = False

        # Migration 1: Add project_path column to heuristics
        if not column_exists(conn, "heuristics", "project_path"):
            logger.debug("Migration: Adding project_path column to heuristics...")
            cursor.execute(
                "ALTER TABLE heuristics ADD COLUMN project_path TEXT DEFAULT NULL"
            )
            logger.debug("  ✓ Added heuristics.project_path")
            migrations_run = True
        else:
            logger.debug("  - Column heuristics.project_path already exists")

        # Migration 2: Add project_path column to learnings
        if not column_exists(conn, "learnings", "project_path"):
            logger.debug("Migration: Adding project_path column to learnings...")
            cursor.execute(
                "ALTER TABLE learnings ADD COLUMN project_path TEXT DEFAULT NULL"
            )
            logger.debug("  ✓ Added learnings.project_path")
            migrations_run = True
        else:
            logger.debug("  - Column learnings.project_path already exists")

        # Migration 3: Create index on heuristics.project_path
        if not index_exists(conn, "heuristic_project_path"):
            logger.debug("Migration: Creating index on heuristics(project_path)...")
            cursor.execute(
                "CREATE INDEX heuristic_project_path ON heuristics (project_path)"
            )
            logger.debug("  ✓ Created heuristic_project_path index")
            migrations_run = True
        else:
            logger.debug("  - Index heuristic_project_path already exists")

        # Migration 4: Create index on learnings.project_path
        if not index_exists(conn, "learning_project_path"):
            logger.debug("Migration: Creating index on learnings(project_path)...")
            cursor.execute(
                "CREATE INDEX learning_project_path ON learnings (project_path)"
            )
            logger.debug("  ✓ Created learning_project_path index")
            migrations_run = True
        else:
            logger.debug("  - Index learning_project_path already exists")

        # Migration 5: Check integrity (only if we made changes or periodically)
        if migrations_run or force:
            logger.debug("Migration: Verifying database integrity...")
            try:
                is_valid, errors = check_integrity(conn)
                if not is_valid:
                    logger.warning(f"  ! Database integrity issues detected: {errors}")
                    cursor.execute("REINDEX")
                    logger.info("  ✓ Indexes rebuilt")
                else:
                    logger.debug("  - Database integrity OK")
            except Exception as e:
                logger.warning(f"  ! Could not verify integrity: {e}, skipping reindex")

        # Migration 6: Vacuum and optimize (only if we made changes)
        if migrations_run:
            logger.debug("Migration: Optimizing database...")
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            logger.debug("  ✓ Database optimized")

        conn.commit()
        
        if migrations_run:
            logger.debug("✅ Migrations completed successfully")
        else:
            logger.debug("✓ Schema up-to-date, no migrations needed")
            
        return migrations_run

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.execute("PRAGMA foreign_keys=ON")  # Re-enable
        conn.close()

async def run_migrations_async(db_path: Optional[str] = None, force: bool = False) -> bool:
    """
    Async wrapper for migrations (currently just calls sync version).

    Future: Could be optimized for async SQLite operations.
    """
    return run_migrations_sync(db_path, force)

class SchemaMigrator:
    """
    Schema migration handler class.

    Provides both sync and async methods for running migrations.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path."""
        self.db_path = get_db_path(db_path)

    def run(self, force: bool = False) -> bool:
        """Run migrations synchronously."""
        return run_migrations_sync(str(self.db_path), force)

    async def run_async(self, force: bool = False) -> bool:
        """Run migrations asynchronously."""
        return await run_migrations_async(str(self.db_path), force)
    
    async def migrate(self) -> dict:
        """
        Run migrations and return detailed results.
        
        This is the main API method used by core.py.
        Returns a dict with migration results for backward compatibility.
        """
        migrations_applied = await self.run_async(force=False)
        
        # Return format expected by core.py
        return {
            "total_applied": 1 if migrations_applied else 0,
            "migrations_applied": ["schema_update"] if migrations_applied else [],
            "migrations_failed": [],
            "skipped": not migrations_applied,
            "message": "Migrations completed" if migrations_applied else "Schema up-to-date"
        }

# IMPORTANT: Auto-run on module import has been REMOVED
# Migrations should be triggered explicitly by the orchestrator/sentinel AI
# when needed, not on every module import. This prevents polluting external
# agent context with migration logs on every check-in/check-out.
#
# To run migrations explicitly:
#   from migrations import run_migrations_sync
#   run_migrations_sync()
#
# Or use the SchemaMigrator class:
#   migrator = SchemaMigrator()
#   migrator.run()
