#!/usr/bin/env python3
"""
Post-tool hook: Auto-sync golden-rules.md to database

Runs after every tool use. If golden-rules.md was modified, syncs to database.
"""

import sqlite3
import re
from pathlib import Path
import hashlib
import json
from datetime import datetime

STATE_FILE = Path.home() / ".opencode/hooks/investigation-state.json"
MARKDOWN_FILE = Path.home() / ".opencode/emergent-learning/memory/golden-rules.md"
DB_FILE = Path.home() / ".opencode/emergent-learning/memory/index.db"


def get_file_hash(filepath):
    """Get SHA256 hash of file."""
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None


def load_state():
    """Load last known state."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
    except:
        pass
    return {}


def save_state(state):
    """Save current state."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except:
        pass


def sync_golden_rules():
    """Sync markdown to database."""
    try:
        # Read markdown
        with open(MARKDOWN_FILE) as f:
            content = f.read()

        golden_titles = re.findall(r"^## \d+\. (.+)$", content, re.MULTILINE)

        # Connect to database
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()

        # Get all heuristics (no status column exists)
        cur.execute("SELECT id, rule, is_golden FROM heuristics")
        all_heuristics = (
            cur.fetchall()
        )

        updates = 0
        for heuristic_id, rule_text, is_golden in all_heuristics:
            should_be_golden = any(
                title.lower() in rule_text.lower() for title in golden_titles
            )

            if should_be_golden != bool(is_golden):
                cur.execute(
                    "UPDATE heuristics SET is_golden=? WHERE id=?",
                    (1 if should_be_golden else 0, heuristic_id),
                )
                updates += 1

        conn.commit()
        conn.close()

        return updates > 0
    except Exception as e:
        print(f"[WARN] Golden rules sync failed: {e}")
        try:
            from hooks.lib.sgr_logger import log_error

            log_error(f"Golden rules sync failed: {e}")
        except:
            pass
        return False


def run():
    # Debug log
    from datetime import datetime
    from pathlib import Path

    LOG_DIR = Path.home() / ".opencode" / "emergent-learning" / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log", "a") as f:
        f.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DEBUG] sync-golden-rules START\n"
        )
    try:
        from hooks.lib.sgr_logger import log_start, log_success, log_error, log_info

        log_start()
    except:
        pass
    """Check if sync is needed and run it."""
    state = load_state()
    current_hash = get_file_hash(MARKDOWN_FILE)
    last_hash = state.get("golden_rules_hash")

    # If markdown changed, sync to database
    if current_hash and current_hash != last_hash:
        if sync_golden_rules():
            try:
                from hooks.lib.sgr_logger import log_success

                log_success("Synced golden-rules.md to database")
            except:
                pass
            state["golden_rules_hash"] = current_hash
            state["golden_rules_last_sync"] = datetime.now().isoformat()
            save_state(state)
            return "Synced golden-rules.md to database"

    return None


if __name__ == "__main__":
    result = run()
    if result:
        try:
            from hooks.lib.sgr_logger import log_info

            log_info(result)
        except:
            pass
        print(f"[SYNC] {result}")
