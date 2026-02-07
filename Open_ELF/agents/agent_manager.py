#!/usr/bin/env python3
"""
AgentManager - Gestionnaire d'agents standard OpenCode

Ce module gère les agents IA en chargeant leurs définitions depuis les fichiers .md
et en maintenant des sessions persistantes par agent.

Usage:
    from agents.agent_manager import AgentManager
    
    manager = AgentManager()
    
    # Interroger un agent spécifique
    response = manager.ask_agent("watcher", "Analyze system health and report anomalies")
    
    # Ou utiliser la méthode de convenance
    result = manager.watcher("Check all services status")
"""

import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
import requests

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)

# Chemins par défaut
DEFAULT_AGENTS_DIR = Path("/home/bamer/.opencode/agents/OPC_ELF_System_Agents")
DEFAULT_OPENCODE_URL = "http://localhost:4096"
DEFAULT_MODEL = "nvidia/minimaxai/minimax-m2"  # Modèle rapide et gratuit


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
        timeout: int = 600,
        logger: Optional[logging.Logger] = None
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
        self.agents_dir = agents_dir or DEFAULT_AGENTS_DIR
        self.timeout = timeout
        self.logger = logger or logging.getLogger("AgentManager")
        
        # Stockage
        self.agents: Dict[str, AgentConfig] = {}
        self.sessions: Dict[str, AgentSession] = {}
        
        # Charger tous les agents
        self._load_all_agents()
        
        self.logger.info(f"✅ AgentManager initialisé avec {len(self.agents)} agents")
    
    def _load_all_agents(self):
        """Charge tous les agents depuis les fichiers .md"""
        if not self.agents_dir.exists():
            self.logger.error(f"❌ Répertoire agents non trouvé: {self.agents_dir}")
            return
        
        for md_file in self.agents_dir.glob("*.md"):
            try:
                agent_config = self._parse_agent_file(md_file)
                self.agents[agent_config.name] = agent_config
                self.logger.info(f"📄 Agent chargé: {agent_config.name}")
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
        yaml_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(yaml_pattern, content, re.DOTALL)
        
        if match:
            yaml_content = match.group(1)
            system_prompt = match.group(2).strip()
            
            # Parser simple du YAML
            for line in yaml_content.strip().split('\n'):
                if ':' in line and not line.strip().startswith('#'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # Convertir les listes
                    if value.startswith('[') and value.endswith(']'):
                        value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                    
                    metadata[key] = value
        
        # Le nom de l'agent est le nom du fichier sans extension
        agent_name = md_file.stem
        
        return AgentConfig(
            name=agent_name,
            metadata=metadata,
            system_prompt=system_prompt
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
                agent_name=agent_name,
                session_id=session_id,
                created_at=datetime.now()
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
            response = requests.get(
                f"{self.opencode_url}/session",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                sessions = response.json()
                for session in sessions:
                    title = session.get("title", "").lower()
                    if agent_config.name.lower() in title:
                        session_id = session.get("id")
                        if session_id:
                            self.logger.debug(f"♻️ Session existante trouvée: {session_id[:8]}...")
                            return session_id
            
            # Créer une nouvelle session
            response = requests.post(
                f"{self.opencode_url}/session",
                json={
                    "title": f"ELF {agent_config.name.title()} Agent Session",
                    "directory": str(Path.home() / ".opencode" / "emergent-learning")
                },
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                session_data = response.json()
                session_id = session_data.get("id")
                
                if session_id:
                    # Envoyer le prompt système initial
                    self._send_system_prompt(session_id, agent_config)
                    return session_id
            else:
                self.logger.error(f"❌ Échec création session: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur création session: {e}")
        
        return None
    
    def _send_system_prompt(self, session_id: str, agent_config: AgentConfig):
        """
        Envoie le prompt système initial à la session.
        
        Args:
            session_id: ID de session
            agent_config: Configuration de l'agent
        """
        try:
            # Le premier message établit le contexte système
            response = requests.post(
                f"{self.opencode_url}/session/{session_id}/message",
                json={
                    "model": {
                        "providerID": "nvidia",
                        "modelID": agent_config.model.split("/")[-1] if "/" in agent_config.model else agent_config.model
                    },
                    "parts": [{
                        "type": "text",
                        "text": f"[SYSTEM PROMPT - DO NOT RESPOND TO THIS MESSAGE]\n\n{agent_config.system_prompt}\n\n[END SYSTEM PROMPT]\n\nAcknowledge that you understand your role as the {agent_config.name} agent."
                    }]
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.logger.debug(f"✅ Prompt système envoyé pour {agent_config.name}")
            else:
                self.logger.warning(f"⚠️ Échec envoi prompt système: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi prompt système: {e}")
    
    def _is_session_valid(self, session_id: str) -> bool:
        """Vérifie si une session est toujours valide"""
        try:
            response = requests.get(
                f"{self.opencode_url}/session/{session_id}",
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def ask_agent(
        self,
        agent_name: str,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Interroge un agent spécifique avec une requête utilisateur.
        
        Cette méthode utilise le vrai prompt système défini dans le fichier .md
        de l'agent et envoie la requête comme message utilisateur.
        
        Args:
            agent_name: Nom de l'agent (ex: "watcher", "sentinel", "ceo")
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
                "error": f"Agent inconnu: {agent_name}. Agents disponibles: {list(self.agents.keys())}"
            }
        
        agent_config = self.agents[agent_name]
        
        try:
            # S'assurer qu'une session existe
            session_id = self._ensure_session(agent_name)
            
            if not session_id:
                return {
                    "success": False,
                    "error": f"Impossible de créer/récupérer une session pour {agent_name}"
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
            
            # Envoyer la requête à OpenCode
            response = requests.post(
                f"{self.opencode_url}/session/{session_id}/message",
                json={
                    "model": {
                        "providerID": "nvidia",
                        "modelID": agent_config.model.split("/")[-1] if "/" in agent_config.model else agent_config.model
                    },
                    "parts": [{"type": "text", "text": message}]
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                parts = data.get("parts", [])
                
                # Extraire la réponse texte
                ai_response = ""
                for part in parts:
                    if part.get("type") == "text":
                        ai_response += part.get("text", "")
                
                self.logger.info(f"✅ {agent_name}: Réponse reçue ({len(ai_response)} chars)")
                
                return {
                    "success": True,
                    "agent": agent_name,
                    "request": user_request,
                    "response": ai_response.strip(),
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "model_used": agent_config.model
                }
            else:
                error_msg = f"OpenCode API error: {response.status_code}"
                self.logger.error(f"❌ {agent_name}: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "agent": agent_name,
                    "request": user_request
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"Timeout après {self.timeout}s"
            self.logger.error(f"⏰ {agent_name}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "agent": agent_name
            }
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ {agent_name}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "agent": agent_name
            }
    
    # Méthodes de convenance pour les agents principaux
    
    def watcher(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent Watcher"""
        return self.ask_agent("watcher", request, context)
    
    def sentinel(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent Sentinel"""
        return self.ask_agent("sentinel", request, context)
    
    def ceo(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent CEO"""
        return self.ask_agent("ceo", request, context)
    
    def orchestrator(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Interroge l'agent Unified Orchestrator"""
        return self.ask_agent("unified-orchestrator", request, context)
    
    def researcher(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
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
    
    def list_agents(self) -> List[str]:
        """Liste tous les agents disponibles"""
        return list(self.agents.keys())
    
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
            "session_id": self.sessions.get(agent_name, AgentSession("", "", datetime.now())).session_id if agent_name in self.sessions else None
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
                    "message_count": session.message_count
                }
            return {"error": f"Pas de session pour {agent_name}"}
        
        return {
            "total_sessions": len(self.sessions),
            "agents": [
                {
                    "agent": name,
                    "messages": session.message_count,
                    "last_used": session.last_used.isoformat()
                }
                for name, session in self.sessions.items()
            ]
        }
    
    def cleanup_session(self, agent_name: str) -> bool:
        """Nettoie une session spécifique"""
        if agent_name not in self.sessions:
            return False
        
        session = self.sessions[agent_name]
        try:
            requests.delete(
                f"{self.opencode_url}/session/{session.session_id}",
                timeout=10
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
    opencode_url: str = DEFAULT_OPENCODE_URL,
    agents_dir: Optional[Path] = None
) -> AgentManager:
    """
    Retourne l'instance singleton du AgentManager.
    
    Usage:
        from agents.agent_manager import get_agent_manager
        
        manager = get_agent_manager()
        result = manager.watcher("Analyze system health")
    """
    global _agent_manager_instance
    if _agent_manager_instance is None:
        _agent_manager_instance = AgentManager(
            opencode_url=opencode_url,
            agents_dir=agents_dir
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
        print(f"  - {agent_name}: {info['description'][:60]}..." if len(info['description']) > 60 else f"  - {agent_name}: {info['description']}")
    
    print("\n✅ AgentManager prêt à l'emploi!")
    print("\nExemple d'utilisation:")
    print("  from agents.agent_manager import get_agent_manager")
    print("  manager = get_agent_manager()")
    print('  result = manager.watcher("Analyze current system state")')
    print('  print(result["response"])')
