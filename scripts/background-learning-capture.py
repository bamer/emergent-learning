#!/usr/bin/env python3
"""
FIXED VERSION: Background Learning Capture Service

Changes:
1. Added project_path detection and recording
2. Fixed domain extraction from text (no more "first word" guessing)
3. Added domain validation (rejects invalid domains)
4. Added proper sanitization of domain field
"""

import json
import sqlite3
import re
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
import subprocess

# Configuration
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = ELF_DIR / "memory" / "index.db"
LOG_FILE = ELF_DIR / ".coordination" / "learning-capture.log"

# OpenCode paths
OPENCODE_DIR = Path.home() / ".local" / "share" / "opencode"
OPENCODE_SESSIONS_DIR = OPENCODE_DIR / "storage" / "session"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Valid domain patterns (letters, numbers, hyphens only)
VALID_DOMAIN_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$|^[a-z0-9]$")

# Pre-approved domains (prevent garbage extraction)
APPROVED_DOMAINS = {
    "react",
    "python",
    "javascript",
    "typescript",
    "testing",
    "api",
    "database",
    "frontend",
    "backend",
    "security",
    "performance",
    "debugging",
    "workflow",
    "infrastructure",
    "system",
    "architecture",
    "development",
    "ci-cd",
    "monitoring",
    "deployment",
    "git",
    "docker",
    "kubernetes",
    "general",
    "core-principles",
    "golden",
    "system-patterns",
    "system-quality",
    "database-performance",
    "autonomousoperations",
    "project-management",
    "system-migration",
    "system-diagnostics",
    "securitysafety",
    "elf-compliance",
    "functionaltest",
    "learnedarchitecture",
    "learnedgeneral",
    "test",
    "test-domain",
}

# Heuristic extraction patterns
HEURISTIC_INDICATORS = [
    "should",
    "always",
    "never",
    "must",
    "don't",
    "avoid",
    "prefer",
    "recommend",
    "best practice",
    "critical to",
    "important to",
    "never forget",
]

LEARNING_PATTERNS = [
    (
        r"\[LEARNED:\s*([a-z0-9\-]+)\]\s*([^.]+)",
        "explicit",
    ),  # Strict: only valid domain chars
    (r"\[LEARNING:\s*([a-z0-9\-]+)\]\s*([^.]+)", "explicit"),
    (r"\[LEARN:\s*([a-z0-9\-]+)\]\s*([^.]+)", "explicit"),
]


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
        logger.debug(f"Invalid domain rejected: {domain}")
        return None

    # Domain must be reasonable (1-30 chars)
    if len(domain) < 2 or len(domain) > 30:
        logger.debug(f"Domain length rejected: {domain} (length: {len(domain)})")
        return None

    return domain


