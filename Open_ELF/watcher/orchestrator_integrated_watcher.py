#!/usr/bin/env python3
"""
Orchestrator-Integrated Watcher System

Watcher modernisé qui utilise l'orchestrateur unifié au lieu d'OpenCode directement.

Features:
- Utilise l'orchestrateur unifié (port 9998) pour toutes les décisions
- Coordonne les escalades via l'API orchestrateur
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
    from agents.logger import setup_logger

    logger = setup_logger("orchestrator_watcher")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("orchestrator_watcher")

# Configuration
ORCHESTRATOR_URL = "http://localhost:9998"
POLL_INTERVAL = 30  # seconds
COORDINATION_DIR = ELF_DIR / ".coordination"
STOP_FILE = COORDINATION_DIR / "watcher-stop"
WATCHER_LOG = COORDINATION_DIR / "watcher-log.md"


class OrchestratorWatcher:
    """Watcher moderne intégré à l'orchestrateur unifié."""

    def __init__(self):
        self.orchestrator_url = ORCHESTRATOR_URL
        self.poll_interval = POLL_INTERVAL
        self.escalation_count = 0

    def ask_orchestrator(self, request_type: str, data: dict) -> dict:
        """Demander des décisions à l'orchestrateur unifié."""
        try:
            response = requests.post(
                f"{self.orchestrator_url}/api/v1/ask",
                json={
                    "component": "orchestrator_watcher",
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
                    f"Orchestrator returned {response.status_code}: {response.text}"
                )
                return {"error": f"Orchestrator returned {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to ask orchestrator: {e}")
            return {"error": str(e)}

    def submit_escalation(self, escalation_data: dict) -> dict:
        """Soumettre une escalade à l'orchestrateur pour traitement CEO."""
        try:
            response = requests.post(
                f"{self.orchestrator_url}/api/v1/mission",
                json={
                    "mission_type": "watcher_escalation",
                    "component": "orchestrator_watcher",
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

    def check_orchestrator_health(self) -> bool:
        """Vérifier si l'orchestrateur est sain."""
        try:
            response = requests.get(f"{self.orchestrator_url}/status", timeout=5)
            return response.status_code == 200
        except:
            return False

    def gather_system_state(self) -> Dict[str, Any]:
        """Collecter l'état du système pour analyse."""
        state = {
            "timestamp": datetime.now().isoformat(),
            "orchestrator_healthy": self.check_orchestrator_health(),
            "services": {},
            "processes": {},
            "escalation_count": self.escalation_count,
        }

        # Vérifier les services clés
        services_to_check = [
            ("dashboard_backend", "http://localhost:8888/api/v1/health"),
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

    def analyze_with_orchestrator(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyser l'état du système via l'orchestrateur."""
        orchestrator_response = self.ask_orchestrator(
            "system_analysis",
            {
                "system_state": system_state,
                "analysis_type": "watcher_cycle",
                "timestamp": datetime.now().isoformat(),
            },
        )

        if "error" not in orchestrator_response:
            return orchestrator_response.get("data", {})

        # Fallback analysis si orchestrateur indisponible
        return self.fallback_analysis(system_state)

    def fallback_analysis(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse de secours si orchestrateur indisponible."""
        orchestrator_healthy = system_state.get("orchestrator_healthy", False)
        services_healthy = all(system_state.get("services", {}).values())

        if not orchestrator_healthy:
            status = "critical"
            analysis = "Orchestrator unifié non disponible"
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

    def handle_escalation(
        self, analysis: Dict[str, Any], system_state: Dict[str, Any]
    ) -> bool:
        """Gérer les escalades via l'orchestrateur."""
        if analysis.get("status") != "critical":
            return False  # Pas besoin d'escalade

        escalation_data = {
            "analysis": analysis,
            "system_state": system_state,
            "source": "orchestrator_watcher",
            "timestamp": datetime.now().isoformat(),
            "escalation_id": f"esc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }

        escalation_response = self.submit_escalation(escalation_data)

        if "error" not in escalation_response:
            logger.info(
                f"✅ Escalade soumise à l'orchestrateur: {escalation_data['escalation_id']}"
            )
            self.escalation_count += 1
            return True
        else:
            logger.error(
                f"❌ Échec de soumission d'escalade: {escalation_response['error']}"
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
        logger.info("🔍 Orchestrator Watcher - Starting monitoring cycle...")

        # Collecter l'état du système
        system_state = self.gather_system_state()

        # Analyser via orchestrateur
        analysis = self.analyze_with_orchestrator(system_state)

        # Gérer les escalades si nécessaire
        escalation_needed = self.handle_escalation(analysis, system_state)

        # Enregistrer les résultats
        self.log_findings(system_state, analysis)

        # Afficher le statut
        self.display_status(system_state, analysis, escalation_needed)

        result = {
            "timestamp": datetime.now().isoformat(),
            "system_state": system_state,
            "analysis": analysis,
            "escalation_needed": escalation_needed,
            "escalation_submitted": escalation_needed,
        }

        return result

    def display_status(
        self,
        system_state: Dict[str, Any],
        analysis: Dict[str, Any],
        escalation_needed: bool,
    ):
        """Afficher le statut du système."""
        status_emoji = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(
            analysis.get("status", "unknown"), "⚪"
        )

        orchestrator_healthy = system_state.get("orchestrator_healthy", False)
        orchestrator_status = "🟢 Intégré" if orchestrator_healthy else "🔴 Standalone"

        print(f"\n🔍 Orchestrator Watcher - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        print(f"{status_emoji} Statut: {analysis.get('status', 'unknown').upper()}")
        print(f"🎯 Orchestrateur: {orchestrator_status}")
        print(f"📊 Analyse: {analysis.get('analysis', 'No analysis')}")

        # Services
        services = system_state.get("services", {})
        print(f"\n🌐 Services:")
        for service, healthy in services.items():
            print(f"  {service}: {'🟢' if healthy else '🔴'}")

        # Escalades
        if escalation_needed:
            print(f"\n🚨 Escalade soumise à l'orchestrateur")

        print("\n" + "=" * 60)

    def start_continuous_monitoring(self):
        """Démarrer la surveillance continue."""
        logger.info(
            f"🚀 Orchestrator Watcher starting continuous monitoring (interval: {self.poll_interval}s)"
        )

        try:
            while True:
                # Vérifier le signal d'arrêt
                if STOP_FILE.exists():
                    logger.info("⏹️ Stop file detected, exiting gracefully")
                    break

                # Exécuter le cycle de monitoring
                self.run_monitoring_cycle()

                # Attendre le prochain cycle
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("⏹️ Stopped by user")
        except Exception as e:
            logger.error(f"❌ Orchestrator Watcher crashed: {e}")
            raise


def main():
    """Point d'entrée principal."""
    watcher = OrchestratorWatcher()
    watcher.start_continuous_monitoring()


if __name__ == "__main__":
    main()
