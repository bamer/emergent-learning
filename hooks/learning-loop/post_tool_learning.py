#!/usr/bin/env python3
"""
Post-Tool Learning Hook: Validate heuristics and close the learning loop.

This hook completes the learning loop by:
1. Checking task outcomes (success/failure)
2. Validating heuristics that were consulted
3. Auto-recording failures when they happen
4. Incrementing validation counts on successful tasks
5. Flagging heuristics that may have led to failures
6. Laying trails for hotspot tracking
7. Advisory verification of risky patterns (warns but never blocks)

The key insight: If we showed heuristics before a task and the task succeeded,
those heuristics were useful. If the task failed, maybe they weren't.
"""

import json
import re
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import trail helper
try:
    from trail_helper import extract_file_paths, lay_trails
except ImportError:

    def extract_file_paths(content):
        return []

    def lay_trails(*args, **kwargs):
        pass


# Paths - resolve from repo/root detection or explicit ELF_BASE_PATH
def _resolve_base_path() -> Path:
    try:
        from elf_paths import get_base_path
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from elf_paths import get_base_path
    return get_base_path()


EMERGENT_LEARNING_PATH = _resolve_base_path()
DB_PATH = EMERGENT_LEARNING_PATH / "memory" / "index.db"
STATE_FILE = (
    Path.home() / ".opencode" / "hooks" / "learning-loop" / "session-state.json"
)

# Import security patterns
try:
    from security_patterns import RISKY_PATTERNS
except ImportError:
    # Fallback to basic patterns if import fails
    RISKY_PATTERNS = {
        "code": [
            (r"eval\s*\(", "eval() detected - potential code injection risk"),
            (r"exec\s*\(", "exec() detected - potential code injection risk"),
        ],
        "file_operations": [],
    }

# Session logger for learning extraction
SESSION_LOGGER = None
try:
    sys.path.insert(0, str(EMERGENT_LEARNING_PATH / "data" / "sessions"))
    from logger import SessionLogger

    SESSION_LOGGER = SessionLogger()
except ImportError:
    pass  # Will be handled gracefully in logging functions


class AdvisoryVerifier:
    """
    Post-action verification that warns but NEVER blocks.
    Philosophy: Advisory only, human decides.
    """

    def __init__(self):
        self.warnings = []

    def analyze_edit(self, file_path: str, old_content: str, new_content: str) -> Dict:
        """Analyze a file edit for risky patterns."""
        warnings = []

        # Only check what was ADDED (not existing code)
        added_lines = self._get_added_lines(old_content, new_content)

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

        return {
            "has_warnings": len(warnings) > 0,
            "warnings": warnings,
            "recommendation": self._get_recommendation(warnings),
        }

    def _is_comment_line(self, line: str) -> bool:
        """Check if a line is entirely a comment (not code with comment).

        Returns True for:
        - Python comments: starts with #
        - JS/C/Go single-line comments: starts with //
        - C-style multi-line comment start: starts with /*
        - Multi-line comment bodies: starts with *
        - Docstrings: starts with triple quotes

        Returns False for:
        - Mixed lines like: x = eval(y)  # comment
        - Code before comment: foo()  // comment
        """
        stripped = line.strip()
        if not stripped:
            return False

        # Check for pure comment lines (line starts with comment marker)
        triple_quote = chr(34) * 3
        single_triple = chr(39) * 3
        comment_markers = ["#", "//", "/*", "*", triple_quote, single_triple]
        return any(stripped.startswith(marker) for marker in comment_markers)

    def _get_added_lines(self, old: str, new: str) -> List[str]:
        """Get lines that were added (simple diff), excluding pure comment lines."""
        old_lines = set(old.split("\n")) if old else set()
        new_lines = new.split("\n") if new else []
        added_lines = [line for line in new_lines if line not in old_lines]

        # Filter out pure comment lines to avoid false positives
        return [line for line in added_lines if not self._is_comment_line(line)]

    def _get_recommendation(self, warnings: List[Dict]) -> str:
        if not warnings:
            return "No concerns detected."
        if len(warnings) >= 3:
            return "[!] Multiple concerns - consider CEO escalation"
        return "[!] Review flagged items before proceeding"


def get_hook_input() -> dict:
    """Read hook input from stdin or command-line argument."""
    # Try stdin first
    try:
        if not sys.stdin.isatty():
            return json.load(sys.stdin)
    except (json.JSONDecodeError, IOError, ValueError):
        pass

    # Fallback: check command-line arguments (for plugin compatibility)
    if len(sys.argv) > 1:
        try:
            return json.loads(sys.argv[1])
        except (json.JSONDecodeError, ValueError):
            pass

    return {}


def output_result(result: dict):
    """Output hook result to stdout."""
    print(json.dumps(result))


