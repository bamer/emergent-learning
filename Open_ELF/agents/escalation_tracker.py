#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Escalation Tracker - Track escalations and responses in database

This module provides functions to:
- Create escalation records when escalations are created
- Update escalation records with responses
- Query escalations by agent (received vs emitted)
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import centralized logger
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_error

    logger = get_logger("escalation_tracker")
except ImportError:
    import logging

    logger = logging.getLogger("escalation_tracker")

# Database path
DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"


def get_db_connection():
    """Get database connection with proper settings."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def create_escalation(
    source_agent: str,
    target_agent: str,
    escalation_file_path: str,
    escalation_content: str,
    severity: Optional[str] = None,
) -> int:
    """
    Create a new escalation record.

    Args:
        source_agent: Agent sending the escalation (e.g., 'sentinel', 'orchestrator')
        target_agent: Agent receiving the escalation (e.g., 'orchestrator', 'ceo')
        escalation_file_path: Path to the escalation markdown file
        escalation_content: Full content of the escalation
        severity: Severity level (optional)

    Returns:
        ID of the created escalation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO escalations (
                source_agent, target_agent, escalation_file_path,
                escalation_content, severity, status, created_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """,
            (
                source_agent,
                target_agent,
                escalation_file_path,
                escalation_content,
                severity,
                datetime.now().isoformat(),
            ),
        )

        escalation_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(
            f"✅ Created escalation #{escalation_id}: {source_agent} → {target_agent}"
        )
        return escalation_id

    except Exception as e:
        logger.error(f"❌ Error creating escalation: {e}")
        raise


def update_escalation_response(
    escalation_id: int,
    response_content: str,
    response_agent: str,
) -> bool:
    """
    Update an escalation with a response.

    Args:
        escalation_id: ID of the escalation
        response_content: The response from the agent
        response_agent: Agent that provided the response

    Returns:
        True if successful
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE escalations
            SET response_content = ?,
                response_agent = ?,
                status = 'resolved',
                responded_at = ?
            WHERE id = ?
        """,
            (
                response_content,
                response_agent,
                datetime.now().isoformat(),
                escalation_id,
            ),
        )

        conn.commit()
        conn.close()

        logger.info(
            f"✅ Updated escalation #{escalation_id} with response from {response_agent}"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Error updating escalation response: {e}")
        return False


def get_escalations_by_agent(
    agent_type: str,
    direction: str = "received",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get escalations for a specific agent.

    Args:
        agent_type: Type of agent ('orchestrator' or 'ceo')
        direction: 'received' (sent TO agent) or 'emitted' (sent BY agent)
        limit: Maximum number of escalations to return

    Returns:
        List of escalation dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if direction == "received":
            # Escalations sent TO this agent
            cursor.execute(
                """
                SELECT id, source_agent, target_agent, escalation_file_path,
                       escalation_content, response_content, response_agent,
                       status, severity, created_at, responded_at
                FROM escalations
                WHERE target_agent = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (agent_type, limit),
            )
        else:
            # Escalations sent BY this agent
            cursor.execute(
                """
                SELECT id, source_agent, target_agent, escalation_file_path,
                       escalation_content, response_content, response_agent,
                       status, severity, created_at, responded_at
                FROM escalations
                WHERE source_agent = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (agent_type, limit),
            )

        rows = cursor.fetchall()
        conn.close()

        escalations = []
        for row in rows:
            escalations.append(
                {
                    "id": row["id"],
                    "source_agent": row["source_agent"],
                    "target_agent": row["target_agent"],
                    "escalation_file_path": row["escalation_file_path"],
                    "escalation_content": row["escalation_content"],
                    "response_content": row["response_content"],
                    "response_agent": row["response_agent"],
                    "status": row["status"],
                    "severity": row["severity"],
                    "created_at": row["created_at"],
                    "responded_at": row["responded_at"],
                    "has_response": bool(row["response_content"]),
                }
            )

        return escalations

    except Exception as e:
        logger.error(f"❌ Error getting escalations: {e}")
        return []


def get_escalation_by_id(escalation_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific escalation by ID.

    Args:
        escalation_id: ID of the escalation

    Returns:
        Escalation dictionary or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, source_agent, target_agent, escalation_file_path,
                   escalation_content, response_content, response_agent,
                   status, severity, created_at, responded_at
            FROM escalations
            WHERE id = ?
        """,
            (escalation_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "source_agent": row["source_agent"],
                "target_agent": row["target_agent"],
                "escalation_file_path": row["escalation_file_path"],
                "escalation_content": row["escalation_content"],
                "response_content": row["response_content"],
                "response_agent": row["response_agent"],
                "status": row["status"],
                "severity": row["severity"],
                "created_at": row["created_at"],
                "responded_at": row["responded_at"],
                "has_response": bool(row["response_content"]),
            }
        return None

    except Exception as e:
        logger.error(f"❌ Error getting escalation #{escalation_id}: {e}")
        return None


if __name__ == "__main__":
    # Test the escalation tracker
    print("Testing Escalation Tracker...")

    # Create a test escalation
    escalation_id = create_escalation(
        source_agent="sentinel",
        target_agent="ceo",
        escalation_file_path="/test/path.md",
        escalation_content="Test escalation content",
        severity="high",
    )
    print(f"Created escalation #{escalation_id}")

    # Update with response
    update_escalation_response(
        escalation_id=escalation_id,
        response_content="Test response from CEO",
        response_agent="ceo",
    )
    print(f"Updated escalation #{escalation_id} with response")

    # Query escalations
    received = get_escalations_by_agent("ceo", direction="received")
    print(f"Found {len(received)} received escalations for CEO")

    emitted = get_escalations_by_agent("ceo", direction="emitted")
    print(f"Found {len(emitted)} emitted escalations from CEO")

    # Get single escalation
    escalation = get_escalation_by_id(escalation_id)
    print(f"Retrieved escalation: {escalation['status']}")
