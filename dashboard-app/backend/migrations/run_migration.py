#!/usr/bin/env python3
"""
Migration runner for dashboard backend database migrations.

This script executes SQL migration files against the database and provides
feedback on what changes were applied. It handles errors gracefully and
supports both global and project-specific databases.

Usage:
    python run_migration.py [--migration <file.sql>] [--scope <global|project>]

Examples:
    python run_migration.py                                    # Run all pending migrations
    python run_migration.py --migration add_performance_indexes.sql
    python run_migration.py --scope project                   # Run against project DB
"""

import os
import sys
import sqlite3
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import traceback
from datetime import datetime

# Add the backend directory to the path so we can import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import get_db, get_global_db, get_project_db, get_project_context

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles execution of database migrations."""

    def __init__(self, scope: str = "global"):
        """
        Initialize the migration runner.

        Args:
            scope: Database scope ("global" or "project")
        """
        self.scope = scope
        self.migrations_dir = Path(__file__).parent
        self.applied_migrations = {}

    def ensure_migration_table(self, conn: sqlite3.Connection):
        """Ensure the migrations tracking table exists."""
        cursor = conn.cursor()

        # Create migrations table to track applied migrations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                checksum TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INTEGER,
                scope TEXT NOT NULL
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schema_migrations_filename 
            ON schema_migrations (filename)
        """)

        # Create index for scope filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schema_migrations_scope 
            ON schema_migrations (scope)
        """)

        conn.commit()
        logger.info("Migration tracking table ensured")

    def load_applied_migrations(self, conn: sqlite3.Connection):
        """Load list of already applied migrations."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT filename, checksum FROM schema_migrations 
            WHERE scope = ?
        """,
            (self.scope,),
        )

        self.applied_migrations = {
            row["filename"]: row["checksum"] for row in :]
        }

        logger.info(
            f"Loaded {len(self.applied_migrations)} applied migrations for {self.scope} scope"
        )

    def calculate_checksum(self, filepath: Path) -> str:
        """Calculate a simple checksum for the migration file."""
        import hashlib

        with open(filepath, "rb") as f:
            content = f.read()

        # Ignore comments and empty lines for checksum
        lines = content.decode("utf-8").split("\n")
        cleaned_lines = []

        for line in lines:
            # Remove leading/trailing whitespace
            line = line.strip()
            # Skip empty lines and comment lines (but keep SQL comments)
            if line and not (line.startswith("--") and not line.startswith("-- ")):
                cleaned_lines.append(line)

        cleaned_content = "\n".join(cleaned_lines)
        return hashlib.md5(cleaned_content.encode("utf-8")).hexdigest()

    def parse_migration_file(self, filepath: Path) -> List[str]:
        """
        Parse a migration file into individual SQL statements.

        Args:
            filepath: Path to the migration file

        Returns:
            List of SQL statements
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by semicolons on separate lines (simpler and more reliable)
        lines = content.split("\n")
        statements = []
        current_statement = []

        for line in lines:
            line = line.strip()

            # Skip empty lines and comment lines
            if not line or line.startswith("--"):
                continue

            # Add line to current statement
            current_statement.append(line)

            # If line ends with semicolon, we have a complete statement
            if line.endswith(";"):
                statement = " ".join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []

        # Handle any trailing statement without semicolon (unlikely but just in case)
        if current_statement:
            statement = " ".join(current_statement)
            if statement.strip():
                statements.append(statement)

        return statements

    def execute_migration(
        self, conn: sqlite3.Connection, filepath: Path
    ) -> Tuple[bool, str, int]:
        """
        Execute a single migration file.

        Args:
            conn: Database connection
            filepath: Path to migration file

        Returns:
            Tuple of (success, error_message, execution_time_ms)
        """
        start_time = datetime.now()

        try:
            # Parse the migration file
            statements = self.parse_migration_file(filepath)
            logger.info(f"Found {len(statements)} SQL statements in {filepath.name}")

            cursor = conn.cursor()
            executed_count = 0

            # Execute each statement
            for i, statement in enumerate(statements, 1):
                try:
                    # Skip non-executable statements
                    if not statement or statement.startswith("--"):
                        continue

                    cursor.execute(statement)
                    executed_count += 1

                    # Log progress for large migrations
                    if len(statements) > 10 and i % 10 == 0:
                        logger.debug(f"Executed {i}/{len(statements)} statements")

                except sqlite3.Error as e:
                    # Check if this is an "already exists" error (which is OK for migrations)
                    if "already exists" in str(e).lower():
                        logger.debug(f"Ignoring 'already exists': {e}")
                        continue
                    else:
                        raise

            # Record the migration
            checksum = self.calculate_checksum(filepath)
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            cursor.execute(
                """
                    INSERT OR REPLACE INTO schema_migrations (filename, checksum, execution_time_ms, scope)
                    VALUES (?, ?, ?, ?)
                """,
                (filepath.name, checksum, execution_time_ms, self.scope),
            )

            conn.commit()

            success_msg = f"Successfully executed {executed_count} statements"
            return True, success_msg, execution_time_ms

        except Exception as e:
            conn.rollback()
            error_msg = f"Error executing migration: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return False, error_msg, 0

    def run_migration(self, migration_name: str) -> bool:
        """
        Run a specific migration.

        Args:
            migration_name: Name of the migration file

        Returns:
            True if successful, False otherwise
        """
        migration_path = self.migrations_dir / migration_name

        if not migration_path.exists():
            logger.error(f"Migration file not found: {migration_path}")
            return False

        # Check if already applied
        if migration_name in self.applied_migrations:
            current_checksum = self.calculate_checksum(migration_path)
            stored_checksum = self.applied_migrations[migration_name]

            if current_checksum == stored_checksum:
                logger.info(
                    f"Migration {migration_name} already applied (same checksum)"
                )
                return True
            else:
                logger.warning(
                    f"Migration {migration_name} applied but checksum changed!"
                )
                logger.info(f"  Stored: {stored_checksum}")
                logger.info(f"  Current: {current_checksum}")

        logger.info(f"Running migration: {migration_name}")

        # Get the appropriate database connection
        try:
            if self.scope == "project":
                with get_project_db() as conn:
                    self.ensure_migration_table(conn)
                    self.load_applied_migrations(conn)
                    success, message, exec_time = self.execute_migration(
                        conn, migration_path
                    )
            else:
                with get_global_db() as conn:
                    self.ensure_migration_table(conn)
                    self.load_applied_migrations(conn)
                    success, message, exec_time = self.execute_migration(
                        conn, migration_path
                    )

            if success:
                logger.info(f"✓ Migration completed successfully in {exec_time}ms")
                logger.info(f"  {message}")
            else:
                logger.error(f"✗ Migration failed: {message}")

            return success

        except Exception as e:
            logger.error(f"Failed to run migration {migration_name}: {str(e)}")
            return False

    def run_all_pending(self) -> bool:
        """Run all pending migrations."""
        migration_files = sorted(
            [f for f in self.migrations_dir.glob("*.sql") if f.is_file()]
        )

        if not migration_files:
            logger.info("No migration files found")
            return True

        logger.info(f"Found {len(migration_files)} migration files")

        # Load applied migrations first
        try:
            if self.scope == "project":
                with get_project_db() as conn:
                    self.ensure_migration_table(conn)
                    self.load_applied_migrations(conn)
            else:
                with get_global_db() as conn:
                    self.ensure_migration_table(conn)
                    self.load_applied_migrations(conn)
        except Exception as e:
            logger.error(f"Failed to load migration state: {str(e)}")
            return False

        # Identify pending migrations
        pending = []
        for migration_file in migration_files:
            if migration_file.name not in self.applied_migrations:
                pending.append(migration_file.name)

        if not pending:
            logger.info("No pending migrations")
            return True

        logger.info(f"Running {len(pending)} pending migrations:")
        for name in pending:
            logger.info(f"  - {name}")

        # Run each pending migration
        success_count = 0
        for migration_name in pending:
            if self.run_migration(migration_name):
                success_count += 1
            else:
                logger.error(f"Migration {migration_name} failed, stopping")
                return False

        logger.info(
            f"All migrations completed successfully ({success_count}/{len(pending)})"
        )
        return True

    def list_migrations(self):
        """List all migrations and their status."""
        migration_files = sorted(
            [f for f in self.migrations_dir.glob("*.sql") if f.is_file()]
        )

        print(f"\nMigrations directory: {self.migrations_dir}")
        print(f"Database scope: {self.scope}")
        print(f"Total migrations: {len(migration_files)}")
        print()

        # Load applied migrations
        try:
            if self.scope == "project":
                with get_project_db() as conn:
                    self.ensure_migration_table(conn)
                    self.load_applied_migrations(conn)
            else:
                with get_global_db() as conn:
                    self.ensure_migration_table(conn)
                    self.load_applied_migrations(conn)
        except Exception as e:
            logger.error(f"Failed to load migration state: {str(e)}")
            return

        # Display status
        applied_count = len(self.applied_migrations)
        pending_count = len(migration_files) - applied_count

        print(f"Applied: {applied_count} migrations")
        print(f"Pending: {pending_count} migrations")
        print()

        # List each migration
        for migration_file in migration_files:
            status = (
                "✓ Applied"
                if migration_file.name in self.applied_migrations
                else "○ Pending"
            )
            checksum = self.applied_migrations.get(migration_file.name, "N/A")
            print(f"  {status:10} {migration_file.name}")
            if migration_file.name in self.applied_migrations:
                print(f"             Checksum: {checksum}")

        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run database migrations for the dashboard backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run all pending migrations
  %(prog)s --migration add_performance_indexes.sql
  %(prog)s --scope project                   # Run against project database
  %(prog)s --list                           # List migration status
        """,
    )

    parser.add_argument("--migration", "-m", help="Specific migration file to run")

    parser.add_argument(
        "--scope",
        "-s",
        choices=["global", "project"],
        default="global",
        help="Database scope (default: global)",
    )

    parser.add_argument(
        "--list", "-l", action="store_true", help="List all migrations and their status"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if we're in a project context for project scope
    if args.scope == "project":
        ctx = get_project_context()
        if not ctx.has_project:
            logger.error(
                "No project context found. Use --scope global or run from within an ELF project."
            )
            sys.exit(1)
        logger.info(f"Using project database: {ctx.project_db_path}")
    else:
        logger.info("Using global database")

    # Create migration runner
    runner = MigrationRunner(scope=args.scope)

    # Handle list command
    if args.list:
        runner.list_migrations()
        return

    # Run migrations
    success = False
    if args.migration:
        success = runner.run_migration(args.migration)
    else:
        success = runner.run_all_pending()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
