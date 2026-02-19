"""
Lifecycle Manager Package

This package provides heuristic lifecycle management with:
- Rate-limited confidence updates
- EMA smoothing for stability
- Domain elasticity with eviction policies
- Dormancy and revival mechanisms

Main usage:
    from query.lifecycle import LifecycleManager, LifecycleConfig

    manager = LifecycleManager()
    result = manager.update_confidence(heuristic_id, UpdateType.SUCCESS)
"""

# Import from the existing lifecycle_manager.py for backward compatibility
# This allows gradual migration to the modular structure
try:
    from query.lifecycle_manager import (
        LifecycleManager,
        LifecycleConfig,
        Heuristic,
        HeuristicStatus,
        UpdateType,
    )
except ImportError:
    from ..lifecycle_manager import (
        LifecycleManager,
        LifecycleConfig,
        Heuristic,
        HeuristicStatus,
        UpdateType,
    )

# Also export from models for new code
from .models import (
    LifecycleConfig as ModelsConfig,
    Heuristic as ModelsHeuristic,
    HeuristicStatus as ModelsStatus,
    UpdateType as ModelsUpdateType,
)

__all__ = [
    # Main class
    "LifecycleManager",
    # Configuration
    "LifecycleConfig",
    # Models
    "Heuristic",
    "HeuristicStatus",
    "UpdateType",
]
