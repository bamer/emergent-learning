#!/usr/bin/env python3
"""
Mission Engine - Composant autonome de gestion des missions

Orchestrateur de workflow qui gère :
- La file d'attente des missions
- L'exécution des missions via AgentManager
- L'escalade au CEO si critique
- L'intégration avec l'onglet Live

Usage:
    from mission_engine import MissionEngine
    
    engine = MissionEngine()
    
    # Créer une mission
    mission = engine.create_mission(
        title="Analyser le système",
        description="Vérifier l'état de tous les services",
        agent="watcher"
    )
    
    # Exécuter
    result = engine.execute_mission(mission.id)
"""

import json
import logging
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# Ajouter le path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

# Support imports relatifs et absolus
try:
    from .models import (
        Mission, MissionResult, MissionStep,
        MissionStatus, MissionPriority, MissionType, MissionQueue
    )
    from .config import MissionEngineConfig
except ImportError:
    from models import (
        Mission, MissionResult, MissionStep,
        MissionStatus, MissionPriority, MissionType, MissionQueue
    )
    from config import MissionEngineConfig

# Import AgentManager
try:
    from agent_manager import AgentManager, get_agent_manager
    AGENT_MANAGER_AVAILABLE = True
except ImportError:
    AGENT_MANAGER_AVAILABLE = False
    logging.warning("AgentManager non disponible - mode dégradé")


logger = logging.getLogger("MissionEngine")


