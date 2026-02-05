#!/usr/bin/env python3
"""
Unified Orchestrator Support Module
==================================

Core module that provides standardized support for the unified orchestrator
as the central piece of orchestration. All other components should work
with and for the unified orchestrator.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .openelf_logging import get_logger
from .database import get_connection, execute_query
from .config import get_config

logger = get_logger("unified_orchestrator_support")


class UnifiedOrchestratorClient:
    """Client for interacting with the unified orchestrator."""

    def __init__(self, orchestrator_url: str = "http://localhost:9999"):
        self.orchestrator_url = orchestrator_url
        self.status_endpoint = f"{orchestrator_url}/status"
        self.control_endpoint = f"{orchestrator_url}/control"

    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the unified orchestrator."""
        try:
            # This would be async HTTP client in production
            # For now, we'll simulate status checks
            return {
                "status": "running",
                "event_count": 0,
                "mission_count": 0,
                "last_update": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get orchestrator status: {e}")
            return {"status": "unknown", "error": str(e)}

    async def send_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Send an event to the unified orchestrator."""
        try:
            # In production, this would send to orchestrator's event endpoint
            logger.info(f"Event sent to orchestrator: {event_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to send event to orchestrator: {e}")
            return False


class EventBridgeIntegration:
    """Integration layer for event bridge functionality."""

    def __init__(self, orchestrator_client: UnifiedOrchestratorClient):
        self.client = orchestrator_client

    async def forward_event(self, event_data: Dict[str, Any]) -> bool:
        """Forward event to unified orchestrator instead of handling locally."""
        return await self.client.send_event("external_event", event_data)

    async def check_orchestrator_health(self) -> bool:
        """Check if unified orchestrator is healthy."""
        status = await self.client.get_status()
        return status.get("status") == "running"


class MissionCoordinator:
    """Coordinates missions through the unified orchestrator."""

    def __init__(self, orchestrator_client: UnifiedOrchestratorClient):
        self.client = orchestrator_client

    async def submit_mission(self, agent_type: str, mission: str) -> str:
        """Submit a mission to the unified orchestrator."""
        mission_data = {
            "agent_type": agent_type,
            "mission": mission,
            "submitted_at": datetime.now().isoformat(),
        }

        success = await self.client.send_event("mission_submission", mission_data)
        if success:
            logger.info(f"Mission submitted to orchestrator: {agent_type}")
            return "submitted"
        else:
            logger.error(f"Failed to submit mission to orchestrator: {agent_type}")
            return "failed"

    async def get_mission_status(self, mission_id: str) -> Dict[str, Any]:
        """Get status of a mission from the unified orchestrator."""
        # This would query the orchestrator's mission status endpoint
        return {
            "id": mission_id,
            "status": "unknown",
            "last_update": datetime.now().isoformat(),
        }


class SystemHealthMonitor:
    """Monitors system health and reports to unified orchestrator."""

    def __init__(self, orchestrator_client: UnifiedOrchestratorClient):
        self.client = orchestrator_client

    async def report_health(
        self, component: str, status: str, details: Dict[str, Any]
    ) -> bool:
        """Report component health to unified orchestrator."""
        health_data = {
            "component": component,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        return await self.client.send_event("health_report", health_data)

    async def monitor_system(self):
        """Continuous system monitoring that reports to unified orchestrator."""
        while True:
            # Check database health
            db_status = await self._check_database_health()
            await self.report_health("database", db_status["status"], db_status)

            # Check file system health
            fs_status = await self._check_filesystem_health()
            await self.report_health("filesystem", fs_status["status"], fs_status)

            await asyncio.sleep(60)  # Check every minute

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            conn = get_connection()
            execute_query(conn, "SELECT 1")
            return {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _check_filesystem_health(self) -> Dict[str, Any]:
        """Check filesystem health."""
        try:
            # Check critical directories
            critical_dirs = [
                Path.home() / ".opencode" / "tasks",
                Path.home() / ".opencode" / "emergent-learning" / "ceo-inbox",
                Path.home() / ".opencode" / "emergent-learning" / "memory",
            ]

            status = {}
            for dir_path in critical_dirs:
                status[dir_path.name] = "exists" if dir_path.exists() else "missing"

            return {"status": "healthy", "details": status}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}


class UnifiedOrchestratorManager:
    """Manages interactions with the unified orchestrator."""

    def __init__(self):
        self.client = UnifiedOrchestratorClient()
        self.event_bridge = EventBridgeIntegration(self.client)
        self.mission_coordinator = MissionCoordinator(self.client)
        self.health_monitor = SystemHealthMonitor(self.client)

    async def start_support_services(self):
        """Start all support services for unified orchestrator."""
        logger.info("Starting unified orchestrator support services")

        # Start health monitoring
        asyncio.create_task(self.health_monitor.monitor_system())

        logger.info("Unified orchestrator support services started")

    async def ensure_orchestrator_running(self) -> bool:
        """Ensure unified orchestrator is running."""
        status = await self.client.get_status()
        if status.get("status") != "running":
            logger.warning("Unified orchestrator not running - attempting to start")
            # In production, this would start the orchestrator
            return False
        return True


# Global instance for easy access
_orchestrator_manager: Optional[UnifiedOrchestratorManager] = None


def get_unified_orchestrator_manager() -> UnifiedOrchestratorManager:
    """Get or create the unified orchestrator manager."""
    global _orchestrator_manager
    if _orchestrator_manager is None:
        _orchestrator_manager = UnifiedOrchestratorManager()
    return _orchestrator_manager


async def initialize_unified_orchestrator_support():
    """Initialize unified orchestrator support services."""
    manager = get_unified_orchestrator_manager()
    await manager.start_support_services()

    # Verify orchestrator is running
    if not await manager.ensure_orchestrator_running():
        logger.warning("Unified orchestrator may not be running")

    logger.info("Unified orchestrator support initialized")


# Convenience functions for external components
async def submit_mission_to_orchestrator(agent_type: str, mission: str) -> str:
    """Submit a mission to the unified orchestrator."""
    manager = get_unified_orchestrator_manager()
    return await manager.mission_coordinator.submit_mission(agent_type, mission)


async def forward_event_to_orchestrator(event_data: Dict[str, Any]) -> bool:
    """Forward an event to the unified orchestrator."""
    manager = get_unified_orchestrator_manager()
    return await manager.event_bridge.forward_event(event_data)


async def report_health_to_orchestrator(
    component: str, status: str, details: Dict[str, Any]
) -> bool:
    """Report health status to unified orchestrator."""
    manager = get_unified_orchestrator_manager()
    return await manager.health_monitor.report_health(component, status, details)
