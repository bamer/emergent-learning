#!/usr/bin/env python3
"""
ELF Watcher System

Watcher modernisé qui utilise l'Event Bridge au lieu d'OpenCode directement.

Features:
- Utilise l'Event Bridge (port 9998) pour toutes les décisions
- Coordonne les escalades via l'API Event Bridge
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

    # Define fallback functions to prevent NameErrors
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
AI_ANALYSIS_INTERVAL = 300  # seconds (5 minutes for AI analysis)
COORDINATION_DIR = ELF_DIR / ".coordination"
STOP_FILE = COORDINATION_DIR / "watcher-stop"
WATCHER_LOG = COORDINATION_DIR / "watcher-log.md"


class ElfWatcher:
    """Watcher moderne intégré à l'Event Bridge."""

    def __init__(self):
        self.event_bridge_url = EVENT_BRIDGE_URL
        self.basic_poll_interval = BASIC_POLL_INTERVAL
        self.ai_analysis_interval = AI_ANALYSIS_INTERVAL
        self.escalation_count = 0
        self.cycle_count = 0

    def ask_event_bridge(self, request_type: str, data: dict) -> dict:
        """Demander des décisions à l'Event Bridge."""
        try:
            response = requests.post(
                f"{self.event_bridge_url}/api/v1/ask",
                json={
                    "component": "elf_watcher",
                    "request_type": request_type,
                    "data": data,
                    "priority": 2,  # Priorité élevée pour les escalades
                },
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    f"Event Bridge returned {response.status_code}: {response.text}"
                )
                return {"error": f"Event Bridge returned {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to ask Event Bridge: {e}")
            return {"error": str(e)}

    def submit_escalation(self, escalation_data: dict) -> dict:
        """Soumettre une escalade à l'Event Bridge pour traitement CEO."""
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
        }

        # Vérifier les services clés
        services_to_check = [
            ("dashboard_backend", "http://localhost:8888/api/v1/health/status"),
            ("mission_bridge", "http://localhost:9998/api/v1/health/mission_bridge"),
            (
                "sentinel_monitor",
                "http://localhost:9998/api/v1/health/sentinel_monitor",
            ),
        ]

        for service_name, health_url in services_to_check:
            try:
                response = requests.get(health_url, timeout=3)
                state["services"][service_name] = response.status_code == 200
            except:
                state["services"][service_name] = False

        return state

    def analyze_with_event_bridge(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyser l'état du système via l'Event Bridge."""
        event_bridge_response = self.ask_event_bridge(
            "system_analysis",
            {
                "system_state": system_state,
                "analysis_type": "watcher_cycle",
                "timestamp": datetime.now().isoformat(),
            },
        )

        if "error" not in event_bridge_response:
            return event_bridge_response.get("data", {})

        # Fallback analysis si Event Bridge indisponible
        return self.fallback_analysis(system_state)

    def fallback_analysis(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse de secours si Event Bridge indisponible."""
        event_bridge_healthy = system_state.get("event_bridge_healthy", False)
        services_healthy = all(system_state.get("services", {}).values())

        if not event_bridge_healthy:
            status = "critical"
            analysis = "Event Bridge non disponible"
        elif not services_healthy:
            status = "warning"
            analysis = "Certains services ne répondent pas"
        else:
            status = "healthy"
            analysis = "Tous les systèmes opérationnels"

        return {
            "status": status,
            "analysis": analysis,
            "anomalies": [],
            "recommendations": [],
            "priority_actions": [],
        }

    def basic_analysis(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse basique sans appel à l'Event Bridge."""
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
        }

    def handle_escalation(
        self, analysis: Dict[str, Any], system_state: Dict[str, Any]
    ) -> bool:
        """Gérer les escalades via l'Event Bridge."""
        if analysis.get("status") != "critical":
            return False  # Pas besoin d'escalade

        # Log escalation attempt to database
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

            # Log successful escalation to database
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
            # Log failed escalation to database
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

        log_entry = f"{timestamp} | STATUS: {status} | NOTES: {analysis_text}\n"

        try:
            with open(WATCHER_LOG, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write to watcher log: {e}")

    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Exécuter un cycle de monitoring complet."""
        logger.info("🔍 ELF Watcher - Starting monitoring cycle...")

        # Log cycle start to database
        log_to_database(
            tier=1,
            status="info",
            summary=f"Cycle {self.cycle_count} started",
            details={"cycle_count": self.cycle_count},
        )

        # Collecter l'état du système
        system_state = self.gather_system_state()

        # Vérifier si nous devons faire une analyse AI (tous les 5 cycles si basic_poll_interval = 60s)
        should_run_ai_analysis = (
            self.cycle_count % (self.ai_analysis_interval // self.basic_poll_interval)
        ) == 0

        if should_run_ai_analysis:
            logger.info("🤖 Running AI analysis cycle")
            # Log AI analysis start
            log_to_database(
                tier=2,
                status="info",
                summary="AI analysis cycle started",
                details={"cycle_count": self.cycle_count},
            )
            # Analyser via Event Bridge
            analysis = self.analyze_with_event_bridge(system_state)
        else:
            # Analyse basique seulement
            logger.info("📋 Running basic system check only")
            analysis = self.basic_analysis(system_state)

        # Gérer les escalades si nécessaire (seulement pour AI analysis)
        escalation_needed = False
        if should_run_ai_analysis:
            escalation_needed = self.handle_escalation(analysis, system_state)

        # Enregistrer les résultats
        self.log_findings(system_state, analysis)

        # Log cycle completion to database
        cycle_status = analysis.get("status", "unknown")
        analysis_text = analysis.get("analysis", "")
        log_to_database(
            tier=1,
            status=cycle_status,
            summary=f"Cycle {self.cycle_count} completed - {cycle_status}: {analysis_text}",
            details={
                "cycle_count": self.cycle_count,
                "ai_analysis_run": should_run_ai_analysis,
                "escalation_needed": escalation_needed,
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

        print(f"\n🔍 ELF Watcher - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        print(f"{status_emoji} Statut: {analysis.get('status', 'unknown').upper()}")
        print(f"🎯 Event Bridge: {event_bridge_status}")
        print(f"📊 Analyse: {analysis.get('analysis', 'No analysis')}")
        print(
            f"⏱️  Cycle: {self.cycle_count} ({'AI Analysis' if ai_analysis_run else 'Basic Check'})"
        )

        # Calculer le temps jusqu'à la prochaine analyse AI
        cycles_until_ai = (self.ai_analysis_interval // self.basic_poll_interval) - (
            self.cycle_count % (self.ai_analysis_interval // self.basic_poll_interval)
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
        logger.info(f"🚀 ELF Watcher starting continuous monitoring")
        logger.info(f"   Basic checks: every {self.basic_poll_interval}s")
        logger.info(
            f"   AI analysis: every {self.ai_analysis_interval}s ({self.ai_analysis_interval // 60} minutes)"
        )

        # Log watcher start to database
        log_to_database(
            tier=1,
            status="info",
            summary="Watcher process started - beginning continuous monitoring",
            details={
                "basic_interval": self.basic_poll_interval,
                "ai_analysis_interval": self.ai_analysis_interval,
            },
        )

        try:
            while True:
                # Vérifier le signal d'arrêt
                if STOP_FILE.exists():
                    logger.info("⏹️ Stop file detected, exiting gracefully")

                    # Log watcher stop to database
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
            # Log keyboard interrupt to database
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
            # Log crash to database
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
