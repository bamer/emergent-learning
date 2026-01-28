#!/usr/bin/env python3
"""
Record event to event_chronicle table.
Writes events from the plugin to the timeline.
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Setup paths
ELF_BASE = Path(__file__).parent.parent
DB_PATH = ELF_BASE / "memory" / "index.db"


def record_event(event_data):
    """Write event to event_chronicle table."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        event_type = event_data.get('event_type', 'unknown')
        source = event_data.get('source', 'unknown')
        source_id = event_data.get('source_id', '')
        summary = event_data.get('summary', '')
        status = event_data.get('status', 'success')
        data = event_data.get('data')
        timestamp = event_data.get('timestamp', datetime.utcnow().isoformat() + 'Z')
        
        cursor.execute("""
            INSERT INTO event_chronicle 
            (event_type, source, source_id, summary, status, data, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (event_type, source, source_id, summary, status, data, timestamp))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "event_id": cursor.lastrowid}
        
    except Exception as e:
        print(f"Error recording event: {e}", file=sys.stderr)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            event_data = json.loads(sys.argv[1])
            result = record_event(event_data)
            print(json.dumps(result))
        except json.JSONDecodeError as e:
            print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
    else:
        print(json.dumps({"success": False, "error": "No event data provided"}))
