#!/usr/bin/env python3
"""
Test script to verify metrics-based heuristic extraction
"""

import json
import re
from datetime import datetime
from pathlib import Path

# Configuration
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = ELF_DIR / "memory" / "index.db"


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


# Test with actual metrics data
sample_data = {
    "metrics": {
        "timestamp": "2026-02-07T00:58:06.460585",
        "services": {"frontend": True, "backend": True, "overall": True},
        "data": {
            "learnings": 421,
            "golden_rules": 21,
            "regular_heuristics": 41,
            "experiments": 4,
            "spike_reports": 2,
            "system_failures_24h": 0,
            "total_items": 489,
        },
        "activity": {
            "recent_learnings": 0,
            "recent_heuristics": 0,
            "activity_score": 0,
        },
        "quality": {
            "high_confidence_heuristics": 35,
            "average_confidence": 0.794,
            "quality_score": 0.5645161290322581,
        },
    }
}

print("Testing metrics extraction with sample data:")
heuristics = extract_heuristics_from_metrics(sample_data["metrics"])
print(f"\nFound {len(heuristics)} heuristics:")
for i, h in enumerate(heuristics):
    print(f"  {i + 1}. [{h['domain']}] {h['rule']} (confidence: {h['confidence']})")