class MissionEngine:
    """
    Moteur d'exécution de missions autonome.
    
    Gère la file d'attente, l'exécution via AgentManager,
    l'escalade CEO et l'intégration Live Tab.
    
    Attributes:
        config: Configuration du moteur
        queue: File d'attente des missions
        agent_manager: Instance d'AgentManager
        running: Si le moteur est actif
        _thread: Thread de traitement en arrière-plan
        _callbacks: Callbacks enregistrés pour les événements
    """
    
    def __init__(self, config: Optional[MissionEngineConfig] = None):
        """
        Initialise le Mission Engine.
        
        Args:
            config: Configuration optionnelle (sinon chargée depuis l'env)
        """
        self.config = config or MissionEngineConfig.from_env()
        self.config.ensure_directories()
        
        # Setup logging
        self._setup_logging()
        
        # File d'attente
        self.queue = MissionQueue(max_size=100)
        
        # AgentManager
        self.agent_manager: Optional[AgentManager] = None
        if AGENT_MANAGER_AVAILABLE:
            try:
                self.agent_manager = get_agent_manager(
                    opencode_url=self.config.opencode_url,
                    agents_dir=self.config.agents_dir
                )
                logger.info("✅ AgentManager initialisé")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation AgentManager: {e}")
        
        # État
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            "mission_created": [],
            "mission_started": [],
            "mission_completed": [],
            "mission_failed": [],
            "mission_escalated": [],
            "live_mission_updated": [],
        }
        
        # Historique
        self._execution_log: List[Dict[str, Any]] = []
        
        logger.info(f"✅ Mission Engine initialisé (v1.0.0)")
    
    def _setup_logging(self):
        """Configure le logging"""
        log_format = "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format=log_format
        )
        
        if self.config.log_to_file:
            log_file = self.config.logs_dir / f"mission_engine_{datetime.now():%Y%m%d}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(file_handler)
    
    # ==================== Gestion des Missions ====================
    
    def create_mission(
        self,
        title: str,
        description: str,
        agent: Optional[str] = None,
        mission_type: MissionType = MissionType.CUSTOM,
        priority: MissionPriority = MissionPriority.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        is_critical: bool = False,
        live_tab_visible: bool = True,
    ) -> Mission:
        """
        Crée une nouvelle mission.
        
        Args:
            title: Titre de la mission
            description: Description détaillée
            agent: Nom de l'agent à utiliser
            mission_type: Type de mission
            priority: Priorité
            context: Contexte additionnel
            is_critical: Si critique
            live_tab_visible: Si visible dans le Live Tab
            
        Returns:
            Mission créée
        """
        mission = Mission(
            title=title,
            description=description,
            type=mission_type,
            priority=priority,
            agent=agent,
            context=context or {},
            is_critical=is_critical,
            live_tab_visible=live_tab_visible,
        )
        
        # Ajouter à la file
        if self.queue.add(mission):
            logger.info(f"📋 Mission créée: {mission.id} - {title}")
            
            # Notifier les callbacks
            self._trigger_callbacks("mission_created", mission)
            
            return mission
        else:
            raise RuntimeError("File d'attente pleine")
    
    def create_live_mission(
        self,
        title: str,
        description: str,
        agent: Optional[str] = None,
        priority: MissionPriority = MissionPriority.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
    ) -> Mission:
        """
        Crée une mission spécifique pour l'onglet Live.
        
        Args:
            title: Titre affiché dans le Live Tab
            description: Description détaillée
            agent: Agent à utiliser
            priority: Priorité
            context: Contexte
            
        Returns:
            Mission créée avec live_tab_id
        """
        mission = self.create_mission(
            title=title,
            description=description,
            agent=agent,
            mission_type=MissionType.LIVE_TAB,
            priority=priority,
            context=context,
            live_tab_visible=True,
        )
        
        # Générer un ID spécifique pour le Live Tab
        mission.live_tab_id = f"live_{mission.id}"
        
        logger.info(f"📺 Mission Live créée: {mission.live_tab_id}")
        
        return mission
    
    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Récupère une mission par son ID"""
        for mission in self.queue.missions:
            if mission.id == mission_id or mission.live_tab_id == mission_id:
                return mission
        return None
    
    def get_missions_by_status(self, status: MissionStatus) -> List[Mission]:
        """Récupère les missions par statut"""
        return self.queue.get_by_status(status)
    
    def get_live_missions(self, visible_only: bool = True) -> List[Mission]:
        """
        Récupère les missions de l'onglet Live.
        
        Args:
            visible_only: Si True, retourne uniquement les missions visibles
            
        Returns:
            Liste des missions Live
        """
        live_missions = self.queue.get_by_type(MissionType.LIVE_TAB)
        if visible_only:
            live_missions = [m for m in live_missions if m.live_tab_visible]
        return live_missions
    
    def cancel_mission(self, mission_id: str) -> bool:
        """Annule une mission"""
        mission = self.get_mission(mission_id)
        if mission and mission.is_active:
            mission.status = MissionStatus.CANCELLED
            mission.completed_at = datetime.now()
            logger.info(f"🚫 Mission annulée: {mission_id}")
            return True
        return False
    
    # ==================== Exécution ====================
    
    def execute_mission(self, mission_id: str) -> MissionResult:
        """
        Exécute une mission spécifique.
        
        Workflow:
        1. Démarre la mission
        2. Appelle l'agent pour analyse (si spécifié)
        3. Détermine si critique
        4. Escalade au CEO si nécessaire
        5. Exécute les actions
        6. Retourne le résultat
        
        Args:
            mission_id: ID de la mission
            
        Returns:
            Résultat de la mission
        """
        mission = self.get_mission(mission_id)
        if not mission:
            return MissionResult(success=False, output=f"Mission non trouvée: {mission_id}")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 EXÉCUTION MISSION: {mission.title}")
        logger.info(f"{'='*70}")
        
        # Démarrer
        mission.start()
        self._trigger_callbacks("mission_started", mission)
        
        start_time = time.time()
        
        try:
            # Étape 1: Analyse par agent (si spécifié)
            if mission.agent:
                analysis_result = self._execute_agent_analysis(mission)
                if not analysis_result["success"]:
                    mission.fail(f"Échec analyse agent: {analysis_result.get('error')}")
                    return mission.result
            else:
                analysis_result = {"success": True, "analysis": None}
            
            # Étape 2: Vérifier criticité
            is_critical = self._is_critical_mission(mission, analysis_result.get("analysis"))
            mission.is_critical = is_critical
            
            if is_critical:
                logger.warning(f"🚨 Mission CRITIQUE détectée: {mission.id}")
            
            # Étape 3: Escalade CEO si critique et configuré
            ceo_decision = None
            if is_critical and self.config.auto_escalate_critical:
                mission.status = MissionStatus.ESCALATING
                ceo_result = self._escalate_to_ceo(mission, analysis_result.get("analysis"))
                
                if ceo_result["success"]:
                    ceo_decision = ceo_result["decision"]
                    mission.escalated_to_ceo = True
                    logger.info(f"✅ Décision CEO reçue")
                else:
                    logger.error(f"❌ Échec escalation CEO: {ceo_result.get('error')}")
            
            # Étape 4: Extraire et exécuter les actions
            mission.status = MissionStatus.EXECUTING
            actions = self._extract_actions(ceo_decision or analysis_result.get("analysis", ""))
            
            # Étape 5: Finaliser
            execution_time = int((time.time() - start_time) * 1000)
            
            result = MissionResult(
                success=True,
                output=f"Mission {mission.id} exécutée avec succès",
                actions=actions,
                agent_analysis=analysis_result.get("analysis"),
                ceo_decision=ceo_decision,
                execution_time_ms=execution_time,
                metadata={
                    "mission_id": mission.id,
                    "agent_used": mission.agent,
                    "is_critical": is_critical,
                    "escalated": mission.escalated_to_ceo,
                }
            )
            
            mission.complete(result)
            self._trigger_callbacks("mission_completed", mission)
            
            logger.info(f"✅ Mission terminée: {mission.id}")
            
            # Log
            self._execution_log.append({
                "mission_id": mission.id,
                "title": mission.title,
                "success": True,
                "timestamp": datetime.now().isoformat(),
            })
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Erreur exécution mission {mission_id}: {error_msg}")
            
            mission.fail(error_msg)
            self._trigger_callbacks("mission_failed", mission)
            
            return MissionResult(
                success=False,
                output=error_msg,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def _execute_agent_analysis(self, mission: Mission) -> Dict[str, Any]:
        """
        Exécute l'analyse par l'agent spécifié.
        
        Args:
            mission: Mission à analyser
            
        Returns:
            Dict avec success, analysis, error
        """
        if not self.agent_manager:
            return {
                "success": False,
                "error": "AgentManager non disponible"
            }
        
        mission.status = MissionStatus.ANALYZING
        step = mission.add_step(f"Analyse par {mission.agent}")
        step.started_at = datetime.now()
        
        try:
            # Préparer la requête
            request_text = f"""Analyse cette mission et fournis des insights actionnables.