def load_session_state() -> dict:
    """Load current session state with validation and TTL-based recovery.

    Uses TTL-based session detection (4 hours) instead of date-based.
    This handles cross-midnight work sessions more accurately.
    """
    # Session TTL: 4 hours in seconds
    SESSION_TTL = 4 * 60 * 60  # 14400 seconds
    current_time = datetime.now()

    default_state = {
        "session_start": current_time.isoformat(),
        "heuristics_consulted": [],
        "domains_queried": [],
        "task_context": None,
        "last_updated": current_time.isoformat(),
        "version": 1,  # Schema version for future migrations
    }

    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())

            # Validate required fields
            required_fields = [
                "session_start",
                "heuristics_consulted",
                "domains_queried",
            ]
            if not all(field in state for field in required_fields):
                sys.stderr.write(
                    "[SESSION] Invalid state file - missing required fields, creating new session\n"
                )
                return default_state

            # Check if state has expired based on TTL
            last_updated = state.get("last_updated", state.get("session_start", ""))
            if last_updated:
                try:
                    last_time = datetime.fromisoformat(last_updated)
                    time_since_last = (current_time - last_time).total_seconds()

                    if time_since_last > SESSION_TTL:
                        sys.stderr.write(
                            f"[SESSION] Session expired ({time_since_last / 3600:.1f}h > {SESSION_TTL / 3600}h TTL), creating new session\n"
                        )
                        return default_state
                except (ValueError, KeyError):
                    sys.stderr.write(
                        "[SESSION] Invalid timestamp in state, creating new session\n"
                    )
                    return default_state

            # Ensure arrays are initialized
            if not isinstance(state.get("heuristics_consulted"), list):
                state["heuristics_consulted"] = []
            if not isinstance(state.get("domains_queried"), list):
                state["domains_queried"] = []

            # Update last_updated timestamp
            state["last_updated"] = current_time.isoformat()

            return state

        except (json.JSONDecodeError, IOError, ValueError) as e:
            sys.stderr.write(
                f"[SESSION] Failed to load state file: {e}, creating new session\n"
            )
            return default_state

    return default_state


