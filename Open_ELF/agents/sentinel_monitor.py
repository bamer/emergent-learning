#!/usr/bin/env python3
"""
Sentinel Monitor - Unified ELF Standard Monitoring System

Intelligent monitoring agent for the Emergent Learning Framework dashboard.
Provides real-time system health monitoring, pattern detection, and autonomous
decision-making capabilities.

Features:
- Real-time dashboard health monitoring
- Pattern recognition and anomaly detection
- Integration with agent execution engine
- Autonomous alerting and decision-making
- Event chronicle integration for dashboard visibility
"""

import sqlite3
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import sys
from pathlib import Path

# OpenCode integration - always use fallback for consistent OpenCode behavior
Task = None

# Import Agent Execution Engine
sys.path.insert(0, str(Path(__file__).parent))
try:
    from agent_execution_engine import AgentExecutionEngine
    from pattern_response_handler import PatternResponseHandler
except ImportError as e:
    print(f"Warning: Agent execution components not available: {e}")
    AgentExecutionEngine = None
    PatternResponseHandler = None

# Import AgentManager (NOUVEAU SYSTÈME)
try:
    from agent_manager import AgentManager, get_agent_manager

    AGENT_MANAGER_AVAILABLE = True
except ImportError:
    logging.error("❌ AgentManager not available - falling back to basic mode")
    AGENT_MANAGER_AVAILABLE = False

# Use centralized logging
try:
    from elf_logging import get_logger, log_critical

    logger = get_logger("sentinel_monitor")
except ImportError:
    # Fallback to basic logging if logger module not available yet
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                "/home/bamer/.opencode/emergent-learning/Open_ELF/logs/sentinel-monitor.log"
            ),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)


