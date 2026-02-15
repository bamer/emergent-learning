"""
OpenCode Swarm - Phased Multi-Agent Workshop
================================================

Implements the correct swarm workflow pattern for the ELF system.

Usage:
    from Open_ELF.elf_swarm import SwarmOrchestrator

    orchestrator = SwarmOrchestrator(task="Implement feature X")
    orchestrator.run()
"""

from .orchestrator import SwarmOrchestrator
from .swarm_manager import SwarmManager

__all__ = ["SwarmOrchestrator", "SwarmManager"]
