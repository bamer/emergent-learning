#!/usr/bin/env python3
"""
Force Learning Extraction from Recent Sessions
This script manually extracts learnings from the last N hours of sessions
and records them to the database.
"""

import sys
import json
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path.home() / ".opencode" / "emergent-learning"))
sys.path.insert(
    0, str(Path.home() / ".opencode" / "emergent-learning" / "hooks" / "learning-loop")
)

# Import the extraction functions
try:
    from post_tool_learning import extract_implicit_learnings, get_db_connection
except ImportError as e:
    print(f"❌ Cannot import learning functions: {e}")
    sys.exit(1)

# Configuration
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = ELF_DIR / "memory" / "index.db"
SESSIONS_DIR = Path.home() / ".opencode" / "sessions"


def get_recent_sessions(hours=24):
    """Find session files from the last N hours."""
    sessions = []
    cutoff = datetime.now() - timedelta(hours=hours)

    if not SESSIONS_DIR.exists():
        print(f"⚠️ Sessions directory not found: {SESSIONS_DIR}")
        return sessions

    for session_file in SESSIONS_DIR.rglob("*.jsonl"):
        try:
            # Check file modification time
            mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
            if mtime > cutoff:
                sessions.append(session_file)
        except Exception as e:
            print(f"⚠️ Error checking {session_file}: {e}")

    return sessions


def extract_from_session_file(session_file):
    """Extract learnings from a session file."""
    learnings = []

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())

                    # Extract from assistant responses
                    if (
                        event.get("type") == "message"
                        and event.get("role") == "assistant"
                    ):
                        content = event.get("content", "")

                        # Get text content
                        if isinstance(content, list):
                            text_parts = [
                                item.get("text", "")
                                for item in content
                                if isinstance(item, dict)
                            ]
                            content = "\n".join(text_parts)

                        # Extract learnings
                        extracted = extract_implicit_learnings(
                            outcome="success",
                            domains=["general"],
                            task_description="",
                            output_content=content,
                        )

                        learnings.extend(extracted)

                        # Also check for explicit markers
                        learning_pattern = r"\[LEARN(?:ED|ING)?:?([^\]]*)\]\s*([^\n]+)"
                        matches = re.findall(learning_pattern, content, re.IGNORECASE)

                        for domain_hint, learning in matches:
                            domain = (
                                domain_hint.strip()
                                if domain_hint.strip()
                                else "general"
                            )
                            learnings.append(
                                {
                                    "type": "heuristic",
                                    "domain": domain,
                                    "rule": learning.strip(),
                                    "confidence": 0.8,
                                    "source": "explicit-marker",
                                }
                            )

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"⚠️ Error reading {session_file}: {e}")

    return learnings


def record_learning_to_db(learning):
    """Record a single learning to the database."""
    try:
        conn = get_db_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        # Check for duplicates
        cursor.execute(
            "SELECT id FROM heuristics WHERE domain = ? AND rule = ?",
            (learning["domain"], learning["rule"]),
        )

        if cursor.fetchone():
            # Update existing
            cursor.execute(
                """
                UPDATE heuristics 
                SET times_validated = times_validated + 1,
                    confidence = MIN(1.0, confidence + 0.05),
                    updated_at = CURRENT_TIMESTAMP
                WHERE domain = ? AND rule = ?
                """,
                (learning["domain"], learning["rule"]),
            )
            return "updated"
        else:
            # Insert new
            cursor.execute(
                """
                            INSERT INTO heuristics 
                            (domain, rule, explanation, confidence, source_type, times_validated, times_violated, is_golden, created_at, updated_at)
                            VALUES (?, ?, ?, ?, 'auto-extracted', 1, 0, 0, ?, ?)
                            """,
                (
                    learning["domain"],
                    learning["rule"],
                    f"Auto-extracted on {datetime.now().isoformat()}",
                    learning["confidence"],
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )
        return "inserted"

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"❌ Error recording learning: {e}")
        return False


def main():
    print("=" * 60)
    print("FORCE LEARNING EXTRACTION - Recent Sessions")
    print("=" * 60)

    # Get sessions from last 24 hours
    print("\n🔍 Finding recent sessions...")
    sessions = get_recent_sessions(hours=24)
    print(f"✅ Found {len(sessions)} recent session files")

    if not sessions:
        print("⚠️ No recent sessions found")
        return

    # Extract learnings
    all_learnings = []
    print("\n📥 Extracting learnings...")

    for session_file in sessions:
        learnings = extract_from_session_file(session_file)
        if learnings:
            print(f"  📄 {session_file.name}: {len(learnings)} learnings")
            all_learnings.extend(learnings)

    print(f"\n📊 Total learnings extracted: {len(all_learnings)}")

    if not all_learnings:
        print("⚠️ No learnings found in recent sessions")
        return

    # Record to database
    print("\n💾 Recording to database...")
    inserted = 0
    updated = 0

    for learning in all_learnings:
        result = record_learning_to_db(learning)
        if result == "inserted":
            inserted += 1
            print(f"  ✨ NEW: {learning['rule'][:50]}...")
        elif result == "updated":
            updated += 1

    print(f"\n✅ Done!")
    print(f"   New heuristics: {inserted}")
    print(f"   Updated heuristics: {updated}")
    print(f"   Total: {inserted + updated}")


if __name__ == "__main__":
    main()
