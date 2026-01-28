#!/usr/bin/env python3
"""
fix_database.py - Create missing database tables (golden_rules, sessions)

Ensures database schema is complete and compatible with all ELF components.
"""

import sqlite3
import sys
from pathlib import Path

ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = ELF_DIR / "memory" / "index.db"


def create_missing_tables():
    """Create golden_rules and sessions tables if they don't exist."""
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        print(f"Found {len(existing_tables)} existing tables")
        
        # Create golden_rules table if missing
        if 'golden_rules' not in existing_tables:
            print("Creating golden_rules table...")
            cursor.execute("""
                CREATE TABLE golden_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule TEXT NOT NULL UNIQUE,
                    category TEXT,
                    confidence REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    use_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    source TEXT,
                    explanation TEXT
                )
            """)
            print("✅ Created golden_rules table")
        else:
            print("✓ golden_rules table exists")
        
        # Create sessions table if missing
        if 'sessions' not in existing_tables:
            print("Creating sessions table...")
            cursor.execute("""
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds INTEGER,
                    agent_type TEXT,
                    status TEXT,
                    context_size INTEGER,
                    learned_count INTEGER DEFAULT 0,
                    rules_applied INTEGER DEFAULT 0,
                    notes TEXT
                )
            """)
            print("✅ Created sessions table")
        else:
            print("✓ sessions table exists")
        
        # Verify all required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        required = {'heuristics', 'golden_rules', 'sessions', 'pheromone_trails'}
        missing = required - tables
        
        if missing:
            print(f"⚠️  Still missing tables: {missing}")
            print("   Run: python3 setup_db.py")
        else:
            print(f"✅ All required tables present")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.close()
        return False


if __name__ == "__main__":
    success = create_missing_tables()
    sys.exit(0 if success else 1)