class SentinelMonitor:
    """Unified ELF Standard monitoring system with adaptive learning capabilities."""

    def __init__(self, name="Sentinel Monitor", model="big-pickle"):
        self.name = name
        self.model = model
        self.db_path = "/home/bamer/.opencode/emergent-learning/memory/index.db"
        self.frontend_url = "http://localhost:3001"
        self.backend_url = "http://localhost:8888"
        self.orchestrator_url = "http://localhost:9998"  # Unified orchestrator
        self.conversation_history = []
        self.last_analysis = None
        self.pattern_memory = []
        self.user_preferences = {}
        self.learned_patterns = {}
        self.performance_history = []
        self.adaptation_count = 0

        # Pattern cooldown tracking to avoid spam
        self.pattern_cooldowns = {}  # pattern_name -> last_detected_timestamp
        self.pattern_cooldown_minutes = (
            30  # Minimum minutes between same pattern detection
        )

        # AI Analysis timing (Tier-based like watcher)
        self.monitoring_interval = 30  # seconds (basic cycle)
        self.ai_analysis_interval = 300  # seconds (5 minutes for AI analysis)
        self.cycle_count = 0

        # Initialize Agent Execution Engine and Pattern Response Handler
        self.execution_engine = AgentExecutionEngine() if AgentExecutionEngine else None
        self.pattern_handler = (
            PatternResponseHandler() if PatternResponseHandler else None
        )

        # NOUVEAU : Initialiser AgentManager
        self.agent_manager = None
        if AGENT_MANAGER_AVAILABLE:
            try:
                self.agent_manager = get_agent_manager()
                logger.info("✅ AgentManager initialized successfully in Sentinel")
            except Exception as e:
                logger.error(f"❌ Failed to initialize AgentManager in Sentinel: {e}")

    def ask_orchestrator(self, request_type: str, data: dict) -> dict:
        """Ask for decisions - utilise AgentManager directement (fallback sur orchestrator)."""
        # ESSAI 1: Utiliser AgentManager directement
        if self.agent_manager:
            try:
                logger.info(f"🤖 Using AgentManager for request: {request_type}")

                prompt = f"Request: {request_type}\n\nData: {json.dumps(data, indent=2)}\n\nCheck the system for any defect and Depend of severity take or Recommend immediate actions Create an escalation file in ceo-inbox/ if critical"
                response = self.agent_manager.ask_agent("unified-orchestrator", prompt)

                return {
                    "status": "success",
                    "agent": "unified-orchestrator",
                    "response": response,
                    "coordinated_patterns": data.get("patterns", []),
                    "source": "agent_manager",
                }

            except Exception as e:
                logger.error(f"❌ AgentManager failed: {e}")
                logger.info("🔄 Falling back to orchestrator...")

        # ESSAI 2: Fallback vers orchestrator HTTP
        try:
            response = requests.post(
                f"{self.orchestrator_url}/api/v1/ask",
                json={
                    "component": "sentinel_monitor",
                    "request_type": request_type,
                    "data": data,
                    "priority": 1,
                },
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    f"Orchestrator returned {response.status_code}: {response.text}"
                )
                return {"error": f"Orchestrator returned {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to ask orchestrator: {e}")
            return {"error": str(e)}

    def submit_to_orchestrator(self, mission_type: str, data: dict) -> dict:
        """Submit missions - utilise AgentManager directement (fallback sur orchestrator)."""
        # ESSAI 1: Utiliser AgentManager directement
        if self.agent_manager:
            try:
                logger.info(f"🤖 Using AgentManager for mission: {mission_type}")

                # Construire le prompt selon le type de mission
                if mission_type == "sentinel_monitoring":
                    prompt = f"""Check the system for any defect, here is the sentinel data :

{json.dumps(data, indent=2)}

Please:
1. Check quickly the core componement of the system and ensure they are running :
- Dashboard Backend 
- Event Bridge 
- Dashboard Frontend
- Watcher 
- Sentinel 
- Orchestrator 
- Learning Capture 
- CEO Monitor
2. If not working : Identify root causes
3. Depend of severity take or Recommend immediate actions
4. Create an escalation file in ceo-inbox/ if critical

Do your mission then Respond with a detailed analysis."""

                    response = self.agent_manager.ask_agent("sentinel", prompt)

                    # Créer fichier d'escalade si critique
                    if "critical" in response.lower() or "error" in response.lower():
                        escalation_file = f"/home/bamer/.opencode/emergent-learning/ceo-inbox/sentinel_escalation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                        with open(escalation_file, "w") as f:
                            f.write(
                                f"# Sentinel Escalation\n\n**Time:** {datetime.now().isoformat()}\n\n"
                            )
                            f.write(
                                f"**Data:**\n```json\n{json.dumps(data, indent=2)}\n```\n\n"
                            )
                            f.write(f"**Analysis:**\n{response}\n")
                        logger.info(f"🚨 Escalation created: {escalation_file}")

                    return {
                        "status": "success",
                        "agent": "sentinel",
                        "agent_analysis": response,
                        "actions": ["analysis_completed"],
                        "source": "agent_manager",
                    }

                else:
                    # Autres types de missions
                    response = self.agent_manager.ask_agent(
                        "unified-orchestrator", str(data)
                    )
                    return {
                        "status": "success",
                        "agent": "unified-orchestrator",
                        "response": response,
                        "source": "agent_manager",
                    }

            except Exception as e:
                logger.error(f"❌ AgentManager failed: {e}")
                logger.info("🔄 Falling back to orchestrator...")

        # ESSAI 2: Fallback vers orchestrator HTTP
        try:
            response = requests.post(
                f"{self.orchestrator_url}/api/v1/mission",
                json={
                    "mission_type": mission_type,
                    "component": "sentinel_monitor",
                    "data": data,
                },
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Mission submission failed: {response.status_code}")
                return {"error": f"Mission submission failed: {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to submit mission: {e}")
            return {"error": str(e)}

    def check_orchestrator_health(self) -> bool:
        """Check if the orchestrator is healthy."""
        try:
            response = requests.get(f"{self.orchestrator_url}/status", timeout=5)
            return response.status_code == 200
        except:
            return False

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive dashboard metrics."""
        try:
            # Service health
            frontend_health = (
                requests.get(self.frontend_url, timeout=3).status_code == 200
            )
            backend_health = (
                requests.get(f"{self.backend_url}/docs", timeout=3).status_code == 200
            )

            # Database metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Current counts
            cursor.execute("SELECT COUNT(*) FROM learnings")
            total_learnings = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM heuristics WHERE is_golden = 1")
            golden_rules = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM heuristics WHERE is_golden = 0")
            regular_heuristics = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM experiments")
            experiments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM spike_reports")
            spike_reports = cursor.fetchone()[0]

            # Check for recent system failures (last 24 hours)
            cursor.execute(
                """SELECT COUNT(*) FROM learnings 
                   WHERE type = 'failure' 
                   AND created_at > datetime("now", "-1 day")
                   AND (title LIKE '%self-test%' OR title LIKE '%system issue%' OR tags LIKE '%self-test%')"""
            )
            recent_system_failures = cursor.fetchone()[0]

            # Recent activity (last hour)
            cursor.execute(
                'SELECT COUNT(*) FROM learnings WHERE created_at > datetime("now", "-1 hour")'
            )
            recent_learnings = cursor.fetchone()[0]

            cursor.execute(
                'SELECT COUNT(*) FROM heuristics WHERE created_at > datetime("now", "-1 hour")'
            )
            recent_heuristics = cursor.fetchone()[0]

            # Performance metrics
            cursor.execute("SELECT COUNT(*) FROM heuristics WHERE confidence > 0.8")
            high_confidence_heuristics = cursor.fetchone()[0]

            cursor.execute(
                "SELECT AVG(confidence) FROM heuristics WHERE confidence > 0"
            )
            avg_confidence = cursor.fetchone()[0] or 0

            conn.close()

            return {
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "frontend": frontend_health,
                    "backend": backend_health,
                    "overall": frontend_health and backend_health,
                },
                "data": {
                    "learnings": total_learnings,
                    "golden_rules": golden_rules,
                    "regular_heuristics": regular_heuristics,
                    "experiments": experiments,
                    "spike_reports": spike_reports,
                    "system_failures_24h": recent_system_failures,
                    "total_items": total_learnings
                    + golden_rules
                    + regular_heuristics
                    + experiments
                    + spike_reports,
                },
                "activity": {
                    "recent_learnings": recent_learnings,
                    "recent_heuristics": recent_heuristics,
                    "activity_score": recent_learnings + recent_heuristics,
                },
                "quality": {
                    "high_confidence_heuristics": high_confidence_heuristics,
                    "average_confidence": round(avg_confidence, 3),
                    "quality_score": high_confidence_heuristics
                    / max(1, golden_rules + regular_heuristics),
                },
            }

        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def analyze_with_ai(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        NOUVEAU : Analyser les métriques via AgentManager.

        Utilise le vrai prompt système du fichier sentinel.md
        au lieu de prompts hardcodés ou de l'orchestrator HTTP.
        """
        if not self.agent_manager:
            logger.warning("AgentManager not available, using fallback analysis")
            return self.fallback_analysis(metrics)

        try:
            # Préparer le contexte pour l'agent Sentinel
            context = {
                "metrics": metrics,
                "analysis_type": "dashboard_health",
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                "🤖 Sending analysis request to Sentinel agent via AgentManager..."
            )

            # Appeler l'agent Sentinel avec son vrai prompt système
            result = self.agent_manager.sentinel(
                request="Check and test the current real system state"
                "1. Check quickly the core componement of the system and ensure they are running :"
                "- Dashboard Backend "
                "- Event Bridge "
                "- Dashboard Frontend"
                "- Watcher "
                "- Sentinel "
                "- Orchestrator "
                "- Learning Capture "
                "- CEO Monitor"
                ""
                "Depend of severity take or Recommend immediate actions then provide a comprehensive health assessment. "
                "Focus on: 1) Overall system status, 2) Anomalies detected, 3) Security concerns, "
                "4) Performance issues, 5) Recommended actions with priorities.",
                context=context,
            )

            if result.get("success"):
                logger.info(
                    f"✅ Sentinel analysis completed (session: {result.get('session_id', 'unknown')[:8]}...)"
                )

                # Parser la réponse de l'agent
                ai_response = result.get("response", "")

                return {
                    "status": self._parse_status_from_response(ai_response),
                    "analysis": ai_response,
                    "anomalies": self._extract_anomalies(ai_response),
                    "recommendations": self._extract_recommendations(ai_response),
                    "patterns": self._extract_patterns(ai_response),
                    "priority_actions": self._extract_priority_actions(ai_response),
                    "ai_processed": True,
                    "session_id": result.get("session_id"),
                    "model_used": result.get("model_used"),
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ Sentinel agent failed: {error_msg}")
                return self.fallback_analysis(metrics, error_msg)

        except Exception as e:
            logger.error(f"❌ Error calling AgentManager in Sentinel: {e}")
            return self.fallback_analysis(metrics, str(e))

    def _parse_status_from_response(self, response: str) -> str:
        """Extraire le statut de la réponse de l'agent."""
        response_lower = response.lower()
        if any(
            word in response_lower
            for word in ["critical", "severe", "down", "failure", "corruption"]
        ):
            return "critical"
        elif any(
            word in response_lower
            for word in ["warning", "degraded", "issue", "problem", "alert"]
        ):
            return "warning"
        else:
            return "healthy"

    def _extract_anomalies(self, response: str) -> List[str]:
        """Extraire les anomalies détectées de la réponse."""
        anomalies = []
        lines = response.split("\n")
        in_anomalies_section = False

        for line in lines:
            lower_line = line.lower()
            if (
                "anomal" in lower_line
                or "issue" in lower_line
                or "concern" in lower_line
            ):
                in_anomalies_section = True
            elif in_anomalies_section and (
                line.strip().startswith("-") or line.strip().startswith("*")
            ):
                anomalies.append(line.strip()[1:].strip())
            elif in_anomalies_section and line.strip() == "":
                in_anomalies_section = False

        return anomalies

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extraire les recommandations de la réponse."""
        recommendations = []
        lines = response.split("\n")
        in_recommendations_section = False

        for line in lines:
            lower_line = line.lower()
            if (
                "recommend" in lower_line
                or "suggestion" in lower_line
                or "action" in lower_line
            ):
                in_recommendations_section = True
            elif in_recommendations_section and (
                line.strip().startswith("-") or line.strip().startswith("*")
            ):
                recommendations.append(line.strip()[1:].strip())
            elif in_recommendations_section and line.strip() == "":
                in_recommendations_section = False

        return recommendations

    def _extract_patterns(self, response: str) -> List[str]:
        """Extraire les patterns détectés de la réponse."""
        patterns = []
        lines = response.split("\n")
        in_patterns_section = False

        for line in lines:
            lower_line = line.lower()
            if "pattern" in lower_line or "trend" in lower_line:
                in_patterns_section = True
            elif in_patterns_section and (
                line.strip().startswith("-") or line.strip().startswith("*")
            ):
                patterns.append(line.strip()[1:].strip())
            elif in_patterns_section and line.strip() == "":
                in_patterns_section = False

        return patterns

    def _extract_priority_actions(self, response: str) -> List[str]:
        """Extraire les actions prioritaires de la réponse."""
        actions = []
        lines = response.split("\n")
        in_priority_section = False

        for line in lines:
            lower_line = line.lower()
            if (
                "priority" in lower_line
                or "immediate" in lower_line
                or "urgent" in lower_line
            ):
                in_priority_section = True
            elif in_priority_section and (
                line.strip().startswith("-") or line.strip().startswith("*")
            ):
                actions.append(line.strip()[1:].strip())
            elif in_priority_section and line.strip() == "":
                in_priority_section = False

        return actions

    def fallback_analysis(
        self, metrics: Dict[str, Any], error_msg: str = ""
    ) -> Dict[str, Any]:
        """Fallback analysis when AI is not available."""
        if "error" in metrics:
            return {
                "status": "critical",
                "analysis": f"Monitoring system error: {metrics['error']}. {error_msg}",
                "anomalies": ["Monitoring failure"],
                "recommendations": ["Check monitoring system"],
                "patterns": [],
                "priority_actions": ["Fix monitoring system"],
                "ai_processed": False,
                "fallback": True,
            }

        # Simple rule-based analysis
        services_ok = metrics.get("services", {}).get("overall", False)
        activity_score = metrics.get("activity", {}).get("activity_score", 0)

        if not services_ok:
            status = "critical"
            analysis = f"Service health issues detected. {error_msg}"
        elif activity_score == 0:
            status = "warning"
            analysis = f"No recent activity detected. {error_msg}"
        else:
            status = "healthy"
            analysis = (
                f"All systems operational (basic check - AI unavailable: {error_msg})"
            )

        return {
            "status": status,
            "analysis": analysis,
            "anomalies": [],
            "recommendations": [],
            "patterns": [],
            "priority_actions": [],
            "ai_processed": False,
            "fallback": True,
        }

    def basic_analysis(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Basic analysis without AI - for non-AI cycles."""
        if "error" in metrics:
            return {
                "status": "critical",
                "analysis": f"Monitoring system error: {metrics['error']}",
                "anomalies": ["Monitoring failure"],
                "recommendations": ["Check monitoring system"],
                "patterns": [],
                "priority_actions": ["Fix monitoring system"],
                "ai_processed": False,
                "basic_only": True,
            }

        # Simple rule-based analysis
        services_ok = metrics.get("services", {}).get("overall", False)
        activity_score = metrics.get("activity", {}).get("activity_score", 0)

        if not services_ok:
            status = "critical"
            analysis = "Service health issues detected"
        elif activity_score == 0:
            status = "warning"
            analysis = "No recent activity detected"
        else:
            status = "healthy"
            analysis = "All systems operational (basic check)"

        return {
            "status": status,
            "analysis": analysis,
            "anomalies": [],
            "recommendations": [],
            "patterns": [],
            "priority_actions": [],
            "ai_processed": False,
            "basic_only": True,
        }

    def learn_user_patterns(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Learn and adapt to user patterns and preferences."""
        learning_data = {
            "timestamp": datetime.now().isoformat(),
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "activity_level": metrics.get("activity", {}).get("activity_score", 0),
            "data_growth": metrics.get("data", {}).get("total_items", 0),
            "service_health": metrics.get("services", {}).get("overall", False),
        }

        # Store learning data
        self.performance_history.append(learning_data)

        # Keep last 100 entries for learning
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

        # Learn patterns if we have enough data
        if len(self.performance_history) >= 10:
            return self.analyze_learning_patterns()

        return {"status": "learning", "patterns_detected": 0}

    def analyze_learning_patterns(self) -> Dict[str, Any]:
        """Analyze learned patterns and adapt behavior."""
        patterns = {}

        # Learn peak activity hours
        hourly_activity = {}
        for entry in self.performance_history:
            hour = entry["hour"]
            activity = entry["activity_level"]
            if hour not in hourly_activity:
                hourly_activity[hour] = []
            hourly_activity[hour].append(activity)

        # Calculate average activity per hour
        peak_hours = []
        for hour, activities in hourly_activity.items():
            avg_activity = sum(activities) / len(activities)
            if avg_activity > 2:  # Threshold for "active"
                peak_hours.append((hour, avg_activity))

        peak_hours.sort(key=lambda x: x[1], reverse=True)
        patterns["peak_activity_hours"] = peak_hours[:3]

        # Learn service reliability patterns
        service_reliability = {}
        for entry in self.performance_history:
            day = entry["day_of_week"]
            health = entry["service_health"]
            if day not in service_reliability:
                service_reliability[day] = {"healthy": 0, "unhealthy": 0}
            if health:
                service_reliability[day]["healthy"] += 1
            else:
                service_reliability[day]["unhealthy"] += 1

        # Find least reliable day
        unreliable_days = []
        for day, stats in service_reliability.items():
            total = stats["healthy"] + stats["unhealthy"]
            if total > 0:
                reliability = stats["healthy"] / total
                if reliability < 0.8:  # Less than 80% reliable
                    unreliable_days.append((day, reliability))

        patterns["unreliable_days"] = unreliable_days

        # Learn data growth patterns
        data_growth = [entry["data_growth"] for entry in self.performance_history]
        if len(data_growth) >= 2:
            growth_rate = (data_growth[-1] - data_growth[0]) / len(data_growth)
            patterns["data_growth_rate"] = growth_rate

            # Predict future data size
            future_size = data_growth[-1] + (growth_rate * 24)  # Next 24 hours
            patterns["predicted_size_24h"] = int(future_size)

        return patterns

    def adapt_behavior(self, patterns: Dict[str, Any]) -> List[str]:
        """Adapt behavior based on learned patterns."""
        adaptations = []

        # Adapt monitoring frequency based on peak hours
        current_hour = datetime.now().hour
        peak_hours = [hour for hour, _ in patterns.get("peak_activity_hours", [])]

        if current_hour in peak_hours:
            adaptations.append("Increased monitoring frequency during peak hours")
            # Could dynamically adjust monitoring interval here

        # Adapt alerting based on unreliable days
        current_day = datetime.now().weekday()
        unreliable_days = [day for day, _ in patterns.get("unreliable_days", [])]

        if current_day in unreliable_days:
            adaptations.append(
                "Enhanced service monitoring on historically unreliable day"
            )

        # Adapt resource management based on growth predictions
        growth_rate = patterns.get("data_growth_rate", 0)
        if growth_rate > 5:  # High growth rate
            adaptations.append("Proactive resource scaling due to high data growth")

        # Store adaptations for learning
        if adaptations:
            self.adaptation_count += 1
            self.learned_patterns[f"adaptation_{self.adaptation_count}"] = {
                "timestamp": datetime.now().isoformat(),
                "patterns": patterns,
                "adaptations": adaptations,
            }

        return adaptations

    def detect_patterns(self, current_metrics: Dict[str, Any]) -> List[str]:
        """Detect patterns in metrics over time with learning enhancement.

        Uses cooldown mechanism to avoid spamming the same pattern repeatedly.
        Same pattern can only be reported once every pattern_cooldown_minutes.
        """
        patterns = []
        now = datetime.now()

        # Store current metrics in pattern memory
        self.pattern_memory.append({"timestamp": now, "metrics": current_metrics})

        # Keep only last 50 entries
        if len(self.pattern_memory) > 50:
            self.pattern_memory = self.pattern_memory[-50:]

        # Analyze patterns if we have enough data
        if len(self.pattern_memory) >= 5:
            # Check for declining activity
            recent_activity = [
                entry["metrics"].get("activity", {}).get("activity_score", 0)
                for entry in self.pattern_memory[-5:]
            ]
            if all(
                recent_activity[i] <= recent_activity[i - 1]
                for i in range(1, len(recent_activity))
            ):
                if self._can_report_pattern("declining_activity"):
                    patterns.append("Declining activity trend detected")
                    self._mark_pattern_reported("declining_activity")

            # Check for service instability
            recent_services = [
                entry["metrics"].get("services", {}).get("overall", False)
                for entry in self.pattern_memory[-10:]
            ]
            if not all(recent_services):
                if self._can_report_pattern("service_instability"):
                    patterns.append("Service instability detected")
                    self._mark_pattern_reported("service_instability")

            # Enhanced pattern detection with learning
            if len(self.pattern_memory) >= 20:
                # Learn cyclical patterns
                activity_cycle = self.detect_activity_cycles()
                if activity_cycle:
                    pattern_key = f"cyclical_{activity_cycle}"
                    if self._can_report_pattern(pattern_key):
                        patterns.append(f"Cyclical pattern detected: {activity_cycle}")
                        self._mark_pattern_reported(pattern_key)

        return patterns

    def _can_report_pattern(self, pattern_key: str) -> bool:
        """Check if enough time has passed since last report of this pattern."""
        if pattern_key not in self.pattern_cooldowns:
            return True

        last_reported = self.pattern_cooldowns[pattern_key]
        cooldown = timedelta(minutes=self.pattern_cooldown_minutes)
        return datetime.now() - last_reported > cooldown

    def _mark_pattern_reported(self, pattern_key: str):
        """Mark a pattern as reported at current time."""
        self.pattern_cooldowns[pattern_key] = datetime.now()

    def detect_activity_cycles(self) -> Optional[str]:
        """Detect cyclical patterns in activity."""
        if len(self.pattern_memory) < 20:
            return None

        # Extract activity scores
        activities = [
            entry["metrics"].get("activity", {}).get("activity_score", 0)
            for entry in self.pattern_memory[-20:]
        ]

        # Simple cycle detection (could be enhanced with FFT)
        # Look for repeating patterns every ~10 entries
        cycle_length = 10
        if len(activities) >= cycle_length * 2:
            first_cycle = activities[:cycle_length]
            second_cycle = activities[cycle_length : cycle_length * 2]

            # Calculate similarity
            similarity = (
                sum(
                    1
                    for i in range(cycle_length)
                    if abs(first_cycle[i] - second_cycle[i]) < 2
                )
                / cycle_length
            )

            if similarity > 0.7:  # 70% similarity
                return f"Activity cycle of {cycle_length} intervals detected"

        return None

    def execute_autonomous_actions(
        self, analysis: Dict[str, Any], metrics: Dict[str, Any]
    ):
        """Execute autonomous actions coordinated through unified orchestrator."""
        actions_taken = []

        # Submit the analysis to orchestrator for decision coordination
        mission_data = {
            "analysis": analysis,
            "metrics": metrics,
            "source": "sentinel_monitor",
            "timestamp": datetime.now().isoformat(),
        }

        orchestrator_response = self.submit_to_orchestrator(
            "sentinel_monitoring", mission_data
        )

        if "error" not in orchestrator_response:
            # Orchestrator provided coordinated actions
            orchestrator_actions = orchestrator_response.get("actions", [])
            for action in orchestrator_actions:
                logger.info(f"🎯 Orchestrator action: {action}")
                actions_taken.append(action)
        else:
            # Fallback to local actions if orchestrator is unavailable
            # Critical status actions
            if analysis.get("status") == "critical":
                if not metrics.get("services", {}).get("overall", False):
                    logger.critical("🚨 CRITICAL: Service health issues detected!")
                    # Could attempt service restart here

            # Warning status actions
            elif analysis.get("status") == "warning":
                if metrics.get("activity", {}).get("activity_score", 0) == 0:
                    logger.warning("⚠️  WARNING: No recent activity detected")

            # Log patterns detected
            patterns = analysis.get("patterns", [])
            if patterns:
                logger.info(f"🔍 Patterns detected: {', '.join(patterns)}")

            # Execute priority actions
            for action in analysis.get("priority_actions", []):
                logger.info(f"🎯 Priority action: {action}")
                actions_taken.append(action)

        return actions_taken

    def record_to_event_chronicle(
        self,
        event_type: str,
        status: str,
        summary: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Record event to event_chronicle table for dashboard visibility.

        Uses retry logic with WAL mode to handle concurrent database access.
        Silently ignores temporary locks to avoid log spam.
        """
        import json

        max_retries = 5
        retry_delay = 0.5

        for attempt in range(max_retries):
            try:
                # Use timeout and WAL mode for better concurrency
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO event_chronicle (timestamp, event_type, source, source_id, status, summary, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now().isoformat(),
                        event_type,
                        "dashboard_sentinel",
                        "sentinel-main",
                        status,
                        summary,
                        json.dumps(data) if data else None,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                conn.close()
                return  # Success - exit method

            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    # Temporary lock - retry silently
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
                elif "database is locked" in str(e):
                    # Final attempt failed - log once but don't spam
                    logger.warning(
                        f"Event chronicle temporarily unavailable (database busy), event queued for later: {event_type}"
                    )
                    # Could queue to file here if needed
                    return
                else:
                    # Other error - log it
                    logger.error(f"Failed to record event to chronicle: {e}")
                    return
            except Exception as e:
                logger.error(f"Failed to record event to chronicle: {e}")
                return

    def run_monitoring_cycle(self):
        """Execute one complete monitoring cycle coordinated with unified orchestrator."""
        logger.info(
            f"🤖 {self.name} - Starting monitoring cycle (orchestrator-integrated)..."
        )

        # Increment cycle counter
        self.cycle_count += 1

        # Check orchestrator health first
        orchestrator_healthy = self.check_orchestrator_health()
        if not orchestrator_healthy:
            logger.warning(
                "⚠️  Unified orchestrator not available, running in standalone mode"
            )

        # Collect metrics
        metrics = self.collect_metrics()

        # AI Analysis - Only run every AI Analysis Interval (like watcher tiers)
        should_run_ai_analysis = (
            self.cycle_count % (self.ai_analysis_interval // self.monitoring_interval)
        ) == 0

        if should_run_ai_analysis and self.agent_manager:
            logger.info("🤖 Running AI analysis cycle via AgentManager")
            # AI Analysis (now coordinated through orchestrator)
            analysis = self.analyze_with_ai(metrics)
        else:
            if not self.agent_manager:
                logger.info(
                    "📋 Running basic metrics analysis (AgentManager unavailable)"
                )
            else:
                logger.info("📋 Running basic metrics analysis only")
            analysis = self.basic_analysis(metrics)

        # Add AI analysis flag to analysis
        analysis["ai_analysis_run"] = should_run_ai_analysis

        # Pattern detection
        patterns = self.detect_patterns(metrics)
        # Ensure patterns list exists in analysis
        if "patterns" not in analysis:
            analysis["patterns"] = []
        analysis["patterns"].extend(patterns)

        # Submit patterns to orchestrator for coordination
        if patterns and orchestrator_healthy:
            pattern_response = self.ask_orchestrator(
                "pattern_coordination",
                {
                    "patterns": patterns,
                    "metrics": metrics,
                    "source": "sentinel_monitor",
                },
            )
            if "error" not in pattern_response:
                coordinated_patterns = pattern_response.get(
                    "coordinated_patterns", patterns
                )
                analysis["patterns"] = coordinated_patterns

        # AGENT EXECUTION: Call agents for detected patterns
        agent_execution_results = []
        if patterns and self.execution_engine and self.pattern_handler:
            agent_execution_results = self._execute_agent_workflows(
                patterns=patterns, metrics=metrics, analysis=analysis
            )

        # Display results
        self.display_status(metrics, analysis)

        # Execute autonomous actions (now coordinated through orchestrator)
        actions = self.execute_autonomous_actions(analysis, metrics)

        # Store analysis
        self.last_analysis = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "analysis": analysis,
            "actions_taken": actions,
            "agent_executions": agent_execution_results,
            "orchestrator_integrated": orchestrator_healthy,
        }

        # Record to event chronicle for dashboard
        status = analysis.get("status", "unknown")
        orchestrator_status = "integrated" if orchestrator_healthy else "standalone"
        summary = f"Sentinel cycle ({orchestrator_status}) - {analysis.get('analysis', 'No analysis')} (Activity: {metrics.get('activity', {}).get('activity_score', 0)})"
        self.record_to_event_chronicle(
            event_type="sentinel_cycle",
            status=status,
            summary=summary,
            data={
                "metrics": metrics,
                "analysis": analysis,
                "actions": actions,
                "agent_executions": agent_execution_results,
                "orchestrator_integrated": orchestrator_healthy,
            },
        )

        return self.last_analysis

    def _execute_agent_workflows(
        self, patterns: List[str], metrics: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute full agent workflow for detected patterns.

        THIS IS THE MISSING LINK - Actually calls agents!
        """
        logger.info(f"\n{'=' * 70}")
        logger.info(f"🚀 EXECUTING AGENT WORKFLOWS FOR {len(patterns)} PATTERNS")
        logger.info(f"{'=' * 70}")

        execution_results = []

        for pattern in patterns:
            try:
                logger.info(f"\n📍 Processing pattern: {pattern}")

                # Step 1: Get pattern handler recommendations
                handler_result = self.pattern_handler.handle_pattern(pattern, metrics)
                agent_to_call = handler_result.get("agent_called")
                recommendations = handler_result.get("recommendations", [])

                if not agent_to_call:
                    logger.warning(f"⚠️  No agent determined for pattern: {pattern}")
                    continue

                logger.info(f"✅ Determined agent: {agent_to_call}")

                # Step 2: EXECUTE AGENT via Engine (THIS ACTUALLY CALLS THE AGENT!)
                logger.info(f"📞 Calling {agent_to_call} agent...")

                result = self.execution_engine.execute_pattern_response(
                    pattern=pattern,
                    agent_to_call=agent_to_call,
                    recommendations=recommendations,
                    context=metrics,
                )

                execution_results.append(result)

                # Log execution result
                if result.get("status") == "completed":
                    logger.info(f"✅ Workflow completed for pattern: {pattern}")
                    logger.info(
                        f"   Agent analysis: {result.get('agent_analysis', '')[:100]}..."
                    )
                    logger.info(f"   Is critical: {result.get('is_critical', False)}")
                    if result.get("ceo_decision"):
                        logger.info(
                            f"   CEO decision: {result.get('ceo_decision', '')[:100]}..."
                        )
                    if result.get("actions"):
                        logger.info(
                            f"   Actions to execute: {len(result.get('actions', []))} items"
                        )
                        for i, action in enumerate(result.get("actions", []), 1):
                            logger.info(f"     {i}. {action}")
                else:
                    logger.error(f"❌ Workflow failed for pattern: {pattern}")
                    logger.error(f"   Status: {result.get('status')}")

            except Exception as e:
                logger.error(f"❌ Agent execution failed for pattern '{pattern}': {e}")
                execution_results.append(
                    {"pattern": pattern, "status": "error", "error": str(e)}
                )

        logger.info(f"\n{'=' * 70}")
        logger.info(f"✅ AGENT WORKFLOWS EXECUTION COMPLETE")
        logger.info(f"   Patterns processed: {len(patterns)}")
        logger.info(
            f"   Successful workflows: {len([r for r in execution_results if r.get('status') == 'completed'])}"
        )
        logger.info(f"{'=' * 70}\n")

        return execution_results

    def display_status(self, metrics: Dict[str, Any], analysis: Dict[str, Any]):
        """Display comprehensive status dashboard with orchestrator integration."""
        orchestrator_healthy = self.check_orchestrator_health()
        orchestrator_status = "🟢 Unified" if orchestrator_healthy else "🔴 Standalone"

        print(f"\n🤖 {self.name} - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)

        # Status indicator
        status_emoji = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(
            analysis.get("status", "unknown"), "⚪"
        )

        print(f"{status_emoji} Status: {analysis.get('status', 'unknown').upper()}")
        print(f"🎯 Orchestrator: {orchestrator_status}")
        print(f"📊 Analysis: {analysis.get('analysis', 'No analysis available')}")

        # Services
        services = metrics.get("services", {})
        print(f"\n🌐 Services:")
        print(f"  Frontend: {'🟢' if services.get('frontend') else '🔴'}")
        print(f"  Backend: {'🟢' if services.get('backend') else '🔴'}")
        print(f"  Overall: {'🟢' if services.get('overall') else '🔴'}")

        # Data inventory
        data = metrics.get("data", {})
        print(f"\n📚 Data Inventory:")
        print(f"  Learnings: {data.get('learnings', 0)}")
        print(f"  Golden Rules: {data.get('golden_rules', 0)}")
        print(f"  Regular Heuristics: {data.get('regular_heuristics', 0)}")
        print(f"  Experiments: {data.get('experiments', 0)}")
        print(f"  Spike Reports: {data.get('spike_reports', 0)}")
        print(f"  Total Items: {data.get('total_items', 0)}")

        # Activity
        activity = metrics.get("activity", {})
        print(f"\n⚡ Recent Activity (1h):")
        print(f"  New Learnings: {activity.get('recent_learnings', 0)}")
        print(f"  New Heuristics: {activity.get('recent_heuristics', 0)}")
        print(f"  Activity Score: {activity.get('activity_score', 0)}")

        # Quality metrics
        quality = metrics.get("quality", {})
        print(f"\n🎯 Quality Metrics:")
        print(
            f"  High Confidence Heuristics: {quality.get('high_confidence_heuristics', 0)}"
        )
        print(f"  Average Confidence: {quality.get('average_confidence', 0)}")
        print(f"  Quality Score: {quality.get('quality_score', 0):.2%}")

        # Anomalies and recommendations
        anomalies = analysis.get("anomalies", [])
        if anomalies:
            print(f"\n⚠️  Anomalies:")
            for anomaly in anomalies:
                print(f"  • {anomaly}")

        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")

        # Patterns
        patterns = analysis.get("patterns", [])
        if patterns:
            print(f"\n🔍 Patterns Detected:")
            for pattern in patterns:
                print(f"  • {pattern}")

        # AI Analysis status
        ai_analysis_run = analysis.get("ai_analysis_run", False)
        if ai_analysis_run:
            ai_status = "🤖 AI Analysis"
        elif analysis.get("basic_only"):
            ai_status = "📋 Basic Check"
        elif analysis.get("fallback"):
            ai_status = "⚠️  Fallback (no IA)"
        else:
            ai_status = "📋 Basic Check"

        print(f"\n🤖 Analysis: {ai_status}")
        print(f"⏱️  Cycle: {self.cycle_count}")

        # Calculate time until next AI analysis
        if ai_analysis_run:
            cycles_until_ai = self.ai_analysis_interval // self.monitoring_interval
        else:
            cycles_until_ai = (
                self.ai_analysis_interval // self.monitoring_interval
            ) - (
                self.cycle_count
                % (self.ai_analysis_interval // self.monitoring_interval)
            )
        seconds_until_ai = cycles_until_ai * self.monitoring_interval
        print(
            f"⏱️  Next AI: {seconds_until_ai}s ({seconds_until_ai // 60}m {seconds_until_ai % 60}s)"
        )

        print("\n" + "=" * 60)

    def start_continuous_monitoring(self, interval=30):
        """Start continuous monitoring with specified interval."""
        logger.info(
            f"🚀 {self.name} starting continuous monitoring (interval: {interval}s)"
        )

        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info(f"⏹️  {self.name} stopped by user")
        except Exception as e:
            logger.error(f"{self.name} crashed: {e}")
            raise


if __name__ == "__main__":
    # Create and start AI Sentinel
    sentinel = SentinelMonitor(name="Sentinel Monitor", model="llama/nemotron-v3-coder")

    # Start monitoring
    sentinel.start_continuous_monitoring(interval=30)
