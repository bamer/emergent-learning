#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Escalation Monitoring Router - Dashboard API for escalation tracking

Provides endpoints for:
- List escalations for CEO and Orchestrator (received/emitted)
- Get escalation details with responses
- Escalation metrics and statistics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

# Import escalation tracker
from Open_ELF.agents.escalation_tracker import (
    get_escalations_by_agent,
    get_escalation_by_id,
)
from Open_ELF.utils.elf_logging import get_logger

logger = get_logger("escalation_monitoring")

router = APIRouter(prefix="/api/v1/monitoring", tags=["escalations"])


@router.get("/escalations/{agent_type}")
async def get_escalations(
    agent_type: str,
    direction: str = Query("received", description="received or emitted"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of escalations"),
):
    """
    Get escalations for a specific agent.

    Args:
        agent_type: Type of agent ('orchestrator' or 'ceo')
        direction: 'received' (sent TO agent) or 'emitted' (sent BY agent)
        limit: Maximum number of escalations to return
    """
    try:
        if agent_type not in ["orchestrator", "ceo"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent_type: {agent_type}. Must be 'orchestrator' or 'ceo'",
            )

        if direction not in ["received", "emitted"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid direction: {direction}. Must be 'received' or 'emitted'",
            )

        escalations = get_escalations_by_agent(
            agent_type=agent_type, direction=direction, limit=limit
        )

        return {
            "status": "ok",
            "agent_type": agent_type,
            "direction": direction,
            "count": len(escalations),
            "escalations": escalations,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting escalations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escalations/detail/{escalation_id}")
async def get_escalation_detail(escalation_id: int):
    """
    Get detailed information about a specific escalation including response.

    Args:
        escalation_id: ID of the escalation
    """
    try:
        escalation = get_escalation_by_id(escalation_id)

        if not escalation:
            raise HTTPException(
                status_code=404, detail=f"Escalation {escalation_id} not found"
            )

        return {
            "status": "ok",
            "escalation": escalation,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting escalation detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escalations/metrics")
async def get_escalation_metrics():
    """Get escalation metrics for all agents."""
    try:
        # Get metrics for CEO
        ceo_received = get_escalations_by_agent("ceo", direction="received", limit=1000)
        ceo_emitted = get_escalations_by_agent("ceo", direction="emitted", limit=1000)

        # Get metrics for Orchestrator
        orchestrator_received = get_escalations_by_agent(
            "orchestrator", direction="received", limit=1000
        )
        orchestrator_emitted = get_escalations_by_agent(
            "orchestrator", direction="emitted", limit=1000
        )

        metrics = {
            "ceo": {
                "received": {
                    "total": len(ceo_received),
                    "pending": sum(1 for e in ceo_received if e["status"] == "pending"),
                    "resolved": sum(
                        1 for e in ceo_received if e["status"] == "resolved"
                    ),
                    "with_response": sum(1 for e in ceo_received if e["has_response"]),
                },
                "emitted": {
                    "total": len(ceo_emitted),
                    "pending": sum(1 for e in ceo_emitted if e["status"] == "pending"),
                    "resolved": sum(
                        1 for e in ceo_emitted if e["status"] == "resolved"
                    ),
                },
            },
            "orchestrator": {
                "received": {
                    "total": len(orchestrator_received),
                    "pending": sum(
                        1 for e in orchestrator_received if e["status"] == "pending"
                    ),
                    "resolved": sum(
                        1 for e in orchestrator_received if e["status"] == "resolved"
                    ),
                    "with_response": sum(
                        1 for e in orchestrator_received if e["has_response"]
                    ),
                },
                "emitted": {
                    "total": len(orchestrator_emitted),
                    "pending": sum(
                        1 for e in orchestrator_emitted if e["status"] == "pending"
                    ),
                    "resolved": sum(
                        1 for e in orchestrator_emitted if e["status"] == "resolved"
                    ),
                },
            },
        }

        return {
            "status": "ok",
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Error getting escalation metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
