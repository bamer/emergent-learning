#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
AgentManager - Gestionnaire d'agents standard OpenCode

Ce module gère les agents IA en chargeant leurs définitions depuis les fichiers .md
et en maintenant des sessions persistantes par agent.

Usage:
    from agents.agent_manager import AgentManager

    manager = AgentManager()

    # Interroger un agent spécifique
    response = manager.ask_agent("sentinel", "Analyze system health and report anomalies")

    # Ou utiliser la méthode de convenance
    result = manager.sentinel("Check all services status")
"""

import json
import time as _time
import traceback
import threading
import traceback as _traceback

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import (
        get_logger,
        log_critical,
        log_error,
        log_warning,
        log_info,
    )

    logger = get_logger("agent_manager")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("agent_manager")

import logging  # Import here for class type hints

# Chemins par défaut
DEFAULT_AGENTS_DIRS = [
    Path("/home/bamer/.opencode/agents/OPC_ELF_System_Agents"),
    Path.home() / ".config" / "opencode" / "agents",
    Path.home() / ".opencode" / "agents" / "plugins",
]
DEFAULT_OPENCODE_URL = "http://localhost:4096"
DEFAULT_MODEL = "model: llamacpp/nemotron-v3-coder"  # Modèle rapide et gratuit
DEFAULT_WORKDIR = Path("/home/bamer/OPC_ELF")
# SDK client path - using scripts directory for correct module resolution
# Note: The old opencode_sdk_client.mjs in agents/ is deprecated due to module resolution issues
# The @opencode-ai/sdk package.json exports are broken, so we use direct path import
SDK_CLIENT_PATH = Path(__file__).parents[2] / "scripts" / "sdk-client.mjs"


class AgentConfig:
    """Configuration d'un agent chargé depuis un fichier .md"""

    def __init__(self, name: str, metadata: Dict[str, Any], system_prompt: str):
        self.name = name
        self.metadata = metadata
        self.system_prompt = system_prompt
        self.model = metadata.get("model", DEFAULT_MODEL)
        self.description = metadata.get("description", "")
        self.tags = metadata.get("tags", [])
        self.permissions = metadata.get("permissions", {})

    def __repr__(self) -> str:
        return f"AgentConfig(name={self.name}, model={self.model})"


class AgentSession:
    """Session persistante pour un agent"""

    def __init__(self, agent_name: str, session_id: str, created_at: datetime):
        self.agent_name = agent_name
        self.session_id = session_id
        self.created_at = created_at
        self.last_used = created_at
        self.message_count = 0

    def touch(self):
        """Met à jour le timestamp de dernière utilisation"""
        self.last_used = datetime.now()
        self.message_count += 1