MISSION: {mission.title}

DESCRIPTION:
{mission.description}

CONTEXTE:
{json.dumps(mission.context, indent=2, default=str)[:500]}

Merci de fournir:
1. Analyse de la situation
2. Impacts potentiels
3. Actions recommandées (liste à puces)
4. Timeline suggérée
5. Métriques de succès"""

            logger.info(f"🤖 Appel agent {mission.agent}...")
            
            # Appeler l'agent
            result = self.agent_manager.ask_agent(
                agent_name=mission.agent.lower(),
                user_request=request_text,
                context={
                    "mission_id": mission.id,
                    "mission_type": mission.type.value,
                    "priority": mission.priority.name,
                }
            )
            
            step.completed_at = datetime.now()
            
            if result.get("success"):
                analysis = result.get("response", "")
                step.result = f"Analyse reçue ({len(analysis)} caractères)"
                logger.info(f"✅ Analyse reçue ({len(analysis)} chars)")
                return {"success": True, "analysis": analysis}
            else:
                error = result.get("error", "Erreur inconnue")
                step.error = error
                logger.error(f"❌ Échec analyse: {error}")
                return {"success": False, "error": error}
                
        except Exception as e:
            step.error = str(e)
            logger.error(f"❌ Exception analyse: {e}")
            return {"success": False, "error": str(e)}
    
    def _is_critical_mission(self, mission: Mission, analysis: Optional[str]) -> bool:
        """
        Détermine si une mission est critique.
        
        Vérifie:
        - Le flag is_critical de la mission
        - Les mots-clés dans l'analyse
        - Le niveau de priorité
        
        Args:
            mission: Mission à évaluer
            analysis: Analyse de l'agent (optionnel)
            
        Returns:
            True si critique
        """
        # Flag explicite
        if mission.is_critical:
            return True
        
        # Priorité CEO_REVIEW
        if mission.priority == MissionPriority.CEO_REVIEW:
            return True
        
        # Mots-clés critiques
        if analysis:
            critical_keywords = [
                "critical", "severe", "urgent", "immediately",
                "failure", "down", "crash", "security", "breach",
                "data loss", "must fix", "crucial", "vital"
            ]
            combined = f"{mission.title} {mission.description} {analysis}".lower()
            return any(kw in combined for kw in critical_keywords)
        
        return False
    
    def _escalate_to_ceo(self, mission: Mission, analysis: str) -> Dict[str, Any]:
        """
        Escalade une mission critique au CEO.
        
        Args:
            mission: Mission critique
            analysis: Analyse de l'agent
            
        Returns:
            Dict avec success, decision, error
        """
        if not self.agent_manager:
            return {
                "success": False,
                "error": "AgentManager non disponible pour CEO"
            }
        
        mission.status = MissionStatus.ESCALATING
        step = mission.add_step("Escalade CEO")
        step.started_at = datetime.now()
        
        try:
            request_text = f"""Une mission critique vous est escaladée pour décision.

