"""
Mission Engine - Composant autonome de gestion des missions

Ce module gère l'exécution des missions de l'onglet Live et fournit
un orchestrateur de workflow indépendant.

Usage:
    from mission_engine import MissionEngine, LiveMissionHandler
    
    engine = MissionEngine()
    
    # Créer une mission Live
    mission = engine.create_live_mission(
        title="Analyser le système",
        description="Vérifier l'état de tous les services"
    )
    
    # Exécuter la mission
    result = engine.execute_mission(mission.id)
"""

from .mission_engine import MissionEngine, Mission, MissionStatus, MissionPriority
from .mission_live_handler import LiveMissionHandler
from .config import MissionEngineConfig

__version__ = "1.0.0"
__all__ = [
    "MissionEngine",
    "Mission", 
    "MissionStatus",
    "MissionPriority",
    "LiveMissionHandler",
    "MissionEngineConfig",
]
