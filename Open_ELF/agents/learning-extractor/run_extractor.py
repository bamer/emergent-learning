#!/usr/bin/env python3
"""
Learning Extractor - Processes session JSONL logs to extract learnings.

Reads session logs, extracts:
- [LEARNED:domain] markers from responses
- Failure patterns (repeated failures with similar input)
- Success patterns (high-confidence outcomes)

Outputs proposals to proposals/pending/ as markdown files.

Usage:
    python run_extractor.py [log_file1.jsonl] [log_file2.jsonl] ...
    python run_extractor.py --all  # Process all unprocessed logs
"""

import json
import re
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path("/home/bamer/.opencode/emergent-learning")
PROPOSALS_DIR = BASE_DIR / "proposals" / "pending"
SESSIONS_DIR = BASE_DIR / "sessions"
DB_PATH = BASE_DIR / "memory" / "index.db"
PROCESSED_MARKER = SESSIONS_DIR / ".processed"


def ensure_dirs():
    """Ensure required directories exist."""
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    (SESSIONS_DIR / "logs").mkdir(parents=True, exist_ok=True)


def read_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """Read a JSONL file and return list of entries."""
    entries = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except IOError as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return entries


def extract_learned_markers(text: str) -> List[Dict[str, str]]:
    """Extract [LEARNED:domain] markers from text."""
    pattern = r'\[LEARNED:?\s*([^\]]*)\]\s*(.+?)(?=\[LEARNED|$)'
    markers = []
    for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
        domain = match.group(1).strip() or "general"
        lesson = match.group(2).strip()
        if lesson and len(lesson) > 10:
            markers.append({
                "domain": domain,
                "lesson": lesson[:500],
            })
    return markers


def extract_failure_patterns(entries: List[Dict]) -> List[Dict[str, Any]]:
    """Identify repeated failure patterns."""
    failures = [e for e in entries if e.get("outcome") == "failure"]
    patterns = {}
    
    for f in failures:
        agent = f.get("agent", "unknown")
        summary = f.get("input_summary", "")[:80]
        key = f"{agent}:{summary[:40]}"
        if key not in patterns:
            patterns[key] = {
                "agent": agent,
                "summary": summary,
                "count": 0,
                "timestamps": [],
            }
        patterns[key]["count"] += 1
        patterns[key]["timestamps"].append(f.get("ts", ""))
    
    return [p for p in patterns.values() if p["count"] >= 2]


def extract_heuristic_candidates(entries: List[Dict]) -> List[Dict[str, str]]:
    """Extract potential heuristics from successful interactions."""
    candidates = []
    heuristic_keywords = ["always", "never", "should", "must", "avoid", "prefer", "ensure"]
    
    for entry in entries:
        if entry.get("outcome") != "success":
            continue
        summary = entry.get("input_summary", "")
        for keyword in heuristic_keywords:
            if keyword in summary.lower():
                candidates.append({
                    "rule": summary[:200],
                    "domain": entry.get("agent", "general"),
                    "source": "session_extraction",
                    "confidence": 0.3,
                })
                break
    
    return candidates


def write_proposal(proposal: Dict[str, Any], index: int) -> Path:
    """Write a proposal as a markdown file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"proposal_{timestamp}_{index:03d}.md"
    filepath = PROPOSALS_DIR / filename
    
    ptype = proposal.get("type", "observation")
    domain = proposal.get("domain", "general")
    confidence = proposal.get("confidence", 0.5)
    
    content = f"""# Proposal: {proposal.get('title', 'Untitled')}

**Type:** {ptype}
**Domain:** {domain}
**Confidence:** {confidence}
**Extracted:** {datetime.now().isoformat()}
**Source:** Session log analysis

## Summary

{proposal.get('summary', 'No summary available.')}

## Evidence

{proposal.get('evidence', 'Extracted from session logs.')}

## Suggested Action

