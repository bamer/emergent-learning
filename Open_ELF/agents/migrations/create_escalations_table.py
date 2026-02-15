#!/usr/bin/env python3
"""
Migration: Create escalations table for tracking escalations and responses

This migration creates a new table to track:
- Escalations sent between agents (sentinel → orchestrator → CEO)
- CEO/Orchestrator responses to escalations
- Status lifecycle (pending → responding → resolved → closed)
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"


def migrate():
    """Create escalations table."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Create escalations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_agent TEXT NOT NULL,
            target_agent TEXT NOT NULL,
            escalation_file_path TEXT NOT NULL,
            escalation_content TEXT,
            response_content TEXT,
            response_agent TEXT,
            status TEXT DEFAULT 'pending',
            severity TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            responded_at DATETIME
        )
    """)

    # Create indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_source_target ON escalations(source_agent, target_agent)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON escalations(status)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_created_at ON escalations(created_at)"
    )

    conn.commit()
    conn.close()

    print(f"✅ Migration complete: escalations table created in {DB_PATH}")


if __name__ == "__main__":
    migrate()
