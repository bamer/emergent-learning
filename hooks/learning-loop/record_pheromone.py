#!/usr/bin/env python3
"""
record_pheromone.py - Record pheromone trails from tool execution

Pheromone trails track which files are accessed/modified during tasks.
Over time, hotspot analysis reveals which files are most frequently
accessed, helping identify critical code sections and collaboration points.

Called by ELF_superpowers.js post-tool hook for Read, Grep, Bash, etc.
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def extract_file_paths(tool_name: str, tool_input: str) -> list:
    """
    Extract file paths from tool input.

    Different tools have different input formats:
    - Read: file path directly
    - Grep: --path followed by path, or pattern and path
    - Bash: might contain file operations (cat, ls, etc.)
    - edit_file/create_file: path parameter
    """
    paths = set()

    if tool_name in ["Read", "create_file", "edit_file"]:
        # First argument is usually the path
        parts = tool_input.strip().split()
        if parts:
            path_str = parts[0]
            if path_str.startswith("/") or path_str.startswith("."):
                paths.add(path_str)

    elif tool_name == "Grep":
        # Look for --path parameter
        if "--path" in tool_input:
            match = re.search(r"--path\s+([^\s]+)", tool_input)
            if match:
                paths.add(match.group(1))

    elif tool_name == "Bash":
        # Extract file paths from common commands
        # cat, ls, find, grep, etc.
        patterns = [
            r"\b(?:cat|ls|find|grep|rm|touch|mv|cp)\s+([^\s|;>]+)",
            r"(?:^|\s)(/[^\s|;>]+)",  # Absolute paths
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, tool_input)
            for match in matches:
                path_str = match.group(1) if match.lastindex else match.group(0)
                if path_str and not path_str in ["|", ";", ">"]:
                    paths.add(path_str)

    return list(paths)


def record_trail(file_path: str, tool_name: str, timestamp: str) -> bool:
    """
    Record a pheromone trail for a file access.

    Returns: True if recorded successfully
    """
    try:
        # Resolve home directory
        home = Path.home()
        file_path_obj = Path(file_path).expanduser()

        # Only record files within ELF directory
        elf_home = home / ".opencode" / "emergent-learning"

        # Debug: Log what we're trying to record
        try:
            relative_path = file_path_obj.relative_to(elf_home)
            print(f"[DEBUG] Recording trail: {relative_path} ({tool_name})")
        except:
            pass

        try:
            file_path_obj.relative_to(elf_home)
        except ValueError:
            # File not in ELF directory, skip
            try:
                from rp_logger import log_info

                log_info(f"SKIPPED (outside ELF): {file_path_obj}")
            except:
                pass
            return False

        # Connect to database
        db_path = elf_home / "memory" / "index.db"
        if not db_path.exists():
            return False

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Insert or update trail
        cursor.execute(
            """
            INSERT INTO pheromone_trails (file_path, tool_name, last_access)
            VALUES (?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                access_count = access_count + 1,
                last_access = ?,
                total_weight = total_weight + 1.0
        """,
            (str(file_path_obj), tool_name, timestamp, timestamp),
        )

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        # Silently fail - pheromone trails are non-critical
        try:
            print(f"[ERROR] FAILED to record trail: {e}")
        except:
            pass
        return False

        # Connect to database
        db_path = elf_home / "memory" / "index.db"
        if not db_path.exists():
            return False

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Ensure pheromone_trails table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pheromone_trails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                tool_name TEXT,
                access_count INTEGER DEFAULT 1,
                first_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_weight REAL DEFAULT 1.0
            )
        """)

        # Insert or update trail
        cursor.execute(
            """
            INSERT INTO pheromone_trails (file_path, tool_name, last_access)
            VALUES (?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                access_count = access_count + 1,
                last_access = ?,
                total_weight = total_weight + 1.0
        """,
            (str(file_path_obj), tool_name, timestamp, timestamp),
        )

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        # Silently fail - pheromone trails are non-critical
        return False


def main():
    """
    Main entry point.

    Receives JSON context from post-tool hook.
    """

    if len(sys.argv) < 2:
        return 0

    try:
        context = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        return 0

    tool_name = context.get("tool_name", "")
    tool_input = context.get("tool_input", "")
    timestamp = context.get("timestamp", datetime.now().isoformat())

    if not tool_name or not tool_input:
        return 0

    # Extract file paths
    file_paths = extract_file_paths(tool_name, tool_input)

    # Record trails
    recorded_count = 0
    for file_path in file_paths:
        if record_trail(file_path, tool_name, timestamp):
            recorded_count += 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
