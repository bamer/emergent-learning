#!/usr/bin/env python3
"""Database operations library using Python sqlite3"""

import sqlite3
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

def ensure_db(db_path: str) -> bool:
    """Ensure database exists and has required schema."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create experiments table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hypothesis TEXT,
                status TEXT DEFAULT 'active',
                folder_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

def insert_experiment(
    db_path: str,
    name: str,
    hypothesis: str,
    status: str = 'active',
    folder_path: str = ''
) -> Optional[int]:
    """Insert experiment and return ID."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO experiments (name, hypothesis, status, folder_path)
            VALUES (?, ?, ?, ?)
        ''', (name, hypothesis, status, folder_path))
        
        exp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return exp_id
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

def get_experiment(db_path: str, exp_id: int) -> Optional[Dict[str, Any]]:
    """Get experiment by ID."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM experiments WHERE id = ?', (exp_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

def list_experiments(db_path: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all experiments, optionally filtered by status."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM experiments WHERE status = ? ORDER BY created_at DESC', (status,))
        else:
            cursor.execute('SELECT * FROM experiments ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []

def update_experiment(db_path: str, exp_id: int, **kwargs) -> bool:
    """Update experiment fields."""
    if not kwargs:
        return True
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Build dynamic update query
        cols = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        vals = list(kwargs.values()) + [exp_id]
        
        cursor.execute(f'UPDATE experiments SET {cols} WHERE id = ?', vals)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

def main():
    """CLI for database operations."""
    if len(sys.argv) < 3:
        print("Usage: db.py <command> <db_path> [args...]", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    db_path = sys.argv[2]
    
    if command == 'ensure':
        if ensure_db(db_path):
            print("OK")
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'insert':
        if len(sys.argv) < 5:
            print("Usage: db.py insert <db_path> <name> <hypothesis> [status] [folder_path]", file=sys.stderr)
            sys.exit(1)
        
        name = sys.argv[3]
        hypothesis = sys.argv[4]
        status = sys.argv[5] if len(sys.argv) > 5 else 'active'
        folder_path = sys.argv[6] if len(sys.argv) > 6 else ''
        
        exp_id = insert_experiment(db_path, name, hypothesis, status, folder_path)
        if exp_id is not None:
            print(exp_id)
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'get':
        if len(sys.argv) < 4:
            print("Usage: db.py get <db_path> <id>", file=sys.stderr)
            sys.exit(1)
        
        exp_id = int(sys.argv[3])
        exp = get_experiment(db_path, exp_id)
        if exp:
            print(json.dumps(exp))
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif command == 'list':
        status = sys.argv[3] if len(sys.argv) > 3 else None
        exps = list_experiments(db_path, status)
        print(json.dumps(exps))
        sys.exit(0)
    
    elif command == 'update':
        if len(sys.argv) < 5:
            print("Usage: db.py update <db_path> <id> <key=value> ...", file=sys.stderr)
            sys.exit(1)
        
        exp_id = int(sys.argv[3])
        updates = {}
        for arg in sys.argv[4:]:
            if '=' in arg:
                key, val = arg.split('=', 1)
                updates[key] = val
        
        if update_experiment(db_path, exp_id, **updates):
            print("OK")
            sys.exit(0)
        else:
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
