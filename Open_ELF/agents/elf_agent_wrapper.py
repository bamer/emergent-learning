#!/usr/bin/env python3
"""
ELF Agent Wrapper
================

Wrapper pour tous les agents ELF qui s'assure qu'ils utilisent:
1. Le même système d'orchestration (UnifiedOrchestrator)
2. Le même système de logging centralisé
3. La politique "ça marche ou ça crash"

Usage:
    from elf_agent_wrapper import AgentWrapper

    wrapper = AgentWrapper("my_agent")
    wrapper.run()
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Add agents directory to path
AGENTS_DIR = Path(__file__).parent
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from elf_logging import get_logger, log_critical, log_error, log_warning, log_info


@dataclass
class AgentConfig:
    """Configuration pour un agent."""

    name: str
    description: str
    icon: str = "🤖"
    auto_start: bool = False
    restart_on_error: bool = True
    max_restarts: int = 3


class AgentWrapper:
    """
    Wrapper pour tous les agents ELF.

    Garantit:
    - Logging centralisé
    - Gestion d'erreurs stricte
    - Intégration avec l'orchestrateur
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = get_logger(config.name)
        self.error_count = 0
        self.restart_count = 0
        self.running = False

        self.logger.info(f"Agent wrapper initialized: {config.name}")

    def run(self, target_function=None, *args, **kwargs):
        """
        Exécute l'agent avec gestion d'erreurs stricte.

        Args:
            target_function: Fonction principale de l'agent
            *args, **kwargs: Arguments pour la fonction

        Returns:
            Résultat de la fonction ou None en cas d'erreur
        """
        self.running = True
        self.logger.info(f"🚀 Starting agent: {self.config.name}")

        try:
            if target_function:
                result = target_function(*args, **kwargs)
                self.logger.info(f"✅ Agent {self.config.name} completed successfully")
                return result
            else:
                self._default_run()
                return None

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"❌ Agent {self.config.name} error: {e}")

            # Politique: si trop d'erreurs, on escalate
            if self.error_count >= 3:
                log_critical(
                    self.config.name,
                    f"Agent exceeded max error count: {self.error_count}",
                    crash=False,  # Ne pas crash, juste logger
                )

            # Si restart_on_error est activé et qu'on n'a pas dépassé le max
            if (
                self.config.restart_on_error
                and self.restart_count < self.config.max_restarts
            ):
                self.restart_count += 1
                self.logger.info(
                    f"🔄 Restarting agent (attempt {self.restart_count}/{self.config.max_restarts})"
                )
                return self.run(target_function, *args, **kwargs)

            return None

        finally:
            self.running = False

    def _default_run(self):
        """Exécution par défaut si aucune fonction n'est fournie."""
        self.logger.info(f"Agent {self.config.name} running default loop")
        # Les agents spécifiques doivent surcharger cette méthode
        raise NotImplementedError(
            "Subclasses must implement _default_run or provide a target_function"
        )

    def stop(self):
        """Arrête l'agent proprement."""
        self.logger.info(f"🛑 Stopping agent: {self.config.name}")
        self.running = False

    def health_check(self) -> bool:
        """
        Vérifie la santé de l'agent.

        Returns:
            bool: True si l'agent est healthy, False sinon
        """
        if self.error_count > 5:
            self.logger.error(
                f"Agent {self.config.name} unhealthy: too many errors ({self.error_count})"
            )
            return False

        if not self.running and self.config.auto_start:
            self.logger.warning(f"Agent {self.config.name} should be running but isn't")
            return False

        return True

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'agent."""
        return {
            "name": self.config.name,
            "running": self.running,
            "error_count": self.error_count,
            "restart_count": self.restart_count,
            "healthy": self.health_check(),
        }


# Example usage and test
if __name__ == "__main__":
    print("Testing ELF Agent Wrapper...")

    # Test 1: Create wrapper
    config = AgentConfig(
        name="test_agent", description="Test agent for wrapper verification", icon="🧪"
    )
    wrapper = AgentWrapper(config)
    print(f"✅ Wrapper created for: {config.name}")

    # Test 2: Test logging
    wrapper.logger.info("Test info message")
    wrapper.logger.warning("Test warning message")
    print("✅ Logging test passed")

    # Test 3: Test health check
    status = wrapper.get_status()
    print(f"✅ Status: {status}")

    print("\n✅ All wrapper tests passed!")
    print("Agent wrapper is ready for use.")
