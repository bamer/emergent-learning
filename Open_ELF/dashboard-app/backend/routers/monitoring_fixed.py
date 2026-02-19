# TEMPORAIRE: Copie de monitoring.py pour debug
# Nous allons restaurer le premier endpoint sentinel/status

import json
import sqlite3
import subprocess
import os
import signal
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import requests

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import (
        get_logger,
        log_critical,
        log_error,
        log_warning,
        log_info,
    )

    logger = get_logger("monitoring")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("monitoring")

# Import database utilities
try:
    from utils.database import get_db_connection, dict_from_row
except ImportError:
    import sys
    from pathlib import Path

    # Add backend directory to path for imports
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    try:
        from utils.database import get_db_connection, dict_from_row
    except ImportError:

        def get_db_connection():
            import sqlite3

            db_path = (
                Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
            )
            return sqlite3.connect(str(db_path))

        def dict_from_row(row):
            """Convert sqlite3.Row to dict"""
            return dict(row) if hasattr(row, "keys") else row


# Unified logging (best-effort)
try:
    sys.path.insert(0, str(Path.home() / ".opencode" / "emergent-learning" / "agents"))
    import logging

    logger = logging.getLogger(__name__)

    unified_logger = logger

    def _log_info(message: str) -> None:
        logger.info(message)

    def _log_error(message: str) -> None:
        logger.error(message)

except Exception:
    unified_logger = logger

    def _log_info(message: str) -> None:
        logger.info(message)

    def _log_error(message: str) -> None:
        logger.error(message)


# Router instance
router = APIRouter(prefix="/api/v1")

# ==============================================================================
# Data Processing Functions
# ==============================================================================


def detect_patterns_from_cycles(cycles: List[Dict]) -> List[Dict]:
    """Simple pattern detection from sentinel cycles."""
    patterns = []

    # Simple frequency analysis
    if len(cycles) >= 5:
        # Check if recent cycles have increasing activity scores
        recent_activity_scores = [
            cycle.get("metrics", {}).get("activity", {}).get("activity_score", 0)
            for cycle in cycles[:5]
            if cycle.get("metrics", {}).get("activity", {}).get("activity_score")
            is not None
        ]

        if len(recent_activity_scores) >= 3:
            # Simple increasing trend detection
            increasing_trend = all(
                recent_activity_scores[i] <= recent_activity_scores[i + 1]
                for i in range(len(recent_activity_scores) - 1)
            )

            if increasing_trend and max(recent_activity_scores) > 80:
                patterns.append(
                    {
                        "pattern_name": "Increasing Activity Trend",
                        "description": "System activity showing consistent upward trend",
                        "severity": "warning",
                        "detected_at": cycles[0].get("timestamp"),
                    }
                )

    return patterns


# ==============================================================================
# Sentinel Endpoints (RESTORED VERSION)
# ==============================================================================


@router.get("/monitoring/sentinel/status")
async def get_sentinel_status_restored():
    """Get current sentinel monitoring status and recent cycles (RESTORED)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent sentinel cycles from event_chronicle
        cursor.execute(
            """
            SELECT timestamp, data, summary, status
            FROM event_chronicle
            WHERE event_type = 'sentinel_cycle'
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )

        cycles = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row["data"]) if row["data"] else {}
                cycles.append(
                    {
                        "timestamp": row["timestamp"],
                        "metrics": data.get("metrics", {}),
                        "analysis": data.get("analysis", {}),
                        "actions_taken": data.get("actions", []),
                        "agent_executions": data.get("agent_executions", []),
                    }
                )
            except json.JSONDecodeError:
                continue

        conn.close()

        # Get current cycle (most recent)
        current_cycle = cycles[0] if cycles else None

        # Detect patterns from cycles
        patterns = detect_patterns_from_cycles(cycles[:20])

        return {
            "status": "ok",
            "current_cycle": current_cycle,
            "recent_cycles": cycles[:20],
            "patterns": patterns,
            "total_cycles": len(cycles),
        }

    except Exception as e:
        logger.error(f"Error fetching sentinel status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Original monitoring endpoints from the file...
# ==============================================================================

# ... [rest of original monitoring.py content] ...
