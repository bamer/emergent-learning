#!/usr/bin/env python3
"""
ELF Unified Agent Orchestrator
==============================

Système d'orchestration unifié pour tous les agents ELF avec OpenCode.

Exigences respectées:
1. Système unique utilisé partout
2. Fiable et facile à utiliser (spawn/stop agents)
3. Arrêt propre des agents
4. Coordination Sentinel + Watcher + 4 agents avec escalation
5. Logging centralisé dans /home/bamer/.opencode/emergent-learning/logs/
6. Politique "ça marche ou ça crash" - aucune erreur silencieuse

Usage:
    python unified_orchestrator.py start        # Démarre l'orchestrateur
    python unified_orchestrator.py stop         # Arrête tout
    python unified_orchestrator.py status       # Status des agents
    python unified_orchestrator.py spawn <agent> # Spawn un agent spécifique
    python unified_orchestrator.py kill <agent>  # Kill un agent spécifique

Agents disponibles:
    - orchestrator: Orchestrateur central
    - sentinel: Surveillance continue
    - watcher: Vérifications périodiques
    - researcher: Investigation
    - architect: Conception
    - skeptic: Analyse critique
    - creative: Innovation
    - ceo: Décisions exécutives
"""

import json
import time
import logging
import sqlite3
import requests
import threading
import atexit
import os
import sys
import signal
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass, field

# Import centralized logging
from elf_logging import (
    get_logger,
    log_critical,
    log_error,
    log_warning,
    log_info,
    verify_logging,
)

# Configuration
ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")
LOGS_DIR = ELF_DIR / "logs"
COORDINATION_DIR = ELF_DIR / ".coordination"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
COORDINATION_DIR.mkdir(parents=True, exist_ok=True)

# Logger principal
logger = get_logger("unified_orchestrator")


class AgentStatus(Enum):
    """États du cycle de vie d'un agent."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"
    CRASHED = "crashed"


class AgentType(Enum):
    """Types d'agents avec leurs rôles."""

    ORCHESTRATOR = "orchestrator"
    SENTINEL = "sentinel"
    WATCHER = "watcher"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    SKEPTIC = "skeptic"
    CREATIVE = "creative"
    CEO = "ceo"


@dataclass
class AgentDefinition:
    """Définition d'un agent avec sa configuration."""

    agent_type: AgentType
    name: str
    description: str
    icon: str
    priority: int = 5
    auto_start: bool = False
    session_timeout: int = 3600
    restart_on_crash: bool = True
    max_restarts: int = 3
    status: AgentStatus = field(default=AgentStatus.STOPPED)
    session_id: Optional[str] = None
    last_activity: Optional[datetime] = None
    start_time: Optional[datetime] = None
    error_count: int = 0
    restart_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class EscalationManager:
    """Gestionnaire d'escalade pour coordonner les agents."""

    def __init__(self, orchestrator: "UnifiedOrchestrator"):
        self.orchestrator = orchestrator
        self.escalation_history: List[Dict] = []
        self.logger = get_logger("escalation")

    def escalate(self, from_agent: AgentType, issue: str, severity: str = "warning"):
        """Escalade un problème au niveau approprié."""
        self.logger.info(f"🚨 ESCALATION: {from_agent.value} -> {severity}: {issue}")

        escalation = {
            "timestamp": datetime.now().isoformat(),
            "from": from_agent.value,
            "issue": issue,
            "severity": severity,
        }
        self.escalation_history.append(escalation)

        # Politique d'escalade stricte
        if severity == "critical":
            # Crash immédiat pour les erreurs critiques
            self.logger.critical(f"CRITICAL ERROR - CRASHING SYSTEM: {issue}")
            self._handle_critical_crash(from_agent, issue)
        elif severity == "error":
            # Redémarrage de l'agent
            self.logger.error(
                f"Restarting agent {from_agent.value} due to error: {issue}"
            )
            self.orchestrator.restart_agent(from_agent)
        elif severity == "warning":
            # Notification au CEO si disponible
            if self.orchestrator.agents[AgentType.CEO].status == AgentStatus.RUNNING:
                self._notify_ceo(from_agent, issue)

    def _handle_critical_crash(self, agent: AgentType, issue: str):
        """Gère un crash critique - arrête tout proprement."""
        self.logger.critical(
            f"System crash initiated due to critical error in {agent.value}"
        )

        # Créer un fichier de crash pour investigation
        crash_file = LOGS_DIR / f"CRASH_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        crash_info = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent.value,
            "issue": issue,
            "system_state": self.orchestrator.get_agent_status(),
        }
        crash_file.write_text(json.dumps(crash_info, indent=2))

        # Arrêt brutal mais propre
        self.orchestrator.emergency_shutdown()

        # Sortie avec code d'erreur
        sys.exit(1)

    def _notify_ceo(self, from_agent: AgentType, issue: str):
        """Notifie l'agent CEO d'un problème."""
        ceo_agent = self.orchestrator.agents.get(AgentType.CEO)
        if ceo_agent and ceo_agent.status == AgentStatus.RUNNING:
            self.logger.info(f"Notifying CEO of issue from {from_agent.value}: {issue}")


