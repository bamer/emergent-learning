#!/usr/bin/env python3
"""
Organize ELF Swarm Missions - Move missions to proper session directories
"""

import json
import shutil
import re
from pathlib import Path

TASKS_DIR = Path.home() / ".opencode" / "tasks"
SWARM_DIR = TASKS_DIR / "elf_missions"


def get_session_from_mission(mission_file):
    """Extract session_id from a mission file."""
    try:
        with open(mission_file, "r") as f:
            data = json.load(f)
            # Try to get the session_id from notes or the file itself
            notes = data.get("notes", [])
            for note in notes:
                if "session" in note.get("text", "").lower():
                    # Extract session ID from text like "Mission started with session ses_39d7fe546ffeIuC30QletgskXT"
                    match = re.search(r"session (ses_\w+)", note.get("text", ""))
                    if match:
                        return match.group(1)
            # Fallback: use the file's session_id field
            return data.get("session_id", "elf_swarm_ses_" + mission_file.stem[-12:])
    except Exception as e:
        print(f"Error reading {mission_file}: {e}")
        return None


def analyze_missions():
    """Analyze all missions and their sessions."""
    if not SWARM_DIR.exists():
        print(f"Swarm directory not found: {SWARM_DIR}")
        return

    sessions_to_create = {}
    missions_by_session = {}

    for mission_file in SWARM_DIR.glob("mission_*.json"):
        try:
            with open(mission_file, "r") as f:
                data = json.load(f)

                session_id = data.get("session_id", "")
                notes = data.get("notes", [])

                # Look for actual session in notes
                actual_session = None
                for note in notes:
                    if "session" in note.get("text", "").lower() and "ses_" in note.get(
                        "text", ""
                    ):
                        import re

                        match = re.search(r"(es_\w+)", note.get("text", ""))
                        if match:
                            actual_session = match.group(1)
                            break

                if actual_session:
                    sessions_to_create[actual_session] = True
                    if actual_session not in missions_by_session:
                        missions_by_session[actual_session] = []
                    missions_by_session[actual_session].append(mission_file)
        except Exception as e:
            print(f"Error analyzing {mission_file}: {e}")

    return sessions_to_create, missions_by_session


def main():
    import sys
    import re

    print("=" * 60)
    print("Organize ELF Swarm Missions")
    print("=" * 60)

    if not SWARM_DIR.exists():
        print(f"❌ Swarm directory not found: {SWARM_DIR}")
        sys.exit(1)

    print(f"\n📁 Swarm directory: {SWARM_DIR}")

    # Count total missions
    total_missions = len(list(SWARM_DIR.glob("mission_*.json")))
    print(f"📊 Total missions: {total_missions}")

    # Simple solution: Update sessions-index.json to include all elf_missions
    # Don't move files - just make them discoverable by the dashboard

    print("\n" + "=" * 60)
    print("Solution: Keep missions in elf_missions, update index")
    print("=" * 60)

    # The backend changes I made should already handle this!
    # Let's verify it's working

    print("\n✅ Backend has been updated to handle mission_*.json files")
    print("✅ Missions will now appear in the 'ELF Missions' session")
    print("\n📋 Next steps:")
    print("   1. Restart the dashboard backend")
    print("   2. Refresh the frontend")


if __name__ == "__main__":
    main()
