#!/usr/bin/env python3
"""
Escalation Protocol for ELF Agent System
Defines clear escalation paths and responsibilities for all agents.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import sys
from pathlib import Path

# Add agents directory to path
ROOT_DIR = Path(__file__).resolve().parents[1]  # emergent-learning dir
AGENTS_DIR = ROOT_DIR / "agents"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

# Import centralized logger
try:
    from Open_ELF.utils.elf_logging import get_logger, log_critical

    escalation_logger = get_logger("escalation")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    escalation_logger = logging.getLogger("escalation")


class AgentRole(Enum):
    """Define agent roles and responsibilities."""

    ORCHESTRATOR = "orchestrator"  # Central coordination
    SENTINEL = "sentinel"  # Continuous monitoring
    WATCHER = "sentinel"  # Periodic checks
    RESEARCHER = "researcher"  # Deep investigation
    ARCHITECT = "architect"  # System design
    SKEPTIC = "skeptic"  # Critical analysis
    CREATIVE = "creative"  # Innovation
    CEO = "ceo"  # Executive decisions


class EscalationLevel(Enum):
    """Define escalation levels."""

    LEVEL_1 = "level_1"  # Local agent handles
    LEVEL_2 = "level_2"  # Escalate to Orchestrator
    LEVEL_3 = "level_3"  # Escalate to CEO
    CRITICAL = "critical"  # Immediate system halt


@dataclass
class EscalationRule:
    """Define when and how to escalate issues."""

    name: str
    condition: str
    from_role: AgentRole
    to_role: AgentRole
    level: EscalationLevel
    cooldown_minutes: int = 30
    last_triggered: Optional[datetime] = None


class EscalationProtocol:
    """Central escalation protocol for all agents."""

    def __init__(self):
        self.logger = escalation_logger
        self.rules = self._define_rules()
        self.cooldowns = {}  # rule_name -> last_triggered_timestamp

    def _define_rules(self) -> List[EscalationRule]:
        """Define all escalation rules."""
        return [
            # Sentinel escalations
            EscalationRule(
                name="sentinel_service_failure",
                condition="Service health check fails",
                from_role=AgentRole.SENTINEL,
                to_role=AgentRole.CEO,
                level=EscalationLevel.CRITICAL,
                cooldown_minutes=5,
            ),
            EscalationRule(
                name="sentinel_pattern_detection",
                condition="Critical pattern detected",
                from_role=AgentRole.SENTINEL,
                to_role=AgentRole.CEO,
                level=EscalationLevel.LEVEL_3,
                cooldown_minutes=30,
            ),
            # Watcher escalations
            EscalationRule(
                name="sentinel_stale_agent",
                condition="Agent becomes unresponsive",
                from_role=AgentRole.WATCHER,
                to_role=AgentRole.ORCHESTRATOR,
                level=EscalationLevel.LEVEL_2,
                cooldown_minutes=10,
            ),
            EscalationRule(
                name="sentinel_complex_issue",
                condition="Complex issue requiring human decision",
                from_role=AgentRole.WATCHER,
                to_role=AgentRole.CEO,
                level=EscalationLevel.LEVEL_3,
                cooldown_minutes=60,
            ),
            # Agent escalations
            EscalationRule(
                name="agent_execution_failure",
                condition="Agent execution fails repeatedly",
                from_role=AgentRole.ORCHESTRATOR,
                to_role=AgentRole.CEO,
                level=EscalationLevel.LEVEL_3,
                cooldown_minutes=15,
            ),
            EscalationRule(
                name="agent_resource_exhaustion",
                condition="Agent consumes excessive resources",
                from_role=AgentRole.ORCHESTRATOR,
                to_role=AgentRole.CEO,
                level=EscalationLevel.CRITICAL,
                cooldown_minutes=5,
            ),
        ]

    def can_escalate(self, rule_name: str) -> bool:
        """Check if enough time has passed since last escalation of this rule."""
        if rule_name not in self.cooldowns:
            return True

        rule = next((r for r in self.rules if r.name == rule_name), None)
        if not rule:
            return True

        last_triggered = self.cooldowns[rule_name]
        cooldown = rule.cooldown_minutes * 60  # Convert to seconds
        elapsed = (datetime.now() - last_triggered).total_seconds()

        return elapsed > cooldown

    def escalate(self, rule_name: str, details: Dict[str, Any]) -> bool:
        """Process an escalation request."""
        # Find the rule
        rule = next((r for r in self.rules if r.name == rule_name), None)
        if not rule:
            self.logger.error(f"Unknown escalation rule: {rule_name}")
            return False

        # Check cooldown
        if not self.can_escalate(rule_name):
            self.logger.warning(f"Escalation {rule_name} is in cooldown period")
            return False

        # Log escalation
        self.logger.info(f"🚨 ESCALATION TRIGGERED: {rule_name}")
        self.logger.info(f"   From: {rule.from_role.value}")
        self.logger.info(f"   To: {rule.to_role.value}")
        self.logger.info(f"   Level: {rule.level.value}")
        self.logger.info(f"   Details: {json.dumps(details, indent=2)}")

        # Update cooldown
        self.cooldowns[rule_name] = datetime.now()
        rule.last_triggered = datetime.now()

        # Process based on level
        if rule.level == EscalationLevel.CRITICAL:
            self._handle_critical_escalation(rule, details)
        elif rule.level == EscalationLevel.LEVEL_3:
            self._handle_ceo_escalation(rule, details)
        elif rule.level == EscalationLevel.LEVEL_2:
            self._handle_orchestrator_escalation(rule, details)
        else:
            self._handle_local_escalation(rule, details)

        return True

    def _handle_critical_escalation(
        self, rule: EscalationRule, details: Dict[str, Any]
    ):
        """Handle critical escalations that may require system halt."""
        self.logger.critical(f"CRITICAL ESCALATION: {rule.name}")
        self.logger.critical(f"Details: {json.dumps(details, indent=2)}")

        # In a real implementation, this might:
        # 1. Halt all non-critical agents
        # 2. Notify system administrator immediately
        # 3. Initiate emergency backup procedures
        # 4. Possibly shut down the system

        # For now, we'll just log it as critical
        # Use self.logger.critical instead of log_critical_error to ensure we have a defined logger
        self.logger.critical(f"Critical escalation {rule.name}: {json.dumps(details, indent=2)}")

    def _handle_ceo_escalation(self, rule: EscalationRule, details: Dict[str, Any]):
        """Handle escalations to CEO agent."""
        self.logger.info(f"Escalating to CEO: {rule.name}")

        # In a real implementation, this would:
        # 1. Create a ticket in the CEO inbox
        # 2. Notify the CEO agent
        # 3. Set priority flags

        # For now, we'll simulate this by creating a file
        ceo_inbox = Path("/home/bamer/.opencode/emergent-learning/ceo-inbox")
        ceo_inbox.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = ceo_inbox / f"escalation_{rule.name}_{timestamp}.md"

        content = f"""# Escalation: {rule.name}