def save_session_state(state: dict):
    """Save session state with timestamp and atomic write."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Update timestamp before saving
    state["last_updated"] = datetime.now().isoformat()

    # Atomic write: write to temp file then rename
    temp_file = STATE_FILE.with_suffix(".tmp")
    try:
        temp_file.write_text(json.dumps(state, indent=2))
        temp_file.replace(STATE_FILE)  # Atomic rename
    except Exception as e:
        sys.stderr.write(f"[SESSION] Failed to save state: {e}\n")
        # Fallback: try direct write
        try:
            STATE_FILE.write_text(json.dumps(state, indent=2))
        except Exception as e2:
            sys.stderr.write(f"[SESSION] Fallback save also failed: {e2}\n")


def get_db_connection():
    """Get SQLite connection."""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def auto_detect_domains(tool_output: dict, task_description: str) -> List[str]:
    """Auto-detect domains from tool output and task description when no domains were consulted."""
    content = ""
    if isinstance(tool_output, dict):
        content = str(tool_output.get("content", ""))
    elif isinstance(tool_output, str):
        content = tool_output

    # Combine with task description for better detection
    full_text = (content + " " + task_description).lower()

    # Domain detection patterns
    domain_patterns = {
        "security": [
            "security",
            "vulnerability",
            "attack",
            "encrypt",
            "password",
            "auth",
            "permission",
            "validate",
            "sanitize",
            "injection",
            "xss",
            "csrf",
        ],
        "performance": [
            "performance",
            "speed",
            "slow",
            "fast",
            "cache",
            "optimize",
            "memory",
            "cpu",
            "database",
            "query",
            "async",
            "batch",
        ],
        "testing": [
            "test",
            "testing",
            "pytest",
            "unittest",
            "mock",
            "assert",
            "coverage",
            "validation",
        ],
        "api": [
            "api",
            "endpoint",
            "request",
            "response",
            "http",
            "rest",
            "json",
            "payload",
        ],
        "database": [
            "database",
            "sql",
            "sqlite",
            "postgres",
            "mysql",
            "table",
            "query",
            "migration",
        ],
        "frontend": [
            "frontend",
            "ui",
            "html",
            "css",
            "javascript",
            "react",
            "component",
            "dom",
        ],
        "deployment": [
            "deploy",
            "docker",
            "kubernetes",
            "k8s",
            "ci/cd",
            "pipeline",
            "build",
            "release",
        ],
        "general": [
            "code",
            "function",
            "class",
            "module",
            "import",
            "error",
            "exception",
            "fix",
            "bug",
        ],
    }

    detected_domains = []
    for domain, keywords in domain_patterns.items():
        if any(keyword in full_text for keyword in keywords):
            detected_domains.append(domain)

    # Return at least "general" if nothing detected
    return detected_domains if detected_domains else ["general"]


def determine_outcome(tool_output: dict) -> Tuple[str, str]:
    """Determine if the task succeeded or failed.

    Returns: (outcome, reason)
    - outcome: 'success', 'failure', 'unknown'
    - reason: description of why
    """
    if not tool_output:
        return "unknown", "No output to analyze"

    # Get content
    content = ""
    if isinstance(tool_output, dict):
        content = tool_output.get("content", "") or ""
        if isinstance(content, list):
            content = "\n".join(
                item.get("text", "") for item in content if isinstance(item, dict)
            )
    elif isinstance(tool_output, str):
        content = tool_output

    if not content:
        return "unknown", "Empty output"

    content_lower = content.lower()

    # Strong failure indicators (case-insensitive with word boundaries)
    failure_patterns = [
        (r"(?i)\berror\b[:\s]", "Error detected"),
        (r"(?i)\bexception\b[:\s]", "Exception raised"),
        (r"(?i)\bfailed\b[:\s]", "Operation failed"),
        (r"(?i)\bcould not\b", "Could not complete"),
        (r"(?i)\bunable to\b", "Unable to complete"),
        (r"\[BLOCKER\]", "Blocker encountered"),
        (r"(?i)\btraceback\b", "Exception traceback"),
        (r"(?i)\bpermission denied\b", "Permission denied"),
        (r"(?i)\btimed?\s+out\b", "Timeout occurred"),  # Match "timeout" or "timed out"
        (r"(?i)^.*\bnot found\s*$", "Resource not found"),  # Only at end of line
    ]

    # Patterns to exclude false positives
    # These indicate discussion of errors/failures, not actual errors
    false_positive_patterns = [
        r"(?i)was not found to be",
        r"(?i)\berror handling\b",
        r"(?i)\bno errors?\b",
        r"(?i)\bwithout errors?\b",
        r"(?i)\berror.?free\b",
        r"(?i)\b(fixed|resolved|corrected|repaired)\b.*\b(error|failure|bug|issue|exception)",  # "fixed the error"
        r"(?i)\b(error|failure|bug|issue|exception)\b.*(fixed|resolved|corrected|repaired)",  # "error was fixed"
        r"(?i)\binvestigated.*\b(failed|error|failure)",  # "investigated the failure"
        r"(?i)\banalyzed.*\b(error|failure|failed)",  # "analyzed the error"
        r"(?i)\bhandl(e|es|ed|ing).*\b(error|failure|exception)",  # "handles errors"
        r"(?i)\b(error|failure|exception)\s+handl",  # "exception handling"
        r"(?i)resolved.*\b(error|failure|exception)",  # "resolved the exception"
    ]

    for pattern, reason in failure_patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            # Verify this isn't a false positive by checking surrounding context
            match_start = max(0, match.start() - 30)
            match_end = min(len(content), match.end() + 30)
            context = content[match_start:match_end]

            # Skip if this match is part of a false positive pattern
            is_false_positive = any(
                re.search(fp, context) for fp in false_positive_patterns
            )
            if not is_false_positive:
                return "failure", reason

    # Strong success indicators - explicit completion phrases
    explicit_success_patterns = [
        (r"\bsuccessfully\s+\w+", "Successfully completed action"),
        (r"\btask\s+complete", "Task completed"),
        (r"\b(work|task) is (done|finished|complete)", "Work is done"),
        (r"\ball tests pass", "Tests passed"),
        (r"\[success\]", "Success marker found"),
        (r"## FINDINGS", "Findings reported"),
        (r"\bcompleted\s+successfully", "Completed successfully"),
    ]

    for pattern, reason in explicit_success_patterns:
        if re.search(pattern, content_lower):
            return "success", reason

    # Action verbs that indicate work was done (past tense)
    # These are strong indicators that a task was completed
    action_verb_patterns = [
        (r"\b(created|generated|built|made)\b\s+\w+", "Created something"),
        (r"\b(fixed|resolved|corrected|repaired)\b\s+\w+", "Fixed something"),
        (r"\b(updated|modified|changed|revised)\b\s+\w+", "Updated something"),
        (r"\b(implemented|added|introduced)\b\s+\w+", "Implemented something"),
        (r"\b(analyzed|examined|reviewed|investigated)\b\s+\w+", "Analyzed something"),
        (r"\b(identified|found|discovered|located)\b\s+\w+", "Identified something"),
        (r"\b(removed|deleted|cleaned)\b\s+\w+", "Removed something"),
        (r"\b(refactored|reorganized|restructured)\b\s+\w+", "Refactored something"),
        (r"\b(tested|validated|verified)\b\s+\w+", "Tested something"),
        (r"\b(deployed|released|published)\b\s+\w+", "Deployed something"),
    ]

    for pattern, reason in action_verb_patterns:
        if re.search(pattern, content_lower):
            return "success", reason

    # Reporting patterns - agent is presenting findings/results
    reporting_patterns = [
        (
            r"\bhere (is|are) (the |my )?(\w+\s+)?(findings|results|analysis|summary)",
            "Presented findings",
        ),
        (r"\bi (have |\'ve )?(completed|finished|done)", "Agent reported completion"),
        (
            r"\bthe (task|work|analysis|fix|implementation) is (complete|done|finished)",
            "Work is complete",
        ),
        (
            r"^\s*(finished|completed|done)\s+\w+",
            "Started with completion verb",
        ),  # "Finished the X", "Completed the Y"
        (r"\b(summary|conclusion):", "Provided summary"),
        (r"\brecommend(ations|s)?:", "Provided recommendations"),
    ]

    for pattern, reason in reporting_patterns:
        if re.search(pattern, content_lower):
            return "success", reason

    # If we got substantial output without errors, probably success
    # Lowered threshold from 100 to 50 chars since short completions are valid
    if len(content) > 50:
        return "success", "Substantial output without errors"

    return "unknown", "Could not determine outcome"


def validate_heuristics(heuristic_ids: List[int], outcome: str):
    """Update heuristic validation counts based on outcome.

    FAIL-STOP: If validation fails, the error is propagated to prevent silent failures
    in the reinforcement learning loop.
    """
    if not heuristic_ids:
        return

    conn = get_db_connection()
    if not conn:
        error_msg = "[VALIDATION FAILED] Database connection unavailable - cannot validate heuristics"
        sys.stderr.write(f"{error_msg}\n")
        raise RuntimeError(error_msg)

    try:
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        placeholders = ",".join("?" * len(heuristic_ids))

        if outcome == "success":
            # Batch UPDATE: Increment times_validated for all consulted heuristics
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

            # Batch INSERT: Log all validations in single operation
            validation_records = [
                (
                    "heuristic_validated",
                    "validation",
                    1,
                    f"heuristic_id:{hid}",
                    "success",
                    timestamp,
                )
                for hid in heuristic_ids
            ]
            cursor.executemany(
                """
                INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                validation_records,
            )

            sys.stderr.write(
                f"[VALIDATION] Validated {len(heuristic_ids)} heuristics (success)\n"
            )

        elif outcome == "failure":
            # Batch UPDATE: Increment times_violated
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

            # Batch INSERT: Log all violations
            violation_records = [
                (
                    "heuristic_violated",
                    "violation",
                    1,
                    f"heuristic_id:{hid}",
                    "failure",
                    timestamp,
                )
                for hid in heuristic_ids
            ]
            cursor.executemany(
                """
                INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                violation_records,
            )

            sys.stderr.write(
                f"[VALIDATION] Recorded {len(heuristic_ids)} heuristic violations\n"
            )

        elif outcome == "unknown":
            # Batch UPDATE: Record unknown outcomes
            cursor.execute(
                f"""
                UPDATE heuristics
                SET times_consulted = COALESCE(times_consulted, 0) + 1,
                    times_unknown = COALESCE(times_unknown, 0) + 1,
                    confidence = MAX(0.0, confidence - 0.005),
                    updated_at = ?
                WHERE id IN ({placeholders})
            """,
                (timestamp, *heuristic_ids),
            )

            # Batch INSERT: Log consultations
            consultation_records = [
                (
                    "heuristic_consulted",
                    "unknown_outcome",
                    1,
                    f"heuristic_id:{hid}",
                    "unknown",
                    timestamp,
                )
                for hid in heuristic_ids
            ]
            cursor.executemany(
                """
                INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                consultation_records,
            )

        conn.commit()
        sys.stderr.write(
            f"[VALIDATION] Batch validation completed for {len(heuristic_ids)} heuristics (outcome: {outcome})\n"
        )

    except Exception as e:
        conn.rollback()
        error_msg = f"[VALIDATION FAILED] Heuristic validation error: {e}"
        sys.stderr.write(f"{error_msg}\n")
        import traceback

        sys.stderr.write(f"[VALIDATION FAILED] Traceback: {traceback.format_exc()}\n")
        # FAIL-STOP: Re-raise the exception to prevent silent failures
        raise RuntimeError(error_msg) from e
    finally:
        conn.close()