def get_db():
    """Get database connection."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def extract_heuristics_from_text(text: str, domain_hint: str = "general") -> list:
    """Extract heuristics from text content."""
    heuristics = []

    if not text:
        return heuristics

    # 1. Extract explicit [LEARNED:domain] markers with strict validation
    for pattern, marker_type in LEARNING_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for domain, rule in matches:
            domain = validate_domain(domain)
            if not domain:
                logger.debug(f"Skipping marker with invalid domain: {domain}")
                continue

            rule = rule.strip()
            if len(rule) > 15:
                heuristics.append(
                    {
                        "domain": domain,
                        "rule": rule,
                        "confidence": 0.8,
                        "source": f"marker-{marker_type}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    # 2. Extract implicit patterns (sentences with heuristic keywords)
    # Use domain_hint instead of guessing from first word
    sentences = re.split(r"[.!?\n]+", text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 300:
            continue

        has_indicator = any(
            indicator in sentence.lower() for indicator in HEURISTIC_INDICATORS
        )
        if has_indicator:
            # Clean up
            clean = re.sub(r"^[^a-zA-Z]*", "", sentence).strip()
            clean = re.sub(r"\s+", " ", clean)

            if clean and len(clean) > 20:
                # Use validated domain_hint, don't guess from first word
                domain = validate_domain(domain_hint) or "general"

                # Check for duplicates
                is_duplicate = any(h["rule"].startswith(clean[:30]) for h in heuristics)
                if not is_duplicate:
                    heuristics.append(
                        {
                            "domain": domain,
                            "rule": clean,
                            "confidence": 0.5,
                            "source": "implicit-pattern",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

    return heuristics


def extract_heuristics_from_metrics(
    metrics_data: dict, domain_hint: str = "system"
) -> list:
    """Extract heuristics from structured metrics data."""
    heuristics = []

    if not metrics_data or not isinstance(metrics_data, dict):
        return heuristics

    try:
        # Extract from data section
        data = metrics_data.get("data", {})
        activity = metrics_data.get("activity", {})
        quality = metrics_data.get("quality", {})

        # Default domain for metrics extraction
        domain = validate_domain(domain_hint) or "system"

        # Heuristic: Low activity might indicate a problem
        if "activity_score" in activity and activity["activity_score"] == 0:
            heuristics.append(
                {
                    "domain": domain,
                    "rule": "When system activity score is 0, investigate potential service disruptions or idle periods",
                    "confidence": 0.7,
                    "source": "metrics-analysis",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Heuristic: High confidence heuristics indicate mature system
        if (
            "high_confidence_heuristics" in quality
            and quality["high_confidence_heuristics"] > 30
        ):
            heuristics.append(
                {
                    "domain": domain,
                    "rule": "Systems with over 30 high-confidence heuristics demonstrate stable learning patterns",
                    "confidence": 0.8,
                    "source": "metrics-analysis",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Heuristic: Quality score threshold
        if "quality_score" in quality and quality["quality_score"] < 0.6:
            heuristics.append(
                {
                    "domain": domain,
                    "rule": "Quality scores below 0.6 indicate need for heuristic refinement or validation",
                    "confidence": 0.75,
                    "source": "metrics-analysis",
                    "timestamp": datetime.now().isoformat(),
                }
            )

    except Exception as e:
        logger.debug(f"Error extracting heuristics from metrics: {e}")

    return heuristics


def record_heuristic(heuristic: dict) -> bool:
    """Record a heuristic to the database with project_path."""
    try:
        conn = get_db()
        if not conn:
            return False

        cursor = conn.cursor()

        # Get current project path
        project_path = get_current_project_path()
        project_path_str = str(project_path) if project_path else None

        # Check for existing
        cursor.execute(
            "SELECT id, times_validated FROM heuristics WHERE domain = ? AND rule = ? AND (project_path IS NULL OR project_path = ?)",
            (heuristic["domain"], heuristic["rule"], project_path_str),
        )
        existing = cursor.fetchone()

        if existing:
            # Update validation count
            cursor.execute(
                """
                UPDATE heuristics
                SET times_validated = times_validated + 1,
                    confidence = MIN(1.0, confidence + 0.02),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (existing["id"],),
            )
            conn.commit()
            conn.close()
            logger.debug(f"Updated heuristic: {heuristic['rule'][:50]}...")
            return True

        # Insert new heuristic with project_path
        cursor.execute(
            """
            INSERT INTO heuristics
            (domain, rule, explanation, confidence, source_type, times_validated, times_violated, is_golden, created_at, updated_at, project_path)
            VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)
            """,
            (
                heuristic["domain"],
                heuristic["rule"],
                f"Auto-captured by background service on {heuristic['timestamp']}",
                heuristic["confidence"],
                heuristic["source"],
                heuristic["timestamp"],
                heuristic["timestamp"],
                project_path_str,
            ),
        )

        heuristic_id = cursor.lastrowid

        # Also create embedding via API (now async, won't block)
        try:
            embedding_text = f"{heuristic['domain']}: {heuristic['rule']}"
            requests.post(
                "http://localhost:8888/api/v1/persistence/heuristics",
                json={
                    "domain": heuristic["domain"],
                    "rule": heuristic["rule"],
                    "confidence": heuristic["confidence"],
                    "source_type": "auto-capture",
                },
                timeout=10,  # API now responds quickly, embedding in background
            )
        except Exception as e:
            logger.debug(f"Embedding API call (non-critical): {e}")
            pass  # Non-critical, heuristic is already saved

        conn.commit()
        conn.close()

        logger.info(
            f"✨ NEW HEURISTIC: [{heuristic['domain']}] {heuristic['rule'][:60]}..."
            + (f" [{Path(project_path).name}]" if project_path else " [global]")
        )
        return True

    except Exception as e:
        logger.error(f"Error recording heuristic: {e}")
        return False


