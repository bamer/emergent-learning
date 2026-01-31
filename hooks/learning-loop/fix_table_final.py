#!/usr/bin/env python3
"""
Fix pheromone_trails table by dropping and recreating with UNIQUE constraint - FOR REAL
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"

print("Dropping and recreating pheromone_trails table with UNIQUE constraint...")

try:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Drop existing table completely
    cursor.execute("DROP TABLE IF EXISTS pheromone_trails")
    print("✓ Dropped existing table")

    # Recreate with UNIQUE constraint on file_path
    cursor.execute("""
        CREATE TABLE pheromone_trails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            tool_name TEXT,
            access_count INTEGER DEFAULT 1,
            first_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_weight REAL DEFAULT 1.0
        )
    """)
    print("✓ Created table with UNIQUE constraint on file_path")

    conn.commit()
    conn.close()

    print("✅ pheromone_trails table fixed for real!")

except Exception as e:
    print(f"❌ Error fixing table: {e}")