def check_golden_rule_promotion(conn):
    """Check if any heuristics should be promoted to golden rules."""
    try:
        cursor = conn.cursor()

        # Find heuristics with high confidence and many validations
        cursor.execute("""
            SELECT id, domain, rule, confidence, times_validated, times_violated
            FROM heuristics
            WHERE is_golden = 0
              AND confidence >= 0.9
              AND times_validated >= 10
              AND (times_violated = 0 OR times_validated / times_violated > 10)
        """)

        candidates = cursor.fetchall()

        for c in candidates:
            # Promote to golden
            cursor.execute(
                """
                UPDATE heuristics
                SET is_golden = 1, updated_at = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), c["id"]),
            )

            # Log the promotion
            cursor.execute(
                """
                INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context)
                VALUES ('golden_rule_promotion', 'promotion', ?, ?, ?)
            """,
                (c["id"], f"domain:{c['domain']}", c["rule"][:100]),
            )

            sys.stderr.write(f"PROMOTED TO GOLDEN RULE: {c['rule'][:50]}...\n")

        conn.commit()

    except Exception as e:
        sys.stderr.write(f"Warning: Failed to check golden rule promotion: {e}\n")


def auto_record_failure(
    tool_input: dict, tool_output: dict, outcome_reason: str, domains: List[str]
):
    """Auto-record a failure using the record-failure.sh script."""
    try:
        import subprocess
        import os

        # Extract details
        description = tool_input.get("description", "unknown task")

        # Get output content
        output_content = ""
        if isinstance(tool_output, dict):
            output_content = str(tool_output.get("content", ""))[:500]
        elif isinstance(tool_output, str):
            output_content = tool_output[:500]

        # Set environment variables for the script
        env = os.environ.copy()
        env["FAILURE_TITLE"] = f"Auto-captured: {description[:50]}"
        env["FAILURE_DOMAIN"] = domains[0] if domains else "general"
        env["FAILURE_SUMMARY"] = (
            f"Reason: {outcome_reason}\n\nTask: {description}\n\nOutput snippet: {output_content[:200]}"
        )
        env["FAILURE_SEVERITY"] = "3"  # Medium severity

        # Find and execute the record-failure.sh script
        script_paths = [
            str(EMERGENT_LEARNING_PATH / "scripts" / "record-failure.sh"),
            str(EMERGENT_LEARNING_PATH / "tools" / "scripts" / "record-failure.sh"),
        ]

        script_found = False
        for script_path in script_paths:
            if os.path.exists(script_path):
                try:
                    # Run the script with environment variables
                    result = subprocess.run(
                        ["bash", script_path],
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        sys.stderr.write(
                            f"AUTO-RECORDED FAILURE: {env['FAILURE_TITLE']}\n"
                        )
                        script_found = True
                        break
                    else:
                        sys.stderr.write(f"record-failure.sh failed: {result.stderr}\n")
                except Exception as e:
                    sys.stderr.write(f"Error running record-failure.sh: {e}\n")
                break

        # Fallback to database recording if script not found or failed
        if not script_found:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = f"auto-failures/failure_{timestamp}.md"
                    title = env["FAILURE_TITLE"]
                    summary = env["FAILURE_SUMMARY"]
                    domain = env["FAILURE_DOMAIN"]

                    cursor.execute(
                        """
                        INSERT INTO learnings (type, filepath, title, summary, domain, severity, created_at)
                        VALUES ('failure', ?, ?, ?, ?, 3, ?)
                    """,
                        (filepath, title, summary, domain, datetime.now().isoformat()),
                    )

                    # Log the auto-capture
                    cursor.execute(
                        """
                        INSERT INTO metrics (metric_type, metric_name, metric_value, context)
                        VALUES ('auto_failure_capture', 'capture', 1, ?)
                    """,
                        (title,),
                    )

                    conn.commit()
                    sys.stderr.write(f"FALLBACK AUTO-RECORDED FAILURE: {title}\n")
                except Exception as e:
                    sys.stderr.write(
                        f"Warning: Failed to fallback auto-record failure: {e}\n"
                    )
                finally:
                    conn.close()

    except Exception as e:
        sys.stderr.write(f"Warning: Failed to auto-record failure: {e}\n")


def log_advisory_warning(file_path: str, advisory_result: Dict):
    """Log advisory warnings to the building (non-blocking)."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Log each warning
        for warning in advisory_result.get("warnings", []):
            cursor.execute(
                """
                INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context)
                VALUES ('advisory_warning', ?, 1, ?, ?)
            """,
                (warning["category"], f"file:{file_path}", warning["message"]),
            )

            # Write to stderr for visibility
            sys.stderr.write(
                f"[ADVISORY] {warning['category']}: {warning['message']}\n"
                f"           Line: {warning['line_preview']}\n"
            )

        # If multiple warnings, log the escalation recommendation
        if len(advisory_result.get("warnings", [])) >= 3:
            sys.stderr.write(
                f"\n[ADVISORY] {advisory_result['recommendation']}\n"
                f"           File: {file_path}\n\n"
            )

        conn.commit()

    except Exception as e:
        sys.stderr.write(f"Warning: Failed to log advisory warning: {e}\n")
    finally:
        conn.close()


