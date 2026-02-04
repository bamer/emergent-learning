#!/usr/bin/env python3
"""Rebuild all empty/corrupted SQLite databases"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path('/home/bamer/.opencode/emergent-learning/memory')

DATABASES = {
    'building.db': '''
CREATE TABLE IF NOT EXISTS golden_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule TEXT NOT NULL UNIQUE,
    domain TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_count INTEGER DEFAULT 0,
    confidence REAL DEFAULT 1.0,
    source TEXT
);

CREATE TABLE IF NOT EXISTS heuristics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule TEXT NOT NULL,
    domain TEXT,
    confidence REAL DEFAULT 0.5,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_count INTEGER DEFAULT 0,
    violation_count INTEGER DEFAULT 0,
    tags TEXT,
    evidence TEXT
);

CREATE TABLE IF NOT EXISTS failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    severity TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stack_trace TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolution TEXT
);

CREATE TABLE IF NOT EXISTS successes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metrics TEXT,
    evidence TEXT
);

CREATE TABLE IF NOT EXISTS learnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    domain TEXT,
    type TEXT,
    confidence REAL DEFAULT 0.5,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_heuristics_domain ON heuristics(domain);
CREATE INDEX IF NOT EXISTS idx_failures_domain ON failures(domain);
CREATE INDEX IF NOT EXISTS idx_learnings_domain ON learnings(domain);
''',
    'conductor.db': '''
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'planning',
    phase TEXT DEFAULT 'spec',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    product TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER,
    description TEXT,
    status TEXT DEFAULT 'pending',
    assigned_to TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER,
    name TEXT,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);
''',
    'learning_database.db': '''
CREATE TABLE IF NOT EXISTS captured_learnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    source TEXT,
    domain TEXT,
    confidence REAL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processing_result TEXT
);

CREATE TABLE IF NOT EXISTS learning_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_type TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    learnings_captured INTEGER DEFAULT 0
);
''',
    'learning.db': '''
CREATE TABLE IF NOT EXISTS captured_learnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    source TEXT,
    domain TEXT,
    confidence REAL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);
''',
    'learnings.db': '''
CREATE TABLE IF NOT EXISTS learnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    domain TEXT,
    type TEXT,
    confidence REAL DEFAULT 0.5,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''
}

def rebuild_database(db_name, schema):
    db_path = BASE_DIR / db_name
    
    # Backup existing if not empty
    if db_path.exists() and os.path.getsize(db_path) > 0:
        backup_path = BASE_DIR / f"{db_name}.backup.$(date +%Y%m%d%H%M)"
        os.rename(db_path, backup_path)
        print(f"  📦 Backed up existing {db_name} to {backup_path.name}")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print(f"  ✅ Rebuilt {db_name} with full schema")
    return True

print("\n" + "=" * 60)
print("🔧 REBUILDING EMPTY CORRUPTED DATABASES")
print("=" * 60)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

success_count = 0
for db_name, schema in DATABASES.items():
    print(f"📊 Processing {db_name}...")
    try:
        if rebuild_database(db_name, schema):
            success_count += 1
    except Exception as e:
        print(f"  ❌ Error rebuilding {db_name}: {e}")

print()
print("=" * 60)
print(f"✅ DATABASE REBUILD COMPLETE")
print(f"   Success: {success_count}/{len(DATABASES)} databases rebuilt")
print("=" * 60)
