#!/usr/bin/env python3
"""
FIXED VERSION: Record a heuristic in the Emergent Learning Framework

Changes:
1. Added project_path detection and recording
2. Added --project-path CLI argument
3. Fixed domain validation
4. Added project_path to INSERT statement
"""

import sqlite3
import argparse
import os
import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime
import logging
import json

import requests

# Setup logging
script_dir = Path(__file__).parent
base_dir = script_dir.parent
logs_dir = base_dir / "logs"
logs_dir.mkdir(exist_ok=True)

log_file = logs_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [record-heuristic] %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# Database path
db_path = base_dir / "memory" / "index.db"
heuristics_dir = base_dir / "memory" / "heuristics"

# Ollama configuration
OLLAMA_SERVER = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

# Event-driven consolidation settings
CONSOLIDATION_THRESHOLD = 5  # Trigger consolidation after X new failures
CONSOLIDATION_WINDOW_HOURS = 1  # Within this time window
FAILURE_TRACKER_FILE = logs_dir / ".failure_tracker.json"

# Input constraints
MAX_RULE_LENGTH = 500
MAX_DOMAIN_LENGTH = 100
MAX_EXPLANATION_LENGTH = 5000

# Valid domain patterns (letters, numbers, hyphens only)
VALID_DOMAIN_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$|^[a-z0-9]$")

# Pre-approved domains (can be expanded)
APPROVED_DOMAINS = {
    "core-principles",
    "golden",
    "infrastructure",
    "test",
    "performance",
    "security",
    "system-patterns",
    "testing",
    "workflow",
    "react",
    "architecture",
    "system-quality",
    "test-domain",
    "api",
    "autonomousoperations",
    "database-performance",
    "debugging",
    "development",
    "escalation",
    "frontend",
    "general",
    "monitoring",
    "parallel",
    "project-management",
    "provide",
    "recommendation",
    "recommended",
    "status",
    "severitybased",
    "system",
    "system-diagnostics",
    "system-migration",
    "securitysafety",
    "elf-compliance",
    "functionaltest",
    "learnedarchitecture",
    "learnedgeneral",
}


