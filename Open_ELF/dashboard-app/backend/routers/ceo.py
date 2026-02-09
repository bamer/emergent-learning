"""
CEO Monitoring Router - Dashboard API Integration with CEO Inbox

This router provides endpoints for:
- CEO inbox status and metrics
- Pending, active, and archived CEO items
- CEO Inbox Monitor autonomous processing status
- CEO escalation tracking

Added in v0.5.3 - Refactoring alignment (2026-02-09)
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_error, log_warning

    logger = get_logger("ceo_monitoring")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ceo_monitoring")


router = APIRouter(prefix="/api/v1/ceo", tags=["ceo"])

# Paths
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
CEO_INBOX_DIR = ELF_DIR / "ceo-inbox"
CEO_ARCHIVE_DIR = CEO_INBOX_DIR / "archive"

# Ensure directories exist
CEO_INBOX_DIR.mkdir(exist_ok=True)
CEO_ARCHIVE_DIR.mkdir(exist_ok=True)


# ============================================================================
# Data Models
# ============================================================================


class CeoStatus(BaseModel):
    """CEO status response."""

    status: str  # active, idle, overloaded
    pending_count: int
    inbox_path: str


class CeoMetrics(BaseModel):
    """CEO inbox metrics."""

    pending: int
    critical: int
    high: int
    medium: int
    low: int
    resolved: int
    archived: int
    total: int


class CeoItem(BaseModel):
    """CEO inbox item."""

    filename: str
    title: str
    priority: str  # Critical, High, Medium, Low
    status: str  # pending, acknowledged, resolved
    date: Optional[str]
    summary: str
    path: str
    created_at: str


class CeoAnalysis(BaseModel):
    """CEO analysis status."""

    status: str  # active, idle, overloaded, error
    analysis: str
    actions: List[str]
    patterns: List[str]


class CeoCycle(BaseModel):
    """CEO processing cycle data."""

    timestamp: str
    items_processed: int
    decisions_made: List[str]
    actions_taken: List[str]


class CeoMonitorStatus(BaseModel):
    """CEO Inbox Monitor autonomous processing status."""

    running: bool
    last_check: Optional[str]
    items_processed_today: int
    escalations_archived: int
    automation_enabled: bool
    cycle_count: int


# ============================================================================
# Parsing Functions
# ============================================================================


def parse_ceo_item(file_path: Path) -> Optional[Dict[str, Any]]:
    """Parse a CEO inbox markdown file.

    Extracts frontmatter (title, priority, status, date, summary) and content.
    """
    try:
        content = file_path.read_text()

        # Extract frontmatter between --- markers
        frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)

        frontmatter = {}
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            # Parse key: value pairs
            for line in frontmatter_text.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()

        # Extract summary/content
        summary_match = re.search(r"---\n(.*)", content, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""

        return {
            "filename": file_path.name,
            "filepath": str(file_path.relative_to(ELF_DIR)),
            "title": frontmatter.get("title", file_path.stem),
            "priority": frontmatter.get("priority", "Medium").capitalize(),
            "status": frontmatter.get("status", "pending").lower(),
            "date": frontmatter.get("date"),
            "summary": summary[:500] + "..." if len(summary) > 500 else summary,
            "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "path": str(file_path),
        }
    except Exception as e:
        logger.error(f"Error parsing CEO item {file_path}: {e}")
        return None


def calculate_ceo_metrics() -> CeoMetrics:
    """Calculate CEO inbox metrics from files."""
    metrics = {
        "pending": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "resolved": 0,
        "archived": 0,
        "total": 0,
    }

    # Process pending items (not in archive)
    for file in CEO_INBOX_DIR.glob("escalation_*.md"):
        if file.parent == CEO_ARCHIVE_DIR:
            metrics["archived"] += 1
            continue

        item = parse_ceo_item(file)
        if item:
            metrics["total"] += 1
            metrics["pending"] += 1

            priority = item.get("priority", "Medium").lower()
            if priority == "critical":
                metrics["critical"] += 1
            elif priority == "high":
                metrics["high"] += 1
            elif priority == "medium":
                metrics["medium"] += 1
            elif priority == "low":
                metrics["low"] += 1

            if item.get("status") == "resolved":
                metrics["resolved"] += 1

    return CeoMetrics(**metrics)


def get_ceo_monitor_status() -> Dict[str, Any]:
    """Get CEO Inbox Monitor autonomous processing status."""
    # Read from coordination files
    monitor_log = ELF_DIR / ".coordination" / "ceo-monitor.log"

    status = {
        "running": False,
        "last_check": None,
        "items_processed_today": 0,
        "escalations_archived": 0,
        "automation_enabled": False,
        "cycle_count": 0,
    }

    # Check for running process
    try:
        import subprocess

        result = subprocess.run(
            ["pgrep", "-f", "ceo_inbox_monitor.py"], capture_output=True, text=True
        )
        status["running"] = bool(result.stdout.strip())
    except:
        pass

    # Read monitor log if exists
    if monitor_log.exists():
        try:
            log_content = monitor_log.read_text()
            # Extract last check timestamp
            last_check_match = re.search(
                r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", log_content[-500:]
            )
            if last_check_match:
                status["last_check"] = last_check_match.group(1)

            # Count cycle markers
            status["cycle_count"] = log_content.count("Cycle #")

            # Extract metrics from log
            items_match = re.search(
                r"items_processed_today[:\s]+(\d+)", log_content[-200:]
            )
            if items_match:
                status["items_processed_today"] = int(items_match.group(1))

            archived_match = re.search(
                r"escalations_archived[:\s]+(\d+)", log_content[-200:]
            )
            if archived_match:
                status["escalations_archived"] = int(archived_match.group(1))

            status["automation_enabled"] = True  # Enabled if log file exists
        except Exception as e:
            logger.error(f"Error reading CEO monitor log: {e}")

    return status


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/status", response_model=CeoStatus)
async def get_ceo_status():
    """Get CEO inbox status (active/idle/overloaded)."""
    try:
        # Count pending items
        pending_items = [
            f
            for f in CEO_INBOX_DIR.glob("escalation_*.md")
            if f.parent != CEO_ARCHIVE_DIR
        ]
        pending_count = len(pending_items)

        # Determine status based on load
        if pending_count > 10:
            status = "overloaded"
        elif pending_count > 0:
            status = "active"
        else:
            status = "idle"

        return CeoStatus(
            status=status, pending_count=pending_count, inbox_path=str(CEO_INBOX_DIR)
        )

    except Exception as e:
        logger.error(f"Error getting CEO status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=CeoMetrics)
async def get_ceo_metrics():
    """Get CEO inbox metrics (counts by priority and status)."""
    try:
        return calculate_ceo_metrics()

    except Exception as e:
        logger.error(f"Error calculating CEO metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items", response_model=List[CeoItem])
async def get_ceo_items(
    status: Optional[str] = Query(
        None, description="Filter by status: pending, acknowledged, resolved"
    ),
    priority: Optional[str] = Query(
        None, description="Filter by priority: Critical, High, Medium, Low"
    ),
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of items to return"
    ),
):
    """List CEO inbox items with optional filtering."""
    try:
        items = []

        for file in CEO_INBOX_DIR.glob("escalation_*.md"):
            # Skip archive directory by default
            if file.parent == CEO_ARCHIVE_DIR:
                continue

            item = parse_ceo_item(file)
            if not item:
                continue

            # Apply filters
            if status and item.get("status") != status:
                continue
            if priority and item.get("priority") != priority:
                continue

            items.append(item)

        # Sort by date (newest first) and limit
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        items = items[:limit]

        return [CeoItem(**item) for item in items]

    except Exception as e:
        logger.error(f"Error getting CEO items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{item_id}")
async def get_ceo_item(item_id: str):
    """Get a specific CEO item by filename or ID."""
    try:
        # Try to find by filename
        if not item_id.endswith(".md"):
            item_id = f"escalation_{item_id}.md"

        # Search in inbox and archive
        for search_dir in [CEO_INBOX_DIR, CEO_ARCHIVE_DIR]:
            file_path = search_dir / item_id
            if file_path.exists():
                item = parse_ceo_item(file_path)
                if item:
                    # Read full content
                    content = file_path.read_text()
                    item["content"] = content
                    return item

        raise HTTPException(status_code=404, detail=f"CEO item {item_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CEO item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/status", response_model=CeoMonitorStatus)
async def get_ceo_monitor_status():
    """Get CEO Inbox Monitor autonomous processing status."""
    try:
        status = get_ceo_monitor_status()
        return CeoMonitorStatus(**status)

    except Exception as e:
        logger.error(f"Error getting CEO monitor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis", response_model=CeoAnalysis)
async def get_ceo_analysis():
    """Get CEO analysis and recommendations based on inbox state."""
    try:
        metrics = calculate_ceo_metrics()
        monitor_status = get_ceo_monitor_status()

        # Determine analysis status
        if metrics.pending > 10:
            status = "overloaded"
            analysis = f"CEO inbox contains {metrics.pending} pending items exceeding threshold. Immediate attention required to prevent escalation backlog."
            actions = [
                "Review and resolve Critical priority items first",
                "Consider increasing CEO Inbox Monitor processing frequency",
                "Escalate to human for manual intervention if needed",
            ]
            patterns = [
                "Sustained high escalation rate",
                "Potential system crisis forming",
            ]
        elif metrics.pending > 5:
            status = "active"
            analysis = f"CEO inbox has {metrics.pending} pending items. Normal operational level, timely processing recommended."
            actions = [
                "Process High and Critical priority items",
                "Monitor for accumulation trends",
            ]
            patterns = ["Normal escalation flow"]
        elif metrics.pending > 0:
            status = "active"
            analysis = f"CEO inbox has {metrics.pending} pending items. Low volume, processing on track."
            actions = ["Process remaining items at scheduled intervals"]
            patterns = ["Healthy escalation flow"]
        else:
            status = "idle"
            analysis = "CEO inbox is empty. System operating normally with no pending escalations."
            actions = [
                "Continue autonomous monitoring",
                "Monitor for unusual escalation patterns",
            ]
            patterns = ["System stable", "No escalations pending"]

        # Add automation status to actions
        if monitor_status["running"]:
            actions.append(
                f"CEO Inbox Monitor automation is active (cycle #{monitor_status['cycle_count']})"
            )
        else:
            actions.append(
                "CEO Inbox Monitor automation is NOT running - manual processing required"
            )

        return CeoAnalysis(
            status=status, analysis=analysis, actions=actions, patterns=patterns
        )

    except Exception as e:
        logger.error(f"Error getting CEO analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cycles", response_model=List[CeoCycle])
async def get_ceo_cycles(limit: int = Query(10, ge=1, le=50)):
    """Get recent CEO processing cycles from monitor log."""
    try:
        monitor_log = ELF_DIR / ".coordination" / "ceo-monitor.log"
        cycles = []

        if not monitor_log.exists():
            return []

        log_content = monitor_log.read_text()

        # Extract cycle information
        # Pattern: Cycle #N - YYYY-MM-DD HH:MM:SS
        cycle_pattern = re.compile(
            r"Cycle #(\d+)\s+-\s+(.+?)\n(.*?)(?=\nCycle #|\Z)", re.DOTALL
        )
        for match in cycle_pattern.finditer(log_content):
            cycle_num = int(match.group(1))
            timestamp = match.group(2)
            cycle_content = match.group(3)

            # Parse cycle content for decisions and actions
            decisions = []
            actions = []
            items_processed = 0

            if "Processing escalation:" in cycle_content:
                items_processed += 1
            if "Decision:" in cycle_content:
                for decision_match in re.finditer(
                    r"Decision:\s*(.+?)(?:\n|$)", cycle_content
                ):
                    decisions.append(decision_match.group(1).strip())
            if "Action:" in cycle_content or "Archived:" in cycle_content:
                for action_match in re.finditer(
                    r"(?:Action|Archived):\s*(.+?)(?:\n|$)", cycle_content
                ):
                    actions.append(action_match.group(1).strip())

            cycles.append(
                {
                    "timestamp": timestamp,
                    "items_processed": items_processed,
                    "decisions_made": decisions,
                    "actions_taken": actions,
                }
            )

        # Return most recent cycles
        cycles.reverse()
        cycles = cycles[:limit]

        return [CeoCycle(**cycle) for cycle in cycles]

    except Exception as e:
        logger.error(f"Error getting CEO cycles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inbox")
async def get_ceo_inbox_summary():
    """Get comprehensive CEO inbox summary."""
    try:
        metrics = calculate_ceo_metrics()
        status = await get_ceo_status()

        # Get recent items (pending only, top 5)
        pending_items = await get_ceo_items(status="pending", limit=5)

        monitor_status = get_ceo_monitor_status()

        # Get latest cycle if available
        cycles = await get_ceo_cycles(limit=1)
        latest_cycle = cycles[0] if cycles else None

        return {
            "status": status.dict(),
            "metrics": metrics.dict(),
            "pending_items": pending_items,
            "monitor_status": monitor_status,
            "latest_cycle": latest_cycle.dict() if latest_cycle else None,
            "inbox_path": str(CEO_INBOX_DIR),
            "archive_path": str(CEO_ARCHIVE_DIR),
        }

    except Exception as e:
        logger.error(f"Error getting CEO inbox summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