## From: {rule.from_role.value}
## To: {rule.to_role.value}
## Level: {rule.level.value}
## Time: {datetime.now().isoformat()}

## Details:
```json
{json.dumps(details, indent=2)}
```

## Action Required:
Please review and provide decision.
"""

        filename.write_text(content)
        self.logger.info(f"Created CEO escalation ticket: {filename}")

    def _handle_orchestrator_escalation(
        self, rule: EscalationRule, details: Dict[str, Any]
    ):
        """Handle escalations to Orchestrator."""
        self.logger.info(f"Escalating to Orchestrator: {rule.name}")

        # In a real implementation, this would:
        # 1. Send a message to the orchestrator
        # 2. Update agent statuses
        # 3. Trigger corrective actions

        # For now, we'll just log it
        self.logger.info(
            f"Orchestrator escalation details: {json.dumps(details, indent=2)}"
        )

    def _handle_local_escalation(self, rule: EscalationRule, details: Dict[str, Any]):
        """Handle local escalations within the same agent."""
        self.logger.info(f"Local escalation: {rule.name}")

        # In a real implementation, this would:
        # 1. Retry the operation with different parameters
        # 2. Switch to backup methods
        # 3. Adjust internal settings

        # For now, we'll just log it
        self.logger.info(f"Local escalation details: {json.dumps(details, indent=2)}")


# Global escalation protocol instance
escalation_protocol = EscalationProtocol()


def get_escalation_protocol():
    """Get the global escalation protocol instance."""
    return escalation_protocol


if __name__ == "__main__":
    # Test the escalation protocol
    protocol = get_escalation_protocol()

    print("Testing Escalation Protocol...")

    # Test critical escalation
    protocol.escalate(
        "sentinel_service_failure",
        {"service": "frontend", "status": "down", "error": "Connection refused"},
    )

    # Test CEO escalation
    protocol.escalate(
        "sentinel_pattern_detection",
        {"pattern": "declining_activity_trend", "confidence": 0.95, "impact": "high"},
    )

    print("Escalation protocol test completed.")
