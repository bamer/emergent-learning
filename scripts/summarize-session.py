#!/usr/bin/env python3
"""
Session Summarizer - Uses the learning-extractor agent to generate summaries.

Designed to be called as a background agent or CLI tool.
Reads raw session JSONL, extracts key info, generates summary via AgentManager.

Usage:
    python summarize-session.py <session_id>
    python summarize-session.py --batch --older-than 1h
    python summarize-session.py --all-unsummarized
"""

import json
import sqlite3
import sys
import os
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import Counter

# Paths
def _resolve_base_path() -> Path:
    env_path = os.environ.get("ELF_BASE_PATH")
    if env_path:
        return Path(env_path)

    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "src" / "elf_paths.py").exists():
            sys.path.insert(0, str(parent / "src"))
            try:
                from elf_paths import get_base_path
                return get_base_path(parent)
            except ImportError:
                break

    return Path.home() / ".opencode" / "emergent-learning"


ELF_DIR = _resolve_base_path()
PROJECTS_DIR = Path.home() / ".opencode" / "projects"
DB_PATH = ELF_DIR / "memory" / "index.db"
QUEUE_FILE = ELF_DIR / "memory" / "summarization_queue.jsonl"
LEARNING_EXTRACTOR_TIMEOUT = int(os.environ.get("LEARNING_EXTRACTOR_TIMEOUT", "21600"))


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def load_queue_entries() -> List[Dict[str, Any]]:
    if not QUEUE_FILE.exists():
        return []
    entries = []
    with open(QUEUE_FILE, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

def write_queue_entries(entries: List[Dict[str, Any]]) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")

def queue_session(session_id: str, reason: str) -> None:
    entries = load_queue_entries()
    if any(entry.get("session_id") == session_id for entry in entries):
        return
    entries.append(
        {
            "session_id": session_id,
            "queued_at": datetime.now().isoformat(),
            "reason": reason,
        }
    )
    write_queue_entries(entries)

def dequeue_session(session_id: str) -> None:
    entries = load_queue_entries()
    filtered = [entry for entry in entries if entry.get("session_id") != session_id]
    if len(filtered) != len(entries):
        write_queue_entries(filtered)

def queued_session_ids() -> set:
    return {entry.get("session_id") for entry in load_queue_entries()}


def find_session_file(session_id: str) -> Optional[Path]:
    """Find the JSONL file for a session ID."""
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        jsonl_path = project_dir / f"{session_id}.jsonl"
        if jsonl_path.exists():
            return jsonl_path
    return None


def extract_session_data(file_path: Path) -> Dict[str, Any]:
    """
    Extract structured data from session JSONL without loading full content.
    Returns metadata and truncated summaries suitable for nvidia/qwen/qwen3-next-80b-a3b-instruct processing.
    """
    tool_counts = Counter()
    files_touched = set()
    message_count = 0
    user_prompts = []
    assistant_snippets = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Skip sidechains
                if data.get("isSidechain"):
                    continue

                msg_type = data.get("type")
                if msg_type == "user":
                    message_count += 1
                    # Extract user prompt (first 200 chars)
                    msg_content = data.get("message", {}).get("content", "")
                    if isinstance(msg_content, str) and msg_content.strip():
                        user_prompts.append(msg_content[:200])
                    elif isinstance(msg_content, list):
                        for item in msg_content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                user_prompts.append(item.get("text", "")[:200])
                                break

                elif msg_type == "assistant":
                    msg_content = data.get("message", {}).get("content", [])
                    if isinstance(msg_content, list):
                        for item in msg_content:
                            if isinstance(item, dict):
                                if item.get("type") == "text":
                                    text = item.get("text", "")
                                    if text and len(text) > 50:
                                        assistant_snippets.append(text[:150])
                                elif item.get("type") == "tool_use":
                                    tool_name = item.get("name", "unknown")
                                    tool_counts[tool_name] += 1

                                    # Extract file paths from tool inputs
                                    tool_input = item.get("input", {})
                                    if isinstance(tool_input, dict):
                                        for key in ["file_path", "path", "filepath"]:
                                            if key in tool_input:
                                                files_touched.add(tool_input[key])

    except Exception as e:
        return {"error": str(e)}

    return {
        "message_count": message_count,
        "tool_counts": dict(tool_counts),
        "files_touched": list(files_touched)[:50],  # Cap at 50 files
        "user_prompts": user_prompts[:10],  # First 10 prompts
        "assistant_snippets": assistant_snippets[:5],  # First 5 snippets
        "file_size": file_path.stat().st_size
    }


def generate_summary_prompt(session_data: Dict[str, Any], session_id: str) -> str:
    """Create a prompt for the learning-extractor agent."""
    tool_str = ", ".join(f"{k}: {v}" for k, v in session_data.get("tool_counts", {}).items())
    files_str = "\n".join(f"  - {f}" for f in session_data.get("files_touched", [])[:20])
    prompts_str = "\n".join(f"  - {p}" for p in session_data.get("user_prompts", [])[:5])

    return f"""Summarize this Opencode session concisely. Return JSON only.

Session ID: {session_id}
Messages: {session_data.get('message_count', 0)}
Tools used: {tool_str or 'none'}
Files touched:
{files_str or '  (none)'}

User prompts (first few):
{prompts_str or '  (none)'}

Return this exact JSON structure (no markdown, just raw JSON):
{{
  "tool_summary": "<one line: what tools were used and how many times>",
  "content_summary": "<one line: what files/code was worked on>",
  "conversation_summary": "<one line: what the user asked for and what was done>"
}}"""


def call_learning_extractor(prompt: str) -> Optional[Dict[str, Any]]:
    """Use AgentManager to ask the learning-extractor agent for JSON output."""
    try:
        open_elf_dir = Path(__file__).resolve().parents[1]
        if str(open_elf_dir) not in sys.path:
            sys.path.insert(0, str(open_elf_dir))

        from agents.agent_manager import get_agent_manager

        manager = get_agent_manager()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(manager.ask_agent, "learning-extractor", prompt)
            try:
                if LEARNING_EXTRACTOR_TIMEOUT <= 0:
                    result = future.result()
                else:
                    result = future.result(timeout=LEARNING_EXTRACTOR_TIMEOUT)
            except FutureTimeoutError:
                return None
        if not result.get("success"):
            return None
        response = result.get("response", "")
        if not response:
            return None
        return json.loads(response)
    except Exception:
        return None


def generate_fallback_summary(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a basic summary without LLM when nvidia/qwen/qwen3-next-80b-a3b-instruct fails."""
    tool_counts = session_data.get("tool_counts", {})
    files = session_data.get("files_touched", [])

    # Tool summary
    if tool_counts:
        parts = [f"{v}x {k}" for k, v in sorted(tool_counts.items(), key=lambda x: -x[1])[:5]]
        tool_summary = f"Used {', '.join(parts)}"
    else:
        tool_summary = "No tool usage recorded"

    # Content summary
    if files:
        # Group by directory
        dirs = set(str(Path(f).parent) for f in files[:10])
        content_summary = f"Worked on {len(files)} files in {len(dirs)} directories"
    else:
        content_summary = "No files modified"

    # Conversation summary from first prompt
    prompts = session_data.get("user_prompts", [])
    if prompts:
        first_prompt = prompts[0][:100]
        conversation_summary = f"Started with: {first_prompt}..."
    else:
        conversation_summary = "Session content not available"

    return {
        "tool_summary": tool_summary,
        "content_summary": content_summary,
        "conversation_summary": conversation_summary
    }


def summarize_session(
    session_id: str,
    use_llm: bool = True,
    queue_on_fail: bool = True,
) -> bool:
    """
    Summarize a single session and store in database.

    Args:
        session_id: The session UUID
        use_llm: Whether to use learning-extractor (True) or fallback summary (False)
        queue_on_fail: Queue the session if learning-extractor is unavailable

    Returns:
        True if successful, False otherwise
    """
    # Find session file
    file_path = find_session_file(session_id)
    if not file_path:
        print(f"Session file not found: {session_id}", file=sys.stderr)
        return False

    project = file_path.parent.name

    # Extract session data
    session_data = extract_session_data(file_path)
    if "error" in session_data:
        print(f"Error extracting session data: {session_data['error']}", file=sys.stderr)
        return False

    # Generate summary
    is_stale = 0
    if use_llm:
        prompt = generate_summary_prompt(session_data, session_id)
        summary = call_learning_extractor(prompt)
        if not summary:
            if queue_on_fail:
                queue_session(session_id, "learning-extractor unavailable")
                print(
                    "Learning-extractor failed, queued for later", file=sys.stderr
                )
                summary = generate_fallback_summary(session_data)
                model = "fallback"
                is_stale = 1
            else:
                return False
        else:
            model = "learning-extractor"
    else:
        summary = generate_fallback_summary(session_data)
        model = "fallback"

    # Store in database
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO session_summaries (
                session_id, project,
                tool_summary, content_summary, conversation_summary,
                files_touched, tool_counts, message_count,
                session_file_path, session_file_size, session_last_modified,
                summarized_at, summarizer_model, is_stale
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
        """, (
            session_id,
            project,
            summary.get("tool_summary", ""),
            summary.get("content_summary", ""),
            summary.get("conversation_summary", ""),
            json.dumps(session_data.get("files_touched", [])),
            json.dumps(session_data.get("tool_counts", {})),
            session_data.get("message_count", 0),
            str(file_path),
            session_data.get("file_size", 0),
            datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            model,
            is_stale,
        ))
        conn.commit()
        if model == "learning-extractor":
            dequeue_session(session_id)
        print(f"Summarized {session_id} ({model})")
        return True

    except Exception as e:
        print(f"Database error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def get_unsummarized_sessions(older_than_hours: float = 1.0) -> List[str]:
    """Get list of session IDs that need summarization."""
    unsummarized = []
    cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

    conn = get_db()
    cursor = conn.cursor()

    # Get already summarized sessions
    cursor.execute("SELECT session_id FROM session_summaries WHERE is_stale = 0")
    summarized = set(row[0] for row in cursor)
    conn.close()
    summarized.update(queued_session_ids())

    # Scan projects for unsummarized sessions
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        for jsonl_file in project_dir.glob("*.jsonl"):
            # Skip agent files
            if jsonl_file.name.startswith("agent-"):
                continue

            session_id = jsonl_file.stem

            # Skip if already summarized
            if session_id in summarized:
                continue

            # Check if file is old enough
            file_mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
            if file_mtime < cutoff_time:
                unsummarized.append(session_id)

    return unsummarized

def process_queue(limit: int = 10) -> int:
    entries = load_queue_entries()
    if not entries:
        return 0
    processed = 0
    for entry in entries[:limit]:
        session_id = entry.get("session_id")
        if not session_id:
            continue
        if summarize_session(session_id, use_llm=True, queue_on_fail=False):
            dequeue_session(session_id)
        processed += 1
    return processed


def main():
    parser = argparse.ArgumentParser(description="Summarize Claude sessions with nvidia/qwen/qwen3-next-80b-a3b-instruct")
    parser.add_argument("session_id", nargs="?", help="Session ID to summarize")
    parser.add_argument("--batch", action="store_true", help="Batch summarize multiple sessions")
    parser.add_argument("--older-than", type=str, default="1h", help="Only sessions older than (e.g., 1h, 30m)")
    parser.add_argument("--limit", type=int, default=10, help="Max sessions to process in batch")
    parser.add_argument("--no-llm", action="store_true", help="Use fallback summary (no API call)")
    parser.add_argument("--process-queue", action="store_true", help="Process queued summaries")
    parser.add_argument("--queue-limit", type=int, default=10, help="Max queued sessions to process")
    parser.add_argument("--list-unsummarized", action="store_true", help="List unsummarized sessions")

    args = parser.parse_args()

    # Parse time threshold
    older_than_str = args.older_than
    if older_than_str.endswith("h"):
        older_than_hours = float(older_than_str[:-1])
    elif older_than_str.endswith("m"):
        older_than_hours = float(older_than_str[:-1]) / 60
    else:
        older_than_hours = float(older_than_str)

    if args.process_queue:
        processed = process_queue(limit=args.queue_limit)
        print(f"Processed {processed} queued sessions")
        return 0

    if args.list_unsummarized:
        sessions = get_unsummarized_sessions(older_than_hours)
        print(f"Found {len(sessions)} unsummarized sessions (older than {args.older_than}):")
        for sid in sessions[:20]:
            print(f"  {sid}")
        if len(sessions) > 20:
            print(f"  ... and {len(sessions) - 20} more")
        return 0

    if args.session_id:
        # Summarize single session
        success = summarize_session(args.session_id, use_llm=not args.no_llm)
        return 0 if success else 1

    if args.batch:
        # Batch summarize
        sessions = get_unsummarized_sessions(older_than_hours)
        print(f"Found {len(sessions)} unsummarized sessions, processing up to {args.limit}")

        success_count = 0
        for session_id in sessions[:args.limit]:
            if summarize_session(session_id, use_llm=not args.no_llm):
                success_count += 1

        print(f"Summarized {success_count}/{min(len(sessions), args.limit)} sessions")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
