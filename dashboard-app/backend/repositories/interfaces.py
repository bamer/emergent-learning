"""
Repository interfaces for the ELF Dashboard.

Defines abstract interfaces for data access layers, following the repository pattern.
Each interface provides contract for specific data operations while hiding
implementation details from the business logic layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class IHeuristicsRepository(ABC):
    """Repository interface for heuristics data access."""

    @abstractmethod
    def get_by_id(self, heuristic_id: int) -> Optional[Dict[str, Any]]:
        """Get a heuristic by ID."""
        pass

    @abstractmethod
    def list_heuristics(
        self,
        domain: Optional[str] = None,
        golden_only: bool = False,
        sort_by: str = "confidence",
        limit: int = 50,
        scope: str = "global",
    ) -> List[Dict[str, Any]]:
        """List heuristics with filtering options."""
        pass

    @abstractmethod
    def create_heuristic(self, data: Dict[str, Any]) -> int:
        """Create a new heuristic."""
        pass

    @abstractmethod
    def update_heuristic(self, heuristic_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing heuristic."""
        pass

    @abstractmethod
    def delete_heuristic(self, heuristic_id: int) -> bool:
        """Delete a heuristic."""
        pass

    @abstractmethod
    def promote_to_golden(self, heuristic_id: int) -> bool:
        """Promote a heuristic to golden rule."""
        pass

    @abstractmethod
    def demote_from_golden(self, heuristic_id: int) -> bool:
        """Demote a golden rule back to heuristic."""
        pass

    @abstractmethod
    def get_heuristic_graph(self) -> Dict[str, Any]:
        """Get heuristic graph data for visualization."""
        pass


class IDecisionsRepository(ABC):
    """Repository interface for architecture decisions."""

    @abstractmethod
    def get_by_id(self, decision_id: int) -> Optional[Dict[str, Any]]:
        """Get a decision by ID."""
        pass

    @abstractmethod
    def list_decisions(
        self,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List decisions with filtering options."""
        pass

    @abstractmethod
    def create_decision(self, data: Dict[str, Any]) -> int:
        """Create a new decision."""
        pass

    @abstractmethod
    def update_decision(self, decision_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing decision."""
        pass

    @abstractmethod
    def delete_decision(self, decision_id: int) -> bool:
        """Delete a decision."""
        pass

    @abstractmethod
    def supersede_decision(
        self, old_decision_id: int, new_decision_data: Dict[str, Any]
    ) -> int:
        """Supersede a decision with a new one."""
        pass


class IAssumptionsRepository(ABC):
    """Repository interface for assumptions."""

    @abstractmethod
    def get_by_id(self, assumption_id: int) -> Optional[Dict[str, Any]]:
        """Get an assumption by ID."""
        pass

    @abstractmethod
    def list_assumptions(
        self,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        min_confidence: Optional[float] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List assumptions with filtering options."""
        pass

    @abstractmethod
    def create_assumption(self, data: Dict[str, Any]) -> int:
        """Create a new assumption."""
        pass

    @abstractmethod
    def update_assumption(self, assumption_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing assumption."""
        pass

    @abstractmethod
    def delete_assumption(self, assumption_id: int) -> bool:
        """Delete an assumption."""
        pass

    @abstractmethod
    def verify_assumption(self, assumption_id: int) -> Dict[str, Any]:
        """Verify an assumption (increment verified_count)."""
        pass

    @abstractmethod
    def challenge_assumption(self, assumption_id: int) -> Dict[str, Any]:
        """Challenge an assumption (increment challenged_count)."""
        pass


class IInvariantsRepository(ABC):
    """Repository interface for invariants."""

    @abstractmethod
    def get_by_id(self, invariant_id: int) -> Optional[Dict[str, Any]]:
        """Get an invariant by ID."""
        pass

    @abstractmethod
    def list_invariants(
        self,
        domain: Optional[str] = None,
        scope: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List invariants with filtering options."""
        pass

    @abstractmethod
    def create_invariant(self, data: Dict[str, Any]) -> int:
        """Create a new invariant."""
        pass

    @abstractmethod
    def update_invariant(self, invariant_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing invariant."""
        pass

    @abstractmethod
    def delete_invariant(self, invariant_id: int) -> bool:
        """Delete an invariant."""
        pass

    @abstractmethod
    def validate_invariant(self, invariant_id: int) -> bool:
        """Mark an invariant as validated."""
        pass

    @abstractmethod
    def record_violation(self, invariant_id: int) -> Dict[str, Any]:
        """Record a violation of an invariant."""
        pass


class ISpikeReportsRepository(ABC):
    """Repository interface for spike reports."""

    @abstractmethod
    def get_by_id(self, spike_id: int) -> Optional[Dict[str, Any]]:
        """Get a spike report by ID."""
        pass

    @abstractmethod
    def list_spike_reports(
        self,
        domain: Optional[str] = None,
        tags: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "recent",
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List spike reports with filtering options."""
        pass

    @abstractmethod
    def search_spike_reports(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search spike reports."""
        pass

    @abstractmethod
    def create_spike_report(self, data: Dict[str, Any]) -> int:
        """Create a new spike report."""
        pass

    @abstractmethod
    def update_spike_report(self, spike_id: int, data: Dict[str, Any]) -> bool:
        """Update a spike report."""
        pass

    @abstractmethod
    def delete_spike_report(self, spike_id: int) -> bool:
        """Delete a spike report."""
        pass

    @abstractmethod
    def rate_spike_report(self, spike_id: int, score: float) -> Dict[str, Any]:
        """Rate a spike report's usefulness."""
        pass


class IWorkflowsRepository(ABC):
    """Repository interface for workflows."""

    @abstractmethod
    def list_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflow definitions."""
        pass

    @abstractmethod
    def create_workflow(self, data: Dict[str, Any]) -> int:
        """Create a new workflow."""
        pass

    @abstractmethod
    def get_workflow_runs(
        self,
        workflow_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get workflow runs with filtering."""
        pass

    @abstractmethod
    def get_workflow_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific workflow run."""
        pass


class ILearningsRepository(ABC):
    """Repository interface for learnings (failures, successes, observations)."""

    @abstractmethod
    def list_learnings(
        self, type: Optional[str] = None, domain: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List learnings with filtering options."""
        pass

    @abstractmethod
    def create_learning(self, data: Dict[str, Any]) -> int:
        """Create a new learning."""
        pass

    @abstractmethod
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        pass


class IMetricsRepository(ABC):
    """Repository interface for metrics and analytics."""

    @abstractmethod
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics."""
        pass

    @abstractmethod
    def get_domain_stats(self) -> List[Dict[str, Any]]:
        """Get statistics by domain."""
        pass

    @abstractmethod
    def record_metric(self, data: Dict[str, Any]) -> int:
        """Record a new metric."""
        pass

    @abstractmethod
    def get_metrics(
        self,
        metric_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get metrics with filtering."""
        pass
