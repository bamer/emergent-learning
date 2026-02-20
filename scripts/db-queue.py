#!/usr/bin/env python3
"""
Queue-based database writer for ELF
When database is locked, writes are queued to JSON files and processed later
"""

import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import sys

BASE_DIR = Path("/home/bamer/OPC_ELF")
QUEUE_DIR = BASE_DIR / "memory" / "queue"
DB_PATH = BASE_DIR / "memory" / "index.db"


def ensure_queue_dir():
    """Ensure queue directory exists."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)


def queue_write(table: str, data: Dict[str, Any]) -> bool:
    """
    Queue a database write when database is locked.
    Returns True if queued successfully.
    """
    ensure_queue_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    queue_file = QUEUE_DIR / f"{table}_{timestamp}.json"

    queue_data = {
        "table": table,
        "data": data,
        "queued_at": datetime.now().isoformat(),
        "retry_count": 0,
    }

    try:
        with open(queue_file, "w") as f:
            json.dump(queue_data, f, indent=2)
        print(f"📝 Write queued: {queue_file.name}")
        return True
    except Exception as e:
        print(f"❌ Failed to queue write: {e}", file=sys.stderr)
        return False


def process_queue() -> int:
    """
    Process all queued writes.
    Returns number of successful writes.
    """
    if not QUEUE_DIR.exists():
        return 0

    queue_files = sorted(QUEUE_DIR.glob("*.json"))
    if not queue_files:
        return 0

    processed = 0
    failed = 0

    print(f"🔄 Processing {len(queue_files)} queued writes...")

    for queue_file in queue_files:
        try:
            with open(queue_file, "r") as f:
                queue_data = json.load(f)

            table = queue_data["table"]
            data = queue_data["data"]

            # Try to write to database
            if write_to_db(table, data):
                # Success - remove queue file
                queue_file.unlink()
                processed += 1
            else:
                # Failed - increment retry count
                queue_data["retry_count"] = queue_data.get("retry_count", 0) + 1
                queue_data["last_attempt"] = datetime.now().isoformat()

                if queue_data["retry_count"] > 10:
                    # Too many retries - move to failed
                    failed_file = QUEUE_DIR / "failed" / queue_file.name
                    failed_file.parent.mkdir(exist_ok=True)
                    queue_file.rename(failed_file)
                    print(
                        f"⚠️  Max retries exceeded, moved to failed: {queue_file.name}"
                    )
                else:
                    # Update queue file with retry count
                    with open(queue_file, "w") as f:
                        json.dump(queue_data, f, indent=2)
                failed += 1

        except Exception as e:
            print(f"❌ Error processing {queue_file.name}: {e}", file=sys.stderr)
            failed += 1

    if processed > 0:
        print(f"✅ Processed {processed} queued writes")
    if failed > 0:
        print(f"⚠️  {failed} writes still pending")

    return processed


def write_to_db(table: str, data: Dict[str, Any]) -> bool:
    """
    Write data to database table.
    Returns True if successful.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        cursor = conn.cursor()

        if table == "learnings":
            cursor.execute(
                """
                INSERT INTO learnings (type, filepath, title, summary, tags, domain, severity, created_at)
                VALUES (:type, :filepath, :title, :summary, :tags, :domain, :severity, :created_at)
            """,
                data,
            )
        elif table == "heuristics":
            cursor.execute(
                """
                INSERT INTO heuristics (domain, rule, explanation, source_type, confidence, created_at, updated_at)
                VALUES (:domain, :rule, :explanation, :source_type, :confidence, :created_at, :updated_at)
            """,
                data,
            )
        else:
            print(f"❌ Unknown table: {table}", file=sys.stderr)
            return False

        conn.commit()
        conn.close()
        return True

    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            return False
        raise
    except Exception as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        return False


def try_write_or_queue(table: str, data: Dict[str, Any]) -> bool:
    """
    Try to write to database, queue if locked.
    Returns True if written or queued successfully.
    """
    # First, try to write directly
    if write_to_db(table, data):
        print(f"✅ Written to database: {data.get('title', 'N/A')}")
        return True

    # If failed, queue it
    print(f"⏳ Database locked, queuing write...")
    return queue_write(table, data)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ELF Queue-based Database Writer")
    parser.add_argument(
        "--process-queue", action="store_true", help="Process all queued writes"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon, processing queue every 30s",
    )

    args = parser.parse_args()

    if args.daemon:
        print("🤖 Queue processor daemon started")
        print(f"   Processing queue every 30 seconds...")
        print(f"   Press Ctrl+C to stop")
        try:
            while True:
                count = process_queue()
                if count > 0:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Processed {count} items"
                    )
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n👋 Daemon stopped")
    elif args.process_queue:
        process_queue()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