{proposal.get('action', 'Review and validate this observation.')}
"""
    
    filepath.write_text(content, encoding='utf-8')
    return filepath


def store_learning_in_db(domain: str, lesson: str, source: str = "extractor"):
    """Store a learning directly in the database."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        
        conn.execute("""
            INSERT OR IGNORE INTO learnings 
            (type, domain, description, outcome, timestamp, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "observation",
            domain,
            lesson[:1000],
            "extracted",
            datetime.now().isoformat(),
            json.dumps({"source": source}),
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB write failed: {e}", file=sys.stderr)
        return False


def get_processed_files() -> List[str]:
    """Get list of already processed files."""
    if not PROCESSED_MARKER.exists():
        return []
    try:
        data = json.loads(PROCESSED_MARKER.read_text(encoding='utf-8'))
        return data.get('processed_files', [])
    except (json.JSONDecodeError, IOError):
        return []


def mark_processed(filenames: List[str]):
    """Mark files as processed."""
    processed = get_processed_files()
    processed.extend(f for f in filenames if f not in processed)
    
    data = {
        'processed_files': processed,
        'last_processed': datetime.now().isoformat(),
    }
    
    import tempfile, os
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=SESSIONS_DIR, prefix='.processed_', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, PROCESSED_MARKER)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def process_log_files(log_files: List[Path]) -> Dict[str, Any]:
    """Process a list of log files and extract learnings."""
    ensure_dirs()
    
    all_entries = []
    for lf in log_files:
        all_entries.extend(read_jsonl(lf))
    
    if not all_entries:
        return {"processed": 0, "learnings": 0, "proposals": 0, "failures": 0}
    
    results = {
        "processed": len(all_entries),
        "learnings": 0,
        "proposals": 0,
        "failures": 0,
        "files": [f.name for f in log_files],
    }
    
    # Extract [LEARNED:] markers from all entries
    proposal_index = 0
    for entry in all_entries:
        # Check input_summary and any response text for markers
        for field in ["input_summary"]:
            text = entry.get(field, "")
            markers = extract_learned_markers(text)
            for marker in markers:
                store_learning_in_db(marker["domain"], marker["lesson"])
                results["learnings"] += 1
    
    # Extract failure patterns
    failure_patterns = extract_failure_patterns(all_entries)
    for pattern in failure_patterns:
        proposal_index += 1
        write_proposal({
            "title": f"Repeated failure: {pattern['agent']} - {pattern['summary'][:60]}",
            "type": "failure_pattern",
            "domain": pattern["agent"],
            "confidence": min(0.3 + pattern["count"] * 0.1, 0.9),
            "summary": f"Agent '{pattern['agent']}' failed {pattern['count']} times with similar input: {pattern['summary']}",
            "evidence": f"Failures at: {', '.join(pattern['timestamps'][:5])}",
            "action": "Investigate root cause and add preventive heuristic.",
        }, proposal_index)
        results["failures"] += 1
    
    # Extract heuristic candidates
    candidates = extract_heuristic_candidates(all_entries)
    for candidate in candidates[:10]:  # Limit proposals per run
        proposal_index += 1
        write_proposal({
            "title": f"Potential heuristic: {candidate['rule'][:60]}",
            "type": "heuristic_candidate",
            "domain": candidate["domain"],
            "confidence": candidate["confidence"],
            "summary": candidate["rule"],
            "evidence": "Extracted from successful session interaction.",
            "action": "Validate and promote to heuristic if confirmed.",
        }, proposal_index)
        results["proposals"] += 1
    
    # Mark files as processed
    mark_processed([f.name for f in log_files])
    
    return results


def main():
    """Main entry point."""
    ensure_dirs()
    
    if len(sys.argv) < 2:
        print("Usage: python run_extractor.py [--all | file1.jsonl file2.jsonl ...]")
        sys.exit(1)
    
    if sys.argv[1] == "--all":
        # Process all unprocessed logs
        logs_dir = SESSIONS_DIR / "logs"
        if not logs_dir.exists():
            print("No logs directory found.")
            sys.exit(0)
        
        processed = set(get_processed_files())
        today = datetime.now().strftime("%Y-%m-%d")
        
        log_files = [
            f for f in sorted(logs_dir.glob("*.jsonl"))
            if f.name not in processed and not f.name.startswith(today)
        ]
        
        if not log_files:
            print("No unprocessed log files found.")
            sys.exit(0)
        
        print(f"Processing {len(log_files)} log file(s)...")
    else:
        log_files = [Path(f) for f in sys.argv[1:] if Path(f).exists()]
        if not log_files:
            print("No valid log files provided.")
            sys.exit(1)
    
    results = process_log_files(log_files)
    
    print(f"\nExtraction complete:")
    print(f"  Entries processed: {results['processed']}")
    print(f"  Learnings stored:  {results['learnings']}")
    print(f"  Proposals created: {results['proposals']}")
    print(f"  Failure patterns:  {results['failures']}")


if __name__ == "__main__":
    main()
