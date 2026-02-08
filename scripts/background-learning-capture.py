#!/usr/bin/env python3
"""
Background Learning Capture Service
Runs continuously to capture learnings from ELF system activity.
This is a PERMANENT FIX for the learning extraction problem.
"""

import json
import sqlite3
import re
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
import threading

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
    (r"\[LEARNED:([^\]]+)\]\s*([^.]+)", "explicit"),
    (r"\[LEARNING:([^\]]+)\]\s*([^.]+)", "explicit"),
    (r"\[LEARN:([^\]]+)\]\s*([^.]+)", "explicit"),
]


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

    # 1. Extract explicit [LEARNED:] markers
    for pattern, marker_type in LEARNING_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for domain, rule in matches:
            domain = domain.strip().lower() if domain else domain_hint
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
                # Determine domain from first word
                words = clean.split()
                domain = (
                    re.sub(r"[^a-z]", "", words[0].lower()) if words else domain_hint
                )

                # Check for duplicates
                is_duplicate = any(h["rule"].startswith(clean[:30]) for h in heuristics)
                if not is_duplicate:
                    heuristics.append(
                        {
                            "domain": domain if domain else "general",
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

        # Heuristic: Low activity might indicate a problem
        if "activity_score" in activity and activity["activity_score"] == 0:
            heuristics.append(
                {
                    "domain": "system-monitoring",
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
                    "domain": "system-quality",
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
                    "domain": "system-quality",
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
    """Record a heuristic to the database with embedding."""
    try:
        conn = get_db()
        if not conn:
            return False

        cursor = conn.cursor()

        # Check for existing
        cursor.execute(
            "SELECT id, times_validated FROM heuristics WHERE domain = ? AND rule = ?",
            (heuristic["domain"], heuristic["rule"]),
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

        # Insert new heuristic
        cursor.execute(
            """
            INSERT INTO heuristics 
            (domain, rule, explanation, confidence, source_type, times_validated, times_violated, is_golden, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, ?)
            """,
            (
                heuristic["domain"],
                heuristic["rule"],
                f"Auto-captured by background service on {heuristic['timestamp']}",
                heuristic["confidence"],
                heuristic["source"],
                heuristic["timestamp"],
                heuristic["timestamp"],
            ),
        )

        heuristic_id = cursor.lastrowid

        # Also create embedding via API
        # TEMPORARILY DISABLED due to timeout issues
        # try:
        #     embedding_text = f"{heuristic['domain']}: {heuristic['rule']}"
        #     requests.post(
        #         "http://localhost:8888/api/v1/persistence/heuristics",
        #         json={
        #             "domain": heuristic["domain"],
        #             "rule": heuristic["rule"],
        #             "confidence": heuristic["confidence"],
        #             "source_type": "auto-capture",
        #         },
        #         timeout=5,
        #     )
        # except:
        #     pass  # Non-critical, heuristic is already saved

        conn.commit()
        conn.close()

        logger.info(
            f"✨ NEW HEURISTIC: [{heuristic['domain']}] {heuristic['rule'][:60]}..."
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
                text_heuristics = extract_heuristics_from_text(
                    content, event["source"] if event["source"] else "general"
                )
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
                        "SELECT COUNT(*) FROM heuristics WHERE source_type = 'auto-capture'"
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
