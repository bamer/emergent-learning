#!/usr/bin/env python3
"""
Debug script to test learning capture functionality
"""

import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path

# Configuration
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = ELF_DIR / "memory" / "index.db"

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
        print(f"Database connection failed: {e}")
        return None


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

        print(
            f"DEBUG: Processing metrics data - data keys: {list(data.keys()) if data else 'None'}"
        )
        print(f"DEBUG: Activity data: {activity}")
        print(f"DEBUG: Quality data: {quality}")

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
            print("DEBUG: Found low activity heuristic")

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
            print("DEBUG: Found high confidence heuristic")

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
            print("DEBUG: Found quality score heuristic")

    except Exception as e:
        print(f"DEBUG: Error extracting heuristics from metrics: {e}")

    print(f"DEBUG: Extracted {len(heuristics)} heuristics from metrics")
    return heuristics


def extract_heuristics_from_text(text: str, domain_hint: str = "general") -> list:
    """Extract heuristics from text content."""
    heuristics = []

    if not text:
        return heuristics

    print(f"DEBUG: Processing text of length {len(text)}")

    # 1. Extract explicit [LEARNED:] markers
    for pattern, marker_type in LEARNING_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        print(f"DEBUG: Found {len(matches)} explicit matches for pattern {pattern}")
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
    print(f"DEBUG: Split text into {len(sentences)} sentences")

    matched_sentences = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 300:
            continue

        has_indicator = any(
            indicator in sentence.lower() for indicator in HEURISTIC_INDICATORS
        )
        if has_indicator:
            matched_sentences += 1
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

    print(f"DEBUG: Found {matched_sentences} sentences with heuristic indicators")
    print(f"DEBUG: Extracted {len(heuristics)} heuristics total from text")
    return heuristics

    print(f"DEBUG: Processing text of length {len(text)}")

    # 1. Extract explicit [LEARNED:] markers
    for pattern, marker_type in LEARNING_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        print(f"DEBUG: Found {len(matches)} explicit matches for pattern {pattern}")
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
    print(f"DEBUG: Split text into {len(sentences)} sentences")

    matched_sentences = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 300:
            continue

        has_indicator = any(
            indicator in sentence.lower() for indicator in HEURISTIC_INDICATORS
        )
        if has_indicator:
            matched_sentences += 1
            # Clean up
            clean = re.sub(r"^[^a-zA-Z]*", "", sentence).strip()
            clean = re.sub(r"\s+", " ", clean)

            if clean and len(clean) > 20:
                # Determine domain from first word
                words = clean.split()
                domain = (
                    words[0].lower().replace("[^a-z]", "") if words else domain_hint
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

    print(f"DEBUG: Found {matched_sentences} sentences with heuristic indicators")
    print(f"DEBUG: Extracted {len(heuristics)} heuristics total")
    return heuristics


def debug_event_chronicle():
    """Debug event chronicle extraction."""
    print("=" * 60)
    print("DEBUGGING EVENT CHRONICLE EXTRACTION")
    print("=" * 60)

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
            LIMIT 5
        """)

        events = cursor.fetchall()
        conn.close()

        print(f"Found {len(events)} recent events")

        total_heuristics = 0
        for i, event in enumerate(events):
            print(f"\n--- Event {i + 1} ---")
            print(f"ID: {event['id']}")
            print(f"Timestamp: {event['timestamp']}")
            print(f"Type: {event['event_type']}")
            print(f"Source: {event['source']}")

            content = ""
            if event["summary"]:
                content += event["summary"] + " "
                print(f"Summary length: {len(event['summary'])}")
            if event["data"]:
                try:
                    data = json.loads(event["data"])
                    if isinstance(data, dict):
                        content += str(data)
                    else:
                        content += str(event["data"])
                except:
                    content += str(event["data"])
                print(f"Data length: {len(str(event['data']))}")

            print(f"Total content length: {len(content)}")

            if content:
                heuristics = extract_heuristics_from_text(
                    content, event["source"] if event["source"] else "general"
                )

                # Also try to extract from structured data
                if event["data"]:
                    try:
                        data = json.loads(event["data"])
                        if isinstance(data, dict) and "metrics" in data:
                            metrics_heuristics = extract_heuristics_from_metrics(
                                data["metrics"],
                                event["source"] if event["source"] else "general",
                            )
                            heuristics.extend(metrics_heuristics)
                    except json.JSONDecodeError:
                        pass

                print(f"Extracted {len(heuristics)} heuristics from this event")
                total_heuristics += len(heuristics)

                for j, h in enumerate(heuristics):
                    print(f"  Heuristic {j + 1}: [{h['domain']}] {h['rule'][:100]}...")

        print(f"\nTOTAL HEURISTICS FROM EVENTS: {total_heuristics}")

    except Exception as e:
        print(f"Error debugging event chronicle: {e}")


def debug_watcher_log():
    """Debug watcher log extraction."""
    print("\n" + "=" * 60)
    print("DEBUGGING WATCHER LOG EXTRACTION")
    print("=" * 60)

    try:
        watcher_log = ELF_DIR / ".coordination" / "watcher-log.md"
        if not watcher_log.exists():
            print("Watcher log not found")
            return

        # Read content
        content = watcher_log.read_text()
        print(f"Watcher log size: {len(content)} characters")

        # Show sample content
        lines = content.split("\n")
        print(f"Watcher log lines: {len(lines)}")
        print("First 10 lines:")
        for i, line in enumerate(lines[:10]):
            print(f"  {i + 1}: {line[:100]}")

        heuristics = extract_heuristics_from_text(content, "watcher")
        print(f"\nTOTAL HEURISTICS FROM WATCHER LOG: {len(heuristics)}")

        for i, h in enumerate(heuristics):
            print(f"  Heuristic {i + 1}: [{h['domain']}] {h['rule'][:100]}...")

    except Exception as e:
        print(f"Error debugging watcher log: {e}")


if __name__ == "__main__":
    debug_event_chronicle()
    debug_watcher_log()