def extract_implicit_learnings(
    outcome: str, domains: List[str], task_description: str, output_content: str
) -> List[Dict]:
    """Extract learnings from outcomes even without explicit [LEARNED:] markers."""
    learnings = []
    content = (output_content + " " + task_description).lower()

    # Common patterns that indicate learnings
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
        "never forget",
        "remember to",
    ]

    # Extract sentences containing heuristic indicators
    sentences = re.split(r"[.!?]", output_content)
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 10:
            continue

        # Check if sentence contains learning indicators
        if any(indicator in sentence.lower() for indicator in heuristic_indicators):
            # Clean up the sentence
            clean_sentence = re.sub(r"^[^a-zA-Z]*", "", sentence).strip()
            clean_sentence = re.sub(r"\s+", " ", clean_sentence)

            if clean_sentence:
                learnings.append(
                    {
                        "type": "heuristic",
                        "domain": domains[0] if domains else "general",
                        "rule": clean_sentence,
                        "confidence": 0.7,
                        "source": "auto-extracted",
                    }
                )

    return learnings


def extract_and_record_learnings(
    tool_output: dict, domains: List[str], task_description: str = ""
):
    """Extract learnings from successful task output and record them."""
    # Debug
    with open("/tmp/elf_hook_debug.log", "a") as f:
        f.write(f"    -> extract_and_record_learnings called\n")

    conn = get_db_connection()
    if not conn:
        with open("/tmp/elf_hook_debug.log", "a") as f:
            f.write(f"    -> No DB connection\n")
        return

    # Get content
    output_content = ""
    if isinstance(tool_output, dict):
        output_content = tool_output.get("content", "")
        if isinstance(output_content, list):
            output_content = "\n".join(
                item.get("text", "")
                for item in output_content
                if isinstance(item, dict)
            )
    elif isinstance(tool_output, str):
        output_content = tool_output

    # Extract implicit learnings (auto-detection without markers)
    learnings = extract_implicit_learnings(
        "success", domains, task_description, output_content
    )

    # Debug
    with open("/tmp/elf_hook_debug.log", "a") as f:
        f.write(f"    -> Extracted {len(learnings)} learnings\n")
        for l in learnings:
            f.write(f"       - {l['rule'][:50]}...\n")

    if not learnings:
        with open("/tmp/elf_hook_debug.log", "a") as f:
            f.write(f"    -> No learnings found, returning\n")
        return

    try:
        cursor = conn.cursor()
        recorded_count = 0

        # Process implicit learnings (auto-extracted)
        for learning_data in learnings:
            domain = learning_data["domain"]
            rule = learning_data["rule"]

            # Record as heuristic with UPSERT
            cursor.execute(
                """
                INSERT INTO heuristics (domain, rule, explanation, confidence, source_type, created_at)
                VALUES (?, ?, 'Auto-extracted from task output', ?, 'auto', ?)
                ON CONFLICT(domain, rule) DO UPDATE SET
                    times_validated = times_validated + 1,
                    confidence = MIN(1.0, confidence + 0.05),
                    updated_at = CURRENT_TIMESTAMP
            """,
                (domain, rule, learning_data["confidence"], datetime.now().isoformat()),
            )
            recorded_count += 1
            sys.stderr.write(f"AUTO-EXTRACTED HEURISTIC: {rule[:50]}...\n")

        # Also check for explicit [LEARNED:] markers as backup
        learning_pattern = r"\[LEARN(?:ED|ING)?:?([^\]]*)\]\s*([^\n]+)"
        matches = re.findall(learning_pattern, output_content, re.IGNORECASE)

        for domain_hint, learning in matches:
            domain = (
                domain_hint.strip()
                if domain_hint.strip()
                else (domains[0] if domains else "general")
            )

            # Check if this might be a heuristic
            is_heuristic = any(
                word in learning.lower()
                for word in [
                    "always",
                    "never",
                    "should",
                    "must",
                    "don't",
                    "avoid",
                    "prefer",
                ]
            )

            if is_heuristic:
                cursor.execute(
                    """
                    INSERT INTO heuristics (domain, rule, explanation, confidence, source_type, created_at)
                    VALUES (?, ?, 'Auto-extracted from task output', 0.5, 'auto', ?)
                    ON CONFLICT(domain, rule) DO UPDATE SET
                        times_validated = times_validated + 1,
                        confidence = MIN(1.0, confidence + 0.05),
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (domain, learning.strip(), datetime.now().isoformat()),
                )
                recorded_count += 1
                sys.stderr.write(f"MARKER-EXTRACTED HEURISTIC: {learning[:50]}...\n")

        conn.commit()

        if recorded_count > 0:
            sys.stderr.write(
                f"[LEARNING] Recorded {recorded_count} learnings from task output\n"
            )

    except Exception as e:
        sys.stderr.write(f"[LEARNING ERROR] Failed to record learnings: {e}\n")
        import traceback

        sys.stderr.write(f"[LEARNING ERROR] Traceback: {traceback.format_exc()}\n")
    finally:
        conn.close()


def main():
    # Debug log
    import sys
    from datetime import datetime
    from pathlib import Path

    LOG_DIR = Path.home() / ".opencode" / "emergent-learning" / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log", "a") as f:
        f.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DEBUG] post_tool_learning START\n"
        )
    """Main hook logic."""
    hook_input = get_hook_input()

    # Debug: Log hook invocation to file (flush immediately)
    debug_file = "/tmp/elf_hook_debug.log"
    with open(debug_file, "a") as f:
        f.write(
            f"[{datetime.now().isoformat()}] Hook called with: {json.dumps(hook_input)[:200]}...\n"
        )
        f.flush()

    tool_name = hook_input.get("tool_name", hook_input.get("tool"))
    tool_input = hook_input.get("tool_input", hook_input.get("input", {}))
    tool_output = hook_input.get("tool_output", hook_input.get("output", {}))

    if not tool_name:
        with open(debug_file, "a") as f:
            f.write(f"  -> No tool_name, returning early\n")
        output_result({})
        return

    # Log session for learning extraction (early logging for all tools)
    if SESSION_LOGGER:
        try:
            # Determine preliminary outcome for logging
            outcome, reason = determine_outcome(tool_output)
            SESSION_LOGGER.log_tool_use(
                tool=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                outcome=outcome,
            )
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to log session: {e}\n")

    # Advisory verification for Edit/Write tools
    if tool_name in ("Edit", "Write"):
        verifier = AdvisoryVerifier()
        file_path = tool_input.get("file_path", "")

        # Get old and new content for comparison
        old_content = ""
        new_content = ""

        if tool_name == "Edit":
            # For Edit: old_string is the old content, new_string is the new content
            # But we need full file context - check if tool_output contains it
            old_content = tool_output.get(
                "old_content", tool_input.get("old_string", "")
            )
            new_content = tool_input.get("new_string", "")
        elif tool_name == "Write":
            # For Write: content is the new content, old content might be in output
            old_content = tool_output.get("old_content", "")
            new_content = tool_input.get("content", "")

        # Run analysis
        result = verifier.analyze_edit(
            file_path=file_path, old_content=old_content, new_content=new_content
        )

        # Log warnings if any (non-blocking)
        if result["has_warnings"]:
            log_advisory_warning(file_path, result)

        # Always approve, just attach advisory info
        output_result(
            {
                "decision": "approve",
                "advisory": result if result["has_warnings"] else None,
            }
        )
        return

    # Track file operations (Read/Edit/Write/Glob/Grep) for hotspot trails
    file_operation_tools = {"Read", "Edit", "Write", "Glob", "Grep"}
    if tool_name in file_operation_tools:
        try:
            file_path = tool_input.get("file_path") or tool_input.get("path", "")
            if file_path:
                # Normalize path
                file_path = file_path.replace("\\", "/")
                # Extract relative path from common markers
                markers = [
                    EMERGENT_LEARNING_PATH.as_posix().rstrip("/") + "/",
                    "emergent-learning/",
                    "dashboard-app/",
                ]
                for marker in markers:
                    if marker in file_path:
                        file_path = file_path[file_path.index(marker) :]
                        break

                # Determine scent based on operation type
                scent = "read" if tool_name in ("Read", "Glob", "Grep") else "write"
                strength = (
                    0.5 if tool_name == "Read" else 0.9
                )  # Writes are more significant

                # Record trail
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        # Use correct column name 'location' (not 'run_id' which doesn't exist in schema)
                        cursor.execute(
                            "INSERT INTO trails (location, location_type, scent, strength, agent_id, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                file_path,
                                "file",
                                scent,
                                strength,
                                "claude-main",
                                f"{tool_name} operation",
                                datetime.now().isoformat(),
                            ),
                        )
                        conn.commit()
                        sys.stderr.write(
                            f"[TRAIL] Recorded {tool_name} on {file_path}\n"
                        )
                    except Exception as e:
                        sys.stderr.write(f"[TRAIL_ERROR] Database error: {e}\n")
                        import traceback

                        sys.stderr.write(
                            f"[TRAIL_ERROR] Traceback: {traceback.format_exc()}\n"
                        )
                    finally:
                        conn.close()
        except Exception as e:
            sys.stderr.write(
                f"[TRAIL_ERROR] Failed to record file operation trail: {e}\n"
            )

        # NOTE: Don't return early here - continue to learning extraction below
        # so that Edit/Write/Read operations can also generate learnings

    # Load session state
    state = load_session_state()
    heuristics_consulted = state.get("heuristics_consulted", [])
    domains_queried = state.get("domains_queried", [])

    # Determine outcome
    outcome, reason = determine_outcome(tool_output)

    # Log session for learning extraction
    if SESSION_LOGGER:
        try:
            SESSION_LOGGER.log_tool_use(
                tool=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                outcome=outcome,
            )
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to log session: {e}\n")

    # Record to conductor for dashboard visibility
    try:
        sys.path.insert(0, str(EMERGENT_LEARNING_PATH / "conductor"))
        from conductor import Conductor, Node

        conductor = Conductor(
            base_path=str(EMERGENT_LEARNING_PATH),
            project_root=str(EMERGENT_LEARNING_PATH),
        )

        # Create a workflow run for this task
        description = tool_input.get("description", "Unknown task")
        run_id = conductor.start_run(
            workflow_name=f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            input_data={
                "description": description,
                "prompt": tool_input.get("prompt", "")[:500],  # Truncate
            },
        )

        # Record the execution
        if run_id:
            # Create a node record
            node = Node(
                id=f"task-{datetime.now().timestamp()}",
                name=description[:100],
                node_type="single",
                prompt_template=tool_input.get("prompt", "")[:500],
                config={"model": "claude"},
            )
            exec_id = conductor.record_node_start(
                run_id, node, tool_input.get("prompt", "")
            )

            # Record completion or failure
            # Note: 'unknown' is treated as success (optimistic) because:
            # 1. Task tool with run_in_background=true has empty initial output
            # 2. Most tasks complete successfully even without verbose output
            # 3. Learning systems should assume success unless failure is explicit
            if outcome == "failure":
                conductor.record_node_failure(
                    exec_id=exec_id, error_message=reason, error_type="task_failure"
                )
                conductor.update_run_status(run_id, "failed", error_message=reason)
            else:  # 'success' OR 'unknown'
                conductor.record_node_completion(
                    exec_id=exec_id,
                    result_text=str(
                        tool_output.get("content", "")
                        if isinstance(tool_output, dict)
                        else tool_output
                    )[:1000],
                    result_dict={"outcome": outcome, "reason": reason},
                )
                conductor.update_run_status(
                    run_id, "completed", output={"outcome": outcome, "reason": reason}
                )
    except Exception as e:
        # Don't fail the hook if conductor fails
        sys.stderr.write(f"Conductor integration error (non-fatal): {e}\n")

    # Lay trails for files mentioned in output (for Task tool)
    if tool_name == "Task":
        try:
            output_content = ""

            if isinstance(tool_output, dict):
                output_content = str(tool_output.get("content", ""))
            elif isinstance(tool_output, str):
                output_content = tool_output

            file_paths = extract_file_paths(output_content)

            if file_paths:
                description = tool_input.get("description", "")
                agent_type = tool_input.get("subagent_type", "unknown")
                lay_trails(
                    file_paths, outcome, agent_id=agent_type, description=description
                )
                sys.stderr.write(f"[TRAIL] Task tool laid {len(file_paths)} trails\n")
        except Exception as e:
            sys.stderr.write(f"[TRAIL_ERROR] Failed to lay trails for Task: {e}\n")

    # Validate heuristics based on outcome
    if heuristics_consulted:
        validate_heuristics(heuristics_consulted, outcome)

    # Check for golden rule promotions
    conn = get_db_connection()
    tool_output = hook_input.get("tool_output", hook_input.get("output", {}))
    if conn:
        check_golden_rule_promotion(conn)
        conn.close()

    # Auto-record failure if task failed
    if outcome == "failure":
        auto_record_failure(tool_input, tool_output, reason, domains_queried)

    # Extract any explicit learnings from output
    # Extract for both 'success' and 'unknown' outcomes (not failure)
    # This ensures Read/Edit/Write tools can also generate learnings
    if outcome in ("success", "unknown"):
        task_description = tool_input.get("description", "")

        # Auto-detect domains if none were consulted (e.g., for simple tools like Read/Edit)
        if not domains_queried:
            domains_queried = auto_detect_domains(tool_output, task_description)

        # Debug
        with open("/tmp/elf_hook_debug.log", "a") as f:
            f.write(
                f"  -> Extracting learnings for domains: {domains_queried} (outcome={outcome})\n"
            )

        extract_and_record_learnings(tool_output, domains_queried, task_description)

        # Debug
        with open("/tmp/elf_hook_debug.log", "a") as f:
            f.write(f"  -> Done extracting\n")

    # Clear consulted heuristics for next task
    state["heuristics_consulted"] = []
    save_session_state(state)

    # Log outcome
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context)
                VALUES ('task_outcome', ?, 1, ?, ?)
            """,
                (outcome, f"reason:{reason[:50]}", datetime.now().isoformat()),
            )
            conn.commit()
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to log task outcome: {e}\n")
        finally:
            conn.close()

    # Output (no modification to tool output)
    output_result({})


if __name__ == "__main__":
    main()