class UnifiedOrchestrator:
    """
    Orchestrateur unifié pour tous les agents ELF.

    Respecte les exigences:
    - Un seul système utilisé partout
    - Spawn/Stop fiables
    - Coordination avec escalation
    - Logging centralisé
    - Politique crash (ça marche ou ça crash)
    """

    def __init__(self, server_url: str = "http://localhost:4096"):
        self.server_url = server_url
        self.db_path = ELF_DIR / "memory" / "index.db"
        self.logger = get_logger("unified_orchestrator")

        # Vérifier que le logging fonctionne
        try:
            verify_logging()
        except Exception as e:
            print(f"FATAL: Logging verification failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Agents registry
        self.agents = self._initialize_agents()

        # Escalation manager
        self.escalation = EscalationManager(self)

        # State
        self.running = False
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        self.start_time = None

        # Stats
        self.stats = {
            "agents_started": 0,
            "agents_stopped": 0,
            "agents_crashed": 0,
            "errors_handled": 0,
            "escalations": 0,
            "uptime_seconds": 0,
        }

        # Register cleanup
        atexit.register(self.shutdown)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self.logger.info("UnifiedOrchestrator initialized")

    def _signal_handler(self, signum, frame):
        """Gère les signaux d'arrêt."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)

    def _initialize_agents(self) -> Dict[AgentType, AgentDefinition]:
        """Initialise tous les agents avec leurs configurations."""
        agents = {}

        agents[AgentType.ORCHESTRATOR] = AgentDefinition(
            agent_type=AgentType.ORCHESTRATOR,
            name="Orchestrateur Unifié",
            description="Coordination centrale de tous les agents",
            icon="🎯",
            priority=1,
            auto_start=True,
            restart_on_crash=False,  # L'orchestrateur ne doit pas redémarrer lui-même
        )

        agents[AgentType.SENTINEL] = AgentDefinition(
            agent_type=AgentType.SENTINEL,
            name="Sentinel",
            description="Surveillance continue et détection de patterns",
            icon="🔍",
            priority=2,
            auto_start=True,
            session_timeout=0,  # 0 = pas de timeout (surveillance continue)
        )

        agents[AgentType.WATCHER] = AgentDefinition(
            agent_type=AgentType.WATCHER,
            name="Watcher",
            description="Vérifications périodiques et interventions",
            icon="👁️",
            priority=3,
            auto_start=True,
            session_timeout=300,  # 5 minutes
        )

        agents[AgentType.RESEARCHER] = AgentDefinition(
            agent_type=AgentType.RESEARCHER,
            name="Researcher",
            description="Investigation approfondie et collecte d'evidence",
            icon="🔬",
            priority=4,
            auto_start=False,
        )

        agents[AgentType.ARCHITECT] = AgentDefinition(
            agent_type=AgentType.ARCHITECT,
            name="Architect",
            description="Conception système et planification structure",
            icon="🏗️",
            priority=5,
            auto_start=False,
        )

        agents[AgentType.SKEPTIC] = AgentDefinition(
            agent_type=AgentType.SKEPTIC,
            name="Skeptic",
            description="Analyse critique et identification des risques",
            icon="❓",
            priority=6,
            auto_start=False,
        )

        agents[AgentType.CREATIVE] = AgentDefinition(
            agent_type=AgentType.CREATIVE,
            name="Creative",
            description="Innovation et génération de solutions",
            icon="💡",
            priority=7,
            auto_start=False,
        )

        agents[AgentType.CEO] = AgentDefinition(
            agent_type=AgentType.CEO,
            name="CEO",
            description="Décisions exécutives et direction stratégique",
            icon="👑",
            priority=1,
            auto_start=False,
        )

        return agents

    def spawn_agent(self, agent_type: AgentType) -> bool:
        """
        Spawn un agent spécifique.

        Returns:
            bool: True si succès, False sinon (et log l'erreur)
        """
        if agent_type not in self.agents:
            self.logger.error(f"Type d'agent inconnu: {agent_type}")
            return False

        agent = self.agents[agent_type]

        if agent.status != AgentStatus.STOPPED:
            self.logger.warning(f"Agent {agent.name} déjà en état {agent.status.value}")
            return False

        try:
            self.logger.info(f"🚀 Spawning agent: {agent.name}")
            agent.status = AgentStatus.STARTING

            # Créer une session OpenCode
            session_data = self._create_session(agent)

            if session_data:
                agent.session_id = session_data["id"]
                agent.status = AgentStatus.RUNNING
                agent.last_activity = datetime.now()
                agent.start_time = datetime.now()
                agent.error_count = 0
                agent.restart_count = 0

                self.stats["agents_started"] += 1
                self.logger.info(
                    f"✅ Agent {agent.name} spawné (session: {agent.session_id})"
                )
                return True
            else:
                agent.status = AgentStatus.ERROR
                agent.error_count += 1
                self.logger.error(f"❌ Échec du spawn de l'agent {agent.name}")
                return False

        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_count += 1
            self.logger.error(f"❌ Exception lors du spawn de {agent.name}: {e}")
            # Politique: on escalate immédiatement
            self.escalation.escalate(agent_type, f"Spawn failed: {e}", "error")
            return False

    def kill_agent(self, agent_type: AgentType, force: bool = False) -> bool:
        """
        Arrête (kill) un agent spécifique.

        Args:
            agent_type: Type de l'agent à arrêter
            force: Si True, force l'arrêt immédiat

        Returns:
            bool: True si succès, False sinon
        """
        if agent_type not in self.agents:
            self.logger.error(f"Type d'agent inconnu: {agent_type}")
            return False

        agent = self.agents[agent_type]

        if agent.status == AgentStatus.STOPPED:
            self.logger.warning(f"Agent {agent.name} déjà arrêté")
            return True

        try:
            self.logger.info(f"🛑 Killing agent: {agent.name} (force={force})")
            agent.status = AgentStatus.STOPPING

            # Fermer la session OpenCode
            if agent.session_id:
                if force:
                    # Kill immédiat
                    self._force_kill_session(agent)
                else:
                    # Arrêt gracieux
                    success = self._close_session(agent)
                    if not success:
                        self.logger.warning(
                            f"Graceful stop failed, forcing kill for {agent.name}"
                        )
                        self._force_kill_session(agent)

                agent.session_id = None

            agent.status = AgentStatus.STOPPED
            self.stats["agents_stopped"] += 1
            self.logger.info(f"✅ Agent {agent.name} arrêté")
            return True

        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_count += 1
            self.logger.error(f"❌ Exception lors de l'arrêt de {agent.name}: {e}")
            if force:
                # Si même le force kill échoue, on escalate
                self.escalation.escalate(
                    agent_type, f"Force kill failed: {e}", "critical"
                )
            return False

    def restart_agent(self, agent_type: AgentType) -> bool:
        """Redémarre un agent."""
        self.logger.info(f"🔄 Restarting agent: {agent_type.value}")

        # Kill d'abord
        if not self.kill_agent(agent_type, force=True):
            self.logger.error(f"Failed to kill agent {agent_type.value} for restart")
            return False

        # Petite pause
        time.sleep(1)

        # Respawn
        agent = self.agents[agent_type]
        agent.restart_count += 1

        if agent.restart_count > agent.max_restarts:
            self.logger.critical(
                f"Agent {agent.name} exceeded max restarts ({agent.max_restarts})"
            )
            self.escalation.escalate(agent_type, "Max restarts exceeded", "critical")
            return False

        return self.spawn_agent(agent_type)

    def _persist_state(self):
        """Persist current state to disk."""
        from orchestrator_state import get_state

        state_manager = get_state()
        status = self.get_agent_status()
        state_manager.save_state(status)

    def start(self):
        """Démarre l'orchestrateur et les agents auto-start."""
        self.logger.info("=" * 70)
        self.logger.info("🚀 Démarrage de l'Orchestrateur Unifié ELF")
        self.logger.info("=" * 70)

        self.running = True
        self.start_time = datetime.now()

        # Marquer l'orchestrateur comme running
        self.agents[AgentType.ORCHESTRATOR].status = AgentStatus.RUNNING
        self.agents[AgentType.ORCHESTRATOR].start_time = datetime.now()

        # Démarrer les agents auto-start
        for agent_type, agent_def in self.agents.items():
            if agent_def.auto_start and agent_type != AgentType.ORCHESTRATOR:
                success = self.spawn_agent(agent_type)
                if not success:
                    self.logger.error(f"Failed to auto-start agent {agent_def.name}")
                    # Politique crash: si un agent critique ne démarre pas, on crash
                    if agent_type in [AgentType.SENTINEL, AgentType.WATCHER]:
                        self.escalation.escalate(
                            agent_type,
                            f"Critical agent {agent_def.name} failed to start",
                            "critical",
                        )

        # Démarrer le thread de monitoring
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        # Start state persistence thread
        self.persistence_thread = threading.Thread(
            target=self._persistence_loop, daemon=True
        )
        self.persistence_thread.start()

        self.logger.info("✅ Orchestrateur démarré avec succès")
        self._log_status()

        # Persist initial state
        self._persist_state()

    def _persistence_loop(self):
        """Background thread to persist state periodically."""
        while self.running and not self.shutdown_event.is_set():
            try:
                self._persist_state()
                self.shutdown_event.wait(10)  # Persist every 10 seconds
            except Exception as e:
                self.logger.error(f"Error in persistence loop: {e}")

    def shutdown(self):
        """Arrêt gracieux de tous les agents."""
        if not self.running:
            return

        self.logger.info("🛑 Arrêt de l'orchestrateur...")
        self.running = False
        self.shutdown_event.set()

        # Arrêter tous les agents dans l'ordre inverse de priorité
        sorted_agents = sorted(
            self.agents.items(), key=lambda x: x[1].priority, reverse=True
        )

        for agent_type, agent_def in sorted_agents:
            if agent_type != AgentType.ORCHESTRATOR:
                self.kill_agent(agent_type)

        # Attendre le thread de monitoring
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)

        # Mettre à jour les stats
        if self.start_time:
            self.stats["uptime_seconds"] = (
                datetime.now() - self.start_time
            ).total_seconds()

        self.agents[AgentType.ORCHESTRATOR].status = AgentStatus.STOPPED
        self.logger.info("✅ Orchestrateur arrêté")

    def emergency_shutdown(self):
        """Arrêt d'urgence - kill immédiat de tout."""
        self.logger.critical("🚨 EMERGENCY SHUTDOWN INITIATED")
        self.running = False

        for agent_type, agent_def in self.agents.items():
            if (
                agent_type != AgentType.ORCHESTRATOR
                and agent_def.status != AgentStatus.STOPPED
            ):
                try:
                    self._force_kill_session(agent_def)
                    agent_def.status = AgentStatus.STOPPED
                except:
                    pass

        self.agents[AgentType.ORCHESTRATOR].status = AgentStatus.STOPPED

    def _monitoring_loop(self):
        """Boucle de monitoring en arrière-plan."""
        self.logger.info("🔍 Démarrage de la boucle de monitoring")

        while self.running and not self.shutdown_event.is_set():
            try:
                current_time = datetime.now()

                for agent_type, agent in self.agents.items():
                    if agent_type == AgentType.ORCHESTRATOR:
                        continue

                    if agent.status == AgentStatus.RUNNING:
                        # Vérifier le timeout de session
                        if agent.session_timeout > 0 and agent.last_activity:
                            idle_time = (
                                current_time - agent.last_activity
                            ).total_seconds()
                            if idle_time > agent.session_timeout:
                                self.logger.info(
                                    f"⏰ Timeout de session pour {agent.name}"
                                )
                                self.kill_agent(agent_type)

                    elif agent.status == AgentStatus.ERROR:
                        # Tenter de redémarrer si configuré
                        if (
                            agent.restart_on_crash
                            and agent.restart_count < agent.max_restarts
                        ):
                            self.logger.info(
                                f"🔄 Tentative de redémarrage de {agent.name}"
                            )
                            self.restart_agent(agent_type)
                        else:
                            # Trop de redémarrages - escalate
                            self.escalation.escalate(
                                agent_type,
                                f"Agent en erreur persistante (restarts: {agent.restart_count})",
                                "error",
                            )

                # Vérifier toutes les 30 secondes
                self.shutdown_event.wait(30)

            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de monitoring: {e}")
                # Politique: si le monitoring plante, c'est critique
                self.escalation.escalate(
                    AgentType.ORCHESTRATOR, f"Monitoring loop error: {e}", "critical"
                )

    def _create_session(self, agent: AgentDefinition) -> Optional[Dict[str, Any]]:
        """Crée une session OpenCode pour un agent."""
        try:
            response = requests.post(
                f"{self.server_url}/session",
                json={"title": f"ELF Agent: {agent.name}"},
                timeout=10,
            )

            if response.status_code in [200, 201]:
                return response.json()
            else:
                self.logger.error(
                    f"Échec création session pour {agent.name}: {response.status_code}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Exception création session pour {agent.name}: {e}")
            return None

    def _close_session(self, agent: AgentDefinition) -> bool:
        """Ferme une session OpenCode gracieusement."""
        if not agent.session_id:
            return True

        try:
            response = requests.delete(
                f"{self.server_url}/session/{agent.session_id}", timeout=5
            )
            return response.status_code in [200, 204, 404]
        except Exception as e:
            self.logger.error(f"Exception fermeture session pour {agent.name}: {e}")
            return False

    def _force_kill_session(self, agent: AgentDefinition):
        """Force la fermeture d'une session."""
        if not agent.session_id:
            return

        try:
            # Tentative avec timeout très court
            requests.delete(f"{self.server_url}/session/{agent.session_id}", timeout=1)
        except:
            pass  # On ignore les erreurs en force kill

    def get_agent_status(self) -> Dict[str, Any]:
        """Retourne le status de tous les agents."""
        agent_statuses = {}
        for agent_type, agent in self.agents.items():
            agent_statuses[agent_type.value] = {
                "name": agent.name,
                "status": agent.status.value,
                "icon": agent.icon,
                "session_id": agent.session_id,
                "error_count": agent.error_count,
                "restart_count": agent.restart_count,
                "last_activity": agent.last_activity.isoformat()
                if agent.last_activity
                else None,
                "start_time": agent.start_time.isoformat()
                if agent.start_time
                else None,
            }

        uptime = 0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "orchestrator": {
                "running": self.running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "uptime_seconds": int(uptime),
            },
            "agents": agent_statuses,
            "stats": self.stats.copy(),
            "escalations": len(self.escalation.escalation_history),
        }

    def _log_status(self):
        """Log le status actuel."""
        status = self.get_agent_status()
        active_count = sum(
            1 for a in status["agents"].values() if a["status"] == "running"
        )

        self.logger.info(f"Status: {active_count} agents actifs")
        for agent_info in status["agents"].values():
            emoji = {
                "running": "🟢",
                "stopped": "⚪",
                "error": "🔴",
                "crashed": "💥",
            }.get(agent_info["status"], "⚪")
            self.logger.info(
                f"  {agent_info['icon']} {agent_info['name']}: {emoji} {agent_info['status']}"
            )


