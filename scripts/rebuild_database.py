#!/usr/bin/env python3
"""
Rebuild ELF database with proper schemas.
All tables created with correct constraints, defaults, and types.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "memory" / "index.db"


def rebuild_db():
    """Recreate all tables with proper schemas."""
    db = sqlite3.connect(str(DB_PATH))
    cursor = db.cursor()
    
    # Drop all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire]
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        except:
            pass
    
    print("✓ Dropped all existing tables")
    
    # Recreate schema version
    cursor.execute("""
        CREATE TABLE schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT INTO schema_version (version, description) VALUES (1, 'ELF Database Schema v1')")
    
    # learnings
    cursor.execute("""
        CREATE TABLE learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL DEFAULT 'general',
            source TEXT NOT NULL DEFAULT 'system',
            content TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            verified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # heuristics
    cursor.execute("""
        CREATE TABLE heuristics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            rule TEXT NOT NULL,
            explanation TEXT,
            source_type TEXT DEFAULT 'manual',
            source_id TEXT,
            confidence REAL DEFAULT 0.5,
            times_validated INTEGER DEFAULT 0,
            times_violated INTEGER DEFAULT 0,
            is_golden INTEGER DEFAULT 0,
            project_path TEXT,
            status TEXT DEFAULT 'active',
            dormant_since DATETIME,
            revival_conditions TEXT,
            times_revived INTEGER DEFAULT 0,
            times_contradicted INTEGER DEFAULT 0,
            min_applications INTEGER DEFAULT 0,
            last_confidence_update DATETIME,
            update_count_today INTEGER DEFAULT 0,
            update_count_reset_date DATE,
            last_used_at DATETIME,
            confidence_ema REAL,
            ema_alpha REAL DEFAULT 0.2,
            ema_warmup_remaining INTEGER DEFAULT 10,
            last_ema_update DATETIME,
            fraud_flags TEXT,
            is_quarantined INTEGER DEFAULT 0,
            last_fraud_check DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # golden_rules
    cursor.execute("""
        CREATE TABLE golden_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule TEXT NOT NULL,
            category TEXT,
            confidence REAL DEFAULT 0.8,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME,
            use_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            source TEXT,
            explanation TEXT
        )
    """)
    
    # event_chronicle
    cursor.execute("""
        CREATE TABLE event_chronicle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT NOT NULL,
            source TEXT,
            source_id TEXT,
            status TEXT DEFAULT 'success',
            summary TEXT,
            data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # workflow_runs
    cursor.execute("""
        CREATE TABLE workflow_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow TEXT,
            workflow_name TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            phase TEXT NOT NULL DEFAULT 'init',
            input_json TEXT DEFAULT '{}',
            output_json TEXT DEFAULT '{}',
            context_json TEXT DEFAULT '{}',
            total_nodes INTEGER NOT NULL DEFAULT 0,
            completed_nodes INTEGER NOT NULL DEFAULT 0,
            failed_nodes INTEGER NOT NULL DEFAULT 0,
            started_at DATETIME,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT,
            workflow_id INTEGER
        )
    """)
    
    # node_executions
    cursor.execute("""
        CREATE TABLE node_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_name TEXT NOT NULL,
            node_type TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            input_data TEXT DEFAULT '{}',
            output_data TEXT DEFAULT '{}',
            error_message TEXT,
            duration_ms INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # trails
    cursor.execute("""
        CREATE TABLE trails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trail_type TEXT NOT NULL,
            source TEXT,
            target TEXT,
            strength REAL DEFAULT 1.0,
            last_traversed DATETIME,
            traversal_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # decisions
    cursor.execute("""
        CREATE TABLE decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            confidence REAL DEFAULT 0.5,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # metrics
    cursor.execute("""
        CREATE TABLE metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT NOT NULL,
            metric_name TEXT,
            metric_value REAL,
            tags TEXT,
            context TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # experiments
    cursor.execute("""
        CREATE TABLE experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # sessions
    cursor.execute("""
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            closed_at DATETIME
        )
    """)
    
    # Other tables with minimal schema
    cursor.execute("""
        CREATE TABLE violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER,
            violation_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE invariants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            violation_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            pattern_data TEXT DEFAULT '{}',
            confidence REAL DEFAULT 0.5,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE spike_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spike_type TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'normal',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE workflow_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER,
            from_node TEXT,
            to_node TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE ceo_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_type TEXT NOT NULL,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE building_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            duration_ms INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_type TEXT NOT NULL,
            data TEXT DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE system_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            value REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE db_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL,
            status TEXT DEFAULT 'success',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE conductor_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE assumptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assumption_text TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE pheromone_trails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trail_type TEXT NOT NULL,
            strength REAL DEFAULT 1.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_name TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE game_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_data TEXT DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.commit()
    db.close()
    
    print("✓ All tables recreated with proper schemas")
    return True


if __name__ == "__main__":
    if rebuild_db():
        print("\n✓ Database rebuilt successfully")
    else:
        print("\n✗ Database rebuild failed")
