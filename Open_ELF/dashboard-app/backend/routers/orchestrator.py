"""
Orchestrator Router - Dashboard API Integration with Enhanced Event Bridge

This router integrates the dashboard backend with the enhanced event bridge orchestrator API.
All agent and mission requests are routed through the central orchestrator.
"""

import json
import requests
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orchestrator", tags=["orchestrator"])

# Enhanced Event Bridge Orchestrator API
ORCHESTRATOR_API_URL = "http://localhost:9999"


class OrchestratorRequest(BaseModel):
    """Request model for orchestrator API calls."""

    component: str
    request_type: str
    data: Dict[str, Any]
    priority: int = 1


class OrchestratorResponse(BaseModel):
    """Response model from orchestrator API."""

    request_id: str
    response_type: str
    data: Dict[str, Any]
    timestamp: str
    confidence: float


class MissionSubmission(BaseModel):
    """Mission submission model."""

    agent_type: str
    mission: str
    task_id: Optional[str] = None
    source: str = "dashboard"


class HealthCheck(BaseModel):
    """Health check model."""

    component: str


async def call_orchestrator(request: OrchestratorRequest) -> OrchestratorResponse:
    """Make a request to the orchestrator API."""
    try:
        response = requests.post(
            f"{ORCHESTRATOR_API_URL}/api/v1/ask",
            json={
                "component": request.component,
                "request_type": request.request_type,
                "data": request.data,
                "priority": request.priority,
            },
            timeout=30,
        )

        if response.status_code == 200:
            return OrchestratorResponse(**response.json())
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Orchestrator API error: {response.text}",
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to orchestrator: {e}",
        )


async def submit_mission(mission: MissionSubmission) -> OrchestratorResponse:
    """Submit a mission to the orchestrator."""
    try:
        response = requests.post(
            f"{ORCHESTRATOR_API_URL}/api/v1/mission",
            json=mission.dict(),
            timeout=30,
        )

        if response.status_code == 200:
            return OrchestratorResponse(**response.json())
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Mission submission error: {response.text}",
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot submit mission to orchestrator: {e}",
        )


@router.get("/health/{component}")
async def get_health(component: str):
    """Get health status of a component via orchestrator."""
    try:
        response = requests.get(
            f"{ORCHESTRATOR_API_URL}/api/v1/health/{component}",
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Health check error: {response.text}",
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to orchestrator for health check: {e}",
        )


@router.post("/ask")
async def ask_orchestrator(request: OrchestratorRequest):
    """Ask the orchestrator for a decision or coordination."""
    return await call_orchestrator(request)


@router.post("/mission")
async def submit_mission_endpoint(mission: MissionSubmission):
    """Submit a mission to the orchestrator."""
    return await submit_mission(mission)


@router.get("/status")
async def get_orchestrator_status():
    """Get orchestrator status."""
    try:
        response = requests.get(
            f"{ORCHESTRATOR_API_URL}/status",
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Status check error: {response.text}",
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to orchestrator: {e}",
        )


@router.get("/agents")
async def get_available_agents():
    """Get list of available agents from orchestrator."""
    # Ask orchestrator for available agents
    response = await call_orchestrator(
        OrchestratorRequest(
            component="dashboard",
            request_type="coordination",
            data={"action": "list_agents"},
        )
    )

    return {
        "agents": response.data.get("agents", []),
        "status": "success",
    }


@router.post("/agents/{agent_type}/run")
async def run_agent(agent_type: str, mission: MissionSubmission):
    """Run an agent via orchestrator."""
    mission.agent_type = agent_type
    return await submit_mission(mission)


# Register this router in the main app
# Add this line to main.py:
# from .routers.orchestrator import router as orchestrator_router
# app.include_router(orchestrator_router)
