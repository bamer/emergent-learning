"""
Lifecycle configuration and models.

This module contains the data structures and configuration
for the heuristic lifecycle management system.
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional


class HeuristicStatus(Enum):
    """Status of a heuristic in its lifecycle."""

    ACTIVE = "active"
    DORMANT = "dormant"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class UpdateType(Enum):
    """Type of heuristic update."""

    SUCCESS = "success"
    FAILURE = "failure"
    CONTRADICTION = "contradiction"
    DECAY = "decay"
    REVIVAL = "revival"
    MANUAL = "manual"


@dataclass
class LifecycleConfig:
    """Configuration for lifecycle management."""

    # Dormancy thresholds
    dormant_after_days: int = 60
    archived_after_dormant_days: int = 90

    # Rate-based contradiction threshold
    min_applications_for_deprecation: int = 10
    contradiction_rate_threshold: float = 0.30  # 30%

    # Rate limiting
    max_updates_per_day: int = 5
    cooldown_minutes: int = 60  # Minimum time between updates

    # Eviction policy
    max_active_per_domain: int = 10
    max_dormant_per_domain: int = 20

    # Confidence bounds (prevent extreme values)
    min_confidence: float = 0.05
    max_confidence: float = 0.95

    # Decay settings
    decay_half_life_days: int = 14
    decay_floor: float = 0.20  # Below this = dormant


@dataclass
class Heuristic:
    """Represents a heuristic with lifecycle state."""

    id: int
    domain: str
    rule: str
    explanation: Optional[str]
    confidence: float
    times_validated: int
    times_violated: int
    times_contradicted: int
    status: str
    last_used_at: Optional[datetime]
    dormant_since: Optional[datetime]
    is_golden: bool
    created_at: datetime
    updated_at: datetime


__all__ = [
    "HeuristicStatus",
    "UpdateType",
    "LifecycleConfig",
    "Heuristic",
]
