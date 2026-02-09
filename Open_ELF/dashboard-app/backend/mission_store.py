"""
Mission Storage System - Markdown-based mission tracking

Stores missions as markdown files in .coordination/missions/ directory structure:
- pending/ - Missions waiting to be executed
- running/ - Missions currently being executed
- completed/ - Successfully completed missions
- failed/ - Failed or cancelled missions

Markdown format:
```markdown
# Mission: {mission_id}

## Metadata
- **ID**: {id}
- **Status**: {status}
- **Agent Type**: {agent_type}
- **Created At**: {created_at}
- **Started At**: {started_at}
- **Completed At**: {completed_at}
- **Execution Time**: {duration}

## Mission
{mission_text}

## Result
{result_text}

## Heuristics Extracted
- [domain] heuristic text

## Logs
- [timestamp] log message
```
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class Mission:
    """Represents a mission/task."""

    id: str
    status: str  # pending, running, completed, failed, cancelled
    agent_type: str
    mission_text: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    heuristics: Optional[List[Dict[str, Any]]] = None
    logs: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.heuristics is None:
            self.heuristics = []
        if self.logs is None:
            self.logs = []

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration in seconds."""
        if self.started_at and self.completed_at:
            try:
                start = datetime.fromisoformat(self.started_at)
                end = datetime.fromisoformat(self.completed_at)
                return (end - start).total_seconds()
            except:
                return None
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert mission to dictionary."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Convert mission to markdown format."""
        lines = [
            f"# Mission: {self.id}",
            "",
            "## Metadata",
            f"- **ID**: {self.id}",
            f"- **Status**: {self.status}",
            f"- **Agent Type**: {self.agent_type}",
            f"- **Session ID**: {self.session_id or 'N/A'}",
            f"- **Created At**: {self.created_at}",
        ]

        if self.started_at:
            lines.append(f"- **Started At**: {self.started_at}")
        if self.completed_at:
            lines.append(f"- **Completed At**: {self.completed_at}")
        if self.duration_seconds:
            lines.append(f"- **Execution Time**: {self.duration_seconds:.1f}s")

        lines.extend(
            [
                "",
                "## Mission",
                self.mission_text,
                "",
            ]
        )

        if self.result:
            lines.extend(
                [
                    "## Result",
                    "```",
                    self.result,
                    "```",
                    "",
                ]
            )

        if self.error:
            lines.extend(
                [
                    "## Error",
                    "```",
                    self.error,
                    "```",
                    "",
                ]
            )

        if self.heuristics:
            lines.extend(
                [
                    "## Heuristics Extracted",
                    "",
                ]
            )
            for h in self.heuristics:
                domain = h.get("domain", "general")
                rule = h.get("rule", "")
                lines.append(f"- **[{domain}]** {rule}")
            lines.append("")

        if self.logs:
            lines.extend(
                [
                    "## Logs",
                    "",
                ]
            )
            for log in self.logs:
                timestamp = log.get("timestamp", "")
                message = log.get("message", "")
                level = log.get("level", "INFO")
                lines.append(f"- [{timestamp}] [{level}] {message}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, markdown_text: str) -> "Mission":
        """Parse mission from markdown format."""
        lines = markdown_text.split("\n")

        mission_data = {
            "id": "",
            "status": "pending",
            "agent_type": "auto",
            "mission_text": "",
            "created_at": datetime.now().isoformat(),
            "heuristics": [],
            "logs": [],
        }

        current_section = None
        section_content = []

        for line in lines:
            line = line.strip()

            # Parse title
            if line.startswith("# Mission:"):
                mission_data["id"] = line.replace("# Mission:", "").strip()

            # Parse section headers
            elif line.startswith("## "):
                # Save previous section content
                if current_section == "Mission" and section_content:
                    mission_data["mission_text"] = "\n".join(section_content).strip()
                elif current_section == "Result" and section_content:
                    mission_data["result"] = "\n".join(section_content).strip()
                elif current_section == "Error" and section_content:
                    mission_data["error"] = "\n".join(section_content).strip()

                current_section = line.replace("## ", "").strip()
                section_content = []

            # Parse metadata
            elif line.startswith("- **") and current_section == "Metadata":
                match = re.match(r"- \*\*(.+?)\*\*:\s*(.+)", line)
                if match:
                    key, value = match.groups()
                    key_lower = key.lower().replace(" ", "_")
                    if key_lower == "id":
                        mission_data["id"] = value
                    elif key_lower == "status":
                        mission_data["status"] = value
                    elif key_lower == "agent_type":
                        mission_data["agent_type"] = value
                    elif key_lower == "session_id" and value != "N/A":
                        mission_data["session_id"] = value
                    elif key_lower == "created_at":
                        mission_data["created_at"] = value
                    elif key_lower == "started_at":
                        mission_data["started_at"] = value
                    elif key_lower == "completed_at":
                        mission_data["completed_at"] = value

            # Parse heuristics
            elif line.startswith("- **[") and current_section == "Heuristics Extracted":
                match = re.match(r"- \*\*\[(.+?)\]\*\*\s*(.+)", line)
                if match:
                    domain, rule = match.groups()
                    mission_data["heuristics"].append({"domain": domain, "rule": rule})

            # Parse logs
            elif line.startswith("- [") and current_section == "Logs":
                match = re.match(r"- \[(.+?)\] \[(.+?)\] (.+)", line)
                if match:
                    timestamp, level, message = match.groups()
                    mission_data["logs"].append(
                        {"timestamp": timestamp, "level": level, "message": message}
                    )

            # Collect section content
            elif current_section and line and not line.startswith("```"):
                section_content.append(line)

        # Save last section
        if current_section == "Mission" and section_content:
            mission_data["mission_text"] = "\n".join(section_content).strip()
        elif current_section == "Result" and section_content:
            mission_data["result"] = "\n".join(section_content).strip()
        elif current_section == "Error" and section_content:
            mission_data["error"] = "\n".join(section_content).strip()

        return cls(**mission_data)


class MissionStore:
    """Manages mission storage in markdown files."""

    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            base_path = (
                Path.home()
                / ".opencode"
                / "emergent-learning"
                / ".coordination"
                / "missions"
            )
        self.base_path = Path(base_path)

        # Tasks directory for TaskKanban compatibility
        self.tasks_dir = Path.home() / ".opencode" / "tasks"
        self.missions_session_dir = self.tasks_dir / "elf_missions"

        # Ensure directories exist
        for status in ["pending", "running", "completed", "failed"]:
            (self.base_path / status).mkdir(parents=True, exist_ok=True)

        # Ensure tasks directory exists
        self.missions_session_dir.mkdir(parents=True, exist_ok=True)

    def _get_mission_path(self, mission_id: str, status: str) -> Path:
        """Get file path for a mission."""
        return self.base_path / status / f"{mission_id}.md"

    def _sync_to_task_file(self, mission: Mission) -> None:
        """Sync mission to a task file for TaskKanban compatibility."""
        try:
            # Map mission status to task status
            status_mapping = {
                "pending": "pending",
                "running": "in_progress",
                "completed": "completed",
                "failed": "error",
            }
            task_status = status_mapping.get(mission.status, "pending")

            # Create task data
            task_data = {
                "id": mission.id,
                "subject": f"[{mission.agent_type}] {mission.mission_text[:60]}{'...' if len(mission.mission_text) > 60 else ''}",
                "description": mission.mission_text,
                "status": task_status,
                "session_id": "elf_missions",
                "session_name": f"ELF Missions {datetime.now().strftime('%Y-%m-%d')}",
                "notes": [
                    {
                        "text": log.get("message", ""),
                        "timestamp": log.get("timestamp", datetime.now().isoformat()),
                        "source": log.get("level", "INFO").lower(),
                    }
                    for log in (mission.logs or [])
                ],
            }

            # Add result if available
            if mission.result:
                task_data["output"] = mission.result
            if mission.error:
                task_data["result"] = f"Error: {mission.error}"

            # Write task file
            task_file = self.missions_session_dir / f"{mission.id}.json"
            task_file.write_text(json.dumps(task_data, indent=2))

            # Debug log
            print(
                f"[MissionStore] Synced mission {mission.id} to task file: {task_file}"
            )
            print(f"[MissionStore]   Status: {mission.status} -> {task_status}")
            print(f"[MissionStore]   Mission text: {mission.mission_text[:50]}...")
            if mission.result:
                print(f"[MissionStore]   Result length: {len(mission.result)} chars")
            if mission.error:
                print(f"[MissionStore]   Error: {mission.error}")

        except Exception as e:
            # Non-critical - just log the error
            print(f"[MissionStore] Warning: Failed to sync task file: {e}")
            import traceback

            traceback.print_exc()

    def create_mission(self, agent_type: str, mission_text: str) -> Mission:
        """Create a new pending mission."""
        mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(mission_text) % 10000:04d}"

        mission = Mission(
            id=mission_id,
            status="pending",
            agent_type=agent_type,
            mission_text=mission_text,
            created_at=datetime.now().isoformat(),
            logs=[
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "message": "Mission created and queued",
                }
            ],
        )

        # Save to pending directory
        mission_path = self._get_mission_path(mission_id, "pending")
        mission_path.write_text(mission.to_markdown())

        # Sync to task file for TaskKanban
        self._sync_to_task_file(mission)

        return mission

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Get mission by ID (searches all statuses)."""
        for status in ["pending", "running", "completed", "failed"]:
            mission_path = self._get_mission_path(mission_id, status)
            if mission_path.exists():
                return Mission.from_markdown(mission_path.read_text())
        return None

    def update_mission(self, mission: Mission) -> None:
        """Update mission and move to appropriate directory."""
        # Find current location
        old_path = None
        for status in ["pending", "running", "completed", "failed"]:
            path = self._get_mission_path(mission.id, status)
            if path.exists():
                old_path = path
                break

        # Remove from old location
        if old_path:
            old_path.unlink()

        # Save to new location
        new_path = self._get_mission_path(mission.id, mission.status)
        new_path.write_text(mission.to_markdown())

        # Sync to task file for TaskKanban
        self._sync_to_task_file(mission)

    def list_missions(self, status: Optional[str] = None) -> List[Mission]:
        """List all missions, optionally filtered by status."""
        missions = []
        statuses = [status] if status else ["pending", "running", "completed", "failed"]

        for s in statuses:
            status_dir = self.base_path / s
            if not status_dir.exists():
                continue

            for mission_file in sorted(status_dir.glob("*.md"), reverse=True):
                try:
                    mission = Mission.from_markdown(mission_file.read_text())
                    missions.append(mission)
                except Exception:
                    continue

        return missions

    def start_mission(self, mission_id: str, session_id: str) -> Optional[Mission]:
        """Mark mission as running."""
        mission = self.get_mission(mission_id)
        if not mission:
            return None

        mission.status = "running"
        mission.session_id = session_id
        mission.started_at = datetime.now().isoformat()
        if mission.logs is None:
            mission.logs = []
        mission.logs.append(
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Mission started with session {session_id}",
            }
        )

        self.update_mission(mission)
        return mission

    def complete_mission(
        self, mission_id: str, result: str, heuristics: Optional[List[Dict]] = None
    ) -> Optional[Mission]:
        """Mark mission as completed."""
        mission = self.get_mission(mission_id)
        if not mission:
            return None

        mission.status = "completed"
        mission.result = result
        mission.completed_at = datetime.now().isoformat()
        if heuristics:
            mission.heuristics = heuristics if heuristics else []
        if mission.logs is None:
            mission.logs = []
        mission.logs.append(
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Mission completed successfully ({mission.duration_seconds:.1f}s)",
            }
        )

        self.update_mission(mission)
        return mission

    def fail_mission(self, mission_id: str, error: str) -> Optional[Mission]:
        """Mark mission as failed."""
        mission = self.get_mission(mission_id)
        if not mission:
            return None

        mission.status = "failed"
        mission.error = error
        mission.completed_at = datetime.now().isoformat()
        if mission.logs is None:
            mission.logs = []
        mission.logs.append(
            {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": f"Mission failed: {error}",
            }
        )

        self.update_mission(mission)
        return mission

    def cancel_mission(self, mission_id: str) -> Optional[Mission]:
        """Mark mission as cancelled."""
        mission = self.get_mission(mission_id)
        if not mission:
            return None

        mission.status = "failed"  # Use failed status for cancelled
        mission.error = "Cancelled by user"
        mission.completed_at = datetime.now().isoformat()
        if mission.logs is None:
            mission.logs = []
        mission.logs.append(
            {
                "timestamp": datetime.now().isoformat(),
                "level": "WARNING",
                "message": "Mission cancelled by user",
            }
        )

        self.update_mission(mission)
        return mission


# Global mission store instance
_mission_store: Optional[MissionStore] = None


def get_mission_store() -> MissionStore:
    """Get or create the global mission store."""
    global _mission_store
    if _mission_store is None:
        _mission_store = MissionStore()
    return _mission_store
