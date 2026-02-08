#!/usr/bin/env python3
"""
ELF Watcher System v2.0 - AgentManager Integration

Watcher modernisé qui utilise AgentManager pour les analyses IA
au lieu de l'ancien système Event Bridge + OpenCodeAIClient.

Features:
- Utilise AgentManager avec les vrais prompts système depuis les fichiers .md
- Sessions persistantes par agent (watcher, sentinel, etc.)
- Coordonne les escalades via l'API Event Bridge (pour les missions)
- Intégration complète avec l'architecture unifiée
"""

import json
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directories to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent.parent  # emergent-learning root
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

# Import centralized logger
try:
    from Open_ELF.agents import elf_logging

    logger = elf_logging.get_logger("elf_watcher")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("elf_watcher")

# Import event logger for database logging
try:
    from Open_ELF.utils.event_logger import log_watcher_check, log_event

    EVENT_LOGGER_AVAILABLE = True
except ImportError:
    logger.warning("Event logger not available, database logging disabled")
    EVENT_LOGGER_AVAILABLE = False

    def log_watcher_check(
        tier: int, status: str, summary: str, details: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        return None

    def log_event(
        event_type: str,
        source: str,
        summary: str,
        data: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None,
        status: str = "success",
    ) -> Optional[int]:
        return None


# Import AgentManager (NOUVEAU SYSTÈME)
try:
    from Open_ELF.agents.agent_manager import AgentManager, get_agent_manager

    AGENT_MANAGER_AVAILABLE = True
except ImportError:
    logger.error("❌ AgentManager not available - falling back to basic mode")
    AGENT_MANAGER_AVAILABLE = False


# Helper function for safe database logging
def log_to_database(
    tier: int, status: str, summary: str, details: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """Log watcher event to database safely."""
    if not EVENT_LOGGER_AVAILABLE:
        return None

    try:
        return log_watcher_check(
            tier=tier,
            status=status,
            summary=summary,
            details=details,
        )
    except Exception as e:
        logger.error(f"Failed to log to database: {e}")
        return None


# Configuration
EVENT_BRIDGE_URL = "http://localhost:9998"
BASIC_POLL_INTERVAL = 60  # seconds (basic system checks)
AI_ANALYSIS_INTERVAL = 600  # seconds (10 minutes for AI analysis - Tier 2)
COORDINATION_DIR = ELF_DIR / ".coordination"
STOP_FILE = COORDINATION_DIR / "watcher-stop"
WATCHER_LOG = COORDINATION_DIR / "watcher-log.md"


class ElfWatcher:
    """Watcher moderne intégré à AgentManager v2.0."""

    def __init__(self):
        self.event_bridge_url = EVENT_BRIDGE_URL
        self.basic_poll_interval = BASIC_POLL_INTERVAL
        self.ai_analysis_interval = AI_ANALYSIS_INTERVAL
        self.escalation_count = 0
        self.cycle_count = 0

        # NOUVEAU : Initialiser AgentManager
        self.agent_manager = None
        if AGENT_MANAGER_AVAILABLE:
            try:
                self.agent_manager = get_agent_manager()
                logger.info("✅ AgentManager initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize AgentManager: {e}")

    def check_event_bridge_health(self) -> bool:
        """Vérifier si l'Event Bridge est sain."""
        try:
            response = requests.get(f"{self.event_bridge_url}/status", timeout=5)
            return response.status_code == 200
        except:
            return False

    def gather_system_state(self) -> Dict[str, Any]:
        """Collecter l'état du système pour analyse."""
        state = {
            "timestamp": datetime.now().isoformat(),
            "event_bridge_healthy": self.check_event_bridge_health(),
            "services": {},
            "processes": {},
            "escalation_count": self.escalation_count,
            "cycle_count": self.cycle_count,
        }

        # Vérifier les services clés
        services_to_check = [
            ("dashboard_backend", "http://localhost:8888/api/v1/health/status"),
            ("event_bridge", "http://localhost:9998/status"),
        ]

        for service_name, health_url in services_to_check:
            try:
                response = requests.get(health_url, timeout=3)
                state["services"][service_name] = response.status_code == 200
                logger.debug(f"Service {service_name}: {response.status_code}")
            except Exception as e:
                state["services"][service_name] = False
                logger.debug(f"Service {service_name} check failed: {e}")

        # Vérifier le service Learning Capture via process
        try:
            import subprocess

            result = subprocess.run(
                ["pgrep", "-f", "background-learning-capture.py"],
                capture_output=True,
                text=True,
            )
            state["services"]["learning_capture"] = result.returncode == 0
        except Exception as e:
            state["services"]["learning_capture"] = False

        return state

    def analyze_with_agent_manager(
        self, system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        NOUVEAU : Analyser l'état du système via AgentManager.

        Utilise le vrai prompt système du fichier watcher.md
        au lieu de prompts hardcodés.
        """
        if not self.agent_manager:
            logger.warning("AgentManager not available, using fallback analysis")
            return self.fallback_analysis(system_state)

        try:
            # Préparer le contexte pour l'agent Watcher
            context = {
                "system_state": system_state,
                "analysis_type": "watcher_cycle",
                "timestamp": datetime.now().isoformat(),
                "cycle_count": self.cycle_count,
                "tier": 2,
            }

            logger.info(
                "🤖 Sending analysis request to Watcher agent via AgentManager..."
            )

            # Appeler l'agent Watcher avec son vrai prompt système
            result = self.agent_manager.watcher(
                request="Analyze the current system state and engage necessary actions if needed than make a concise report. "
                "Focus on: 1) Anomalies detected, "
                "2) Recommended actions.",
                context=context,
            )

            if result.get("success"):
                logger.info(
                    f"✅ Watcher analysis completed (session: {result.get('session_id', 'unknown')[:8]}...)"
                )

                # Parser la réponse de l'agent
                ai_response = result.get("response", "")

                return {
                    "status": self._parse_status_from_response(ai_response),
                    "analysis": ai_response,
                    "anomalies": self._extract_anomalies(ai_response),
                    "recommendations": self._extract_recommendations(ai_response),
                    "priority_actions": self._extract_priority_actions(ai_response),
                    "ai_processed": True,
                    "session_id": result.get("session_id"),
                    "model_used": result.get("model_used"),
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ Watcher agent failed: {error_msg}")
                return self.fallback_analysis(system_state, error_msg)

        except Exception as e:
            logger.error(f"❌ Error calling AgentManager: {e}")
            return self.fallback_analysis(system_state, str(e))

    def _parse_status_from_response(self, response: str) -> str:
        """Extraire le statut de la réponse de l'agent."""
        response_lower = response.lower()
        if any(
            word in response_lower for word in ["critical", "severe", "down", "failure"]
        ):
            return "critical"
        elif any(
            word in response_lower
            for word in ["warning", "degraded", "issue", "problem"]
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
            if "anomal" in line.lower() or "issue" in line.lower():
                in_anomalies_section = True
            elif in_anomalies_section and line.strip().startswith("-"):
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
            if "recommend" in line.lower() or "action" in line.lower():
                in_recommendations_section = True
            elif in_recommendations_section and line.strip().startswith("-"):
                recommendations.append(line.strip()[1:].strip())
            elif in_recommendations_section and line.strip() == "":
                in_recommendations_section = False

        return recommendations

    def _extract_priority_actions(self, response: str) -> List[str]:
        """Extraire les actions prioritaires de la réponse."""
        actions = []
        lines = response.split("\n")
        in_priority_section = False

        for line in lines:
            if "priority" in line.lower() or "immediate" in line.lower():
                in_priority_section = True
            elif in_priority_section and line.strip().startswith("-"):
                actions.append(line.strip()[1:].strip())
            elif in_priority_section and line.strip() == "":
                in_priority_section = False

        return actions

    def fallback_analysis(
        self, system_state: Dict[str, Any], error_msg: str = ""
    ) -> Dict[str, Any]:
        """Analyse de secours si AgentManager indisponible."""
        event_bridge_healthy = system_state.get("event_bridge_healthy", False)
        services_healthy = all(system_state.get("services", {}).values())

        if not event_bridge_healthy:
            status = "critical"
            analysis = f"Event Bridge non disponible. {error_msg}"
        elif not services_healthy:
            status = "warning"
            analysis = f"Certains services ne répondent pas. {error_msg}"
        else:
            status = "healthy"
            analysis = f"Tous les systèmes opérationnels (analyse IA indisponible: {error_msg})"

        return {
            "status": status,
            "analysis": analysis,
            "anomalies": [],
            "recommendations": [],
            "priority_actions": [],
            "ai_processed": False,
            "fallback": True,
        }

    def basic_analysis(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse basique sans appel IA."""
        event_bridge_healthy = system_state.get("event_bridge_healthy", False)
        services_healthy = all(system_state.get("services", {}).values())

        if not event_bridge_healthy:
            status = "critical"
            analysis_text = "Event Bridge non disponible"
        elif not services_healthy:
            status = "warning"
            analysis_text = "Certains services ne répondent pas"
        else:
            status = "healthy"
            analysis_text = "Tous les systèmes opérationnels (vérification basique)"

        return {
            "status": status,
            "analysis": analysis_text,
            "anomalies": [],
            "recommendations": [],
            "priority_actions": [],
            "ai_processed": False,
            "basic_only": True,
        }

    def submit_escalation(self, escalation_data: dict) -> dict:
        """Soumettre une escalade - utilise AgentManager directement (fallback sur Event Bridge)."""
        # ESSAI 1: Utiliser AgentManager directement (meilleure option)
        if AGENT_MANAGER_AVAILABLE:
            try:
                logger.info("🤖 Triggering AI agent analysis via AgentManager...")
                manager = get_agent_manager()

                # Construire le prompt d'analyse
                prompt = f"""@Unified-Orchestrator Analyze this watcher escalation:

System State: {json.dumps(escalation_data.get("system_state", {}), indent=2)}
Analysis: {json.dumps(escalation_data.get("analysis", {}), indent=2)}

Please:
1. Analyze the severity of the issue
2. Identify root causes
3. Depend of severity take or Recommend immediate actions
4. Create an escalation file in ceo-inbox/ if critical

Do your mission then Respond with a detailed analysis."""

                # Appeler l'agent unified-orchestrator
                response = manager.ask_agent("unified-orchestrator", prompt)

                logger.info("✅ AI agent analysis completed")

                # Créer un fichier d'escalade dans ceo-inbox
                escalation_id = escalation_data.get(
                    "escalation_id", f"esc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                escalation_file = (
                    ELF_DIR / "ceo-inbox" / f"escalation_{escalation_id}.md"
                )

                with open(escalation_file, "w") as f:
                    f.write(f"# Escalation: {escalation_id}\n\n")
                    f.write(f"**Source:** Watcher System\n\n")
                    f.write(f"**Time:** {datetime.now().isoformat()}\n\n")
                    f.write(
                        f"**System State:**\n```json\n{json.dumps(escalation_data.get('system_state', {}), indent=2)}\n```\n\n"
                    )
                    f.write(
                        f"**Watcher Analysis:**\n```json\n{json.dumps(escalation_data.get('analysis', {}), indent=2)}\n```\n\n"
                    )
                    f.write(f"**AI Agent Analysis:**\n{response}\n")

                logger.info(f"🚨 Escalation file created: {escalation_file}")

                return {
                    "status": "success",
                    "escalation_id": escalation_id,
                    "agent_analysis": "completed",
                    "file_created": str(escalation_file),
                    "agent_triggered": True,
                }

            except Exception as e:
                logger.error(f"❌ AgentManager failed: {e}")
                # Fallback vers Event Bridge
                logger.info("🔄 Falling back to Event Bridge...")

        # ESSAI 2: Fallback vers Event Bridge (si AgentManager échoue ou indisponible)
        try:
            response = requests.post(
                f"{self.event_bridge_url}/api/v1/mission",
                json={
                    "mission_type": "watcher_escalation",
                    "component": "elf_watcher",
                    "data": escalation_data,
                },
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Escalation submission failed: {response.status_code}")
                return {
                    "error": f"Escalation submission failed: {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Failed to submit escalation: {e}")
            return {"error": str(e)}

    def handle_escalation(
        self, analysis: Dict[str, Any], system_state: Dict[str, Any]
    ) -> bool:
        """Gérer les escalades via l'Event Bridge."""
        if analysis.get("status") != "critical":
            return False

        log_to_database(
            tier=1,
            status="warning",
            summary="Escalation needed - preparing submission",
            details={
                "escalation_count": self.escalation_count + 1,
                "analysis": analysis,
            },
        )

        escalation_data = {
            "analysis": analysis,
            "system_state": system_state,
            "source": "elf_watcher",
            "timestamp": datetime.now().isoformat(),
            "escalation_id": f"esc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }

        escalation_response = self.submit_escalation(escalation_data)

        if "error" not in escalation_response:
            logger.info(
                f"✅ Escalade soumise à l'Event Bridge: {escalation_data['escalation_id']}"
            )
            self.escalation_count += 1

            log_to_database(
                tier=1,
                status="success",
                summary=f"Escalation submitted: {escalation_data['escalation_id']}",
                details={
                    "escalation_count": self.escalation_count,
                    "escalation_id": escalation_data["escalation_id"],
                    "escalation_data": escalation_data,
                },
            )
            return True
        else:
            logger.error(
                f"❌ Échec de soumission d'escalation: {escalation_response['error']}"
            )
            log_to_database(
                tier=1,
                status="error",
                summary=f"Escalation submission failed",
                details={
                    "error": escalation_response.get("error"),
                    "escalation_id": escalation_data.get("escalation_id"),
                    "escalation_data": escalation_data,
                },
            )
            return False

    def log_findings(self, system_state: Dict[str, Any], analysis: Dict[str, Any]):
        """Enregistrer les résultats dans le journal."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = analysis.get("status", "unknown")
        analysis_text = analysis.get("analysis", "No analysis")

        log_entry = (
            f"{timestamp} | STATUS: {status} | NOTES: {analysis_text[:100]}...\n"
        )

        try:
            with open(WATCHER_LOG, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write to watcher log: {e}")

    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Exécuter un cycle de monitoring complet."""
        logger.info("🔍 ELF Watcher - Starting monitoring cycle...")

        log_to_database(
            tier=1,
            status="info",
            summary=f"Cycle {self.cycle_count} started",
            details={"cycle_count": self.cycle_count},
        )

        # Collecter l'état du système
        system_state = self.gather_system_state()

        # Vérifier si nous devons faire une analyse IA
        should_run_ai_analysis = (
            self.cycle_count % (self.ai_analysis_interval // self.basic_poll_interval)
        ) == 0

        if should_run_ai_analysis and AGENT_MANAGER_AVAILABLE:
            logger.info("🤖 Running AI analysis cycle via AgentManager")
            log_to_database(
                tier=2,
                status="info",
                summary="AI analysis cycle started via AgentManager",
                details={"cycle_count": self.cycle_count},
            )
            # NOUVEAU : Utiliser AgentManager au lieu de l'Event Bridge
            analysis = self.analyze_with_agent_manager(system_state)
        else:
            if not AGENT_MANAGER_AVAILABLE:
                logger.info("📋 Running basic system check (AgentManager unavailable)")
            else:
                logger.info("📋 Running basic system check only")
            analysis = self.basic_analysis(system_state)

        # Gérer les escalades si nécessaire
        escalation_needed = False
        if should_run_ai_analysis:
            escalation_needed = self.handle_escalation(analysis, system_state)

        # Enregistrer les résultats
        self.log_findings(system_state, analysis)

        # Log cycle completion
        cycle_status = analysis.get("status", "unknown")
        analysis_text = analysis.get("analysis", "")[:100]
        log_to_database(
            tier=1,
            status=cycle_status,
            summary=f"Cycle {self.cycle_count} completed - {cycle_status}: {analysis_text}...",
            details={
                "cycle_count": self.cycle_count,
                "ai_analysis_run": should_run_ai_analysis,
                "escalation_needed": escalation_needed,
                "ai_processed": analysis.get("ai_processed", False),
                "system_state": system_state,
                "analysis": analysis,
            },
        )

        # Afficher le statut
        self.display_status(
            system_state, analysis, escalation_needed, should_run_ai_analysis
        )

        result = {
            "timestamp": datetime.now().isoformat(),
            "system_state": system_state,
            "analysis": analysis,
            "escalation_needed": escalation_needed,
            "escalation_submitted": escalation_needed
            if should_run_ai_analysis
            else False,
            "ai_analysis_run": should_run_ai_analysis,
        }

        return result

    def display_status(
        self,
        system_state: Dict[str, Any],
        analysis: Dict[str, Any],
        escalation_needed: bool,
        ai_analysis_run: bool = False,
    ):
        """Afficher le statut du système."""
        status_emoji = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(
            analysis.get("status", "unknown"), "⚪"
        )

        event_bridge_healthy = system_state.get("event_bridge_healthy", False)
        event_bridge_status = "🟢 Intégré" if event_bridge_healthy else "🔴 Standalone"

        # NOUVEAU : Afficher le mode d'analyse
        if analysis.get("ai_processed"):
            ai_status = "🤖 AgentManager IA"
        elif analysis.get("fallback"):
            ai_status = "⚠️  Fallback (no IA)"
        else:
            ai_status = "📋 Basic Check"

        print(f"\n🔍 ELF Watcher - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        print(f"{status_emoji} Statut: {analysis.get('status', 'unknown').upper()}")
        print(f"🎯 Event Bridge: {event_bridge_status}")
        print(f"🤖 Analyse: {ai_status}")
        print(f"📊 Mode: {analysis.get('analysis', 'No analysis')[:60]}...")
        print(
            f"⏱️  Cycle: {self.cycle_count} ({'AI Analysis' if ai_analysis_run else 'Basic Check'})"
        )

        # Calculer le temps jusqu'à la prochaine analyse IA
        if ai_analysis_run:
            cycles_until_ai = self.ai_analysis_interval // self.basic_poll_interval
        else:
            cycles_until_ai = (
                self.ai_analysis_interval // self.basic_poll_interval
            ) - (
                self.cycle_count
                % (self.ai_analysis_interval // self.basic_poll_interval)
            )
        seconds_until_ai = cycles_until_ai * self.basic_poll_interval
        print(
            f"⏱️  Prochaine AI: {seconds_until_ai}s ({seconds_until_ai // 60}m {seconds_until_ai % 60}s)"
        )

        # Services
        services = system_state.get("services", {})
        print(f"\n🌐 Services:")
        for service, healthy in services.items():
            print(f"  {service}: {'🟢' if healthy else '🔴'}")

        # Escalades
        if escalation_needed:
            print(f"\n🚨 Escalade soumise à l'Event Bridge")

        print("\n" + "=" * 60)

    def start_continuous_monitoring(self):
        """Démarrer la surveillance continue."""
        logger.info(f"🚀 ELF Watcher v2.0 starting continuous monitoring")
        logger.info(f"   Basic checks: every {self.basic_poll_interval}s")
        logger.info(
            f"   AI analysis: every {self.ai_analysis_interval}s ({self.ai_analysis_interval // 60} minutes)"
        )

        if AGENT_MANAGER_AVAILABLE:
            logger.info(f"   ✅ AgentManager: ENABLED")
            logger.info(
                f"   📁 Agents loaded: {len(self.agent_manager.list_agents()) if self.agent_manager else 0}"
            )
        else:
            logger.warning(f"   ⚠️  AgentManager: DISABLED (fallback mode)")

        log_to_database(
            tier=1,
            status="info",
            summary="Watcher v2.0 process started - beginning continuous monitoring",
            details={
                "version": "2.0",
                "basic_interval": self.basic_poll_interval,
                "ai_analysis_interval": self.ai_analysis_interval,
                "agent_manager_available": AGENT_MANAGER_AVAILABLE,
            },
        )

        try:
            while True:
                # Vérifier le signal d'arrêt
                if STOP_FILE.exists():
                    logger.info("⏹️ Stop file detected, exiting gracefully")

                    log_to_database(
                        tier=1,
                        status="info",
                        summary="Stop file detected - watcher stopping gracefully",
                        details={
                            "total_cycles": self.cycle_count,
                            "total_escalations": self.escalation_count,
                        },
                    )
                    break

                # Incrémenter le compteur de cycles
                self.cycle_count += 1

                # Exécuter le cycle de monitoring
                self.run_monitoring_cycle()

                # Attendre le prochain cycle
                time.sleep(self.basic_poll_interval)

        except KeyboardInterrupt:
            logger.info("⏹️ Stopped by user")
            log_to_database(
                tier=1,
                status="info",
                summary="Watcher stopped by user (KeyboardInterrupt)",
                details={
                    "total_cycles": self.cycle_count,
                    "total_escalations": self.escalation_count,
                },
            )
        except Exception as e:
            logger.error(f"❌ ELF Watcher crashed: {e}")
            log_to_database(
                tier=1,
                status="error",
                summary=f"Watcher crashed: {str(e)}",
                details={
                    "total_cycles": self.cycle_count,
                    "total_escalations": self.escalation_count,
                    "error_type": type(e).__name__,
                },
            )
            raise


def main():
    """Point d'entrée principal."""
    watcher = ElfWatcher()
    watcher.start_continuous_monitoring()


if __name__ == "__main__":
    main()
