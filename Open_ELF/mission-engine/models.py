"""
Modèles de données pour le Mission Engine

Définit les classes Mission, MissionResult, et autres structures de données.
"""

import json
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


class MissionStatus(Enum):
    """Statuts possibles d'une mission"""
    PENDING = "pending"           # En attente
    QUEUED = "queued"             # En file d'attente
    RUNNING = "running"           # En cours d'exécution
    ANALYZING = "analyzing"       # Analyse par agent
    ESCALATING = "escalating"     # Escalade au CEO
    DECIDING = "deciding"         # Décision CEO en cours
    EXECUTING = "executing"       # Exécution des actions
    COMPLETED = "completed"       # Terminée avec succès
    FAILED = "failed"             # Échouée
    CANCELLED = "cancelled"       # Annulée
    TIMEOUT = "timeout"           # Timeout
    WAITING_REVIEW = "waiting_review"  # En attente de revue


class MissionPriority(Enum):
    """Niveaux de priorité des missions"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    CEO_REVIEW = 5


class MissionType(Enum):
    """Types de missions supportées"""
    LIVE_TAB = "live_tab"         # Mission de l'onglet Live
    PATTERN_RESPONSE = "pattern_response"  # Réponse à un pattern détecté
    AGENT_TASK = "agent_task"     # Tâche spécifique d'agent
    CEO_ESCALATION = "ceo_escalation"  # Escalade CEO
    SYSTEM_MAINTENANCE = "system_maintenance"  # Maintenance système
    CUSTOM = "custom"             # Mission personnalisée


@dataclass
class MissionStep:
    """Une étape dans l'exécution d'une mission"""
    name: str
    status: MissionStatus = MissionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class MissionResult:
    """Résultat d'une mission exécutée"""
    success: bool
    output: str = ""
    actions: List[str] = field(default_factory=list)
    agent_analysis: Optional[str] = None
    ceo_decision: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "actions": self.actions,
            "agent_analysis": self.agent_analysis,
            "ceo_decision": self.ceo_decision,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class Mission:
    """
    Représente une mission à exécuter
    
    Attributes:
        id: Identifiant unique de la mission
        title: Titre de la mission
        description: Description détaillée
        type: Type de mission
        status: Statut actuel
        priority: Priorité de la mission
        agent: Nom de l'agent à appeler (optionnel)
        context: Contexte additionnel
        created_at: Date de création
        started_at: Date de début d'exécution
        completed_at: Date de fin
        result: Résultat de la mission
        steps: Étapes d'exécution
        is_critical: Si la mission est critique
        escalated_to_ceo: Si escaladée au CEO
    """
    title: str
    description: str
    type: MissionType = MissionType.CUSTOM
    priority: MissionPriority = MissionPriority.MEDIUM
    agent: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Champs auto-générés
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: MissionStatus = MissionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[MissionResult] = None
    steps: List[MissionStep] = field(default_factory=list)
    is_critical: bool = False
    escalated_to_ceo: bool = False
    
    # Pour Live Tab
    live_tab_id: Optional[str] = None  # ID dans l'onglet Live
    live_tab_visible: bool = True  # Visible dans l'onglet Live
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la mission en dictionnaire"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "priority": self.priority.name,
            "agent": self.agent,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result.to_dict() if self.result else None,
            "steps": [step.to_dict() for step in self.steps],
            "is_critical": self.is_critical,
            "escalated_to_ceo": self.escalated_to_ceo,
            "live_tab_id": self.live_tab_id,
            "live_tab_visible": self.live_tab_visible,
        }
    
    def to_json(self) -> str:
        """Convertit la mission en JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def start(self):
        """Marque la mission comme démarrée"""
        self.status = MissionStatus.RUNNING
        self.started_at = datetime.now()
    
    def complete(self, result: MissionResult):
        """Marque la mission comme terminée"""
        self.status = MissionStatus.COMPLETED if result.success else MissionStatus.FAILED
        self.completed_at = datetime.now()
        self.result = result
    
    def fail(self, error: str):
        """Marque la mission comme échouée"""
        self.status = MissionStatus.FAILED
        self.completed_at = datetime.now()
        self.result = MissionResult(success=False, output=error)
    
    def add_step(self, name: str) -> MissionStep:
        """Ajoute une étape à la mission"""
        step = MissionStep(name=name)
        self.steps.append(step)
        return step
    
    def get_execution_time_ms(self) -> int:
        """Calcule le temps d'exécution en millisecondes"""
        if not self.started_at:
            return 0
        end_time = self.completed_at or datetime.now()
        return int((end_time - self.started_at).total_seconds() * 1000)
    
    @property
    def is_active(self) -> bool:
        """Vérifie si la mission est active"""
        return self.status in [
            MissionStatus.PENDING,
            MissionStatus.QUEUED,
            MissionStatus.RUNNING,
            MissionStatus.ANALYZING,
            MissionStatus.ESCALATING,
            MissionStatus.DECIDING,
            MissionStatus.EXECUTING,
            MissionStatus.WAITING_REVIEW,
        ]
    
    @property
    def is_completed(self) -> bool:
        """Vérifie si la mission est terminée"""
        return self.status in [
            MissionStatus.COMPLETED,
            MissionStatus.FAILED,
            MissionStatus.CANCELLED,
            MissionStatus.TIMEOUT,
        ]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mission":
        """Crée une mission depuis un dictionnaire"""
        mission = cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data["title"],
            description=data["description"],
            type=MissionType(data.get("type", "custom")),
            priority=MissionPriority[data.get("priority", "MEDIUM")],
            agent=data.get("agent"),
            context=data.get("context", {}),
            status=MissionStatus(data.get("status", "pending")),
            is_critical=data.get("is_critical", False),
            escalated_to_ceo=data.get("escalated_to_ceo", False),
            live_tab_id=data.get("live_tab_id"),
            live_tab_visible=data.get("live_tab_visible", True),
        )
        
        # Parse dates
        if data.get("created_at"):
            mission.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            mission.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            mission.completed_at = datetime.fromisoformat(data["completed_at"])
        
        # Parse result
        if data.get("result"):
            result_data = data["result"]
            mission.result = MissionResult(
                success=result_data.get("success", False),
                output=result_data.get("output", ""),
                actions=result_data.get("actions", []),
                agent_analysis=result_data.get("agent_analysis"),
                ceo_decision=result_data.get("ceo_decision"),
                metadata=result_data.get("metadata", {}),
                execution_time_ms=result_data.get("execution_time_ms", 0),
            )
        
        return mission