def main():
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(description="ELF Unified Orchestrator")
    parser.add_argument(
        "command", choices=["start", "stop", "status", "spawn", "kill", "restart"]
    )
    parser.add_argument("--agent", help="Agent type for spawn/kill/restart")
    parser.add_argument("--force", action="store_true", help="Force kill")

    args = parser.parse_args()

    # Suppress stdout logging for CLI commands (logs still go to files)
    if args.command in ["status", "spawn", "kill", "restart"]:
        import logging

        # Remove all handlers from root logger that output to stdout
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if (
                isinstance(handler, logging.StreamHandler)
                and handler.stream == sys.stdout
            ):
                root_logger.removeHandler(handler)
        # Also suppress our loggers
        logging.getLogger("elf").setLevel(logging.WARNING)
        logging.getLogger("unified_orchestrator").setLevel(logging.WARNING)

    orchestrator = UnifiedOrchestrator()

    if args.command == "start":
        orchestrator.start()

        # Keep running
        try:
            while orchestrator.running:
                time.sleep(1)
        except KeyboardInterrupt:
            orchestrator.shutdown()

    elif args.command == "stop":
        orchestrator.shutdown()

    elif args.command == "status":
        # For status, read from persistent state if available
        from orchestrator_state import get_state

        state_manager = get_state()
        persisted_state = state_manager.load_state()

        if persisted_state:
            # Use persisted state
            status = persisted_state
        else:
            # Fallback to current instance state
            status = orchestrator.get_agent_status()

        print(json.dumps(status, indent=2))

    elif args.command == "spawn":
        if not args.agent:
            print("Error: --agent required")
            sys.exit(1)
        agent_type = AgentType(args.agent)
        success = orchestrator.spawn_agent(agent_type)
        sys.exit(0 if success else 1)

    elif args.command == "kill":
        if not args.agent:
            print("Error: --agent required")
            sys.exit(1)
        agent_type = AgentType(args.agent)
        success = orchestrator.kill_agent(agent_type, force=args.force)
        sys.exit(0 if success else 1)

    elif args.command == "restart":
        if not args.agent:
            print("Error: --agent required")
            sys.exit(1)
        agent_type = AgentType(args.agent)
        success = orchestrator.restart_agent(agent_type)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
