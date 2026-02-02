#!/usr/bin/env python3
"""
Experiment Lifecycle Manager

Manages active experiments:
- Monitor progress
- Complete when objectives are met
- Archive old experiments
- Generate reports
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

def get_db_path() -> Path:
    """Get database path."""
    return Path(__file__).parent.parent.parent / "memory" / "index.db"

class ExperimentManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
    
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def ensure_schema(self) -> bool:
        """Ensure experiments table has all required columns."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            
            # Check columns exist
            cursor.execute("PRAGMA table_info(experiments)")
            columns = {row[1] for row in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire}
            
            required = {'id', 'name', 'hypothesis', 'status', 'folder_path', 'created_at'}
            if not required.issubset(columns):
                return False
            
            # Add optional columns if missing
            optional = {
                'cycles_run': 'INTEGER DEFAULT 0',
                'updated_at': 'TIMESTAMP',
                'completed_at': 'TIMESTAMP',
                'notes': 'TEXT',
                'result': 'TEXT',
                'success_criteria': 'TEXT',
                'failure_criteria': 'TEXT'
            }
            
            for col, def_str in optional.items():
                if col not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE experiments ADD COLUMN {col} {def_str}")
                    except sqlite3.OperationalError:
                        pass  # Column likely already exists
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error ensuring schema: {e}", file=sys.stderr)
            return False
        finally:
            conn.close()
    
    def list_active(self) -> List[Dict[str, Any]]:
        """Get all active experiments."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM experiments 
                WHERE status = 'active' 
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire]
        finally:
            conn.close()
    
    def list_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get experiments by status."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM experiments 
                WHERE status = ? 
                ORDER BY created_at DESC
            """, (status,))
            return [dict(row) for row in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire]
        finally:
            conn.close()
    
    def complete_experiment(self, exp_id: int, result: str, notes: str = "") -> bool:
        """Mark experiment as completed."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE experiments 
                SET status = 'completed', 
                    completed_at = CURRENT_TIMESTAMP,
                    result = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (result, notes, exp_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def archive_experiment(self, exp_id: int) -> bool:
        """Archive an experiment."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE experiments 
                SET status = 'archived',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (exp_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def archive_old_experiments(self, days_old: int = 90) -> List[int]:
        """Archive experiments older than N days."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(days=days_old)
            
            # Get experiments to archive
            cursor.execute("""
                SELECT id FROM experiments
                WHERE status = 'completed'
                AND completed_at < ?
                ORDER BY completed_at ASC
            """, (cutoff.isoformat(),))
            
            ids = [row['id'] for row in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire]
            
            # Archive them
            if ids:
                placeholders = ','.join('?' * len(ids))
                cursor.execute(f"""
                    UPDATE experiments
                    SET status = 'archived'
                    WHERE id IN ({placeholders})
                """, ids)
                conn.commit()
            
            return ids
        finally:
            conn.close()
    
    def get_experiment(self, exp_id: int) -> Optional[Dict[str, Any]]:
        """Get experiment by ID."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def increment_cycles(self, exp_id: int, count: int = 1) -> bool:
        """Increment cycles_run counter."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE experiments
                SET cycles_run = COALESCE(cycles_run, 0) + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (count, exp_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def add_note(self, exp_id: int, note: str) -> bool:
        """Add a note to an experiment."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT notes FROM experiments WHERE id = ?", (exp_id,))
            row = cursor.fetchone()
            current_notes = row['notes'] if row and row['notes'] else ""
            
            timestamp = datetime.now().isoformat()
            new_notes = f"{current_notes}\n[{timestamp}] {note}".strip()
            
            cursor.execute("""
                UPDATE experiments
                SET notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_notes, exp_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get experiment statistics."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "by_status": {},
                "oldest_active": None,
                "total_completed": 0,
                "total_cycles": 0
            }
            
            # By status
            cursor.execute("""
                SELECT status, COUNT(*) as count, AVG(cycles_run) as avg_cycles
                FROM experiments
                GROUP BY status
            """)
            for row in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire:
                stats["by_status"][row['status'] or 'unknown'] = {
                    "count": row['count'],
                    "avg_cycles": round(row['avg_cycles'] or 0, 1)
                }
            
            # Oldest active
            cursor.execute("""
                SELECT id, name, created_at FROM experiments
                WHERE status = 'active'
                ORDER BY created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                stats["oldest_active"] = {
                    "id": row['id'],
                    "name": row['name'],
                    "created_at": row['created_at'],
                    "days_running": (datetime.now() - datetime.fromisoformat(row['created_at'])).days
                }
            
            # Totals
            cursor.execute("SELECT COUNT(*) as count FROM experiments WHERE status = 'completed'")
            stats["total_completed"] = cursor.fetchone()['count']
            
            cursor.execute("SELECT SUM(COALESCE(cycles_run, 0)) as total FROM experiments")
            stats["total_cycles"] = cursor.fetchone()['total'] or 0
            
            return stats
        finally:
            conn.close()
    
    def get_stale_experiments(self, days_inactive: int = 30) -> List[Dict[str, Any]]:
        """Get experiments that haven't been updated recently."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(days=days_inactive)
            
            cursor.execute("""
                SELECT id, name, status, created_at, updated_at, cycles_run
                FROM experiments
                WHERE status = 'active'
                AND (updated_at < ? OR (updated_at IS NULL AND created_at < ?))
                ORDER BY created_at ASC
            """, (cutoff.isoformat(), cutoff.isoformat()))
            
            return [dict(row) for row in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire]
        finally:
            conn.close()

def main():
    """CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: experiment_manager.py <command> [args]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  list [status]       - List experiments (optionally filtered by status)", file=sys.stderr)
        print("  stats               - Show experiment statistics", file=sys.stderr)
        print("  stale [days]        - Show stale experiments (default: 30 days)", file=sys.stderr)
        print("  complete <id> <result> - Mark experiment as completed", file=sys.stderr)
        print("  archive <id>        - Archive an experiment", file=sys.stderr)
        print("  archive-old [days]  - Archive completed experiments older than N days", file=sys.stderr)
        sys.exit(1)
    
    manager = ExperimentManager()
    manager.ensure_schema()
    
    command = sys.argv[1]
    
    if command == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        if status:
            exps = manager.list_by_status(status)
        else:
            exps = manager.list_active()
        print(json.dumps(exps, indent=2, default=str))
    
    elif command == "stats":
        stats = manager.get_stats()
        print(json.dumps(stats, indent=2))
    
    elif command == "stale":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        stale = manager.get_stale_experiments(days)
        print(json.dumps(stale, indent=2, default=str))
    
    elif command == "complete":
        if len(sys.argv) < 4:
            print("Usage: experiment_manager.py complete <id> <result> [notes]", file=sys.stderr)
            sys.exit(1)
        exp_id = int(sys.argv[2])
        result = sys.argv[3]
        notes = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        if manager.complete_experiment(exp_id, result, notes):
            print(f"Experiment {exp_id} completed")
        else:
            print(f"Failed to complete experiment {exp_id}", file=sys.stderr)
            sys.exit(1)
    
    elif command == "archive":
        if len(sys.argv) < 3:
            print("Usage: experiment_manager.py archive <id>", file=sys.stderr)
            sys.exit(1)
        exp_id = int(sys.argv[2])
        if manager.archive_experiment(exp_id):
            print(f"Experiment {exp_id} archived")
        else:
            print(f"Failed to archive experiment {exp_id}", file=sys.stderr)
            sys.exit(1)
    
    elif command == "archive-old":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        archived = manager.archive_old_experiments(days)
        print(f"Archived {len(archived)} experiments")
        if archived:
            print(f"IDs: {archived}")
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
