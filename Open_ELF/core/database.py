#!/usr/bin/env python3
"""
Centralized SQLite connection module for Open_ELF
Eliminates duplicate connection patterns and enforces best practices

This module provides standardized database connection management
across all Open_ELF components.
"""

import sqlite3
from pathlib import Path
import threading
import time
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """Centralized database connection manager with standardized settings."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._thread_local = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection with standardized settings."""
        if (
            not hasattr(self._thread_local, "connection")
            or self._thread_local.connection is None
        ):
            self._thread_local.connection = self._create_connection()
        return self._thread_local.connection

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with standardized PRAGMA settings."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30,
            check_same_thread=False,
            isolation_level="DEFERRED",
        )
        conn.row_factory = sqlite3.Row

        # Apply standardized PRAGMA settings
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=memory")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

        return conn

    def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query with retry logic for transient errors."""
        conn = self.get_connection()
        max_retries = 3
        retry_count = 0

        while True:
            try:
                cursor = conn.execute(query, params or ())
                results = [dict(row) for row in cursor.fetchall()]
                conn.commit()
                return results
            except (sqlite3.OperationalError, sqlite3.ProgrammingError) as e:
                if retry_count >= max_retries:
                    raise
                retry_count += 1
                backoff = 2**retry_count
                time.sleep(backoff)
                # Reconnect on error
                if (
                    hasattr(self._thread_local, "connection")
                    and self._thread_local.connection
                ):
                    self._thread_local.connection.close()
                self._thread_local.connection = self._create_connection()
            except Exception as e:
                raise

    def close_connections(self):
        """Close all thread-local connections."""
        if hasattr(self._thread_local, "connection") and self._thread_local.connection:
            self._thread_local.connection.close()
            self._thread_local.connection = None


# Global database manager instance
default_db_path = Path("/home/bamer/OPC_ELF/Open_ELF/data.db")
global_db = DatabaseManager(default_db_path)


# Public API functions for external code compatibility
def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Factory function for external code compatibility."""
    if db_path:
        db_manager = DatabaseManager(db_path)
        return db_manager.get_connection()
    return global_db.get_connection()


def execute_query(
    query: str, params: Optional[tuple] = None, db_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Execute a query using the global database connection."""
    if db_path:
        db_manager = DatabaseManager(db_path)
        return db_manager.execute_query(query, params)
    return global_db.execute_query(query, params)


def close_connections(db_path: Optional[Path] = None):
    """Close all open connections across threads."""
    if db_path:
        db_manager = DatabaseManager(db_path)
        return db_manager.close_connections()
    return global_db.close_connections()
