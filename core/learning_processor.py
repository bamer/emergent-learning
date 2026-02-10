#!/usr/bin/env python3
"""
Learning Processor - Centralized Learning & Trail Management

Single entry point for ALL learning operations:
- Pre-tool context injection and heuristic consultation
- Post-tool outcome analysis and validation
- Heuristic capture and promotion
- Pheromone trails (file access tracking)
- Workflow trails with scents (discovery, blocker, hot, cold)
- Hot spot analysis and trail decay
- Auto-failure recording
- Advisory verification

This replaces:
- hooks/learning-loop/post_tool_learning.py
- hooks/learning-loop/record_pheromone.py
- conductor trail functionality
"""

import json
import sys
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Setup logging
try:
    from Open_ELF.utils.elf_logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

# Configuration
DB_PATH = ELF_DIR / "memory" / "index.db"
STATE_FILE = (
    Path.home() / ".opencode" / "hooks" / "learning-loop" / "session-state.json"
)
SEMANTIC_DAEMON_URL = "http://localhost:5001"

# Risky patterns for advisory verification
RISKY_PATTERNS = {
    "code_execution": [
        (r"eval\s*\(", "eval() detected - potential code injection"),
        (r"exec\s*\(", "exec() detected - potential code injection"),
        (
            r"subprocess\.call\s*\([^)]*shell\s*=\s*True",
            "shell=True in subprocess - command injection risk",
        ),
        (r"os\.system\s*\(", "os.system() - command injection risk"),
    ],
    "file_operations": [
        (r"open\s*\([^)]*['\"]w['\"]", "File write operation - check path validation"),
        (r"shutil\.(rmtree|move|copy)", "Dangerous file operation"),
    ],
    "security": [
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
        (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
        (r"token\s*=\s*['\"][^'\"]+['\"]", "Hardcoded token detected"),
    ],
}


@dataclass
class ToolEvent:
    """Represents a tool execution event."""

    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Dict[str, Any]
    session_id: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class LearningProcessor:
    """
    Centralized processor for all learning operations.

    Handles:
    - Pre-tool: context injection, heuristic consultation
    - Post-tool: outcome analysis, validation, learning capture
    - Trail recording (pheromone + workflow)
    - Advisory verification
    - Auto-failure recording
    """

    def __init__(self):
        self.db_path = DB_PATH
        self.elf_dir = ELF_DIR
        self.session_state = self._load_session_state()

    def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Get database connection."""
        if not self.db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=5.0)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}", exc_info=True)
            return None

    def _load_session_state(self) -> Dict:
        """Load session state with TTL-based recovery."""
        SESSION_TTL = 4 * 60 * 60  # 4 hours
        current_time = datetime.now()

        default_state = {
            "session_start": current_time.isoformat(),
            "heuristics_consulted": [],
            "domains_queried": [],
            "last_updated": current_time.isoformat(),
        }

        if STATE_FILE.exists():
            try:
                state = json.loads(STATE_FILE.read_text())
                last_updated = state.get("last_updated", state.get("session_start", ""))

                if last_updated:
                    last_time = datetime.fromisoformat(last_updated)
                    if (current_time - last_time).total_seconds() > SESSION_TTL:
                        return default_state

                # Ensure arrays are initialized
                if not isinstance(state.get("heuristics_consulted"), list):
                    state["heuristics_consulted"] = []
                if not isinstance(state.get("domains_queried"), list):
                    state["domains_queried"] = []

                state["last_updated"] = current_time.isoformat()
                return state
            except Exception as e:
                logger.error(f"Failed to load session state: {e}", exc_info=True)
                return default_state

        return default_state

    def _save_session_state(self):
        """Save session state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.session_state["last_updated"] = datetime.now().isoformat()
        STATE_FILE.write_text(json.dumps(self.session_state, indent=2))

    # =========================================================================
    # PRE-TOOL PROCESSING
    # =========================================================================

    def pre_tool_process(self, event: ToolEvent) -> Dict[str, Any]:
        """
        Process tool BEFORE execution.

        - Load relevant heuristics (keyword)
        - Query semantic memory (embedding)
        - Build injectable context
        - Track consulted heuristics
        """
        result = {
            "context_injected": False,
            "heuristics": [],
            "semantic_memories": [],
            "domains": [],
            "injectable_context": "",
        }

        # Auto-detect domains from tool input
        domains = self._detect_domains(event.tool_input, event.tool_name)
        result["domains"] = domains
        self.session_state["domains_queried"] = domains

        # Consult relevant heuristics (keyword-based)
        heuristics = []
        if domains:
            heuristics = self._consult_heuristics(domains, limit=5)
            result["heuristics"] = heuristics
            result["heuristics_consulted"] = [h["id"] for h in heuristics]
            self.session_state["heuristics_consulted"] = result["heuristics_consulted"]

        # Semantic search (embedding-based)
        query_text = self._build_semantic_query(event)
        if query_text:
            memories = self._semantic_search(query_text, top_k=3, min_similarity=0.25)
            result["semantic_memories"] = memories

        # Build injectable context string
        context_lines = []

        if heuristics:
            context_lines.append("## Relevant Heuristics (from ELF memory)")
            for h in heuristics[:3]:
                conf = h.get("confidence", 0)
                context_lines.append(
                    f"- [{h.get('domain', 'general')}] {h.get('rule', '')} (confidence: {conf:.0%})"
                )
            context_lines.append("")

        if result["semantic_memories"]:
            context_lines.append("## Semantic Memories (similar past experiences)")
            for m in result["semantic_memories"][:3]:
                sim = m.get("similarity", 0)
                text = m.get("text", "")[:150]
                context_lines.append(f"- (similarity: {sim:.0%}) {text}")
            context_lines.append("")

        if context_lines:
            result["injectable_context"] = "\n".join(context_lines)
            result["context_injected"] = True

        self._save_session_state()
        return result

    def _build_semantic_query(self, event: ToolEvent) -> str:
        """Build a semantic search query from tool event."""
        parts = [f"Tool: {event.tool_name}"]

        if isinstance(event.tool_input, dict):
            # Extract meaningful fields
            for key in (
                "filePath",
                "file_path",
                "path",
                "command",
                "pattern",
                "content",
                "description",
            ):
                val = event.tool_input.get(key, "")
                if val and isinstance(val, str):
                    parts.append(val[:200])
                    break

        query = " ".join(parts)
        return query[:500] if query else ""

    def _detect_domains(self, tool_input: Dict, tool_name: str) -> List[str]:
        """Auto-detect domains from tool context."""
        content = json.dumps(tool_input).lower()

        domain_keywords = {
            "security": [
                "security",
                "vulnerability",
                "encrypt",
                "password",
                "auth",
                "permission",
                "validate",
            ],
            "performance": [
                "performance",
                "speed",
                "cache",
                "optimize",
                "memory",
                "cpu",
                "async",
            ],
            "testing": ["test", "pytest", "unittest", "mock", "assert", "coverage"],
            "database": ["database", "sql", "sqlite", "postgres", "query", "migration"],
            "api": ["api", "endpoint", "request", "response", "http", "rest"],
            "frontend": ["frontend", "ui", "html", "css", "javascript", "react"],
        }

        detected = []
        for domain, keywords in domain_keywords.items():
            if any(kw in content for kw in keywords):
                detected.append(domain)

        return detected if detected else ["general"]

    def _consult_heuristics(self, domains: List[str], limit: int = 5) -> List[Dict]:
        """Consult relevant heuristics for given domains."""
        conn = self._get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            heuristics = []

            for domain in domains:
                cursor.execute(
                    """
                    SELECT id, domain, rule, explanation, confidence
                    FROM heuristics
                    WHERE domain = ? OR is_golden = 1
                    ORDER BY is_golden DESC, confidence DESC, times_validated DESC
                    LIMIT ?
                """,
                    (domain, limit),
                )

                for row in cursor.fetchall():
                    h = dict(row)
                    if h not in heuristics:
                        heuristics.append(h)

            return heuristics[:limit]
        except Exception as e:
            print(f"Error consulting heuristics: {e}", file=sys.stderr)
            return []
        finally:
            conn.close()

    def _semantic_search(
        self, query_text: str, top_k: int = 3, min_similarity: float = 0.25
    ) -> List[Dict]:
        """Query semantic daemon for relevant memories."""
        try:
            import urllib.request

            payload = json.dumps(
                {
                    "query": query_text,
                    "top_k": top_k,
                    "min_similarity": min_similarity,
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{SEMANTIC_DAEMON_URL}/search",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("results", [])
        except Exception as e:
            logger.error(f"Failed to fetch embeddings: {e}", exc_info=True)
            return []

    def _store_embedding(
        self,
        text: str,
        source_id: str,
        source_type: str,
        metadata: Optional[Dict] = None,
    ):
        """Store text with embedding in semantic daemon."""
        try:
            import urllib.request

            payload = json.dumps(
                {
                    "text": text,
                    "source_id": source_id,
                    "source_type": source_type,
                    "metadata": metadata or {},
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{SEMANTIC_DAEMON_URL}/store",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass  # Fire and forget
        except Exception as e:
            logger.error(f"Failed to store embedding: {e}", exc_info=True)

    # =========================================================================
    # POST-TOOL PROCESSING
    # =========================================================================

    def post_tool_process(self, event: ToolEvent) -> Dict[str, Any]:
        """
        Process tool AFTER execution.

        - Determine outcome (success/failure/unknown)
        - Validate consulted heuristics
        - Record learnings
        - Lay trails
        - Advisory verification
        - Auto-failure recording
        - Execute PostToolUse hooks
        """
        result = {
            "outcome": "unknown",
            "heuristics_validated": 0,
            "heuristics_violated": 0,
            "learnings_recorded": 0,
            "trails_recorded": 0,
            "advisory_warnings": [],
            "failure_auto_recorded": False,
            "hooks_executed": 0,
        }

        # Determine outcome
        outcome, reason = self._determine_outcome(event.tool_output)
        result["outcome"] = outcome
        result["outcome_reason"] = reason

        # Get consulted heuristics
        heuristic_ids = self.session_state.get("heuristics_consulted", [])

        # Validate heuristics
        if heuristic_ids:
            validated, violated = self._validate_heuristics(heuristic_ids, outcome)
            result["heuristics_validated"] = validated
            result["heuristics_violated"] = violated

        # Record trails
        trails_count = self._record_trails(event, outcome)
        result["trails_recorded"] = trails_count

        # Advisory verification for Edit/Write tools
        if event.tool_name in ("Edit", "Write"):
            warnings = self._advisory_verification(event)
            result["advisory_warnings"] = warnings

        # Extract and record learnings
        if outcome in ("success", "unknown"):
            learnings = self._extract_and_record_learnings(event, outcome)
            result["learnings_recorded"] = learnings

        # Auto-record failure
        if outcome == "failure":
            self._auto_record_failure(event, reason)
            result["failure_auto_recorded"] = True

        # Check for golden rule promotion
        self._check_golden_rule_promotion()

        # Execute PostToolUse hooks (e.g., sync-golden-rules.py)
        hooks_executed = self._execute_post_tool_hooks(event)
        result["hooks_executed"] = hooks_executed

        # Clear session state for next tool
        self.session_state["heuristics_consulted"] = []
        self._save_session_state()

        return result

    def _execute_post_tool_hooks(self, event: ToolEvent) -> int:
        """Execute all PostToolUse hooks from hooks/PostToolUse/ directory."""
        import subprocess
        import os

        hooks_dir = Path.home() / ".opencode" / "hooks" / "PostToolUse"
        if not hooks_dir.exists():
            return 0

        count = 0
        # Find all Python files except utilities (starting with _ or sgr_logger)
        hook_files = [
            f
            for f in hooks_dir.glob("*.py")
            if not f.name.startswith("_")
            and f.name not in ("sgr_logger.py", "sync-golden-rules-logging.py")
        ]

        for hook_file in sorted(hook_files):
            try:
                # Prepare hook input data
                hook_data = {
                    "tool": event.tool_name,
                    "tool_name": event.tool_name,
                    "tool_input": event.tool_input,
                    "tool_output": event.tool_output,
                    "session": {"id": event.session_id} if event.session_id else {},
                    "timestamp": event.timestamp or datetime.now().isoformat(),
                }

                # Execute hook with stdin
                proc = subprocess.run(
                    [sys.executable, str(hook_file)],
                    input=json.dumps(hook_data),
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(Path.home() / ".opencode"),
                )

                if proc.returncode == 0:
                    count += 1
                else:
                    print(
                        f"[HOOK_ERROR] {hook_file.name}: {proc.stderr[:200]}",
                        file=sys.stderr,
                    )

            except subprocess.TimeoutExpired:
                print(f"[HOOK_TIMEOUT] {hook_file.name}", file=sys.stderr)
            except Exception as e:
                print(f"[HOOK_EXCEPTION] {hook_file.name}: {e}", file=sys.stderr)

        return count

    def _determine_outcome(self, tool_output: Dict) -> Tuple[str, str]:
        """Determine if tool execution succeeded, failed, or is unknown."""
        if not tool_output:
            return "unknown", "No output to analyze"

        content = ""
        if isinstance(tool_output, dict):
            content = tool_output.get("content", "")
            if isinstance(content, list):
                content = "\n".join(str(item) for item in content)
        elif isinstance(tool_output, str):
            content = tool_output

        if not content:
            return "unknown", "Empty output"

        content_lower = content.lower()

        # Failure patterns
        failure_patterns = [
            (r"(?i)\berror\b[:\s]", "Error detected"),
            (r"(?i)\bexception\b[:\s]", "Exception raised"),
            (r"(?i)\bfailed\b[:\s]", "Operation failed"),
            (r"(?i)\bcould not\b", "Could not complete"),
            (r"(?i)\bunable to\b", "Unable to complete"),
            (r"\[BLOCKER\]", "Blocker encountered"),
            (r"(?i)\btraceback\b", "Exception traceback"),
            (r"(?i)\bpermission denied\b", "Permission denied"),
        ]

        # False positive patterns
        false_positives = [
            r"(?i)was not found to be",
            r"(?i)\berror handling\b",
            r"(?i)\bno errors?\b",
            r"(?i)\bwithout errors?\b",
            r"(?i)\bfixed.*\berror\b",
        ]

        for pattern, reason in failure_patterns:
            if re.search(pattern, content, re.MULTILINE):
                # Check for false positives
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    match_start = max(0, match.start() - 30)
                    match_end = min(len(content), match.end() + 30)
                    context = content[match_start:match_end]

                    is_false_positive = any(
                        re.search(fp, context) for fp in false_positives
                    )
                    if not is_false_positive:
                        return "failure", reason

        # Success patterns
        success_patterns = [
            r"\bsuccessfully\s+\w+",
            r"\btask\s+complete",
            r"\bcompleted\s+successfully",
            r"\[success\]",
        ]

        for pattern in success_patterns:
            if re.search(pattern, content_lower):
                return "success", "Success indicators found"

        # Action verbs indicating completion
        action_patterns = [
            r"\b(created|generated|built|made|fixed|updated|implemented|analyzed)\b",
        ]

        for pattern in action_patterns:
            if re.search(pattern, content_lower):
                return "success", "Action completed"

        # If substantial output without errors, assume success
        if len(content) > 50:
            return "success", "Substantial output without errors"

        return "unknown", "Could not determine outcome"

    def _validate_heuristics(
        self, heuristic_ids: List[int], outcome: str
    ) -> Tuple[int, int]:
        """Update heuristic validation counts."""
        if not heuristic_ids:
            return 0, 0

        conn = self._get_db_connection()
        if not conn:
            return 0, 0

        try:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            placeholders = ",".join("?" * len(heuristic_ids))

            validated = 0
            violated = 0

            if outcome == "success":
                cursor.execute(
                    f"""
                    UPDATE heuristics
                    SET times_validated = times_validated + 1,
                        confidence = MIN(1.0, confidence + 0.01),
                        updated_at = ?
                    WHERE id IN ({placeholders})
                """,
                    (timestamp, *heuristic_ids),
                )
                validated = cursor.rowcount

            elif outcome == "failure":
                cursor.execute(
                    f"""
                    UPDATE heuristics
                    SET times_violated = times_violated + 1,
                        confidence = MAX(0.0, confidence - 0.02),
                        updated_at = ?
                    WHERE id IN ({placeholders})
                """,
                    (timestamp, *heuristic_ids),
                )
                violated = cursor.rowcount

            conn.commit()
            return validated, violated

        except Exception as e:
            print(f"Error validating heuristics: {e}", file=sys.stderr)
            conn.rollback()
            return 0, 0
        finally:
            conn.close()

    # =========================================================================
    # TRAIL RECORDING
    # =========================================================================

    def _record_trails(self, event: ToolEvent, outcome: str) -> int:
        """Record all types of trails for the tool execution."""
        count = 0

        # Pheromone trails (file access tracking)
        count += self._record_pheromone_trails(event)

        # Workflow trails (scents)
        count += self._record_workflow_trails(event, outcome)

        return count

    def _record_pheromone_trails(self, event: ToolEvent) -> int:
        """
        Record pheromone trails for file operations.
        Tracks which files are accessed/modified.
        """
        file_paths = self._extract_file_paths(event.tool_name, event.tool_input)
        if not file_paths:
            return 0

        conn = self._get_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            count = 0

            for file_path in file_paths:
                # Skip files outside ELF directory
                try:
                    path_obj = Path(file_path).expanduser().resolve()
                    if not str(path_obj).startswith(str(self.elf_dir)):
                        continue
                except Exception as e:
                    logger.debug(f"Could not resolve path {file_path}: {e}")
                    continue

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
                    (str(path_obj), event.tool_name, timestamp, timestamp),
                )
                count += 1

            conn.commit()
            return count

        except Exception as e:
            print(f"Error recording pheromone trails: {e}", file=sys.stderr)
            conn.rollback()
            return 0
        finally:
            conn.close()

    def _record_workflow_trails(self, event: ToolEvent, outcome: str) -> int:
        """
        Record workflow trails with scents.
        Scents: discovery, warning, blocker, hot, cold
        """
        # Determine scent based on tool and outcome
        scent = self._determine_scent(event, outcome)
        if not scent:
            return 0

        file_paths = self._extract_file_paths(event.tool_name, event.tool_input)
        if not file_paths:
            return 0

        conn = self._get_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
            count = 0

            # Determine strength based on outcome
            strength = (
                1.0 if outcome == "success" else 0.5 if outcome == "unknown" else 0.3
            )

            for file_path in file_paths:
                try:
                    path_obj = Path(file_path).expanduser().resolve()
                    if not str(path_obj).startswith(str(self.elf_dir)):
                        continue
                except Exception as e:
                    logger.debug(f"Could not resolve path {file_path}: {e}")
                    continue

                cursor.execute(
                    """
                    INSERT INTO trails (location, location_type, scent, strength,
                                       agent_id, message, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(path_obj),
                        "file",
                        scent,
                        strength,
                        "learning_processor",
                        f"{event.tool_name} - {outcome}",
                        timestamp,
                        expires_at,
                    ),
                )
                count += 1

            conn.commit()
            return count

        except Exception as e:
            print(f"Error recording workflow trails: {e}", file=sys.stderr)
            conn.rollback()
            return 0
        finally:
            conn.close()

    def _determine_scent(self, event: ToolEvent, outcome: str) -> Optional[str]:
        """Determine trail scent based on tool and outcome."""
        tool_lower = event.tool_name.lower()

        # Hot files (frequently accessed)
        if tool_lower in ("read", "edit", "write") and outcome == "success":
            return "hot"

        # Discovery (new files or glob operations)
        if (
            tool_lower in ("glob", "grep")
            or "discover" in str(event.tool_input).lower()
        ):
            return "discovery"

        # Warning (potential issues)
        if outcome == "failure":
            return "warning"

        # Blocker (critical failures)
        if outcome == "failure" and "blocker" in str(event.tool_output).lower():
            return "blocker"

        # Cold (less frequently used)
        if tool_lower == "read" and outcome == "unknown":
            return "cold"

        return "discovery"  # Default

    def _extract_file_paths(self, tool_name: str, tool_input: Dict) -> List[str]:
        """Extract file paths from tool input."""
        paths = set()
        tool_lower = tool_name.lower()

        if isinstance(tool_input, dict):
            if tool_lower in ["read", "edit", "write"]:
                path = tool_input.get("file_path") or tool_input.get("filePath", "")
                if path:
                    paths.add(path)
            elif tool_lower == "grep":
                path = tool_input.get("path", "")
                if path:
                    paths.add(path)
            elif tool_lower == "glob":
                pattern = tool_input.get("pattern") or tool_input.get("path", "")
                if pattern:
                    paths.add(pattern)
            elif tool_lower == "bash":
                command = tool_input.get("command", "")
                # Extract paths from common commands
                patterns = [
                    r"\b(?:cat|ls|find|grep|rm|touch|mv|cp)\s+([^\s|;>]+)",
                    r"(?:^|\s)(/[^\s|;>]+)",
                ]
                for pattern in patterns:
                    for match in re.finditer(pattern, command):
                        path = match.group(1) if match.lastindex else match.group(0)
                        if path and not path.startswith("-"):
                            paths.add(path)

        return list(paths)

    # =========================================================================
    # ADVISORY VERIFICATION
    # =========================================================================

    def _advisory_verification(self, event: ToolEvent) -> List[Dict]:
        """
        Analyze edits for risky patterns.
        Returns warnings but NEVER blocks execution.
        """
        warnings = []

        tool_input = event.tool_input
        tool_output = event.tool_output

        # Get old and new content
        old_content = ""
        new_content = ""

        if event.tool_name == "Edit":
            old_content = tool_output.get(
                "old_content", tool_input.get("old_string", "")
            )
            new_content = tool_input.get("new_string", "")
        elif event.tool_name == "Write":
            old_content = tool_output.get("old_content", "")
            new_content = tool_input.get("content", "")

        # Get added lines only
        added_lines = self._get_added_lines(old_content, new_content)

        # Check for risky patterns
        for line in added_lines:
            for category, patterns in RISKY_PATTERNS.items():
                for pattern, message in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        warnings.append(
                            {
                                "category": category,
                                "message": message,
                                "line_preview": line[:80] + "..."
                                if len(line) > 80
                                else line,
                            }
                        )

        # Log warnings to database
        if warnings:
            self._log_advisory_warnings(warnings, event)

        return warnings

    def _get_added_lines(self, old: str, new: str) -> List[str]:
        """Get lines that were added (excluding pure comments)."""
        old_lines = set(old.split("\n")) if old else set()
        new_lines = new.split("\n") if new else []
        added = [line for line in new_lines if line not in old_lines]

        # Filter out pure comment lines
        comment_markers = ["#", "//", "/*", "*", '"""', "'''"]
        return [
            line
            for line in added
            if not any(line.strip().startswith(marker) for marker in comment_markers)
        ]

    def _log_advisory_warnings(self, warnings: List[Dict], event: ToolEvent):
        """Log advisory warnings to database."""
        conn = self._get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            for warning in warnings:
                cursor.execute(
                    """
                    INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context, timestamp)
                    VALUES ('advisory_warning', ?, 1, ?, ?, ?)
                """,
                    (
                        warning["category"],
                        f"tool:{event.tool_name}",
                        warning["message"],
                        datetime.now().isoformat(),
                    ),
                )

            conn.commit()
        except Exception as e:
            print(f"Error logging advisory warnings: {e}", file=sys.stderr)
            conn.rollback()
        finally:
            conn.close()

    # =========================================================================
    # LEARNING EXTRACTION
    # =========================================================================

    def _extract_and_record_learnings(self, event: ToolEvent, outcome: str) -> int:
        """Extract learnings from tool output and record them."""
        content = ""
        if isinstance(event.tool_output, dict):
            content = event.tool_output.get("content", "")
            if isinstance(content, list):
                content = "\n".join(str(item) for item in content)
        elif isinstance(event.tool_output, str):
            content = event.tool_output

        if not content:
            return 0

        # Extract implicit learnings
        learnings = self._extract_implicit_learnings(content)

        # Extract explicit [LEARNED:] markers
        explicit = self._extract_explicit_learnings(content)
        learnings.extend(explicit)

        if not learnings:
            return 0

        # Record to database
        conn = self._get_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            count = 0

            domains = self.session_state.get("domains_queried", ["general"])

            for learning in learnings:
                domain = learning.get("domain", domains[0] if domains else "general")
                rule = learning.get("rule", "")

                if not rule:
                    continue

                # Upsert heuristic
                cursor.execute(
                    """
                    INSERT INTO heuristics (domain, rule, explanation, confidence, source_type, created_at)
                    VALUES (?, ?, 'Auto-extracted from tool output', ?, 'auto', ?)
                    ON CONFLICT(domain, rule) DO UPDATE SET
                        times_validated = times_validated + 1,
                        confidence = MIN(1.0, confidence + 0.05),
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (domain, rule, learning.get("confidence", 0.5), timestamp),
                )
                count += 1

                # Store embedding in semantic daemon
                self._store_embedding(
                    text=f"{domain}: {rule}",
                    source_id=f"heuristic_{domain}_{hash(rule) % 100000}",
                    source_type="heuristic",
                    metadata={
                        "domain": domain,
                        "confidence": learning.get("confidence", 0.5),
                        "source": learning.get("source", "auto"),
                    },
                )

            conn.commit()
            return count

        except Exception as e:
            print(f"Error recording learnings: {e}", file=sys.stderr)
            conn.rollback()
            return 0
        finally:
            conn.close()

    def _extract_implicit_learnings(self, content: str) -> List[Dict]:
        """Extract implicit learnings from content."""
        learnings = []

        heuristic_indicators = [
            "should",
            "always",
            "never",
            "must",
            "don't",
            "avoid",
            "prefer",
            "recommend",
            "best practice",
            "rule of thumb",
            "lesson",
            "insight",
            "key takeaway",
            "critical to",
            "important to",
        ]

        sentences = re.split(r"[.!?]", content)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            if any(indicator in sentence.lower() for indicator in heuristic_indicators):
                clean = re.sub(r"^[^a-zA-Z]*", "", sentence).strip()
                clean = re.sub(r"\s+", " ", clean)

                if clean and len(clean) > 15:
                    learnings.append(
                        {"rule": clean, "confidence": 0.7, "source": "implicit"}
                    )

        return learnings

    def _extract_explicit_learnings(self, content: str) -> List[Dict]:
        """Extract explicit [LEARNED:] markers from content."""
        learnings = []

        pattern = r"\[LEARN(?:ED|ING)?:?([^\]]*)\]\s*([^\n]+)"
        matches = re.findall(pattern, content, re.IGNORECASE)

        for domain_hint, learning_text in matches:
            learning_text = learning_text.strip()
            if learning_text:
                learnings.append(
                    {
                        "rule": learning_text,
                        "domain": domain_hint.strip()
                        if domain_hint.strip()
                        else "general",
                        "confidence": 0.8,
                        "source": "explicit",
                    }
                )

        return learnings

    # =========================================================================
    # AUTO-FAILURE RECORDING
    # =========================================================================

    def _auto_record_failure(self, event: ToolEvent, reason: str):
        """Auto-record a failure to the database."""
        conn = self._get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            timestamp = datetime.now()

            # Get task description
            description = event.tool_input.get("description", "unknown task")

            # Get output content
            output_content = ""
            if isinstance(event.tool_output, dict):
                output_content = str(event.tool_output.get("content", ""))[:500]
            elif isinstance(event.tool_output, str):
                output_content = event.tool_output[:500]

            domains = self.session_state.get("domains_queried", ["general"])

            cursor.execute(
                """
                INSERT INTO learnings (type, filepath, title, summary, domain, severity, created_at)
                VALUES ('failure', ?, ?, ?, ?, 3, ?)
            """,
                (
                    f"auto-failures/failure_{timestamp.strftime('%Y%m%d_%H%M%S')}.md",
                    f"Auto-captured: {description[:50]}",
                    f"Reason: {reason}\n\nTask: {description}\n\nOutput: {output_content[:200]}",
                    domains[0] if domains else "general",
                    timestamp.isoformat(),
                ),
            )

            # Log the auto-capture
            cursor.execute(
                """
                INSERT INTO metrics (metric_type, metric_name, metric_value, context, timestamp)
                VALUES ('auto_failure_capture', 'capture', 1, ?, ?)
            """,
                (description[:100], timestamp.isoformat()),
            )

            conn.commit()

            # Store failure embedding
            self._store_embedding(
                text=f"Failure: {description[:200]}. {reason}",
                source_id=f"failure_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                source_type="failure",
                metadata={
                    "domain": domains[0] if domains else "general",
                    "reason": reason,
                },
            )

            print(
                f"[LEARNING] Auto-recorded failure: {description[:50]}...",
                file=sys.stderr,
            )

        except Exception as e:
            print(f"Error auto-recording failure: {e}", file=sys.stderr)
            conn.rollback()
        finally:
            conn.close()

    # =========================================================================
    # GOLDEN RULE PROMOTION
    # =========================================================================

    def _check_golden_rule_promotion(self):
        """Check if any heuristics should be promoted to golden rules."""
        conn = self._get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()

            # Find promotion candidates
            cursor.execute("""
                SELECT id, domain, rule, confidence, times_validated, times_violated
                FROM heuristics
                WHERE is_golden = 0
                  AND confidence >= 0.9
                  AND times_validated >= 10
                  AND (times_violated = 0 OR times_validated / times_violated > 10)
            """)

            candidates = cursor.fetchall()

            for candidate in candidates:
                # Promote to golden
                cursor.execute(
                    """
                    UPDATE heuristics
                    SET is_golden = 1, updated_at = ?
                    WHERE id = ?
                """,
                    (timestamp, candidate["id"]),
                )

                # Log promotion
                cursor.execute(
                    """
                    INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context, timestamp)
                    VALUES ('golden_rule_promotion', 'promotion', ?, ?, ?, ?)
                """,
                    (
                        candidate["id"],
                        f"domain:{candidate['domain']}",
                        candidate["rule"][:100],
                        timestamp,
                    ),
                )

                print(
                    f"[LEARNING] Promoted to golden rule: {candidate['rule'][:50]}...",
                    file=sys.stderr,
                )

            conn.commit()

        except Exception as e:
            print(f"Error checking golden rule promotion: {e}", file=sys.stderr)
            conn.rollback()
        finally:
            conn.close()

    # =========================================================================
    # TRAIL MANAGEMENT
    # =========================================================================

    def decay_trails(self, decay_rate: float = 0.1):
        """Decay all trail strengths (simulates pheromone evaporation)."""
        conn = self._get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # Decay workflow trails
            cursor.execute(
                """
                UPDATE trails
                SET strength = strength * (1.0 - ?)
                WHERE expires_at > datetime('now') OR expires_at IS NULL
            """,
                (decay_rate,),
            )

            # Remove very weak trails
            cursor.execute("DELETE FROM trails WHERE strength < 0.01")

            # Decay pheromone trails (using access_count as inverse of strength)
            cursor.execute(
                """
                UPDATE pheromone_trails
                SET total_weight = total_weight * (1.0 - ?)
                WHERE total_weight > 0.1
            """,
                (decay_rate,),
            )

            cursor.execute("DELETE FROM pheromone_trails WHERE total_weight < 0.1")

            conn.commit()

        except Exception as e:
            print(f"Error decaying trails: {e}", file=sys.stderr)
            conn.rollback()
        finally:
            conn.close()

    def get_hot_spots(self, limit: int = 20) -> List[Dict]:
        """Get locations with most trail activity."""
        conn = self._get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            # Combine both trail tables
            cursor.execute(
                """
                SELECT location, 'workflow' as source, COUNT(*) as trail_count,
                       SUM(strength) as total_strength,
                       GROUP_CONCAT(DISTINCT scent) as scents,
                       MAX(created_at) as last_activity
                FROM trails
                GROUP BY location
                
                UNION ALL
                
                SELECT file_path as location, 'pheromone' as source,
                       access_count as trail_count,
                       total_weight as total_strength,
                       tool_name as scents,
                       last_access as last_activity
                FROM pheromone_trails
                
                ORDER BY total_strength DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting hot spots: {e}", file=sys.stderr)
            return []
        finally:
            conn.close()


# =========================================================================
# CLI INTERFACE
# =========================================================================


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Learning Processor")
    parser.add_argument("--decay-trails", action="store_true", help="Decay all trails")
    parser.add_argument("--hot-spots", action="store_true", help="Show hot spots")
    parser.add_argument("--limit", type=int, default=20, help="Limit for hot spots")
    parser.add_argument(
        "--json-rpc",
        action="store_true",
        help="JSON stdin/stdout mode for plugin bridge",
    )

    args = parser.parse_args()

    processor = LearningProcessor()

    if args.json_rpc:
        # JSON RPC mode: read event from stdin, process, write result to stdout
        try:
            raw = sys.stdin.read()
            request = json.loads(raw)
            action = request.get("action", "")
            event_data = request.get("event", {})

            event = ToolEvent(
                tool_name=event_data.get("tool_name", "unknown"),
                tool_input=event_data.get("tool_input", {}),
                tool_output=event_data.get("tool_output", {}),
                session_id=event_data.get("session_id"),
                timestamp=event_data.get("timestamp"),
            )

            if action == "pre":
                result = processor.pre_tool_process(event)
            elif action == "post":
                result = processor.post_tool_process(event)
            else:
                result = {"error": f"Unknown action: {action}"}

            print(json.dumps(result, default=str))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        return

    if args.decay_trails:
        processor.decay_trails()
        print("Trails decayed successfully")

    elif args.hot_spots:
        spots = processor.get_hot_spots(args.limit)
        if spots:
            print(f"\nHot Spots (top {len(spots)}):")
            for spot in spots:
                print(f"  {spot['location']}")
                print(
                    f"    Trails: {spot['trail_count']}, Strength: {spot['total_strength']:.2f}"
                )
                print(f"    Source: {spot['source']}, Scents: {spot['scents']}")
        else:
            print("No trail activity found")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
