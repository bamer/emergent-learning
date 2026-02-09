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


def extract_file_paths(tool_name: str, tool_input) -> list:
    """
    Extract file paths from tool input.

    Different tools have different input formats:
    - Read: file_path parameter in dict
    - Grep: path parameter in dict or --path in string
    - Bash: might contain file operations (cat, ls, etc.)
    - Edit: file_path parameter in dict
    - Write: filePath parameter in dict
    """
    paths = set()

    # Normalize tool_name to lowercase for comparison
    tool_name_lower = tool_name.lower()

    # Handle dict input (superpowers.js / event_bridge format)
    if isinstance(tool_input, dict):
        if tool_name_lower in ["read"]:
            # Read tool sends file_path
            path_str = tool_input.get("file_path", "")
            if path_str:
                paths.add(path_str)
        elif tool_name_lower in ["edit", "write"]:
            # Edit/Write send file_path or filePath
            path_str = tool_input.get("file_path") or tool_input.get("filePath", "")
            if path_str:
                paths.add(path_str)
        elif tool_name_lower in ["grep"]:
            # Grep sends path parameter
            path_str = tool_input.get("path", "")
            if path_str:
                paths.add(path_str)
        elif tool_name_lower in ["glob"]:
            # Glob sends pattern or path
            path_str = tool_input.get("pattern") or tool_input.get("path", "")
            if path_str:
                paths.add(path_str)
        elif tool_name_lower == "bash":
            # Bash might have file paths in the command string
            command = tool_input.get("command", "")
            # Extract file paths from common commands
            patterns = [
                r"\b(?:cat|ls|find|grep|rm|touch|mv|cp)\s+([^\s|;>]+)",
                r"(?:^|\s)(/[^\s|;>]+)",  # Absolute paths
            ]
            for pattern in patterns:
                matches = re.finditer(pattern, command)
                for match in matches:
                    path_str = match.group(1) if match.lastindex else match.group(0)
                    # Filter out options/flags that look like paths
                    if path_str and not path_str.startswith("-"):
                        paths.add(path_str)
        return list(paths)

    # Handle string input (legacy format)
    tool_input = str(tool_input) if tool_input else ""

    if tool_name_lower in ["read", "create_file", "edit_file"]:
        # First argument is usually the path
        parts = tool_input.strip().split()
        if parts:
            path_str = parts[0]
            if path_str.startswith("/") or path_str.startswith("."):
                paths.add(path_str)

    elif tool_name_lower == "grep":
        # Look for --path parameter
        if "--path" in tool_input:
            match = re.search(r"--path\s+([^\s]+)", tool_input)
            if match:
                paths.add(match.group(1))

    elif tool_name_lower == "bash":
        # Extract file paths from common commands
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

        try:
            file_path_obj.relative_to(elf_home)
        except ValueError:
            # File not in ELF directory, skip
            sys.stderr.write(f"[PHEROMONE] Skipping non-ELF file: {file_path}\n")
            return False

        # Connect to database
        db_path = elf_home / "memory" / "index.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Ensure pheromone_trails table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pheromone_trails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
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

        sys.stderr.write(f"[PHEROMONE] ✅ Recorded: {file_path_obj} ({tool_name})\n")
        return True

    except Exception as e:
        # Log error but don't crash - pheromone trails are non-critical
        sys.stderr.write(f"[PHEROMONE] ❌ Failed to record {file_path}: {e}\n")
        return False


def main():
    """
    Main entry point.

    Receives JSON context from post-tool hook.
    - event_bridge: sends data via stdin
    - ELF_superpowers.js: sends data as command-line argument

    Payload structure: { tool_name: "...", tool_input: {...}, ... }
    """

    # Try stdin first (event_bridge)
    context = None
    try:
        if not sys.stdin.isatty():
            context_str = sys.stdin.read()
            if context_str:
                context = json.loads(context_str)
    except (json.JSONDecodeError, IOError):
        pass

    # Fallback to command-line argument (superpowers.js compatibility)
    if context is None and len(sys.argv) >= 2:
        try:
            context = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            return 0

    if not context:
        return 0

    # Handle payload structure (both event_bridge and superpowers.js)
    tool_name = context.get("tool_name", "")
    # 'tool_input' from event_bridge, 'input' from superpowers.js
    tool_input_data = context.get("tool_input") or context.get("input", {})
    timestamp = context.get("timestamp", datetime.now().isoformat())

    if not tool_name:
        return 0

    # Debug: Log received input
    sys.stderr.write(f"[PHEROMONE] 🚀 Processing: {tool_name}\n")
    sys.stderr.write(f"[PHEROMONE] Input type: {type(tool_input_data).__name__}\n")

    # Extract file paths (pass the raw data, function handles both dict and string)
    file_paths = extract_file_paths(tool_name, tool_input_data)

    sys.stderr.write(f"[PHEROMONE] 📋 Extracted {len(file_paths)} file paths\n")

    # Record trails
    recorded_count = 0
    for file_path in file_paths:
        if record_trail(file_path, tool_name, timestamp):
            recorded_count += 1

    sys.stderr.write(
        f"[PHEROMONE] 📊 Recorded {recorded_count}/{len(file_paths)} trails\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