def capture_from_event_chronicle():
    """Capture learnings from recent event chronicle entries."""
    try:
        conn = get_db()
        if not conn:
            return

        cursor = conn.cursor()

        # Get recent events with summaries
        cursor.execute("""
            SELECT id, timestamp, event_type, source, summary, data
            FROM event_chronicle
            WHERE timestamp > datetime('now', '-1 hour')
            AND (summary IS NOT NULL OR data IS NOT NULL)
            ORDER BY timestamp DESC
            LIMIT 100
            """)

        events = cursor.fetchall()
        conn.close()

        logger.debug(f"Found {len(events)} events to process")

        captured = 0
        for event in events:
            content = ""
            if event["summary"]:
                content += event["summary"] + " "

            # Process both text content and structured data
            heuristics = []

            # Extract from text content
            if content:
                domain_hint = (
                    event["source"]
                    if event["source"] and event["source"] not in ["event", "api"]
                    else "general"
                )
                text_heuristics = extract_heuristics_from_text(content, domain_hint)
                heuristics.extend(text_heuristics)
                logger.debug(
                    f"Event {event['id']}: Found {len(text_heuristics)} text heuristics"
                )

            # Extract from structured data (JSON)
            if event["data"]:
                try:
                    data = json.loads(event["data"])
                    if isinstance(data, dict):
                        content += str(data)
                        # Extract heuristics from metrics data
                        if "metrics" in data:
                            metrics_heuristics = extract_heuristics_from_metrics(
                                data["metrics"],
                                event["source"] if event["source"] else "general",
                            )
                            heuristics.extend(metrics_heuristics)
                            logger.debug(
                                f"Event {event['id']}: Found {len(metrics_heuristics)} metrics heuristics"
                            )
                except json.JSONDecodeError:
                    content += str(event["data"])
                    # Still try to extract heuristics from text
                    text_heuristics = extract_heuristics_from_text(
                        str(event["data"]),
                        event["source"] if event["source"] else "general",
                    )
                    heuristics.extend(text_heuristics)
                    logger.debug(
                        f"Event {event['id']}: Found {len(text_heuristics)} data text heuristics"
                    )

            logger.debug(f"Event {event['id']}: Total {len(heuristics)} heuristics")

            for h in heuristics:
                if record_heuristic(h):
                    captured += 1
                    logger.debug(
                        f"Recorded heuristic: [{h['domain']}] {h['rule'][:50]}..."
                    )

        if captured > 0:
            logger.info(f"📝 Captured {captured} heuristics from {len(events)} events")
        elif len(events) > 0:
            logger.debug(f"🔍 Processed {len(events)} events but captured 0 heuristics")

    except Exception as e:
        logger.error(f"Error capturing from event chronicle: {e}")
        logger.exception(e)


def capture_from_watcher_log():
    """Capture learnings from watcher log."""
    try:
        watcher_log = ELF_DIR / ".coordination" / "watcher-log.md"
        if not watcher_log.exists():
            return

        # Read last hour of entries
        content = watcher_log.read_text()
        heuristics = extract_heuristics_from_text(content, "watcher")

        captured = 0
        for h in heuristics:
            if record_heuristic(h):
                captured += 1

        if captured > 0:
            logger.info(f"👁️  Captured {captured} heuristics from watcher log")
        else:
            logger.debug(f"👁️  Processed watcher log but captured 0 heuristics")

    except Exception as e:
        logger.error(f"Error capturing from watcher log: {e}")


def run_capture_loop():
    """Main capture loop - runs continuously."""
    logger.info("=" * 60)
    logger.info("BACKGROUND LEARNING CAPTURE SERVICE STARTED")
    logger.info("=" * 60)
    logger.info("✅ Auto-capturing heuristics from system activity")
    logger.info("📊 Checking every 60 seconds")
    logger.info("📝 Press Ctrl+C to stop")
    logger.info("=" * 60)

    cycle = 0
    while True:
        try:
            cycle += 1

            # Capture from multiple sources
            capture_from_event_chronicle()
            capture_from_watcher_log()

            # Every 10 cycles, log status
            if cycle % 10 == 0:
                conn = get_db()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) FROM heuristics WHERE source_type = 'auto'"
                    )
                    auto_count = cursor.fetchone()[0]
                    cursor.execute(
                        "SELECT COUNT(*) FROM heuristics WHERE date(created_at) = date('now')"
                    )
                    today_count = cursor.fetchone()[0]
                    conn.close()
                    logger.info(
                        f"📊 Status: {today_count} heuristics today, {auto_count} auto-captured total"
                    )

            # Wait before next cycle
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("\n👋 Stopping learning capture service...")
            break
        except Exception as e:
            logger.error(f"Error in capture loop: {e}")
            time.sleep(60)


if __name__ == "__main__":
    run_capture_loop()
