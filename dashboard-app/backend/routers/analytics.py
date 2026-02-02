"""
Analytics Router - Stats, timeline, learning velocity, events, anomalies, domains.
"""

from fastapi import APIRouter, Query
from utils import get_db, dict_from_row
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get("/stats")
async def get_stats():
    """Get overall statistics."""
    with get_db() as conn:
        cursor = conn.cursor()

        stats = {}

        # Consolidate main stats into a single query for performance
        try:
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM workflow_runs) as total_runs,
                    (SELECT COUNT(*) FROM node_executions) as total_executions,
                    (SELECT COUNT(*) FROM trails) as total_trails,
                    (SELECT COUNT(*) FROM heuristics) as total_heuristics,
                    (SELECT COUNT(*) FROM heuristics WHERE is_golden = 1) as golden_rules,
                    (SELECT COUNT(*) FROM learnings) as total_learnings,
                    (SELECT COUNT(*) FROM learnings WHERE type = 'failure') as failures,
                    (SELECT COUNT(*) FROM learnings WHERE type = 'success') as successes,
                    (SELECT COUNT(*) FROM decisions) as total_decisions,
                    (SELECT COUNT(*) FROM decisions WHERE status = 'accepted') as accepted_decisions,
                    (SELECT COUNT(*) FROM decisions WHERE status = 'superseded') as superseded_decisions,
                    (SELECT COUNT(*) FROM workflow_runs WHERE status = 'completed') as successful_runs,
                    (SELECT COUNT(*) FROM workflow_runs WHERE status IN ('failed', 'cancelled')) as failed_runs,
                    (SELECT AVG(confidence) FROM heuristics) as avg_confidence,
                    (SELECT SUM(times_validated) FROM heuristics) as total_validations,
                    (SELECT SUM(times_violated) FROM heuristics) as total_violations,
                    (SELECT COUNT(*) FROM metrics WHERE timestamp > datetime('now', '-1 hour')) as metrics_last_hour,
                    (SELECT COUNT(*) FROM workflow_runs WHERE created_at > datetime('now', '-24 hours')) as runs_today,
                    (SELECT COUNT(*) FROM building_queries) as total_queries,
                    (SELECT COUNT(*) FROM building_queries WHERE created_at > datetime('now', '-24 hours')) as queries_today,
                    (SELECT AVG(duration_ms) FROM building_queries WHERE duration_ms IS NOT NULL) as avg_query_duration_ms,
                    (SELECT COUNT(*) FROM invariants) as total_invariants,
                    (SELECT COUNT(*) FROM invariants WHERE status = 'active') as active_invariants,
                    (SELECT COUNT(*) FROM invariants WHERE status = 'violated') as violated_invariants,
                    (SELECT SUM(violation_count) FROM invariants) as total_invariant_violations
            """)
            row = cursor.fetchone()
            keys = [
                "total_runs",
                "total_executions",
                "total_trails",
                "total_heuristics",
                "golden_rules",
                "total_learnings",
                "failures",
                "successes",
                "total_decisions",
                "accepted_decisions",
                "superseded_decisions",
                "successful_runs",
                "failed_runs",
                "avg_confidence",
                "total_validations",
                "total_violations",
                "metrics_last_hour",
                "runs_today",
                "total_queries",
                "queries_today",
                "avg_query_duration_ms",
                "total_invariants",
                "active_invariants",
                "violated_invariants",
                "total_invariant_violations",
            ]
            # Map values to keys, defaulting None to 0 for counts/sums if appropriate
            for i, key in enumerate(keys):
                val = row[i]
                if val is None and key.startswith(
                    (
                        "total_",
                        "avg_",
                        "metrics_",
                        "runs_",
                        "active_",
                        "violated_",
                        "failures",
                        "successes",
                        "golden_rules",
                    )
                ):
                    val = 0
                stats[key] = val

        except Exception as e:
            # Fallback if the massive query fails (unlikely, but safe)
            print(f"Stats query failed: {e}")
            return {}

        # Spike reports stats (Separate safe query as table might not exist)
        try:
            cursor.execute("SELECT COUNT(*) FROM spike_reports")
            stats["total_spike_reports"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT AVG(usefulness_score) FROM spike_reports WHERE usefulness_score > 0"
            )
            stats["avg_spike_usefulness"] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(time_invested_minutes) FROM spike_reports")
            stats["total_spike_time_invested"] = cursor.fetchone()[0] or 0
        except Exception:
            stats["total_spike_reports"] = 0
            stats["avg_spike_usefulness"] = 0
            stats["total_spike_time_invested"] = 0

        return stats


@router.get("/timeline")
async def get_timeline(days: int = 7):
    """Get activity timeline data from Event Chronicle."""
    try:
        # Try to import Event Chronicle functionality
        import sys
        from pathlib import Path

        # Add Open_ELF to path
        current = Path(__file__).resolve()
        for parent in current.parents:
            open_elf_path = parent.parent / "Open_ELF"
            if open_elf_path.exists():
                sys.path.insert(0, str(open_elf_path))
                break

        from timeline_dashboard.event_adapter import (
            get_chronicle_events,
            get_chronicle_stats,
        )

        # Get recent events (last N days)
        from datetime import datetime, timedelta
        import json

        # For backward compatibility, we'll return the same structure but with real data
        # Get events from the last N days
        events = get_chronicle_events(
            limit=1000
        )  # Get enough events to cover the period
        print(f"DEBUG: Retrieved {len(events)} events from chronicle")
        if events:
            print(
                f"DEBUG: First event: {events[0]['event_type']} at {events[0]['timestamp']}"
            )

        # Group events by day and type for backward compatibility
        from collections import defaultdict

        daily_events = defaultdict(
            lambda: {
                "runs": 0,
                "trails": 0,
                "strength": 0.0,
                "validations": 0,
                "failures": 0,
            }
        )

        # Process events to create daily aggregations
        for event in events:
            try:
                # Parse timestamp
                timestamp = event.get("timestamp", "")
                if timestamp:
                    # Extract date from timestamp (assuming ISO format)
                    try:
                        from datetime import datetime

                        # Handle the timestamp format: 2026-01-28T06:00:41.681422+00:00
                        if "+" in timestamp:
                            date_part = timestamp.split("+")[0].split("T")[0]
                        elif "T" in timestamp:
                            date_part = timestamp.split("T")[0]
                        else:
                            date_part = timestamp.split()[0]
                        date_str = date_part

                        event_type = event.get("event_type", "")

                        # Map event types to categories based on ELF Event Chronicle types
                        if event_type in [
                            "task_start",
                            "task_end",
                            "workflow_started",
                            "agent_spawned",
                        ]:
                            daily_events[date_str]["runs"] += 1
                        elif "trail" in event_type.lower():
                            daily_events[date_str]["trails"] += 1
                            daily_events[date_str]["strength"] += (
                                1.0  # Default strength
                            )
                        elif event_type in [
                            "heuristic_validated",
                            "heuristic_consulted",
                        ]:
                            daily_events[date_str]["validations"] += 1
                        elif event_type in ["failure_recorded", "heuristic_violated"]:
                            daily_events[date_str]["failures"] += 1
                        elif event_type == "heuristic_created":
                            # Treat heuristic creation as a validation event
                            daily_events[date_str]["validations"] += 1
                        elif event_type == "golden_promoted":
                            # Treat golden promotion as a validation event
                            daily_events[date_str]["validations"] += 1
                    except Exception as e:
                        print(f"Error parsing timestamp {timestamp}: {e}")
                        continue
            except Exception as e:
                print(f"Error processing event: {e}")
                continue

        # Convert to the expected format
        runs_by_day = [
            {"date": date, "runs": data["runs"]} for date, data in daily_events.items()
        ]
        trails_by_day = [
            {"date": date, "trails": data["trails"], "strength": data["strength"]}
            for date, data in daily_events.items()
        ]
        validations_by_day = [
            {"date": date, "validations": data["validations"]}
            for date, data in daily_events.items()
        ]
        failures_by_day = [
            {"date": date, "failures": data["failures"]}
            for date, data in daily_events.items()
        ]

        # Sort by date
        runs_by_day.sort(key=lambda x: x["date"])
        trails_by_day.sort(key=lambda x: x["date"])
        validations_by_day.sort(key=lambda x: x["date"])
        failures_by_day.sort(key=lambda x: x["date"])

        return {
            "runs": runs_by_day,
            "trails": trails_by_day,
            "validations": validations_by_day,
            "failures": failures_by_day,
        }

    except ImportError:
        # Fallback to original database-based implementation
        with get_db() as conn:
            cursor = conn.cursor()

            # Runs by day
            cursor.execute(
                """
                SELECT DATE(created_at) as date, COUNT(*) as runs
                FROM workflow_runs
                WHERE created_at > datetime('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date
            """,
                (f"-{days} days",),
            )
            runs_by_day = [dict_from_row(r) for r in cursor.fetchall()]

            # Trails by day
            cursor.execute(
                """
                SELECT DATE(created_at) as date, COUNT(*) as trails, SUM(strength) as strength
                FROM trails
                WHERE created_at > datetime('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date
            """,
                (f"-{days} days",),
            )
            trails_by_day = [dict_from_row(r) for r in cursor.fetchall()]

            # Validations by day
            cursor.execute(
                """
                SELECT DATE(timestamp) as date, COUNT(*) as validations
                FROM metrics
                WHERE metric_type = 'heuristic_validated'
                  AND timestamp > datetime('now', ?)
                GROUP BY DATE(timestamp)
                ORDER BY date
            """,
                (f"-{days} days",),
            )
            validations_by_day = [dict_from_row(r) for r in cursor.fetchall()]

            # Failures by day
            cursor.execute(
                """
                SELECT DATE(timestamp) as date, COUNT(*) as failures
                FROM metrics
                WHERE metric_type = 'auto_failure_capture'
                  AND timestamp > datetime('now', ?)
                GROUP BY DATE(timestamp)
                ORDER BY date
            """,
                (f"-{days} days",),
            )
            failures_by_day = [dict_from_row(r) for r in cursor.fetchall()]

            return {
                "runs": runs_by_day,
                "trails": trails_by_day,
                "validations": validations_by_day,
                "failures": failures_by_day,
            }


@router.get("/learning-velocity")
async def get_learning_velocity(days: int = 30):
    """Get learning velocity metrics over time."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Heuristics created per day
        cursor.execute(
            """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM heuristics
            WHERE created_at > datetime('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date
        """,
            (f"-{days} days",),
        )
        heuristics_by_day = [dict_from_row(r) for r in cursor.fetchall()]

        # Learnings created per day
        cursor.execute(
            """
            SELECT DATE(created_at) as date,
                   COUNT(*) as total,
                   SUM(CASE WHEN type = 'failure' THEN 1 ELSE 0 END) as failures,
                   SUM(CASE WHEN type = 'success' THEN 1 ELSE 0 END) as successes
            FROM learnings
            WHERE created_at > datetime('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date
        """,
            (f"-{days} days",),
        )
        learnings_by_day = [dict_from_row(r) for r in cursor.fetchall()]

        # Golden rule promotions per day
        cursor.execute(
            """
            SELECT DATE(updated_at) as date, COUNT(*) as count
            FROM heuristics
            WHERE is_golden = 1
              AND updated_at > datetime('now', ?)
              AND updated_at > created_at
            GROUP BY DATE(updated_at)
            ORDER BY date
        """,
            (f"-{days} days",),
        )
        promotions_by_day = [dict_from_row(r) for r in cursor.fetchall()]

        # Confidence improvement rate - track average confidence over time
        cursor.execute(
            """
            SELECT DATE(updated_at) as date, AVG(confidence) as avg_confidence
            FROM heuristics
            WHERE updated_at > datetime('now', ?)
            GROUP BY DATE(updated_at)
            ORDER BY date
        """,
            (f"-{days} days",),
        )
        confidence_by_day = [dict_from_row(r) for r in cursor.fetchall()]

        # Calculate weekly aggregates for trend analysis
        cursor.execute(
            """
            SELECT
                strftime('%Y-W%W', created_at) as week,
                COUNT(*) as heuristics_count
            FROM heuristics
            WHERE created_at > datetime('now', ?)
            GROUP BY week
            ORDER BY week
        """,
            (f"-{days} days",),
        )
        heuristics_by_week = [dict_from_row(r) for r in cursor.fetchall()]

        # Learning streak - consecutive days with new heuristics or learnings
        cursor.execute(
            """
            WITH RECURSIVE dates(date) AS (
                SELECT DATE('now')
                UNION ALL
                SELECT DATE(date, '-1 day')
                FROM dates
                WHERE date > DATE('now', ?)
            ),
            activity AS (
                SELECT DISTINCT DATE(created_at) as date
                FROM (
                    SELECT created_at FROM heuristics
                    UNION ALL
                    SELECT created_at FROM learnings
                )
            )
            SELECT COUNT(*) as streak
            FROM dates d
            INNER JOIN activity a ON d.date = a.date
            WHERE d.date <= DATE('now')
            ORDER BY d.date DESC
        """,
            (f"-{days} days",),
        )
        streak_result = cursor.fetchone()
        current_streak = streak_result[0] if streak_result else 0

        # Success/failure trend - ratio over time
        cursor.execute(
            """
            SELECT DATE(created_at) as date,
                   COUNT(*) as total,
                   CAST(SUM(CASE WHEN type = 'success' THEN 1 ELSE 0 END) AS FLOAT) /
                   CAST(COUNT(*) AS FLOAT) as success_ratio
            FROM learnings
            WHERE created_at > datetime('now', ?)
            GROUP BY DATE(created_at)
            HAVING total > 0
            ORDER BY date
        """,
            (f"-{days} days",),
        )
        success_trend = [dict_from_row(r) for r in cursor.fetchall()]

        # Calculate velocity trends (% change week over week)
        heuristics_trend = 0.0
        if len(heuristics_by_week) >= 2:
            recent_week = heuristics_by_week[-1]["heuristics_count"]
            prev_week = heuristics_by_week[-2]["heuristics_count"]
            if prev_week > 0:
                heuristics_trend = ((recent_week - prev_week) / prev_week) * 100

        # Total stats for the period
        total_heuristics_period = sum(d["count"] for d in heuristics_by_day)
        total_learnings_period = sum(d["total"] for d in learnings_by_day)
        total_promotions_period = sum(d["count"] for d in promotions_by_day)

        # Failure-to-learning conversion rate
        cursor.execute(
            """
            SELECT COUNT(*) as total_failures
            FROM learnings
            WHERE type = 'failure'
              AND created_at > datetime('now', ?)
        """,
            (f"-{days} days",),
        )
        total_failures = cursor.fetchone()[0] or 0

        cursor.execute(
            """
            SELECT COUNT(*) as heuristics_from_failures
            FROM heuristics
            WHERE source_type = 'failure'
              AND created_at > datetime('now', ?)
        """,
            (f"-{days} days",),
        )
        heuristics_from_failures = cursor.fetchone()[0] or 0

        failure_to_learning_rate = 0.0
        if total_failures > 0:
            failure_to_learning_rate = (heuristics_from_failures / total_failures) * 100

        # Average confidence change
        avg_confidence_start = 0.0
        avg_confidence_end = 0.0
        if len(confidence_by_day) >= 2:
            avg_confidence_start = confidence_by_day[0].get("avg_confidence", 0) or 0
            avg_confidence_end = confidence_by_day[-1].get("avg_confidence", 0) or 0
        confidence_improvement = avg_confidence_end - avg_confidence_start

        # Golden rule promotion rate
        cursor.execute(
            """
            SELECT COUNT(*) as total_promotable
            FROM heuristics
            WHERE confidence >= 0.8
              AND times_validated >= 5
              AND is_golden = 0
              AND created_at > datetime('now', ?)
        """,
            (f"-{days} days",),
        )
        total_promotable = cursor.fetchone()[0] or 0

        promotion_rate = 0.0
        if total_promotable + total_promotions_period > 0:
            promotion_rate = (
                total_promotions_period / (total_promotable + total_promotions_period)
            ) * 100

        return {
            "heuristics_by_day": heuristics_by_day,
            "learnings_by_day": learnings_by_day,
            "promotions_by_day": promotions_by_day,
            "confidence_by_day": confidence_by_day,
            "heuristics_by_week": heuristics_by_week,
            "success_trend": success_trend,
            "current_streak": current_streak,
            "heuristics_trend": round(heuristics_trend, 1),
            "failure_to_learning_rate": round(failure_to_learning_rate, 1),
            "confidence_improvement": round(confidence_improvement, 2),
            "promotion_rate": round(promotion_rate, 1),
            "totals": {
                "heuristics": total_heuristics_period,
                "learnings": total_learnings_period,
                "promotions": total_promotions_period,
                "failures": total_failures,
                "heuristics_from_failures": heuristics_from_failures,
            },
        }


@router.get("/events")
async def get_events(limit: int = 50):
    """Get recent events feed."""
    with get_db() as conn:
        cursor = conn.cursor()

        events = []

        # Recent metrics (last hour)
        cursor.execute(
            """
            SELECT metric_type, metric_name, metric_value, tags, context, timestamp
            FROM metrics
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        for row in cursor.fetchall():
            r = dict_from_row(row)
            event_type = r["metric_type"]

            # Format event message
            if event_type == "heuristic_validated":
                message = "Heuristic validated"
            elif event_type == "heuristic_violated":
                message = "Heuristic violated"
            elif event_type == "auto_failure_capture":
                message = "Failure auto-captured"
            elif event_type == "golden_rule_promotion":
                message = "New golden rule promoted!"
            elif event_type == "task_outcome":
                message = f"Task {r['metric_name']}"
            else:
                message = f"{event_type}: {r['metric_name']}"

            events.append(
                {
                    "type": event_type,
                    "message": message,
                    "timestamp": r["timestamp"],
                    "tags": r["tags"],
                    "context": r["context"],
                }
            )

        return events


@router.get("/domains")
async def get_domains():
    """Get all domains with counts."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT domain, COUNT(*) as heuristic_count, AVG(confidence) as avg_confidence
            FROM heuristics
            GROUP BY domain
            ORDER BY heuristic_count DESC
        """)

        return [dict_from_row(r) for r in cursor.fetchall()]


@router.get("/anomalies")
async def get_anomalies():
    """Detect and return current anomalies."""
    anomalies = []

    with get_db() as conn:
        cursor = conn.cursor()

        # Repeated failures (same node failing multiple times)
        cursor.execute("""
            SELECT node_name, COUNT(*) as fail_count
            FROM node_executions
            WHERE status = 'failed'
              AND created_at > datetime('now', '-1 day')
            GROUP BY node_name
            HAVING fail_count >= 3
        """)
        for row in cursor.fetchall():
            anomalies.append(
                {
                    "type": "repeated_failure",
                    "severity": "error",
                    "message": f"Node '{row['node_name']}' failed {row['fail_count']} times in 24h",
                    "data": {"node_name": row["node_name"], "count": row["fail_count"]},
                }
            )

        # Sudden hot spots
        cursor.execute("""
            SELECT location, SUM(strength) as strength, COUNT(*) as count
            FROM trails
            WHERE created_at > datetime('now', '-1 day')
              AND location NOT IN (
                  SELECT DISTINCT location FROM trails
                  WHERE created_at <= datetime('now', '-1 day')
                    AND created_at > datetime('now', '-7 days')
              )
            GROUP BY location
            HAVING strength > 1.0
            ORDER BY strength DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            anomalies.append(
                {
                    "type": "new_hotspot",
                    "severity": "info",
                    "message": f"New hot spot: {row['location']} ({row['count']} trails)",
                    "data": {"location": row["location"], "strength": row["strength"]},
                }
            )

        # Heuristics being violated frequently
        cursor.execute("""
            SELECT id, rule, times_violated, confidence
            FROM heuristics
            WHERE times_violated > 3 AND confidence > 0.5
            ORDER BY times_violated DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            anomalies.append(
                {
                    "type": "heuristic_violations",
                    "severity": "warning",
                    "message": f"Heuristic violated {row['times_violated']}x: {row['rule'][:50]}...",
                    "data": {
                        "heuristic_id": row["id"],
                        "violations": row["times_violated"],
                    },
                }
            )

        # Stale runs (running for too long)
        cursor.execute("""
            SELECT id, workflow_name, started_at
            FROM workflow_runs
            WHERE status = 'running'
              AND started_at < datetime('now', '-1 hour')
        """)
        for row in cursor.fetchall():
            anomalies.append(
                {
                    "type": "stale_run",
                    "severity": "warning",
                    "message": f"Run #{row['id']} ({row['workflow_name']}) has been running for >1 hour",
                    "data": {"run_id": row["id"]},
                }
            )

    return anomalies


@router.get("/pheromone-trails")
async def get_pheromone_trails(days: int = 7, limit: int = 50):
    """Get pheromone trails aggregated by file path."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                file_path,
                tool_name,
                access_count,
                total_weight,
                first_access,
                last_access
            FROM pheromone_trails
            WHERE last_access > datetime('now', ?)
            ORDER BY total_weight DESC, last_access DESC
            LIMIT ?
        """,
            (f"-{days} days", limit),
        )

        trails = []
        for row in cursor.fetchall():
            trail = dict_from_row(row)
            trails.append(trail)

        return trails


"""
Event Chronicle Endpoints
"""


@router.get("/timeline/events")
async def get_timeline_events(
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(default=50, le=1000),
):
    """
    Get individual events for timeline display from Event Chronicle.

    This endpoint provides events in the format expected by the dashboard's TimelineView component.

    Args:
        event_type: Filter by event type (e.g., 'heuristic_validated', 'task_start')
        source: Filter by source component (e.g., 'record-heuristic.sh', 'orchestrator')
        limit: Maximum number of events to return (max 1000)

    Returns:
        Dictionary with status, events list, and count
    """
    try:
        # Add Open_ELF to path
        import sys
        from pathlib import Path

        current = Path(__file__).resolve()
        for parent in current.parents:
            open_elf_path = parent.parent / "Open_ELF"
            if open_elf_path.exists():
                sys.path.insert(0, str(open_elf_path))
                break

        from timeline_dashboard.event_adapter import get_chronicle_events

        events = get_chronicle_events(
            event_type=event_type,
            source=source,
            limit=limit,
        )

        return {"status": "ok", "events": events, "count": len(events)}

    except ImportError as e:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500, detail=f"Event Chronicle not available: {str(e)}"
        )


@router.get("/timeline/stats")
async def get_timeline_stats():
    """
    Get timeline statistics from Event Chronicle.

    Returns statistics about events in the chronicle.

    Returns:
        Dictionary with total events, event types, sources, and date range
    """
    try:
        # Add Open_ELF to path
        import sys
        from pathlib import Path

        current = Path(__file__).resolve()
        for parent in current.parents:
            open_elf_path = parent.parent / "Open_ELF"
            if open_elf_path.exists():
                sys.path.insert(0, str(open_elf_path))
                break

        from timeline_dashboard.event_adapter import get_chronicle_stats

        stats = get_chronicle_stats()
        return stats

    except ImportError as e:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500, detail=f"Event Chronicle not available: {str(e)}"
        )


@router.get("/timeline/recent")
async def get_recent_events(limit: int = Query(default=10, le=100)):
    """
    Get most recent events for quick overview from Event Chronicle.

    Args:
        limit: Number of recent events to return (max 100)

    Returns:
        List of recent timeline events
    """
    try:
        # Add Open_ELF to path
        import sys
        from pathlib import Path

        current = Path(__file__).resolve()
        for parent in current.parents:
            open_elf_path = parent.parent / "Open_ELF"
            if open_elf_path.exists():
                sys.path.insert(0, str(open_elf_path))
                break

        from timeline_dashboard.event_adapter import get_chronicle_events

        events = get_chronicle_events(limit=limit)
        return events

    except ImportError as e:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500, detail=f"Event Chronicle not available: {str(e)}"
        )


# Event type constants for frontend use
EVENT_TYPES = [
    "task_start",
    "task_end",
    "heuristic_consulted",
    "heuristic_validated",
    "heuristic_violated",
    "failure_recorded",
    "golden_promoted",
    "agent_spawned",
    "workflow_started",
    "session_started",
    "session_ended",
]


@router.get("/timeline/event-types")
async def get_event_types():
    """
    Get available event types.

    Returns list of event types that can be used for filtering.

    Returns:
        List of event type strings
    """
    return EVENT_TYPES
