"""
Database utility functions for the Emergent Learning Dashboard.

Provides database connection management and helper functions for SQLite operations.
Supports both global and project-specific databases.
"""

import sqlite3
import os
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging
from queue import Queue, Empty

logger = logging.getLogger(__name__)


def get_base_path() -> Path:
    """
    Get the base path for ELF data.
    Always use ~/.opencode/emergent-learning as the single source of truth.
    """
    return Path.home() / ".opencode" / "emergent-learning"


EMERGENT_LEARNING_PATH = get_base_path()
GLOBAL_DB_PATH = EMERGENT_LEARNING_PATH / "memory" / "index.db"

# Legacy alias
DB_PATH = GLOBAL_DB_PATH


@dataclass
class ProjectContext:
    """Current project context for the dashboard."""

    has_project: bool = False
    project_name: Optional[str] = None
    project_root: Optional[Path] = None
    project_db_path: Optional[Path] = None


# Global project context (set at startup)
_current_project: Optional[ProjectContext] = None


def detect_project_context(start_path: Optional[Path] = None) -> ProjectContext:
    """
    Detect if we are in an ELF-initialized project.
    Walks up from start_path looking for .elf/ directory.
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    current = start_path

    while True:
        elf_dir = current / ".elf"
        if elf_dir.exists() and elf_dir.is_dir():
            db_path = elf_dir / "learnings.db"
            project_name = current.name
            config_path = elf_dir / "config.yaml"
            if config_path.exists():
                try:
                    import yaml

                    with open(config_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f) or {}
                    project_name = config.get("project", {}).get("name", current.name)
                except Exception:
                    pass

            return ProjectContext(
                has_project=True,
                project_name=project_name,
                project_root=current,
                project_db_path=db_path if db_path.exists() else None,
            )

        parent = current.parent
        if parent == current:
            break
        current = parent

    return ProjectContext(has_project=False)


def init_project_context(start_path: Optional[Path] = None):
    """Initialize the global project context at startup."""
    global _current_project
    _current_project = detect_project_context(start_path)
    return _current_project


def get_project_context() -> ProjectContext:
    """Get the current project context."""
    global _current_project
    if _current_project is None:
        _current_project = detect_project_context()
    return _current_project


def escape_like(s: str) -> str:
    """Escape SQL LIKE wildcards to prevent wildcard injection."""
    return (
        s.replace(chr(92), chr(92) + chr(92))
        .replace("%", chr(92) + "%")
        .replace("_", chr(92) + "_")
    )


class SimpleConnectionManager:
    """
    Simple connection manager that opens/closes connections per request.
    This prevents long-running connections from locking the database in WAL mode.
    """

    def __init__(self, db_path: Path, timeout: float = 30.0):
        self.db_path = db_path
        self.timeout = timeout
        self._local = threading.local()

        # Ensure database directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with optimal settings for concurrency."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self.timeout,
            check_same_thread=False,
            isolation_level=None,  # Autocommit mode for better concurrency
        )
        conn.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrent reads/writes
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=memory")
        cursor.execute("PRAGMA busy_timeout=5000")  # 5 second busy timeout
        cursor.close()

        return conn

    def get_connection(self) -> sqlite3.Connection:
        """Create a fresh connection for each request."""
        return self._create_connection()

    def return_connection(self, conn: sqlite3.Connection):
        """Close the connection immediately after use."""
        try:
            conn.close()
        except:
            pass

    def close_all(self):
        """No-op since connections are not pooled."""
        pass


# Keep ConnectionPool for backward compatibility but use SimpleConnectionManager internally
ConnectionPool = SimpleConnectionManager

# Global connection managers
_pools: Dict[str, SimpleConnectionManager] = {}
_pools_lock = threading.Lock()


def get_pool(db_path: Path) -> SimpleConnectionManager:
    """Get or create a connection manager for the given database path."""
    db_key = str(db_path.resolve())

    with _pools_lock:
        if db_key not in _pools:
            _pools[db_key] = SimpleConnectionManager(db_path)
        return _pools[db_key]


def close_all_pools():
    """Close all connection managers (for shutdown)."""
    with _pools_lock:
        _pools.clear()


def init_game_tables(conn):
    """Initialize game-related tables if they don't exist."""
    cursor = conn.cursor()

    # Users table for OAuth
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        github_id INTEGER UNIQUE,
        username TEXT NOT NULL,
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Game state table (Anti-Cheat: Server Authoritative)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_state (
        user_id INTEGER PRIMARY KEY,
        score INTEGER DEFAULT 0,
        unlocked_weapons TEXT DEFAULT '["pulse_laser"]',
        unlocked_cursors TEXT DEFAULT '["default"]',
        active_weapon TEXT DEFAULT 'pulse_laser',
        talkinhead_unlocked INTEGER DEFAULT 0,
        talkinhead_autolaunch INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    for col in ["talkinhead_unlocked", "talkinhead_autolaunch"]:
        try:
            cursor.execute(f"ALTER TABLE game_state ADD COLUMN {col} INTEGER DEFAULT 0")
        except:
            pass

    # Performance index for leaderboard queries (ORDER BY score DESC)
    # This index significantly speeds up leaderboard pagination for 1000s of users
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_game_state_score_desc
    ON game_state (score DESC)
    """)

    conn.commit()


@contextmanager
def get_db(scope: str = "global"):
    """Get database connection from connection pool with row factory."""
    if scope == "project":
        ctx = get_project_context()
        if ctx.project_db_path and ctx.project_db_path.exists():
            db_path = ctx.project_db_path
        else:
            db_path = GLOBAL_DB_PATH
    else:
        db_path = GLOBAL_DB_PATH

    # Get connection pool and acquire a connection
    pool = get_pool(db_path)
    conn = pool.get_connection()

    try:
        init_game_tables(conn)
        yield conn
    except Exception:
        try:
            conn.rollback()
        except:
            pass
        raise
    finally:
        pool.return_connection(conn)


@contextmanager
def get_global_db():
    """Get global database connection from pool."""
    pool = get_pool(GLOBAL_DB_PATH)
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        pool.return_connection(conn)


@contextmanager
def get_project_db():
    """Get project database connection from pool (falls back to global if no project)."""
    ctx = get_project_context()
    if ctx.project_db_path and ctx.project_db_path.exists():
        db_path = ctx.project_db_path
    else:
        db_path = GLOBAL_DB_PATH

    pool = get_pool(db_path)
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        pool.return_connection(conn)


def dict_from_row(row) -> dict:
    """Convert sqlite3.Row to dict."""
    return dict(row) if row else {}


async def initialize_database():
    """Ensure database directory exists."""
    GLOBAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return True


async def create_tables():
    """Create all necessary database tables."""
    with get_global_db() as conn:
        cursor = conn.cursor()

        # ==============================================================================
        # Metrics
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                metric_name TEXT,
                metric_value REAL,
                context TEXT,
                tags TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==============================================================================
        # Heuristics
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS heuristics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                rule TEXT NOT NULL,
                explanation TEXT,
                source_type TEXT CHECK(source_type IN ('failure', 'success', 'observation', NULL)),
                source_id INTEGER,
                confidence REAL DEFAULT 0.5 CHECK(confidence >= 0.0 AND confidence <= 1.0),
                times_validated INTEGER DEFAULT 0 CHECK(times_validated >= 0),
                times_violated INTEGER DEFAULT 0 CHECK(times_violated >= 0),
                is_golden BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(domain, rule)
            )
        """)

        # ==============================================================================
        # Learnings
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('failure', 'success', 'observation', 'experiment')),
                filepath TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                summary TEXT,
                tags TEXT,
                domain TEXT,
                severity INTEGER DEFAULT 3 CHECK(severity >= 1 AND severity <= 5),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==============================================================================
        # Decisions (Architecture)
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                context TEXT,
                options_considered TEXT,
                decision TEXT,
                rationale TEXT,
                domain TEXT,
                files_touched TEXT,
                tests_added TEXT,
                status TEXT DEFAULT 'accepted',
                superseded_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==============================================================================
        # Invariants
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invariants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                statement TEXT NOT NULL,
                rationale TEXT,
                domain TEXT,
                scope TEXT DEFAULT 'codebase',
                validation_type TEXT,
                validation_code TEXT,
                severity TEXT DEFAULT 'error',
                status TEXT DEFAULT 'active',
                violation_count INTEGER DEFAULT 0,
                last_validated_at DATETIME,
                last_violated_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==============================================================================
        # Assumptions
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assumptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assumption TEXT NOT NULL,
                context TEXT,
                source TEXT,
                confidence REAL DEFAULT 0.5,
                status TEXT DEFAULT 'active', -- active, verified, challenged, invalidated
                domain TEXT,
                verified_count INTEGER DEFAULT 0,
                challenged_count INTEGER DEFAULT 0,
                last_verified_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==============================================================================
        # Workflows
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                nodes_json TEXT NOT NULL DEFAULT '[]',
                config_json TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER NOT NULL,
                from_node TEXT NOT NULL,
                to_node TEXT NOT NULL,
                condition TEXT DEFAULT '',
                priority INTEGER DEFAULT 100,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER,
                workflow_name TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                phase TEXT DEFAULT 'init',
                input_json TEXT DEFAULT '{}',
                output_json TEXT DEFAULT '{}',
                context_json TEXT DEFAULT '{}',
                total_nodes INTEGER DEFAULT 0,
                completed_nodes INTEGER DEFAULT 0,
                failed_nodes INTEGER DEFAULT 0,
                started_at DATETIME,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        """)

        # ==============================================================================
        # Node Executions & Trails
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS node_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                node_name TEXT,
                node_type TEXT NOT NULL DEFAULT 'single',
                agent_id TEXT,
                session_id TEXT,
                prompt TEXT,
                prompt_hash TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                result_json TEXT DEFAULT '{}',
                result_text TEXT,
                findings_json TEXT DEFAULT '[]',
                files_modified TEXT DEFAULT '[]',
                duration_ms INTEGER,
                token_count INTEGER,
                retry_count INTEGER DEFAULT 0,
                started_at DATETIME,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                error_type TEXT,
                FOREIGN KEY (run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                location TEXT NOT NULL,
                location_type TEXT DEFAULT 'file',
                scent TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                agent_id TEXT,
                node_id TEXT,
                message TEXT,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (run_id) REFERENCES workflow_runs(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conductor_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                decision_type TEXT NOT NULL,
                decision_data TEXT DEFAULT '{}',
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE
            )
        """)

        # ==============================================================================
        # Session Summaries
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_summaries (
                session_id TEXT PRIMARY KEY,
                tool_summary TEXT,
                content_summary TEXT,
                conversation_summary TEXT,
                files_touched TEXT,  -- JSON list
                tool_counts TEXT,    -- JSON list
                message_count INTEGER,
                summarized_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                summarizer_model TEXT,
                is_stale BOOLEAN DEFAULT 0
            )
        """)

        # ==============================================================================
        # Building Queries (Analytics)
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS building_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT,
                duration_ms INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==============================================================================
        # Spike Reports (Analytics)
        # ==============================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spike_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                usefulness_score INTEGER,
                time_invested_minutes INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