class AgentManager:
    """
    Gestionnaire d'agents standard OpenCode.

    Charge les agents depuis les fichiers .md et maintient des sessions persistantes.
    Chaque agent a sa propre session avec son prompt système défini dans le fichier .md.

    Attributes:
        opencode_url: URL du serveur OpenCode
        agents_dir: Répertoire contenant les fichiers .md des agents
        agents: Dict des configurations d'agents chargées
        sessions: Dict des sessions actives par nom d'agent
    """

    def __init__(
        self,
        opencode_url: str = DEFAULT_OPENCODE_URL,
        agents_dir: Optional[Path] = None,
        workdir: Optional[Path] = None,
        timeout: int = 600,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialise le AgentManager.

        Args:
            opencode_url: URL du serveur OpenCode (défaut: http://localhost:4096)
            agents_dir: Répertoire des fichiers .md (défaut: OPC_ELF_System_Agents)
            timeout: Timeout des requêtes en secondes
            logger: Logger optionnel
        """
        self.opencode_url = opencode_url.rstrip("/")
        # Support single agent_dir or multiple
        if agents_dir:
            self.agents_dirs = [agents_dir]
        else:
            self.agents_dirs = DEFAULT_AGENTS_DIRS
        self.timeout = timeout
        self.workdir = workdir or DEFAULT_WORKDIR
        self.logger = logger or logging.getLogger("AgentManager")

        # Stockage
        self.agents: Dict[str, AgentConfig] = {}
        self.sessions: Dict[str, AgentSession] = {}

        # Process tracking to prevent duplicate SDK spawns
        self._sdk_lock = threading.Lock()
        self._active_sdk_requests = 0
        self._sdk_client_path = SDK_CLIENT_PATH

        # Charger tous les agents
        self._load_all_agents()

        # Récupérer les agents depuis l'API OpenCode pour enrichir le catalogue
        self._setup_dynamic_agent_discovery()

        self.logger.info(f"✅ AgentManager initialisé avec {len(self.agents)} agents")
        self.logger.info(f"🔒 SDK process locking enabled (singleton)")

    def _setup_dynamic_agent_discovery(self):
        """
        Configure la découverte dynamique d'agents depuis OpenCode.

        Tente de récupérer les agents via l'API pour enrichir le catalogue
        avec les agents qui ne sont pas dans les fichiers .md locaux.
        """
        try:
            api_agents = self.fetch_agents_from_opencode()
            if api_agents:
                self.logger.info(
                    f"📊 {len(api_agents)} agents découverts via API OpenCode"
                )
        except Exception as e:
            self.logger.warning(f"⚠️ Découverte dynamique désactivée: {e}")
            # Non-critical - continue avec les agents fichiers .md

    def _log_session_entry(
        self,
        agent_name: str,
        session_id: str,
        request: str,
        response: str,
        outcome: str,
        model_used: str,
        duration_ms: int = 0,
    ):
        """Log agent interaction to JSONL session file for inter-session memory."""
        try:
            logs_dir = Path("/home/bamer/OPC_ELF/sessions/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)

            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = logs_dir / f"{date_str}_session.jsonl"

            # Create concise input summary
            input_summary = request[:120].replace("\n", " ")

            entry = {
                "ts": datetime.now().isoformat(),
                "agent": agent_name,
                "session_id": session_id[:12] if session_id else "",
                "tool": f"agent:{agent_name}",
                "input_summary": input_summary,
                "output_length": len(response) if response else 0,
                "outcome": outcome,
                "model_used": model_used,
                "duration_ms": duration_ms,
            }

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as e:
            self.logger.debug(f"Session log write failed: {e}")

    def _session_title(self, agent_name: str, date_label: str) -> str:
        return f"ELF {agent_name.title()} Session {date_label}"

    def _load_all_agents(self):
        """Charge tous les agents depuis les fichiers .md dans tous les répertoires"""
        for agents_dir in self.agents_dirs:
            if not agents_dir.exists():
                continue

            self.logger.debug(f"📂 Recherche agents dans: {agents_dir}")

            # Chercher aussi dans les sous-dossiers (ex: python-development/agents/)
            for md_file in agents_dir.glob("**/*.md"):
                try:
                    agent_config = self._parse_agent_file(md_file)
                    # Skip duplicates, keep first found
                    if agent_config.name not in self.agents:
                        self.agents[agent_config.name] = agent_config
                        self.logger.info(f"📄 Agent chargé: {agent_config.name}")
                    else:
                        self.logger.debug(f"⚠️  Agent déjà chargé: {agent_config.name}")
                except Exception as e:
                    self.logger.error(f"❌ Erreur chargement {md_file.name}: {e}")

    def _parse_agent_file(self, md_file: Path) -> AgentConfig:
        """
        Parse un fichier .md d'agent.

        Extrait:
        - Les métadonnées YAML (entre ---)
        - Le prompt système (le reste du fichier)

        Args:
            md_file: Chemin vers le fichier .md

        Returns:
            AgentConfig configuré
        """
        content = md_file.read_text(encoding="utf-8")

        # Extraire les métadonnées YAML
        metadata = {}
        system_prompt = content

        # Pattern pour les métadonnées YAML entre ---
        yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(yaml_pattern, content, re.DOTALL)

        if match:
            yaml_content = match.group(1)
            system_prompt = match.group(2).strip()

            # Parser simple du YAML
            for line in yaml_content.strip().split("\n"):
                if ":" in line and not line.strip().startswith("#"):
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")

                    # Convertir les listes
                    if value.startswith("[") and value.endswith("]"):
                        value = [v.strip().strip("\"'") for v in value[1:-1].split(",")]

                    metadata[key] = value

        # Le nom de l'agent est le nom du fichier sans extension
        agent_name = md_file.stem

        return AgentConfig(
            name=agent_name, metadata=metadata, system_prompt=system_prompt
        )

    def _ensure_session(self, agent_name: str) -> str:
        """
        S'assure qu'une session existe pour l'agent.
        Crée une nouvelle session si nécessaire.

        Args:
            agent_name: Nom de l'agent

        Returns:
            ID de session
        """
        # Vérifier si une session existe déjà
        if agent_name in self.sessions:
            session = self.sessions[agent_name]
            # Vérifier que la session est toujours valide
            if self._is_session_valid(session.session_id):
                return session.session_id
            else:
                self.logger.info(f"♻️ Session expirée pour {agent_name}, recréation...")
                del self.sessions[agent_name]

        # Créer une nouvelle session
        agent_config = self.agents.get(agent_name)
        if not agent_config:
            raise ValueError(f"Agent inconnu: {agent_name}")

        session_id = self._create_session(agent_config)

        if session_id:
            self.sessions[agent_name] = AgentSession(
                agent_name=agent_name, session_id=session_id, created_at=datetime.now()
            )
            self.logger.info(f"✅ Session créée pour {agent_name}: {session_id[:8]}...")

        return session_id

    def _create_session(self, agent_config: AgentConfig) -> Optional[str]:
        """
        Crée une nouvelle session OpenCode pour un agent.

        Args:
            agent_config: Configuration de l'agent

        Returns:
            ID de session ou None si échec
        """
        try:
            # D'abord, essayer de réutiliser une session existante
            date_label = datetime.now().strftime("%d-%m-%Y")
            expected_title = self._session_title(agent_config.name, date_label)

            list_result = self._sdk_request(
                "session_list",
                payload={"directory": str(self.workdir)},
            )
            if list_result.get("success"):
                sessions = list_result.get("data", [])
                for session in sessions:
                    title = session.get("title", "")
                    if title == expected_title:
                        session_id = session.get("id")
                        if session_id:
                            self.logger.debug(
                                f"♻️ Session existante trouvée: {session_id[:8]}..."
                            )
                            return session_id
            else:
                self.logger.warning(
                    "⚠️ Impossible de lister les sessions: %s",
                    list_result.get("error"),
                )

            # Créer une nouvelle session
            create_result = self._sdk_request(
                "session_create",
                payload={
                    "title": expected_title,
                    "directory": str(self.workdir),
                },
            )
            if create_result.get("success"):
                session_data = create_result.get("data", {})
                session_id = session_data.get("id")

                if session_id:
                    # Initialiser l'agent via binding explicite (AGENTS.md)
                    self._init_session_agent(session_id, agent_config)
                    return session_id
            else:
                self.logger.error(
                    "❌ Échec création session: %s", create_result.get("error")
                )

        except Exception as e:
            self.logger.error(f"❌ Erreur création session: {e}")

        return None

    def _init_session_agent(self, session_id: str, agent_config: AgentConfig) -> None:
        """
        Initialise la session avec un binding explicite d'agent.

        Args:
            session_id: ID de session
            agent_config: Configuration de l'agent
        """
        try:
            provider_id, _, model_id = agent_config.model.partition("/")
            init_result = self._sdk_request(
                "session_prompt",
                payload={
                    "sessionId": session_id,
                    "directory": str(self.workdir),
                    "agent": agent_config.name,
                    "model": {"providerID": provider_id, "modelID": model_id},
                    "noReply": True,
                    "parts": [
                        {
                            "type": "text",
                            "text": f"Initialize agent {agent_config.name}",
                        }
                    ],
                },
            )

            if init_result.get("success"):
                self.logger.debug(f"✅ Agent initialisé pour {agent_config.name}")
            else:
                self.logger.warning(
                    "⚠️ Échec initialisation agent %s: %s",
                    agent_config.name,
                    init_result.get("error"),
                )

        except Exception as e:
            self.logger.error(
                f"❌ Erreur initialisation agent {agent_config.name}: {e}"
            )

    def _is_session_valid(self, session_id: str) -> bool:
        """Vérifie si une session est toujours valide"""
        try:
            result = self._sdk_request(
                "session_get",
                payload={"sessionId": session_id, "directory": str(self.workdir)},
            )
            return bool(result.get("success"))
        except Exception:
            return False

    def _sdk_request(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to OpenCode SDK client with process locking to prevent duplicate spawns."""
        # Use the new SDK client path in scripts/ directory for correct module resolution
        sdk_path = SDK_CLIENT_PATH

        if not sdk_path.exists():
            return {"success": False, "error": f"SDK client not found: {sdk_path}"}

        request_body = {
            "action": action,
            "baseUrl": self.opencode_url,
            "payload": payload,
        }

        # Acquire lock to prevent concurrent SDK spawns
        with self._sdk_lock:
            if self._active_sdk_requests > 0:
                self.logger.warning(
                    f"⚠️ Duplicate SDK request prevented (already {self._active_sdk_requests} in flight)"
                )
                # Wait briefly and retry once
                _time.sleep(0.1)

            self._active_sdk_requests += 1
            max_retries = 2
            last_error = None

            try:
                for attempt in range(max_retries + 1):
                    try:
                        result = subprocess.run(
                            ["bun", str(sdk_path)],
                            input=json.dumps(request_body),
                            capture_output=True,
                            text=True,
                            check=False,
                            timeout=self.timeout,
                        )
                        break
                    except subprocess.TimeoutExpired:
                        last_error = f"SDK request timed out after {self.timeout}s (attempt {attempt + 1})"
                        self.logger.warning(last_error)
                        if attempt < max_retries:
                            _time.sleep(1)
                            continue
                        return {"success": False, "error": last_error}
                    except FileNotFoundError:
                        return {"success": False, "error": "bun command not found"}
                    except Exception as e:
                        last_error = str(e)
                        self.logger.warning(
                            f"SDK request failed (attempt {attempt + 1}): {last_error}"
                        )
                        if attempt < max_retries:
                            _time.sleep(1)
                            continue
                        return {
                            "success": False,
                            "error": f"SDK request failed after {max_retries + 1} attempts: {last_error}",
                        }

                if result.returncode != 0:
                    stderr_msg = (
                        result.stderr[:500] if result.stderr else "No error output"
                    )
                    return {
                        "success": False,
                        "error": f"SDK exited with code {result.returncode}: {stderr_msg}",
                    }

                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as exc:
                    return {"success": False, "error": f"Réponse SDK invalide: {exc}"}

            finally:
                # Always decrement the active request counter
                self._active_sdk_requests -= 1
                if self._active_sdk_requests < 0:
                    self._active_sdk_requests = 0
                    self.logger.error(
                        "⚠️ Active SDK requests counter went negative - bug detected"
                    )

    def ask_agent(
        self,
        agent_name: str,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Interroge un agent spécifique avec une requête utilisateur.

        Cette méthode utilise le vrai prompt système défini dans le fichier .md
        de l'agent et envoie la requête comme message utilisateur.

        Args:
            agent_name: Nom de l'agent (ex: "sentinel", "sentinel", "ceo")
            user_request: Requête utilisateur (pas un prompt système !)
            context: Contexte optionnel à inclure

        Returns:
            Dict avec la réponse et les métadonnées
            {
                "success": bool,
                "agent": str,
                "request": str,
                "response": str,
                "session_id": str,
                "timestamp": str
            }
        """
        if agent_name not in self.agents:
            return {
                "success": False,
                "error": f"Agent inconnu: {agent_name}. Agents disponibles: {list(self.agents.keys())}",
            }

        agent_config = self.agents[agent_name]

        try:
            # S'assurer qu'une session existe
            _start_time = _time.monotonic()
            session_id = self._ensure_session(agent_name)

            if not session_id:
                return {
                    "success": False,
                    "error": f"Impossible de créer/récupérer une session pour {agent_name}",
                }

            # Mettre à jour les stats de session
            if agent_name in self.sessions:
                self.sessions[agent_name].touch()

            # Préparer le message avec contexte optionnel
            message = user_request
            if context:
                context_str = json.dumps(context, indent=2, default=str)
                message = f"Context:\n{context_str}\n\nRequest:\n{user_request}"

            self.logger.info(f"🤖 {agent_name}: Envoi requête ({len(message)} chars)")

            provider_id, _, model_id = agent_config.model.partition(
                "/"
            )  # simplest, no error‑prone unpacking
            # Envoyer la requête à OpenCode
            prompt_result = self._sdk_request(
                "session_prompt",
                payload={
                    "sessionId": session_id,
                    "directory": str(self.workdir),
                    "agent": agent_config.name,
                    "model": {"providerID": provider_id, "modelID": model_id},
                    "parts": [{"type": "text", "text": message}],
                },
            )

            if prompt_result.get("success"):
                data = prompt_result.get("data", {})
                parts = data.get("parts", [])

                # Extraire la réponse texte
                ai_response = ""
                for part in parts:
                    if part.get("type") == "text":
                        ai_response += part.get("text", "")

                self.logger.info(
                    f"✅ {agent_name}: Réponse reçue ({len(ai_response)} chars)"
                )

                _duration = int((_time.monotonic() - _start_time) * 1000)
                self._log_session_entry(
                    agent_name=agent_name,
                    session_id=session_id or "",
                    request=user_request,
                    response=ai_response.strip(),
                    outcome="success",
                    model_used=agent_config.model,
                    duration_ms=_duration,
                )

                return {
                    "success": True,
                    "agent": agent_name,
                    "request": user_request,
                    "response": ai_response.strip(),
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "model_used": agent_config.model,
                }
            else:
                error_msg = prompt_result.get("error", "OpenCode SDK error")
                self.logger.error(f"❌ {agent_name}: {error_msg}")
                _duration = int((_time.monotonic() - _start_time) * 1000)
                self._log_session_entry(
                    agent_name=agent_name,
                    session_id=session_id or "",
                    request=user_request,
                    response="",
                    outcome="failure",
                    model_used=agent_config.model,
                    duration_ms=_duration,
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "agent": agent_name,
                    "request": user_request,
                }
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ {agent_name}: {error_msg}")
            self._log_session_entry(
                agent_name=agent_name,
                session_id="",
                request=user_request,
                response="",
                outcome="failure",
                model_used=self.agents.get(
                    agent_name, AgentConfig(agent_name, {}, "")
                ).model
                if agent_name in self.agents
                else "unknown",
                duration_ms=0,
            )
            return {"success": False, "error": error_msg, "agent": agent_name}

    # Méthodes de convenance pour les agents principaux

    def sentinel(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent Sentinel"""
        return self.ask_agent("sentinel", request, context)

    def ceo(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent CEO"""
        return self.ask_agent("ceo", request, context)

    def orchestrator(
        self, request: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Interroge l'agent Unified Orchestrator"""
        return self.ask_agent("unified-orchestrator", request, context)

    def researcher(
        self, request: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Interroge l'agent Researcher"""
        return self.ask_agent("researcher", request, context)

    def architect(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent Architect"""
        return self.ask_agent("architect", request, context)

    def skeptic(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent Skeptic"""
        return self.ask_agent("skeptic", request, context)

    def creative(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent Creative"""
        return self.ask_agent("creative", request, context)

    # Méthodes utilitaires

    def spawn_agent(
        self,
        agent_name: str,
        mission: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Spawn an agent for a long-running async mission.

        Unlike ask_agent which waits for response, spawn_agent creates a session
        and sends the mission asynchronously, returning immediately.

        Args:
            agent_name: Name of the agent to spawn
            mission: The mission/task to execute
            context: Optional context

        Returns:
            Dict with success status and session_id for monitoring
            {
                "success": bool,
                "session_id": str,
                "agent": str,
                "message": str
            }
        """
        if agent_name not in self.agents:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}",
            }

        agent_config = self.agents[agent_name]

        try:
            # Ensure session exists
            session_id = self._ensure_session(agent_name)

            if not session_id:
                return {
                    "success": False,
                    "error": f"Failed to create session for {agent_name}",
                }

            # Update session stats
            if agent_name in self.sessions:
                self.sessions[agent_name].touch()

            # Prepare message with context
            message = mission
            if context:
                context_str = json.dumps(context, indent=2, default=str)
                message = f"Context:\n{context_str}\n\nMission:\n{mission}"

            self.logger.info(
                f"🚀 {agent_name}: Spawning async mission ({len(message)} chars)"
            )

            # Send mission asynchronously (noReply=True)
            provider_id, _, model_id = agent_config.model.partition("/")
            prompt_result = self._sdk_request(
                "session_prompt",
                payload={
                    "sessionId": session_id,
                    "directory": str(self.workdir),
                    "agent": agent_config.name,
                    "model": {"providerID": provider_id, "modelID": model_id},
                    "parts": [{"type": "text", "text": message}],
                    "noReply": True,  # Async - don't wait for response
                },
            )

            if prompt_result.get("success"):
                self.logger.info(
                    f"✅ {agent_name}: Mission spawned in session {session_id[:8]}..."
                )
                return {
                    "success": True,
                    "session_id": session_id,
                    "agent": agent_name,
                    "message": "Mission spawned successfully",
                }
            else:
                error = prompt_result.get("error", "Unknown error")
                self.logger.error(f"❌ {agent_name}: Failed to spawn - {error}")
                return {
                    "success": False,
                    "error": f"Failed to spawn mission: {error}",
                }

        except Exception as e:
            self.logger.error(f"❌ {agent_name}: Error spawning agent - {e}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
            }

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the status of a session.

        Checks for completion by examining session messages. When using noReply: True,
        we need to check if the AI has responded to determine completion.

        Args:
            session_id: The session ID to check

        Returns:
            Dict with session status and data
        """
        try:
            # First check if session exists
            get_result = self._sdk_request(
                "session_get",
                payload={"sessionId": session_id, "directory": str(self.workdir)},
            )

            self.logger.debug(
                f"Session status check for {session_id[:8]}: success={get_result.get('success')}, has_data={bool(get_result.get('data'))}"
            )

            if not get_result.get("success") or not get_result.get("data"):
                # Session not found - treat as completed/failed
                return {
                    "success": True,
                    "session": None,
                    "status": "completed",  # Session gone = likely completed and cleaned up
                }

            session_data = get_result.get("data", {})

            # Get session messages to check for AI response
            messages_result = self._sdk_request(
                "messages",
                payload={
                    "sessionID": session_id,
                    "directory": str(self.workdir),
                    "limit": 10,
                },
            )

            if messages_result.get("success"):
                messages = messages_result.get("data", {}).get("messages", [])

                # Check if there's a system message indicating completion
                for msg in messages:
                    if msg.get("role") == "system":
                        content = msg.get("content", "")
                        # Handle both string and dict content types
                        if isinstance(content, dict):
                            content_str = str(content)
                        else:
                            content_str = (
                                content if isinstance(content, str) else str(content)
                            )

                        if "error" in content_str.lower():
                            return {
                                "success": True,
                                "session": session_data,
                                "status": "error",
                                "error": msg.get("content"),
                            }

                # Check if last message is from assistant (AI response)
                if messages:
                    last_message = messages[-1] if len(messages) > 0 else None
                    if last_message and last_message.get("role") == "assistant":
                        # AI has responded - mission completed
                        return {
                            "success": True,
                            "session": session_data,
                            "status": "completed",
                            "last_response": last_message.get("content", ""),
                        }
                    else:
                        # No AI response yet - still running
                        return {
                            "success": True,
                            "session": session_data,
                            "status": "running",
                        }
                else:
                    # No messages yet - might be starting up
                    return {
                        "success": True,
                        "session": session_data,
                        "status": "running",
                    }
            else:
                # Can't get messages, check if session exists
                return {
                    "success": True,
                    "session": session_data,
                    "status": "running",
                }

        except Exception as e:
            self.logger.error(f"Error getting session {session_id[:8]} status: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def kill_session(self, session_id: str) -> bool:
        """
        Kill/delete a session.

        Args:
            session_id: The session ID to kill

        Returns:
            True if successful
        """
        try:
            result = self._sdk_request(
                "session_delete",
                payload={"sessionId": session_id, "directory": str(self.workdir)},
            )
            if result.get("success"):
                self.logger.info(f"🗑️ Session killed: {session_id[:8]}...")
                return True
            else:
                self.logger.error(f"❌ Failed to kill session: {result.get('error')}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error killing session: {e}")
            return False

    def list_agents(self) -> List[str]:
        """Liste tous les agents disponibles"""
        return list(self.agents.keys())

    def fetch_agents_from_opencode(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des agents depuis l'API OpenCode.

        Utilise client.app.agents() pour récupérer les agents disponibles
        et met à jour le catalogue local.

        Returns:
            Liste des agents avec leurs métadonnées
        """
        try:
            result = self._sdk_request("agents_list", payload={})

            if result.get("success"):
                agents = result.get("data", [])
                self.logger.info(
                    f"📡 {len(agents)} agents récupérés depuis OpenCode API"
                )

                # Mettre à jour les configs locales avec les données de l'API
                for api_agent in agents:
                    agent_name = api_agent.get("name")
                    if agent_name and agent_name not in self.agents:
                        # Créer une config minimale pour les agents découverts via API
                        metadata = {
                            "description": api_agent.get("description", ""),
                            "model": api_agent.get("model", DEFAULT_MODEL),
                            "tags": api_agent.get("tags", []),
                        }
                        self.agents[agent_name] = AgentConfig(
                            name=agent_name,
                            metadata=metadata,
                            system_prompt=api_agent.get("system_prompt", ""),
                        )
                        self.logger.debug(f"📄 Agent découvert via API: {agent_name}")

                return agents
            else:
                self.logger.warning(
                    f"⚠️ Échec récupération agents API: {result.get('error')}"
                )
                return []
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération agents OpenCode: {e}")
            return []

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Retourne tous les agents disponibles avec leurs métadonnées enrichies.

        Combine les agents chargés depuis fichiers .md et ceux découverts via API.

        Returns:
            Liste de dict avec nom, description, tags, modèle, etc.
        """
        agents_data = []

        for agent_name, config in self.agents.items():
            agents_data.append(
                {
                    "name": agent_name,
                    "description": config.description,
                    "model": config.model,
                    "tags": config.tags,
                    "has_session": agent_name in self.sessions,
                    "session_id": self.sessions.get(
                        agent_name, AgentSession("", "", datetime.now())
                    ).session_id
                    if agent_name in self.sessions
                    else None,
                }
            )

        return agents_data

    def find_best_agent_for_task(
        self,
        task_description: str,
        task_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Trouve le meilleur agent pour une tâche donnée.

        Analyse la tâche et sélectionne l'agent le plus approprié en fonction
        de ses tags, description, et de correspondances spécialisées.

        Args:
            task_description: Description de la tâche
            task_type: Type de tâche (ex: "python", "frontend", "debugging")
            tags: Tags optionnels pour améliorer la sélection

        Returns:
            Nom de l'agent le plus approprié ou None
        """
        task_lower = task_description.lower()
        task_type_lower = (task_type or "").lower()
        tags_lower = [tag.lower() for tag in tags or []]

        # Mapping des mots-clés vers agents
        keyword_mappings = {
            "python": ["python", "backend", "api", "fastapi"],
            "javascript": [
                "javascript",
                "js",
                "typescript",
                "tsx",
                "frontend",
                "react",
            ],
            "frontend": ["frontend", "react", "vue", "ui", "interface", "css", "html"],
            "backend": ["backend", "api", "server", "database", "sql"],
            "debug": ["debug", "error", "bug", "issue", "fix", "problem"],
            "test": ["test", "testing", "unit", "integration"],
            "code": ["code", "feature", "implement", "refactor"],
            "design": ["design", "architecture", "pattern", "structure"],
            "review": ["review", "check", "audit", "analyze"],
            "security": ["security", "auth", "permission", "vulnerability"],
            "performance": ["performance", "optimize", "speed", "cache"],
        }

        # Scorer chaque agent
        agent_scores = {}

        for agent_name, config in self.agents.items():
            score = 0

            # Priorité à certains agents connus
            priority_agents = {
                "coder-agent": 5,
                "multi-agent-orchestrator-bf": 3,
                "multi-agent-coordinator": 3,
            }
            score += priority_agents.get(agent_name, 0)

            # Analyse des tags
            for tag in config.tags:
                tag_lower = tag.lower()
                if any(
                    keyword in task_lower for keyword in keyword_mappings.get(tag, [])
                ):
                    score += 3
                if tag_lower in task_type_lower:
                    score += 2

            # Analyse de la description
            desc_lower = config.description.lower()
            for keywords in keyword_mappings.values():
                if any(
                    keyword in task_lower and keyword in desc_lower
                    for keyword in keywords
                ):
                    score += 2

            # Correspondance directe du nom
            agent_name_lower = agent_name.lower()
            if any(keyword in task_lower for keyword in agent_name_lower.split("-")):
                score += 4

            # Correspondance tags utilisateur
            provided_tags = tags_lower + [task_type_lower]
            for tag in provided_tags:
                if any(
                    pt in agent_name_lower or pt in desc_lower
                    for pt in [tag.lower() for tag in provided_tags]
                ):
                    score += 2

            if score > 0:
                agent_scores[agent_name] = score

        # Retourner l'agent avec le score le plus élevé
        if agent_scores:
            best_agent = max(agent_scores, key=agent_scores.get)
            self.logger.debug(
                f"🎯 Agent sélectionné pour tâche: {best_agent} (score: {agent_scores[best_agent]}, "
                f"options: {agent_scores})"
            )
            return best_agent

        # Fallback: coder-agent s'il existe
        if "coder-agent" in self.agents:
            self.logger.debug("🔄 Fallback vers coder-agent pour tâche générique")
            return "coder-agent"

        return None

    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Retourne les informations sur un agent"""
        config = self.agents.get(agent_name)
        if not config:
            return None

        return {
            "name": config.name,
            "description": config.description,
            "model": config.model,
            "tags": config.tags,
            "has_session": agent_name in self.sessions,
            "session_id": self.sessions.get(
                agent_name, AgentSession("", "", datetime.now())
            ).session_id
            if agent_name in self.sessions
            else None,
        }

    def get_session_stats(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Retourne les statistiques des sessions"""
        if agent_name:
            session = self.sessions.get(agent_name)
            if session:
                return {
                    "agent": agent_name,
                    "session_id": session.session_id[:8] + "...",
                    "created_at": session.created_at.isoformat(),
                    "last_used": session.last_used.isoformat(),
                    "message_count": session.message_count,
                }
            return {"error": f"Pas de session pour {agent_name}"}

        return {
            "total_sessions": len(self.sessions),
            "agents": [
                {
                    "agent": name,
                    "messages": session.message_count,
                    "last_used": session.last_used.isoformat(),
                }
                for name, session in self.sessions.items()
            ],
        }

    def cleanup_session(self, agent_name: str) -> bool:
        """Nettoie une session spécifique"""
        if agent_name not in self.sessions:
            return False

        session = self.sessions[agent_name]
        try:
            self._sdk_request(
                "session_delete",
                payload={
                    "sessionId": session.session_id,
                    "directory": str(self.workdir),
                },
            )
            del self.sessions[agent_name]
            self.logger.info(f"🗑️ Session nettoyée pour {agent_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur nettoyage session {agent_name}: {e}")
            return False

    def cleanup_all_sessions(self):
        """Nettoie toutes les sessions"""
        for agent_name in list(self.sessions.keys()):
            self.cleanup_session(agent_name)


# Fonction singleton pour faciliter l'utilisation
_agent_manager_instance: Optional[AgentManager] = None


def get_agent_manager(
    opencode_url: str = DEFAULT_OPENCODE_URL, agents_dir: Optional[Path] = None
) -> AgentManager:
    """
    Retourne l'instance singleton du AgentManager.

    Usage:
        from agents.agent_manager import get_agent_manager

        manager = get_agent_manager()
        result = manager.sentinel("Analyze system health")
    """
    global _agent_manager_instance
    if _agent_manager_instance is None:
        _agent_manager_instance = AgentManager(
            opencode_url=opencode_url, agents_dir=agents_dir
        )
    return _agent_manager_instance


def reset_agent_manager():
    """Réinitialise l'instance singleton (utile pour les tests)"""
    global _agent_manager_instance
    if _agent_manager_instance:
        _agent_manager_instance.cleanup_all_sessions()
    _agent_manager_instance = None


# Point d'entrée pour tests
if __name__ == "__main__":
    print("🧪 Test du AgentManager")
    print("=" * 60)

    # Créer le manager
    manager = AgentManager()

    # Lister les agents
    print(f"\n📋 Agents chargés ({len(manager.list_agents())}):")
    for agent_name in manager.list_agents():
        info = manager.get_agent_info(agent_name)
        print(
            f"  - {agent_name}: {info['description'][:60]}..."
            if len(info["description"]) > 60
            else f"  - {agent_name}: {info['description']}"
        )

    print("\n✅ AgentManager prêt à l'emploi!")
    print("\nExemple d'utilisation:")
    print("  from agents.agent_manager import get_agent_manager")
    print("  manager = get_agent_manager()")
    print('  result = manager.sentinel("Analyze current system state")')
    print('  print(result["response"])')