def get_current_project_path() -> Path | None:
    """Get the current project path using git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None


def validate_domain(domain: str) -> str | None:
    """Validate domain string. Returns valid domain or None if invalid."""
    if not domain:
        return None

    domain = domain.strip().lower()

    # Check if pre-approved
    if domain in APPROVED_DOMAINS:
        return domain

    # Check if domain follows valid pattern
    if not VALID_DOMAIN_PATTERN.match(domain):
        logger.warning(f"Invalid domain rejected: {domain}")
        return None

    # Domain must be reasonable (1-30 chars)
    if len(domain) < 2 or len(domain) > 30:
        logger.warning(f"Domain length rejected: {domain} (length: {len(domain)})")
        return None

    return domain


def sanitize_input(text):
    """Sanitize input: strip control chars, normalize whitespace"""
    if not text:
        return ""
    # Remove control characters (keep printable + space/tab)
    text = "".join(c for c in text if c.isprintable() or c in "\t\n\r")
    # Normalize multiple spaces to single
    text = " ".join(text.split())
    return text.strip()


def validate_confidence(confidence_str):
    """Validate and convert confidence to float"""
    if not confidence_str:
        return 0.7

    # Try to parse as float
    try:
        conf = float(confidence_str)
        if 0.0 <= conf <= 1.0:
            return conf
    except ValueError:
        pass

    # Try word conversion
    words = {"low": 0.3, "medium": 0.6, "high": 0.85}
    if confidence_str.lower() in words:
        return words[confidence_str.lower()]

    logger.warning(f"Invalid confidence '{confidence_str}', defaulting to 0.7")
    return 0.7


def sanitize_domain(domain):
    """Sanitize domain to prevent path traversal"""
    domain = domain.lower()
    domain = re.sub(r"[^a-z0-9\-]", "", domain.replace(" ", "-"))
    domain = domain.strip("-")[:100]
    return domain


def track_failure_and_maybe_consolidate(source_type: str) -> bool:
    """
    Track failures and trigger consolidation when threshold is reached.
    Returns True if consolidation was triggered.
    """
    # Only track actual failures (not success/observation)
    if source_type != 'failure':
        return False
    
    try:
        # Load or create tracker
        tracker = {"failures": [], "last_consolidation": None}
        if FAILURE_TRACKER_FILE.exists():
            with open(FAILURE_TRACKER_FILE, 'r') as f:
                tracker = json.load(f)
        
        # Add current failure
        now = datetime.now().isoformat()
        tracker["failures"].append({
            "timestamp": now,
            "source_type": source_type
        })
        
        # Clean old failures outside window
        cutoff = datetime.now().timestamp() - (CONSOLIDATION_WINDOW_HOURS * 3600)
        tracker["failures"] = [
            f for f in tracker["failures"]
            if datetime.fromisoformat(f["timestamp"]).timestamp() > cutoff
        ]
        
        # Check if threshold reached
        failure_count = len(tracker["failures"])
        should_consolidate = failure_count >= CONSOLIDATION_THRESHOLD
        
        # Also check time since last consolidation (avoid spam)
        if should_consolidate and tracker.get("last_consolidation"):
            last_consol_time = datetime.fromisoformat(tracker["last_consolidation"])
            time_since = (datetime.now() - last_consol_time).total_seconds()
            if time_since < 300:  # 5 minutes cooldown
                should_consolidate = False
        
        if should_consolidate:
            logger.info(f"🔄 Failure threshold reached ({failure_count} failures), triggering consolidation...")
            
            # Run consolidation script
            try:
                consolidation_script = script_dir / "consolidate_failures.py"
                if consolidation_script.exists():
                    result = subprocess.run(
                        [sys.executable, str(consolidation_script), "--threshold", "2"],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        logger.info("✅ Consolidation completed successfully")
                        print("\n🧠 Auto-consolidation: Converted failure patterns to heuristics")
                        
                        # Reset tracker and mark consolidation time
                        tracker["failures"] = []
                        tracker["last_consolidation"] = now
                        
                        # Save tracker
                        with open(FAILURE_TRACKER_FILE, 'w') as f:
                            json.dump(tracker, f, indent=2)
                        
                        return True
                    else:
                        logger.warning(f"Consolidation script returned error: {result.stderr}")
                        
            except Exception as e:
                logger.error(f"Failed to run consolidation: {e}")
        
        # Save tracker (even if no consolidation)
        with open(FAILURE_TRACKER_FILE, 'w') as f:
            json.dump(tracker, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error in failure tracking: {e}")
    
    return False


def preflight_check():
    """Verify database and directory structure"""
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        print(f"ERROR: Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    heuristics_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Pre-flight checks passed")

def generate_embedding(text: str):
    """Generate embedding using Ollama nomic-embed-text model."""
    try:
        response = requests.post(
            f"{OLLAMA_SERVER}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=10,
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("embedding")
        logger.warning(f"Ollama embedding failed: HTTP {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
    return None

def save_embedding(conn, heuristic_id, text, metadata=None) -> bool:
    """Save heuristic embedding to the embeddings table."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM embeddings WHERE source_type = ? AND source_id = ?",
            ("heuristic", str(heuristic_id)),
        )
        if cursor.fetchone():
            logger.info(f"Embedding already exists for heuristic {heuristic_id}")
            return True

        embedding_vector = generate_embedding(text)
        if not embedding_vector:
            logger.warning(f"No embedding generated for heuristic {heuristic_id}")
            return False

        cursor.execute(
            """
            INSERT INTO embeddings
            (source_id, source_type, text_content, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(heuristic_id),
                "heuristic",
                text,
                json.dumps(embedding_vector),
                json.dumps(metadata) if metadata else None,
                datetime.now().isoformat(),
            ),
        )
        return True
    except Exception as e:
        logger.warning(f"Error saving embedding: {e}")
        return False


def record_heuristic(
    domain, rule, explanation, source_type, confidence, project_path=None
):
    """Record heuristic to database and markdown file with project_path support"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        # Convert project_path to string if provided
        project_path_str = str(project_path) if project_path else None

        cursor.execute(
            """
            INSERT INTO heuristics
            (domain, rule, explanation, source_type, confidence, times_validated, times_violated, is_golden, created_at, updated_at, project_path)
            VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)
            ON CONFLICT(domain, rule) DO UPDATE SET
                times_validated = times_validated + 1,
                confidence = MIN(1.0, confidence + 0.05),
                explanation = COALESCE(excluded.explanation, explanation),
                updated_at = excluded.updated_at
        """,
            (
                domain,
                rule,
                explanation,
                source_type,
                confidence,
                now,
                now,
                project_path_str,
            ),
        )

        cursor.execute(
            "SELECT id FROM heuristics WHERE domain = ? AND rule = ?",
            (domain, rule),
        )
        row = cursor.fetchone()
        heuristic_id = row[0] if row else cursor.lastrowid

        conn.commit()

        embedding_text = f"{domain}: {rule}. {explanation}".strip()
        save_embedding(
            conn,
            heuristic_id,
            embedding_text,
            metadata={
                "domain": domain,
                "confidence": confidence,
                "source_type": source_type,
            },
        )
        conn.commit()
        conn.close()

        logger.info(f"Database record created (ID: {heuristic_id})")
        print(f"Database record created (ID: {heuristic_id})")

        # Write to markdown file
        domain_file = heuristics_dir / f"{domain}.md"

        if not domain_file.exists():
            with open(domain_file, "w", encoding="utf-8") as f:
                f.write(f"# Heuristics: {domain}\n\n")
                f.write(
                    f"Generated from failures, successes, and observations in the **{domain}** domain.\n\n"
                )
                f.write("---\n\n")
            logger.info(f"Created new domain file: {domain_file}")

        with open(domain_file, "a", encoding="utf-8") as f:
            f.write(f"## H-{heuristic_id}: {rule}\n\n")
            f.write(f"**Confidence**: {confidence}\n")
            f.write(f"**Source**: {source_type}\n")
            if project_path_str:
                f.write(f"**Project**: `{project_path_str}`\n")
            f.write(f"**Created**: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(f"{explanation}\n\n")
            f.write("---\n\n")

        print(f"Appended to: {domain_file}")
        logger.info(f"Appended heuristic to: {domain_file}")
        logger.info(f"Heuristic recorded successfully: {rule}")
        if project_path_str:
            logger.info(f"Project path: {project_path_str}")
        print("\nHeuristic recorded successfully!")

        return True

    except Exception as e:
        logger.error(f"Failed to record heuristic: {e}")
        print(f"ERROR: Failed to record heuristic: {e}", file=sys.stderr)
        return False


def interactive_mode():
    """Interactive prompt for heuristic input"""
    print("=== Record Heuristic ===\n")

    try:
        domain = input("Domain: ").strip()
        if not domain:
            logger.error("Domain cannot be empty")
            print("ERROR: Domain cannot be empty", file=sys.stderr)
            sys.exit(1)

        rule = input("Rule (the heuristic): ").strip()
        if not rule:
            logger.error("Rule cannot be empty")
            print("ERROR: Rule cannot be empty", file=sys.stderr)
            sys.exit(1)

        explanation = input("Explanation: ").strip()

        source_type = input(
            "Source type (failure/success/observation) [observation]: "
        ).strip()
        if not source_type:
            source_type = "observation"

        confidence = input("Confidence (0.0-1.0) [0.7]: ").strip()
        if not confidence:
            confidence = "0.7"

        return domain, rule, explanation, source_type, confidence
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.")
        sys.exit(0)


def main():
    preflight_check()

    parser = argparse.ArgumentParser(
        description="Record a heuristic in the Emergent Learning Framework"
    )
    parser.add_argument("--domain", help="Domain for the heuristic")
    parser.add_argument("--rule", help="The heuristic rule")
    parser.add_argument("--explanation", help="Explanation of the heuristic")
    parser.add_argument(
        "--source", dest="source_type", help="Source type (failure/success/observation)"
    )
    parser.add_argument("--confidence", help="Confidence level (0.0-1.0)")
    parser.add_argument(
        "--project-path", help="Project path (auto-detected via git if not specified)"
    )

    args = parser.parse_args()

    logger.info("Script started")

    # Determine interactive vs non-interactive mode
    if args.domain and args.rule:
        domain = args.domain
        rule = args.rule
        explanation = args.explanation or ""
        source_type = args.source_type or "observation"
        confidence = args.confidence or "0.7"
        logger.info("Running in non-interactive mode")
        print("=== Record Heuristic (non-interactive) ===")
    elif not sys.stdin.isatty():
        logger.info("No terminal attached and no arguments provided - showing usage")
        print("Usage (non-interactive):")
        print(f'  python {sys.argv[0]} --domain "domain" --rule "the heuristic rule"')
        print(
            '  Optional: --explanation "why" --source failure|success|observation --confidence 0.8'
        )
        print(
            '  Optional: --project-path "/path/to/project" (auto-detected if not specified)'
        )
        sys.exit(0)
    else:
        logger.info("Running in interactive mode")
        domain, rule, explanation, source_type, confidence = interactive_mode()

    # Validate and sanitize inputs
    domain = sanitize_domain(domain)
    if not domain:
        logger.error("Domain resulted in empty string after sanitization")
        print(
            "ERROR: Domain resulted in empty string after sanitization", file=sys.stderr
        )
        sys.exit(1)

    if len(rule) > MAX_RULE_LENGTH:
        logger.error(f"Rule exceeds maximum length ({MAX_RULE_LENGTH} chars)")
        print(
            f"ERROR: Rule too long (max {MAX_RULE_LENGTH} characters)", file=sys.stderr
        )
        sys.exit(1)

    if len(explanation) > MAX_EXPLANATION_LENGTH:
        logger.error("Explanation exceeds maximum length")
        print(
            f"ERROR: Explanation too long (max {MAX_EXPLANATION_LENGTH} characters)",
            file=sys.stderr,
        )
        sys.exit(1)

    rule = sanitize_input(rule)
    explanation = sanitize_input(explanation)
    confidence = validate_confidence(confidence)

    # Get project path (from argument or auto-detect)
    project_path = None
    if args.project_path:
        project_path = Path(args.project_path.strip())
    else:
        project_path = get_current_project_path()
        if project_path:
            logger.info(f"Auto-detected project path: {project_path}")

    logger.info(
        f"Recording heuristic: {rule} (domain: {domain}, confidence: {confidence})"
    )

    if record_heuristic(
        domain, rule, explanation, source_type, confidence, project_path
    ):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
