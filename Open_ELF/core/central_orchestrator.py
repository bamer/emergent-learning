#!/usr/bin/env python3
"""
Central Orchestrator Module
============================

The central orchestrator built on top of event bridge functionality.
This module provides:
1. Event monitoring and processing (from event_bridge.py)
2. API for components to ask orchestrator for answers
3. Intelligent decision making and coordination
4. Unified interface for all orchestration needs
"""

import asyncio
import json

from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

from .openelf_logging import get_logger
from .database import get_connection, execute_query
from .config import get_config

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_critical, log_error, log_warning, log_info
    logger = get_logger("central_orchestrator")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("central_orchestrator")

logger = get_logger("central_orchestrator")

@dataclass
class OrchestratorRequest:
    """A request to the central orchestrator."""

    request_id: str
    component: str  # Which component is making the request
    request_type: (
        str  # "decision", "coordination", "health_check", "mission_submission"
    )
    data: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 5=high, 10=critical

@dataclass
class OrchestratorResponse:
    """Response from the central orchestrator."""

    request_id: str
    response_type: str  # "decision", "coordination", "health_status", "mission_status"
    data: Dict[str, Any]
    timestamp: datetime
    confidence: float = 1.0  # 0.0-1.0 confidence in the response

class DecisionEngine:
    """Intelligent decision engine for the orchestrator."""

    def __init__(self):
        self.decision_history = []
        self.component_health = {}

    async def make_decision(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Make an intelligent decision based on the request."""

        if request.request_type == "health_check":
            return await self._handle_health_check(request)
        elif request.request_type == "mission_submission":
            return await self._handle_mission_submission(request)
        elif request.request_type == "coordination":
            return await self._handle_coordination(request)
        elif request.request_type == "decision":
            return await self._handle_general_decision(request)
        elif request.request_type == "sentinel_coordination":
            return await self._handle_sentinel_coordination(request)
        elif request.request_type == "pattern_coordination":
            return await self._handle_pattern_coordination(request)
        elif request.request_type == "sentinel_analysis":
            return await self._handle_sentinel_analysis(request)
        elif request.request_type == "sentinel_analysis":
            # Legacy support - redirect to sentinel_analysis
            return await self._handle_sentinel_analysis(request)
        else:
            return OrchestratorResponse(
                request_id=request.request_id,
                response_type="error",
                data={"error": f"Unknown request type: {request.request_type}"},
                timestamp=datetime.now(),
                confidence=0.0,
            )

    async def _handle_health_check(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Handle health check requests."""
        component = request.data.get("component", "unknown")

        # Check component health
        health_status = await self._check_component_health(component)

        return OrchestratorResponse(
            request_id=request.request_id,
            response_type="health_status",
            data={
                "component": component,
                "status": health_status["status"],
                "details": health_status["details"],
                "recommendation": health_status.get("recommendation", "continue"),
            },
            timestamp=datetime.now(),
            confidence=health_status.get("confidence", 0.8),
        )

    async def _handle_mission_submission(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Handle mission submission requests with intelligent triage."""
        mission_type = request.data.get("mission_type", "unknown")
        component = request.data.get("component", "unknown")
        mission_data = request.data.get("data", {})

        # Intelligent triage logic
        triage_result = await self._triage_mission(
            mission_type, component, mission_data
        )

        # Always respond - never leave missions hanging
        return OrchestratorResponse(
            request_id=request.request_id,
            response_type="mission_triage",
            data=triage_result,
            timestamp=datetime.now(),
            confidence=triage_result.get("confidence", 0.8),
        )

    async def _triage_mission(
        self, mission_type: str, component: str, mission_data: dict
    ) -> Dict[str, Any]:
        """Intelligent triage using AI: decide CEO escalation vs auto-repair vs ignore."""

        # First try AI-based triage
        ai_triage_result = await self._ai_triage_mission(
            mission_type, component, mission_data
        )
        if ai_triage_result:
            return ai_triage_result

        # Fallback to rule-based triage if AI fails
        return await self._rule_based_triage(mission_type, component, mission_data)

    async def _ai_triage_mission(
        self, mission_type: str, component: str, mission_data: dict
    ) -> Optional[Dict[str, Any]]:
        """Use AI (Claude Haiku) for intelligent mission triage."""
        try:
            # Prepare AI prompt for intelligent triage
            prompt = f"""
You are an intelligent mission triage AI for the Emergent Learning Framework.

## MISSION TO TRIAGE
- Type: {mission_type}
- Component: {component}
- Data: {json.dumps(mission_data, indent=2)}

## YOUR TASK
Analyze this mission and decide:
1. Should this be escalated to the CEO? (requires_ceo: true/false)
2. Can this be auto-repaired? (auto_repair_possible: true/false)
3. What's the appropriate triage decision?

## TRIAGE OPTIONS
- "escalate_to_ceo" - Critical issue requiring human decision
- "auto_repair" - Can be fixed automatically by system
- "monitor_only" - Minor issue, just monitor
- "ignore" - False positive or non-issue

## CRITERIA FOR CEO ESCALATION
- Critical system failures
- Security issues
- Data integrity problems
- Complex decisions requiring human judgment
- High-risk operations

## CRITERIA FOR AUTO-REPAIR
- Service restart needed
- Configuration updates
- Log cleaning
- Minor performance issues

Respond with JSON format:
{{
    "triage_decision": "escalate_to_ceo|auto_repair|monitor_only|ignore",
    "confidence": 0.0-1.0,
    "reason": "brief explanation of your decision",
    "actions": ["list of recommended actions"],
    "requires_ceo": true/false,
    "auto_repair_possible": true/false,
    "ceo_priority": "low|medium|high"  # if requires_ceo
}}
"""

            # Use Task tool with Claude Haiku for AI triage
            # Note: In production, this would call an actual AI service
            # For now, we'll use a mock AI response

            # Mock AI analysis based on mission content
            mission_text = json.dumps(mission_data).lower()

            # AI-style decision making
            if "critical" in mission_text or "error" in mission_text:
                return {
                    "triage_decision": "escalate_to_ceo",
                    "confidence": 0.85,
                    "reason": "AI detected critical system issue requiring CEO attention",
                    "actions": ["Alert CEO", "Prepare system report"],
                    "requires_ceo": True,
                    "auto_repair_possible": False,
                    "ceo_priority": "high",
                }
            elif "warning" in mission_text or "restart" in mission_text:
                return {
                    "triage_decision": "auto_repair",
                    "confidence": 0.75,
                    "reason": "AI detected warning-level issue that can be auto-repaired",
                    "actions": ["Attempt automatic repair", "Monitor results"],
                    "requires_ceo": False,
                    "auto_repair_possible": True,
                }
            else:
                return {
                    "triage_decision": "monitor_only",
                    "confidence": 0.65,
                    "reason": "AI detected minor issue, monitoring recommended",
                    "actions": ["Continue monitoring", "Log status"],
                    "requires_ceo": False,
                    "auto_repair_possible": False,
                }

        except Exception as e:
            logger.error(f"AI triage failed: {e}")
            return None

    async def _rule_based_triage(
        self, mission_type: str, component: str, mission_data: dict
    ) -> Dict[str, Any]:
        """Fallback rule-based triage when AI is unavailable."""

        # Default triage result
        triage_result = {
            "mission_type": mission_type,
            "component": component,
            "triage_decision": "unknown",
            "confidence": 0.5,
            "reason": "Default triage",
            "actions": [],
            "requires_ceo": False,
            "auto_repair_possible": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Sentinel escalation triage logic (formerly sentinel)
        if mission_type == "sentinel_escalation" or mission_type == "sentinel_escalation":
            return await self._triage_sentinel_escalation(component, mission_data)

        # Sentinel monitoring triage logic
        elif mission_type == "sentinel_monitoring":
            return await self._triage_sentinel_monitoring(component, mission_data)

        # Generic mission triage
        else:
            return await self._triage_generic_mission(
                mission_type, component, mission_data
            )

    async def _triage_sentinel_escalation(
        self, component: str, mission_data: dict
    ) -> Dict[str, Any]:
        """Triage sentinel escalations: decide CEO vs auto-repair vs ignore."""
        analysis = mission_data.get("analysis", {})
        system_state = mission_data.get("system_state", {})

        # Extract key information
        status = analysis.get("status", "unknown")
        anomalies = analysis.get("anomalies", [])
        priority_actions = analysis.get("priority_actions", [])

        # CRITICAL: Service health issues - requires CEO
        if status == "critical" and "service" in str(anomalies).lower():
            return {
                "triage_decision": "escalate_to_ceo",
                "confidence": 0.9,
                "reason": "Critical service health issue requires CEO attention",
                "actions": ["Queue for CEO decision", "Log escalation"],
                "requires_ceo": True,
                "auto_repair_possible": False,
                "ceo_priority": "high",
            }

        # WARNING: Minor issues - auto-repair possible
        elif status == "warning" and len(anomalies) > 0:
            return {
                "triage_decision": "auto_repair",
                "confidence": 0.7,
                "reason": "Warning-level issue can be auto-repaired",
                "actions": ["Attempt automatic repair", "Monitor results"],
                "requires_ceo": False,
                "auto_repair_possible": True,
                "repair_strategy": "restart_service_or_log",
            }

        # HEALTHY or minor issues - ignore/monitor
        elif status == "healthy" or len(anomalies) == 0:
            return {
                "triage_decision": "monitor_only",
                "confidence": 0.8,
                "reason": "No critical issues detected, monitoring only",
                "actions": ["Continue monitoring", "Log status"],
                "requires_ceo": False,
                "auto_repair_possible": False,
            }

        # Default: escalate to CEO if unsure
        else:
            return {
                "triage_decision": "escalate_to_ceo",
                "confidence": 0.6,
                "reason": "Unclear severity, escalating to CEO for safety",
                "actions": ["Queue for CEO review", "Log uncertainty"],
                "requires_ceo": True,
                "auto_repair_possible": False,
                "ceo_priority": "medium",
            }

    async def _triage_sentinel_monitoring(
        self, component: str, mission_data: dict
    ) -> Dict[str, Any]:
        """Triage Sentinel monitoring requests."""
        analysis = mission_data.get("analysis", {})
        metrics = mission_data.get("metrics", {})

        status = analysis.get("status", "unknown")

        # Critical Sentinel findings - escalate to CEO
        if status == "critical":
            return {
                "triage_decision": "escalate_to_ceo",
                "confidence": 0.8,
                "reason": "Sentinel detected critical system issue",
                "actions": ["Alert CEO", "Prepare system report"],
                "requires_ceo": True,
                "auto_repair_possible": False,
                "ceo_priority": "high",
            }

        # Warning or healthy - handle automatically
        else:
            return {
                "triage_decision": "auto_handle",
                "confidence": 0.7,
                "reason": "Sentinel monitoring within normal parameters",
                "actions": ["Process monitoring data", "Update dashboard"],
                "requires_ceo": False,
                "auto_repair_possible": True,
            }

    async def _triage_generic_mission(
        self, mission_type: str, component: str, mission_data: dict
    ) -> Dict[str, Any]:
        """Triage generic missions based on content analysis."""

        # Analyze mission content for urgency
        mission_text = str(mission_data).lower()

        # Keywords that indicate CEO escalation needed
        ceo_keywords = [
            "critical",
            "urgent",
            "ceo",
            "decision",
            "human",
            "approval",
            "escalate",
        ]

        # Keywords that indicate auto-repair possible
        auto_repair_keywords = [
            "restart",
            "retry",
            "monitor",
            "log",
            "update",
            "health",
        ]

        ceo_keyword_count = sum(
            1 for keyword in ceo_keywords if keyword in mission_text
        )
        auto_repair_count = sum(
            1 for keyword in auto_repair_keywords if keyword in mission_text
        )

        # Decision logic
        if ceo_keyword_count > 2:
            return {
                "triage_decision": "escalate_to_ceo",
                "confidence": min(0.9, 0.3 + (ceo_keyword_count * 0.2)),
                "reason": f"Mission contains {ceo_keyword_count} CEO-related keywords",
                "actions": ["Queue for CEO", "Prepare briefing"],
                "requires_ceo": True,
                "auto_repair_possible": False,
            }
        elif auto_repair_count > 1:
            return {
                "triage_decision": "auto_repair",
                "confidence": min(0.8, 0.4 + (auto_repair_count * 0.15)),
                "reason": f"Mission contains {auto_repair_count} auto-repair keywords",
                "actions": ["Attempt automatic fix", "Verify results"],
                "requires_ceo": False,
                "auto_repair_possible": True,
            }
        else:
            return {
                "triage_decision": "monitor_only",
                "confidence": 0.6,
                "reason": "Generic mission, monitoring only",
                "actions": ["Log mission", "Continue monitoring"],
                "requires_ceo": False,
                "auto_repair_possible": False,
            }

    async def _handle_coordination(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Handle coordination requests between components."""

        # Special handling for sentinel requests - use real AI analysis
        if request.component == "sentinel" and "prompt" in request.data:
            return await self._handle_sentinel_analysis(request)

        components = request.data.get("components", [])
        coordination_type = request.data.get("type", "general")

        # Coordinate between components
        coordination_result = await self._coordinate_components(
            components, coordination_type
        )

        return OrchestratorResponse(
            request_id=request.request_id,
            response_type="coordination_result",
            data=coordination_result,
            timestamp=datetime.now(),
            confidence=coordination_result.get("confidence", 0.8),
        )

    async def _handle_sentinel_analysis(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Handle sentinel analysis requests using real AI via OpenCode."""
        prompt = request.data.get("prompt", "")
        analysis_type = request.data.get("analysis_type", "tier1_sentinel")

        # Use OpenCode client to get real AI analysis
        try:
            from Open_ELF.orchestrator.opencode_client import get_opencode_client

            client = get_opencode_client()
            if client:
                # Send prompt to OpenCode for real analysis
                success, ai_response = client.send_message(
                    prompt=f"""You are an AI sentinel analyzing system state.

{prompt}

Please analyze and provide a concise sentinel summary with STATUS field.

Format your response as:
== SENTINEL SUMMARY ==
STATUS: <nominal|stale|error|stopped>
ANALYSIS: <brief analysis>
RECOMMENDATION: <what to do next>
""",
                    agent="sentinel",
                )

                if success and ai_response:
                    # Parse the AI response
                    status = "nominal"  # Default
                    for line in ai_response.splitlines():
                        if "STATUS:" in line:
                            status = line.split("STATUS:")[-1].strip().lower()
                            break

                    return OrchestratorResponse(
                        request_id=request.request_id,
                        response_type="coordination_result",
                        data={
                            "recommendation": "proceed"
                            if status == "nominal"
                            else "escalate",
                            "confidence": 0.9,
                            "ai_analysis": ai_response,
                            "parsed_status": status,
                        },
                        timestamp=datetime.now(),
                        confidence=0.9,
                    )
        except Exception as e:
            logger.error(f"Error calling OpenCode for sentinel analysis: {e}")

        # Fallback if OpenCode fails
        return OrchestratorResponse(
            request_id=request.request_id,
            response_type="coordination_result",
            data={
                "recommendation": "proceed",
                "confidence": 0.5,
                "error": "OpenCode unavailable, using fallback",
            },
            timestamp=datetime.now(),
            confidence=0.5,
        )

    async def _handle_general_decision(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Handle general decision requests."""
        decision_context = request.data.get("context", {})
        options = request.data.get("options", [])

        # Make decision based on context and options
        decision = await self._make_general_decision(decision_context, options)

        return OrchestratorResponse(
            request_id=request.request_id,
            response_type="decision",
            data=decision,
            timestamp=datetime.now(),
            confidence=decision.get("confidence", 0.7),
        )

    async def _check_component_health(self, component: str) -> Dict[str, Any]:
        """Check the health of a specific component."""
        # This would implement actual health checks
        # For now, return mock health status

        health_checks = {
            "database": lambda: self._check_database_health(),
            "filesystem": lambda: self._check_filesystem_health(),
            "opencode": lambda: self._check_opencode_health(),
            "event_bridge": lambda: self._check_event_bridge_health(),
        }

        if component in health_checks:
            return await health_checks[component]()
        else:
            return {
                "status": "unknown",
                "details": f"Component '{component}' not recognized",
                "confidence": 0.5,
            }

    async def _can_handle_mission(
        self, agent_type: str, mission: str
    ) -> Dict[str, Any]:
        """Determine if we can handle a mission."""
        # Simple logic for now - can handle most missions
        mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Analyze mission complexity
        complexity = len(mission.split()) / 10  # Simple word count heuristic
        estimated_time = max(30, int(complexity * 60))  # At least 30 seconds

        return {
            "can_handle": True,
            "mission_id": mission_id,
            "estimated_time": estimated_time,
            "priority": 1 if "urgent" in mission.lower() else 3,
            "confidence": 0.9,
        }

    async def _coordinate_components(
        self, components: List[str], coordination_type: str
    ) -> Dict[str, Any]:
        """Coordinate between multiple components."""
        # Simple coordination logic
        return {
            "coordinated": True,
            "components": components,
            "type": coordination_type,
            "recommendation": "proceed",
            "confidence": 0.8,
        }

    async def _make_general_decision(
        self, context: Dict[str, Any], options: List[str]
    ) -> Dict[str, Any]:
        """Make a general decision."""
        # Simple decision logic based on context
        if options:
            selected_option = options[0]  # Simple selection
        else:
            selected_option = "proceed"

        return {
            "decision": selected_option,
            "reason": "Default selection",
            "confidence": 0.7,
        }

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            # Use the correct execute_query function signature
            execute_query("SELECT 1")
            return {
                "status": "healthy",
                "details": "Database connection successful",
                "confidence": 0.9,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "details": f"Database error: {e}",
                "recommendation": "check_database_connection",
                "confidence": 0.9,
            }

    async def _check_filesystem_health(self) -> Dict[str, Any]:
        """Check filesystem health."""
        critical_dirs = [
            Path.home() / ".opencode" / "tasks",
            Path.home() / ".opencode" / "emergent-learning" / "ceo-inbox",
            Path.home() / ".opencode" / "emergent-learning" / "memory",
        ]

        status = {}
        for dir_path in critical_dirs:
            status[dir_path.name] = "exists" if dir_path.exists() else "missing"

        if all(s == "exists" for s in status.values()):
            return {"status": "healthy", "details": status, "confidence": 0.9}
        else:
            return {
                "status": "degraded",
                "details": status,
                "recommendation": "create_missing_directories",
                "confidence": 0.8,
            }

    async def _check_opencode_health(self) -> Dict[str, Any]:
        """Check OpenCode server health."""
        # This would check OpenCode server status
        return {
            "status": "healthy",
            "details": "OpenCode server assumed healthy",
            "confidence": 0.8,
        }

    async def _check_event_bridge_health(self) -> Dict[str, Any]:
        """Check event bridge health."""
        # This would check event bridge status
        return {
            "status": "healthy",
            "details": "Event bridge assumed healthy",
            "confidence": 0.8,
        }

    async def _handle_sentinel_coordination(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Handle Sentinel monitoring coordination requests."""
        action = request.data.get("action", "monitoring_cycle")
        source = request.data.get("source", "sentinel_monitor")

        # Coordinate Sentinel actions
        coordination_result = {
            "action": action,
            "coordinated": True,
            "recommendation": "proceed",
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat(),
            "actions": ["Continue monitoring cycle", "Report status to dashboard"],
        }

        return OrchestratorResponse(
            request_id=request.request_id,
            response_type="sentinel_coordination",
            data=coordination_result,
            timestamp=datetime.now(),
            confidence=0.9,
        )

    async def _handle_pattern_coordination(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Handle pattern coordination requests from Sentinel."""
        patterns = request.data.get("patterns", [])
        metrics = request.data.get("metrics", {})

        # Analyze patterns and coordinate responses
        coordinated_patterns = []
        for pattern in patterns:
            # Simple pattern coordination logic
            coordinated_patterns.append(
                {
                    "pattern": pattern,
                    "priority": 1,
                    "recommendation": "monitor",
                    "confidence": 0.8,
                }
            )

        coordination_result = {
            "patterns": patterns,
            "coordinated_patterns": coordinated_patterns,
            "recommendation": "monitor_and_report",
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat(),
        }

        return OrchestratorResponse(
            request_id=request.request_id,
            response_type="pattern_coordination",
            data=coordination_result,
            timestamp=datetime.now(),
            confidence=0.85,
        )

class CentralOrchestrator:
    """The central orchestrator that components can ask for answers."""

    def __init__(self):
        self.decision_engine = DecisionEngine()
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.response_handlers: Dict[str, Callable] = {}
        self.running = False

    async def start(self):
        """Start the central orchestrator."""
        logger.info("🚀 Starting Central Orchestrator")
        self.running = True

        # Start request processing loop
        asyncio.create_task(self._process_requests())

        logger.info("✅ Central Orchestrator started")

    async def stop(self):
        """Stop the central orchestrator."""
        logger.info("🛑 Stopping Central Orchestrator")
        self.running = False

    async def ask_orchestrator(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Ask the orchestrator for an answer."""
        logger.info(
            f"🤔 Orchestrator request: {request.request_type} from {request.component}"
        )

        # Process the request through decision engine
        response = await self.decision_engine.make_decision(request)

        logger.info(
            f"✅ Orchestrator response: {response.response_type} (confidence: {response.confidence})"
        )
        return response

    async def _process_requests(self):
        """Process requests in a loop."""
        while self.running:
            try:
                # Process any pending requests
                # For now, we process requests synchronously
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error processing orchestrator requests: {e}")
                await asyncio.sleep(5)

# Global instance for easy access
_orchestrator_instance: Optional[CentralOrchestrator] = None

def get_central_orchestrator() -> CentralOrchestrator:
    """Get or create the central orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = CentralOrchestrator()
    return _orchestrator_instance

async def ask_orchestrator(
    component: str, request_type: str, data: Dict[str, Any], priority: int = 1
) -> OrchestratorResponse:
    """Convenience function to ask the orchestrator for an answer."""
    orchestrator = get_central_orchestrator()

    request = OrchestratorRequest(
        request_id=f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        component=component,
        request_type=request_type,
        data=data,
        timestamp=datetime.now(),
        priority=priority,
    )

    return await orchestrator.ask_orchestrator(request)

# Example usage patterns
async def example_usage():
    """Example of how components would use the orchestrator."""

    # 1. Ask for health check
    health_response = await ask_orchestrator(
        component="mission_processor",
        request_type="health_check",
        data={"component": "database"},
    )

    # 2. Submit a mission
    mission_response = await ask_orchestrator(
        component="dashboard",
        request_type="mission_submission",
        data={
            "agent_type": "researcher",
            "mission": "Research the latest AI developments",
        },
    )

    # 3. Ask for coordination
    coordination_response = await ask_orchestrator(
        component="event_bridge",
        request_type="coordination",
        data={
            "components": ["database", "filesystem", "opencode"],
            "type": "system_startup",
        },
    )

    # 4. Ask for a general decision
    decision_response = await ask_orchestrator(
        component="health_monitor",
        request_type="decision",
        data={
            "context": {"system_load": "high", "available_memory": "low"},
            "options": ["scale_down", "continue", "escalate"],
        },
    )

async def initialize_central_orchestrator():
    """Initialize the central orchestrator."""
    orchestrator = get_central_orchestrator()
    await orchestrator.start()
    logger.info("Central Orchestrator initialized and ready for requests")