@dataclass
class MissionQueue:
    """File d'attente de missions"""
    missions: List[Mission] = field(default_factory=list)
    max_size: int = 100
    
    def add(self, mission: Mission) -> bool:
        """Ajoute une mission à la file"""
        if len(self.missions) >= self.max_size:
            return False
        self.missions.append(mission)
        return True
    
    def get_next(self) -> Optional[Mission]:
        """Récupère la prochaine mission (par priorité)"""
        if not self.missions:
            return None
        
        # Trier par priorité (descendant) puis par date de création
        self.missions.sort(key=lambda m: (-m.priority.value, m.created_at))
        
        # Récupérer la première mission en attente
        for mission in self.missions:
            if mission.status == MissionStatus.PENDING:
                return mission
        
        return None
    
    def remove(self, mission_id: str) -> bool:
        """Supprime une mission de la file"""
        for i, mission in enumerate(self.missions):
            if mission.id == mission_id:
                del self.missions[i]
                return True
        return False
    
    def get_by_status(self, status: MissionStatus) -> List[Mission]:
        """Récupère les missions par statut"""
        return [m for m in self.missions if m.status == status]
    
    def get_by_type(self, mission_type: MissionType) -> List[Mission]:
        """Récupère les missions par type"""
        return [m for m in self.missions if m.type == mission_type]
    
    def clear_completed(self) -> int:
        """Supprime les missions terminées, retourne le nombre supprimé"""
        completed = [m for m in self.missions if m.is_completed]
        self.missions = [m for m in self.missions if not m.is_completed]
        return len(completed)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la file en dictionnaire"""
        return {
            "missions": [m.to_dict() for m in self.missions],
            "max_size": self.max_size,
            "count": len(self.missions),
            "pending": len(self.get_by_status(MissionStatus.PENDING)),
            "running": len(self.get_by_status(MissionStatus.RUNNING)),
            "completed": len([m for m in self.missions if m.is_completed]),
        }
