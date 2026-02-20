#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO 
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Mission Live Handler - Gestionnaire spécifique de l'onglet Live

Ce module gère l'intégration entre le Mission Engine et l'onglet Live
de l'interface utilisateur. Il fournit :
- Création de missions Live
- Mise à jour du statut en temps réel
- Synchronisation avec l'UI
- Gestion des événements Live

Usage:
    from mission_engine import LiveMissionHandler
    
    handler = LiveMissionHandler(mission_engine)
    
    # Créer une mission Live
    mission = handler.create_live_mission(
        title="Analyser le système",
        description="Vérifier l'état des services"
    )
    
    # Démarrer le polling pour mises à jour auto
    handler.start_live_updates()
"""

import json

import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_critical, log_error, log_warning, log_info
    logger = get_logger("mission_live_handler")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("mission_live_handler")

# Support imports relatifs et absolus
try:
    from .mission_engine import MissionEngine
    from .models import Mission, MissionStatus, MissionPriority, MissionType, MissionResult
except ImportError:
    from mission_engine import MissionEngine
    from models import Mission, MissionStatus, MissionPriority, MissionType, MissionResult

logger = logging.getLogger("LiveMissionHandler")

@dataclass
class LiveMissionView:
    """
    Représentation d'une mission pour l'affichage Live.
    
    Cette structure est optimisée pour l'affichage dans l'UI
    et contient uniquement les champs nécessaires.
    """
    id: str
    live_tab_id: str
    title: str
    description: str
    status: str
    priority: str
    progress: int = 0  # 0-100
    agent: Optional[str] = None
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    is_critical: bool = False
    escalated_to_ceo: bool = False
    actions_count: int = 0
    current_step: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour JSON"""
        return {
            "id": self.id,
            "live_tab_id": self.live_tab_id,
            "title": self.title,
            "description": self.description[:200] + "..." if len(self.description) > 200 else self.description,
            "status": self.status,
            "priority": self.priority,
            "progress": self.progress,
            "agent": self.agent,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "is_critical": self.is_critical,
            "escalated_to_ceo": self.escalated_to_ceo,
            "actions_count": self.actions_count,
            "current_step": self.current_step,
        }

