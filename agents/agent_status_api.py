#!/usr/bin/env python3
"""
Agent Status API - REST endpoint for real-time agent status

Provides REST API endpoints for the dashboard to get real-time agent status:
- GET /agents/status - Get current status of all agents
- GET /agents/call/:agent_type - Call specific agent
- POST /agents/start/:agent_type - Start specific agent
- POST /agents/stop/:agent_type - Stop specific agent

This integrates with the orchestrator to provide real-time agent information
instead of the static display that was previously shown.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Flask for REST API
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("Error: Flask not installed. Install with: pip install flask flask-cors")
    sys.exit(1)

# Add path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import AgentOrchestrator, AgentType, AgentStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard

# Global orchestrator instance
orchestrator: Optional[AgentOrchestrator] = None


def init_orchestrator():
    """Initialize the orchestrator if not already done."""
    global orchestrator
    if orchestrator is None:
        logger.info("Initializing Agent Orchestrator...")
        orchestrator = AgentOrchestrator()
        orchestrator.start_orchestrator()
        logger.info("Agent Orchestrator initialized")
    return orchestrator


@app.route("/agents/status", methods=["GET"])
def get_agents_status():
    """Get current status of all agents."""
    try:
        orch = init_orchestrator()
        status = orch.get_agent_status()

        # Transform for dashboard consumption
        dashboard_status = {
            "timestamp": datetime.now().isoformat(),
            "orchestrator": {
                "running": status["orchestrator"]["running"],
                "uptime_seconds": status["orchestrator"]["uptime_seconds"],
                "stats": status["orchestrator"]["stats"],
            },
            "agents": [],
        }

        # Add agents with proper role mapping
        role_mapping = {
            "orchestrator": {
                "display": "Orchestrator",
                "role": "coordination",
                "primary": True,
            },
            "sentinel": {"display": "Sentinel", "role": "monitoring", "primary": False},
            "researcher": {
                "display": "Researcher",
                "role": "investigation",
                "primary": False,
            },
            "architect": {"display": "Architect", "role": "design", "primary": False},
            "skeptic": {"display": "Skeptic", "role": "review", "primary": False},
            "creative": {"display": "Creative", "role": "innovation", "primary": False},
            "ceo": {"display": "CEO", "role": "executive", "primary": False},
        }

        for agent_type, agent_info in status["agents"].items():
            role_info = role_mapping.get(
                agent_type,
                {"display": agent_type.title(), "role": "unknown", "primary": False},
            )

            dashboard_status["agents"].append(
                {
                    "type": agent_type,
                    "name": agent_info["name"],
                    "display_name": role_info["display"],
                    "description": agent_info["description"],
                    "icon": agent_info["icon"],
                    "role": role_info["role"],
                    "is_primary": role_info["primary"],
                    "status": agent_info["status"],
                    "priority": agent_info["priority"],
                    "session_id": agent_info["session_id"],
                    "last_activity": agent_info["last_activity"],
                    "start_time": agent_info["start_time"],
                    "error_count": agent_info["error_count"],
                    "auto_start": agent_info["auto_start"],
                    "status_display": _get_status_display(agent_info["status"]),
                }
            )

        # Sort by priority (lower number = higher priority)
        dashboard_status["agents"].sort(key=lambda x: x["priority"])

        return jsonify(dashboard_status)

    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/agents/call/<agent_type>", methods=["POST"])
def call_agent(agent_type: str):
    """Call a specific agent with a prompt."""
    try:
        orch = init_orchestrator()

        # Parse request
        data = request.get_json() or {}
        prompt = data.get("prompt", "")
        timeout = data.get("timeout", 300)

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # Convert string to AgentType
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            return jsonify({"error": f"Invalid agent type: {agent_type}"}), 400

        # Call agent
        response = orch.call_agent(agent_enum, prompt, timeout)

        return jsonify(
            {
                "success": True,
                "response": response,
                "agent_type": agent_type,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error calling agent {agent_type}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/agents/start/<agent_type>", methods=["POST"])
def start_agent(agent_type: str):
    """Start a specific agent."""
    try:
        orch = init_orchestrator()

        # Convert string to AgentType
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            return jsonify({"error": f"Invalid agent type: {agent_type}"}), 400

        # Start agent
        success = orch.start_agent(agent_enum)

        return jsonify(
            {
                "success": success,
                "agent_type": agent_type,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error starting agent {agent_type}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/agents/stop/<agent_type>", methods=["POST"])
def stop_agent(agent_type: str):
    """Stop a specific agent."""
    try:
        orch = init_orchestrator()

        # Convert string to AgentType
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            return jsonify({"error": f"Invalid agent type: {agent_type}"}), 400

        # Stop agent
        success = orch.stop_agent(agent_enum)

        return jsonify(
            {
                "success": success,
                "agent_type": agent_type,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error stopping agent {agent_type}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "service": "agent-status-api",
            "timestamp": datetime.now().isoformat(),
            "orchestrator_running": orchestrator is not None and orchestrator.running
            if orchestrator
            else False,
        }
    )


def _get_status_display(status: str) -> Dict[str, Any]:
    """Get display information for agent status."""
    status_map = {
        "running": {"text": "Running", "color": "green", "emoji": "🟢"},
        "starting": {"text": "Starting", "color": "yellow", "emoji": "🟡"},
        "stopped": {"text": "Stopped", "color": "gray", "emoji": "⚪"},
        "busy": {"text": "Busy", "color": "orange", "emoji": "🟠"},
        "error": {"text": "Error", "color": "red", "emoji": "🔴"},
        "stopping": {"text": "Stopping", "color": "yellow", "emoji": "🟡"},
    }

    return status_map.get(
        status, {"text": status.title(), "color": "gray", "emoji": "⚪"}
    )


def cleanup():
    """Cleanup on shutdown."""
    global orchestrator
    if orchestrator:
        logger.info("Shutting down orchestrator...")
        orchestrator.shutdown()


if __name__ == "__main__":
    import atexit

    atexit.register(cleanup)

    logger.info("Starting Agent Status API on port 8889")
    logger.info("Endpoints:")
    logger.info("  GET  /agents/status - Get agent status")
    logger.info("  POST /agents/call/<agent_type> - Call agent")
    logger.info("  POST /agents/start/<agent_type> - Start agent")
    logger.info("  POST /agents/stop/<agent_type> - Stop agent")
    logger.info("  GET  /health - Health check")

    app.run(host="0.0.0.0", port=8889, debug=False)