MISSION: {mission.title}

DESCRIPTION:
{mission.description}

ANALYSE DE L'ÉQUIPE:
{analysis[:1000] if analysis else 'Non disponible'}

En tant que CEO, vous devez:
1. Évaluer l'impact business
2. Prendre une décision claire
3. Spécifier les actions exactes
4. Définir la timeline et priorité

Format de réponse:
DECISION: [Votre décision]
RATIONALE: [Pourquoi]
ACTIONS:
- [Action 1]
- [Action 2]
TIMELINE: [Quand]
PRIORITY: [Critical/High/Medium/Low]"""

            logger.info("🤖 Appel CEO...")
            
            result = self.agent_manager.ceo(
                request=request_text,
                context={
                    "mission_id": mission.id,
                    "agent_analysis": analysis[:500] if analysis else None,
                    "priority": mission.priority.name,
                }
            )
            
            step.completed_at = datetime.now()
            
            if result.get("success"):
                decision = result.get("response", "")
                step.result = f"Décision reçue ({len(decision)} caractères)"
                logger.info(f"✅ Décision CEO ({len(decision)} chars)")
                
                # Notifier
                self._trigger_callbacks("mission_escalated", mission, decision)
                
                return {"success": True, "decision": decision}
            else:
                error = result.get("error", "Erreur CEO")
                step.error = error
                return {"success": False, "error": error}
                
        except Exception as e:
            step.error = str(e)
            return {"success": False, "error": str(e)}
    
    def _extract_actions(self, text: str) -> List[str]:
        """Extrait les actions d'un texte"""
        actions = []
        
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                actions.append(line[2:])
            elif line.startswith("Action "):
                actions.append(line)
        
        return actions
    
    # ==================== Mode Background ====================
    
    def start_background_processing(self):
        """Démarre le traitement en arrière-plan des missions"""
        if self.running:
            logger.warning("⚠️ Traitement déjà actif")
            return
        
        self.running = True
        self._stop_event.clear()
        
        self._thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self._thread.start()
        
        logger.info("🔄 Traitement en arrière-plan démarré")
    
    def stop_background_processing(self):
        """Arrête le traitement en arrière-plan"""
        if not self.running:
            return
        
        self._stop_event.set()
        self.running = False
        
        if self._thread:
            self._thread.join(timeout=5)
        
        logger.info("🛑 Traitement en arrière-plan arrêté")
    
    def _process_queue_loop(self):
        """Boucle de traitement de la file"""
        while not self._stop_event.is_set():
            try:
                # Récupérer la prochaine mission
                mission = self.queue.get_next()
                
                if mission:
                    logger.info(f"🎯 Traitement mission: {mission.id}")
                    self.execute_mission(mission.id)
                else:
                    # Attendre si pas de mission
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Erreur boucle traitement: {e}")
                time.sleep(1)
    
    # ==================== Callbacks ====================
    
    def on(self, event: str, callback: Callable):
        """
        Enregistre un callback pour un événement.
        
        Events disponibles:
        - mission_created: Nouvelle mission créée
        - mission_started: Mission démarrée
        - mission_completed: Mission terminée avec succès
        - mission_failed: Mission échouée
        - mission_escalated: Mission escaladée au CEO
        - live_mission_updated: Mission Live mise à jour
        
        Args:
            event: Nom de l'événement
            callback: Fonction à appeler
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, *args):
        """Déclenche les callbacks pour un événement"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"❌ Erreur callback {event}: {e}")
    
    # ==================== Statistiques ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du moteur"""
        return {
            "total_missions": len(self.queue.missions),
            "pending": len(self.get_missions_by_status(MissionStatus.PENDING)),
            "running": len(self.get_missions_by_status(MissionStatus.RUNNING)),
            "completed": len([m for m in self.queue.missions if m.is_completed]),
            "live_missions": len(self.get_live_missions()),
            "agent_manager_available": self.agent_manager is not None,
            "background_processing": self.running,
        }
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Retourne l'historique d'exécution"""
        return self._execution_log.copy()
    
    def clear_completed_missions(self) -> int:
        """Nettoie les missions terminées"""
        count = self.queue.clear_completed()
        logger.info(f"🗑️ {count} missions terminées supprimées")
        return count


# ==================== Singleton ====================

_mission_engine_instance: Optional[MissionEngine] = None


def get_mission_engine(config: Optional[MissionEngineConfig] = None) -> MissionEngine:
    """
    Retourne l'instance singleton du MissionEngine.
    
    Usage:
        from mission_engine import get_mission_engine
        
        engine = get_mission_engine()
        mission = engine.create_mission("Titre", "Description")
    """
    global _mission_engine_instance
    if _mission_engine_instance is None:
        _mission_engine_instance = MissionEngine(config)
    return _mission_engine_instance


def reset_mission_engine():
    """Réinitialise l'instance singleton"""
    global _mission_engine_instance
    if _mission_engine_instance:
        _mission_engine_instance.stop_background_processing()
    _mission_engine_instance = None


# ==================== Point d'entrée ====================

if __name__ == "__main__":
    print("🚀 Mission Engine - Test")
    print("=" * 70)
    
    # Créer le moteur
    engine = MissionEngine()
    
    # Créer une mission de test
    mission = engine.create_mission(
        title="Test Mission",
        description="Mission de test pour vérifier le fonctionnement",
        agent="watcher" if AGENT_MANAGER_AVAILABLE else None,
        priority=MissionPriority.HIGH,
    )
    
    print(f"\n📋 Mission créée:")
    print(f"  ID: {mission.id}")
    print(f"  Titre: {mission.title}")
    print(f"  Status: {mission.status.value}")
    
    # Afficher les stats
    stats = engine.get_stats()
    print(f"\n📊 Statistiques:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Mission Engine prêt!")