class LiveMissionHandler:
    """
    Gestionnaire des missions de l'onglet Live.
    
    Fournit une interface simplifiée pour créer et gérer
    des missions spécifiquement destinées à l'affichage
    dans l'onglet Live.
    
    Attributes:
        engine: Instance du MissionEngine
        update_interval: Intervalle de rafraîchissement (secondes)
        _update_thread: Thread de mise à jour en arrière-plan
        _callbacks: Callbacks pour les événements Live
    """
    
    def __init__(
        self,
        engine: MissionEngine,
        update_interval: int = 30
    ):
        """
        Initialise le handler Live.
        
        Args:
            engine: Instance du MissionEngine
            update_interval: Intervalle de rafraîchissement en secondes
        """
        self.engine = engine
        self.update_interval = update_interval
        
        # État
        self._update_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._live_missions_cache: Dict[str, LiveMissionView] = {}
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            "live_mission_created": [],
            "live_mission_updated": [],
            "live_mission_completed": [],
            "live_status_changed": [],
        }
        
        # Enregistrer les callbacks sur le moteur
        self._register_callbacks()
        
        logger.info(f"✅ LiveMissionHandler initialisé (refresh: {update_interval}s)")
    
    def _register_callbacks(self):
        """Enregistre les callbacks sur le MissionEngine"""
        self.engine.on("mission_created", self._on_mission_created)
        self.engine.on("mission_started", self._on_mission_started)
        self.engine.on("mission_completed", self._on_mission_completed)
        self.engine.on("mission_failed", self._on_mission_failed)
        self.engine.on("mission_escalated", self._on_mission_escalated)
    
    # ==================== Création de Missions Live ====================
    
    def create_live_mission(
        self,
        title: str,
        description: str,
        agent: Optional[str] = None,
        priority: str = "MEDIUM",
        auto_execute: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> Mission:
        """
        Crée une mission spécifiquement pour l'onglet Live.
        
        Args:
            title: Titre affiché dans le Live Tab
            description: Description complète
            agent: Agent à utiliser (sentinel, sentinel, researcher, etc.)
            priority: Priorité (LOW, MEDIUM, HIGH, CRITICAL)
            auto_execute: Si True, démarre l'exécution immédiatement
            context: Contexte additionnel
            
        Returns:
            Mission créée
        """
        # Convertir la priorité
        priority_enum = MissionPriority[priority.upper()]
        
        # Créer la mission via le moteur
        mission = self.engine.create_live_mission(
            title=title,
            description=description,
            agent=agent,
            priority=priority_enum,
            context=context or {},
        )
        
        logger.info(f"📺 Mission Live créée: {mission.live_tab_id}")
        
        # Créer la vue Live
        live_view = self._mission_to_live_view(mission)
        self._live_missions_cache[mission.live_tab_id] = live_view
        
        # Notifier
        self._trigger_callbacks("live_mission_created", live_view)
        
        # Exécuter si demandé
        if auto_execute:
            self._execute_live_mission_async(mission.id)
        
        return mission
    
    def create_analysis_mission(
        self,
        target: str,
        analysis_type: str = "general",
        agent: str = "sentinel",
    ) -> Mission:
        """
        Crée une mission d'analyse pour le Live.
        
        Args:
            target: Cible de l'analyse (ex: "système", "codebase", "performance")
            analysis_type: Type d'analyse (general, security, performance, etc.)
            agent: Agent à utiliser
            
        Returns:
            Mission créée
        """
        title = f"🔍 Analyse {analysis_type}: {target}"
        description = f"Analyse {analysis_type} de {target}. Mission créée depuis l'onglet Live."
        
        return self.create_live_mission(
            title=title,
            description=description,
            agent=agent,
            priority="HIGH",
            context={
                "target": target,
                "analysis_type": analysis_type,
                "source": "live_tab",
            }
        )
    
    def create_pattern_response_mission(
        self,
        pattern: str,
        agent: str,
        recommendations: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Mission:
        """
        Crée une mission de réponse à un pattern détecté.
        
        Args:
            pattern: Pattern détecté
            agent: Agent recommandé
            recommendations: Recommandations initiales
            context: Contexte du pattern
            
        Returns:
            Mission créée
        """
        title = f"⚡ Pattern détecté: {pattern[:50]}..."
        description = f"""Pattern détecté: {pattern}

Recommandations:
{chr(10).join(f"- {r}" for r in recommendations[:5])}

Cette mission a été créée automatiquement suite à la détection d'un pattern."""
        
        mission = self.create_live_mission(
            title=title,
            description=description,
            agent=agent,
            priority="HIGH",
            context={
                "pattern": pattern,
                "recommendations": recommendations,
                **(context or {}),
            }
        )
        
        return mission
    
    # ==================== Gestion des Missions Live ====================
    
    def get_live_missions(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[LiveMissionView]:
        """
        Récupère les missions Live actives.
        
        Args:
            status: Filtrer par statut (optionnel)
            limit: Nombre maximum de missions
            
        Returns:
            Liste des missions Live formatées pour l'affichage
        """
        missions = self.engine.get_live_missions(visible_only=True)
        
        # Mettre à jour le cache
        live_views = []
        for mission in missions[:limit]:
            live_view = self._mission_to_live_view(mission)
            self._live_missions_cache[mission.live_tab_id] = live_view
            live_views.append(live_view)
        
        # Filtrer par statut si demandé
        if status:
            live_views = [v for v in live_views if v.status == status]
        
        return live_views
    
    def get_live_mission(self, live_tab_id: str) -> Optional[LiveMissionView]:
        """
        Récupère une mission Live par son ID.
        
        Args:
            live_tab_id: ID de la mission Live
            
        Returns:
            Vue de la mission ou None
        """
        # Vérifier le cache d'abord
        if live_tab_id in self._live_missions_cache:
            return self._live_missions_cache[live_tab_id]
        
        # Sinon, récupérer depuis le moteur
        mission = self.engine.get_mission(live_tab_id)
        if mission and mission.type == MissionType.LIVE_TAB:
            live_view = self._mission_to_live_view(mission)
            self._live_missions_cache[live_tab_id] = live_view
            return live_view
        
        return None
    
    def cancel_live_mission(self, live_tab_id: str) -> bool:
        """Annule une mission Live"""
        mission = self.engine.get_mission(live_tab_id)
        if mission:
            return self.engine.cancel_mission(mission.id)
        return False
    
    def hide_live_mission(self, live_tab_id: str) -> bool:
        """
        Cache une mission de l'onglet Live (sans l'annuler).
        
        Args:
            live_tab_id: ID de la mission
            
        Returns:
            True si succès
        """
        mission = self.engine.get_mission(live_tab_id)
        if mission:
            mission.live_tab_visible = False
            logger.info(f"👁️ Mission cachée: {live_tab_id}")
            return True
        return False
    
    def clear_completed_live_missions(self) -> int:
        """Supprime les missions Live terminées de l'affichage"""
        count = 0
        for mission in self.engine.get_live_missions(visible_only=True):
            if mission.is_completed:
                mission.live_tab_visible = False
                count += 1
        
        if count > 0:
            logger.info(f"🗑️ {count} missions Live terminées cachées")
        
        return count
    
    # ==================== Conversion et Affichage ====================
    
    def _mission_to_live_view(self, mission: Mission) -> LiveMissionView:
        """
        Convertit une Mission en LiveMissionView.
        
        Args:
            mission: Mission source
            
        Returns:
            Vue formatée pour le Live Tab
        """
        # Calculer la progression
        progress = self._calculate_progress(mission)
        
        # Déterminer l'étape courante
        current_step = None
        if mission.steps:
            current_steps = [s for s in mission.steps if not s.completed_at]
            if current_steps:
                current_step = current_steps[0].name
            else:
                current_step = mission.steps[-1].name if mission.steps else None
        
        # Compter les actions
        actions_count = 0
        if mission.result and mission.result.actions:
            actions_count = len(mission.result.actions)
        
        return LiveMissionView(
            id=mission.id,
            live_tab_id=mission.live_tab_id or f"live_{mission.id}",
            title=mission.title,
            description=mission.description,
            status=mission.status.value,
            priority=mission.priority.name,
            progress=progress,
            agent=mission.agent,
            created_at=mission.created_at.isoformat(),
            started_at=mission.started_at.isoformat() if mission.started_at else None,
            completed_at=mission.completed_at.isoformat() if mission.completed_at else None,
            is_critical=mission.is_critical,
            escalated_to_ceo=mission.escalated_to_ceo,
            actions_count=actions_count,
            current_step=current_step,
        )
    
    def _calculate_progress(self, mission: Mission) -> int:
        """
        Calcule la progression d'une mission (0-100).
        
        Args:
            mission: Mission à évaluer
            
        Returns:
            Progression en pourcentage
        """
        if mission.is_completed:
            return 100 if mission.status == MissionStatus.COMPLETED else 0
        
        if not mission.steps:
            # Basé sur le statut
            progress_map = {
                MissionStatus.PENDING: 0,
                MissionStatus.QUEUED: 5,
                MissionStatus.RUNNING: 10,
                MissionStatus.ANALYZING: 30,
                MissionStatus.ESCALATING: 50,
                MissionStatus.DECIDING: 60,
                MissionStatus.EXECUTING: 80,
                MissionStatus.WAITING_REVIEW: 90,
            }
            return progress_map.get(mission.status, 0)
        
        # Basé sur les étapes complétées
        completed = sum(1 for s in mission.steps if s.completed_at)
        total = len(mission.steps)
        return int((completed / total) * 100) if total > 0 else 0
    
    def get_live_dashboard(self) -> Dict[str, Any]:
        """
        Retourne les données complètes pour le dashboard Live.
        
        Returns:
            Dict avec statistiques et missions
        """
        missions = self.get_live_missions()
        
        # Statistiques
        stats = {
            "total": len(missions),
            "pending": len([m for m in missions if m.status == "pending"]),
            "running": len([m for m in missions if m.status == "running"]),
            "completed": len([m for m in missions if m.status == "completed"]),
            "failed": len([m for m in missions if m.status == "failed"]),
            "critical": len([m for m in missions if m.is_critical]),
            "escalated": len([m for m in missions if m.escalated_to_ceo]),
        }
        
        return {
            "stats": stats,
            "missions": [m.to_dict() for m in missions],
            "last_updated": datetime.now().isoformat(),
        }
    
    def export_live_missions_json(self) -> str:
        """Exporte les missions Live en JSON"""
        dashboard = self.get_live_dashboard()
        return json.dumps(dashboard, indent=2, default=str)
    
    # ==================== Callbacks Internes ====================
    
    def _on_mission_created(self, mission: Mission):
        """Callback quand une mission est créée"""
        if mission.type == MissionType.LIVE_TAB:
            live_view = self._mission_to_live_view(mission)
            self._live_missions_cache[mission.live_tab_id] = live_view
            self._trigger_callbacks("live_mission_created", live_view)
    
    def _on_mission_started(self, mission: Mission):
        """Callback quand une mission démarre"""
        if mission.type == MissionType.LIVE_TAB:
            live_view = self._mission_to_live_view(mission)
            self._live_missions_cache[mission.live_tab_id] = live_view
            self._trigger_callbacks("live_mission_updated", live_view)
    
    def _on_mission_completed(self, mission: Mission):
        """Callback quand une mission se termine"""
        if mission.type == MissionType.LIVE_TAB:
            live_view = self._mission_to_live_view(mission)
            self._live_missions_cache[mission.live_tab_id] = live_view
            self._trigger_callbacks("live_mission_completed", live_view)
    
    def _on_mission_failed(self, mission: Mission):
        """Callback quand une mission échoue"""
        if mission.type == MissionType.LIVE_TAB:
            live_view = self._mission_to_live_view(mission)
            self._live_missions_cache[mission.live_tab_id] = live_view
            self._trigger_callbacks("live_mission_updated", live_view)
    
    def _on_mission_escalated(self, mission: Mission, decision: str):
        """Callback quand une mission est escaladée"""
        if mission.type == MissionType.LIVE_TAB:
            live_view = self._mission_to_live_view(mission)
            self._live_missions_cache[mission.live_tab_id] = live_view
            self._trigger_callbacks("live_mission_updated", live_view)
    
    # ==================== Mise à Jour Auto ====================
    
    def start_live_updates(self):
        """Démarre les mises à jour automatiques du Live Tab"""
        if self._update_thread and self._update_thread.is_alive():
            logger.warning("⚠️ Mises à jour déjà actives")
            return
        
        self._stop_event.clear()
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
        
        logger.info(f"🔄 Mises à jour Live démarrées ({self.update_interval}s)")
    
    def stop_live_updates(self):
        """Arrête les mises à jour automatiques"""
        self._stop_event.set()
        if self._update_thread:
            self._update_thread.join(timeout=5)
        logger.info("🛑 Mises à jour Live arrêtées")
    
    def _update_loop(self):
        """Boucle de mise à jour des missions Live"""
        while not self._stop_event.is_set():
            try:
                # Mettre à jour toutes les missions Live
                for mission in self.engine.get_live_missions(visible_only=True):
                    if mission.live_tab_id in self._live_missions_cache:
                        old_view = self._live_missions_cache[mission.live_tab_id]
                        new_view = self._mission_to_live_view(mission)
                        
                        # Notifier si le statut a changé
                        if old_view.status != new_view.status:
                            self._trigger_callbacks("live_status_changed", new_view, old_view.status)
                        
                        # Mettre à jour le cache
                        self._live_missions_cache[mission.live_tab_id] = new_view
                
                # Attendre l'intervalle
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"❌ Erreur mise à jour Live: {e}")
                time.sleep(self.update_interval)
    
    def _execute_live_mission_async(self, mission_id: str):
        """Exécute une mission Live de manière asynchrone"""
        def execute():
            try:
                self.engine.execute_mission(mission_id)
            except Exception as e:
                logger.error(f"❌ Erreur exécution mission Live {mission_id}: {e}")
        
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
    
    # ==================== Callbacks Publics ====================
    
    def on(self, event: str, callback: Callable):
        """
        Enregistre un callback pour un événement Live.
        
        Events:
        - live_mission_created: Nouvelle mission Live
        - live_mission_updated: Mission mise à jour
        - live_mission_completed: Mission terminée
        - live_status_changed: Changement de statut
        
        Args:
            event: Nom de l'événement
            callback: Fonction à appeler
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, *args):
        """Déclenche les callbacks"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"❌ Erreur callback {event}: {e}")

# ==================== Fonctions Utilitaires ====================

def format_live_mission_for_display(mission: LiveMissionView) -> str:
    """
    Formate une mission Live pour affichage console.
    
    Args:
        mission: Vue de la mission
        
    Returns:
        Chaîne formatée
    """
    status_emoji = {
        "pending": "⏳",
        "running": "🔄",
        "analyzing": "🧠",
        "escalating": "🚨",
        "deciding": "👔",
        "executing": "⚡",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "🚫",
    }.get(mission.status, "❓")
    
    priority_emoji = {
        "LOW": "⚪",
        "MEDIUM": "🔵",
        "HIGH": "🟠",
        "CRITICAL": "🔴",
        "CEO_REVIEW": "👑",
    }.get(mission.priority, "⚪")
    
    lines = [
        f"{status_emoji} {mission.title}",
        f"   ID: {mission.live_tab_id}",
        f"   Priorité: {priority_emoji} {mission.priority}",
        f"   Progression: {mission.progress}%",
    ]
    
    if mission.agent:
        lines.append(f"   Agent: 🤖 {mission.agent}")
    
    if mission.is_critical:
        lines.append("   🚨 MISSION CRITIQUE")
    
    if mission.escalated_to_ceo:
        lines.append("   👔 Escaladée au CEO")
    
    if mission.current_step:
        lines.append(f"   Étape: {mission.current_step}")
    
    return "\n".join(lines)

# ==================== Point d'entrée ====================

if __name__ == "__main__":
    print("📺 Live Mission Handler - Test")
    print("=" * 70)
    
    # Créer le moteur et le handler
    from .mission_engine import MissionEngine
    
    engine = MissionEngine()
    handler = LiveMissionHandler(engine)
    
    # Créer quelques missions de test
    print("\n📋 Création de missions Live de test...")
    
    mission1 = handler.create_live_mission(
        title="🔍 Analyse système",
        description="Vérifier l'état de tous les services",
        agent="sentinel",
        priority="HIGH",
        auto_execute=False,
    )
    
    mission2 = handler.create_analysis_mission(
        target="codebase",
        analysis_type="security",
        agent="sentinel",
    )
    
    # Afficher le dashboard
    print("\n📊 Dashboard Live:")
    dashboard = handler.get_live_dashboard()
    print(f"  Total: {dashboard['stats']['total']}")
    print(f"  En attente: {dashboard['stats']['pending']}")
    print(f"  En cours: {dashboard['stats']['running']}")
    print(f"  Critiques: {dashboard['stats']['critical']}")
    
    # Afficher les missions
    print("\n📋 Missions Live:")
    for live_mission in handler.get_live_missions():
        print(f"\n{format_live_mission_for_display(live_mission)}")
    
    print("\n✅ LiveMissionHandler prêt!")
