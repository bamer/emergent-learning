#!/usr/bin/env python3
"""
Agent Execution Engine - Actually call agents and execute workflow

Turns recommendations into real agent calls:
1. Call recommended agent with task
2. Get analysis result
3. If critical → escalate to CEO
4. CEO makes decision
5. Execute decision
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import json

sys.path.insert(0, str(Path(__file__).parent))

from opencode_client import OpenCodeClient

logger = logging.getLogger(__name__)


class AgentExecutionEngine:
    """Execute real agent workflows through OpenCode API."""

    def __init__(self, server_url: str = "http://localhost:4096"):
        self.server_url = server_url
        self.client = OpenCodeClient(server_url=server_url)
        self.execution_log = []

    def execute_pattern_response(
        self,
        pattern: str,
        agent_to_call: str,
        recommendations: List[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute full workflow for detected pattern:
        1. Call agent to analyze
        2. Get analysis
        3. Escalate if critical
        4. CEO decides
        5. Return decision
        """
        logger.info(f"\n{'=' * 70}")
        logger.info(f"🚀 EXECUTING WORKFLOW FOR PATTERN: {pattern}")
        logger.info(f"{'=' * 70}")

        result = {
            "pattern": pattern,
            "agent_analysis": None,
            "is_critical": False,
            "ceo_decision": None,
            "actions": [],
            "status": "pending",
        }

        # Step 1: Call agent to analyze
        logger.info(f"\n[1️⃣ AGENT CALL] Calling {agent_to_call} agent...")
        agent_result = self._call_agent(
            agent_to_call, pattern, recommendations, context
        )

        if agent_result:
            result["agent_analysis"] = agent_result
            logger.info(f"✅ Agent analysis received ({len(agent_result)} chars)")
        else:
            logger.error(f"❌ Agent {agent_to_call} failed to respond")
            result["status"] = "agent_failed"
            return result

        # Step 2: Determine if critical
        is_critical = self._is_critical(pattern, agent_result)
        result["is_critical"] = is_critical

        if is_critical:
            logger.warning(f"🚨 CRITICAL ISSUE DETECTED - Escalating to CEO")

        # Step 3: Escalate to CEO if critical
        if is_critical:
            logger.info(f"\n[2️⃣ CEO ESCALATION] Sending to CEO for decision...")
            ceo_decision = self._escalate_to_ceo(pattern, agent_result, recommendations)

            if ceo_decision:
                result["ceo_decision"] = ceo_decision
                logger.info(f"✅ CEO made decision: {ceo_decision[:100]}...")
            else:
                logger.error("❌ CEO failed to respond")
                result["status"] = "ceo_failed"
                return result
        else:
            logger.info(
                f"\n[2️⃣ CEO DECISION] Non-critical - using agent recommendations"
            )
            result["ceo_decision"] = (
                f"Execute recommendations from {agent_to_call}: {'; '.join(recommendations[:2])}"
            )

        # Step 4: Extract actions from decision
        logger.info(f"\n[3️⃣ ACTION EXTRACTION] Extracting actions from decision...")
        actions = self._extract_actions(result["ceo_decision"])
        result["actions"] = actions

        for i, action in enumerate(actions, 1):
            logger.info(f"  {i}. {action}")

        # Step 5: Log execution
        result["status"] = "completed"
        self.execution_log.append(result)

        logger.info(f"\n✅ WORKFLOW COMPLETED")
        logger.info(f"{'=' * 70}\n")

        return result

    def _call_agent(
        self,
        agent: str,
        pattern: str,
        recommendations: List[str],
        context: Dict[str, Any],
    ) -> Optional[str]:
        """Call specific agent via OpenCode API."""
        try:
            # Build prompt for agent
            prompt = f"""
You are the {agent} agent. Analyze this detected pattern and provide actionable insights.

PATTERN DETECTED: {pattern}

CONTEXT:
{json.dumps(context, indent=2)[:500]}

INITIAL RECOMMENDATIONS:
{chr(10).join(f"- {r}" for r in recommendations[:3])}

Please provide:
1. Root cause analysis
2. Potential impacts
3. Specific actions to take
4. Timeline for implementation
5. Success metrics

Be concise but thorough.
"""

            logger.debug(f"Calling {agent} agent via OpenCode API...")
            response = self.client.call(prompt, agent=agent, timeout=300)

            if response:
                logger.debug(f"Agent response: {response[:200]}...")

            return response

        except Exception as e:
            logger.error(f"❌ Agent call failed: {e}")
            return None

    def _is_critical(self, pattern: str, analysis: str) -> bool:
        """Determine if pattern is critical based on keywords."""
        critical_keywords = [
            "critical",
            "severe",
            "urgent",
            "immediately",
            "failure",
            "down",
            "crash",
            "security",
            "breach",
            "data loss",
            "must fix",
        ]

        combined = f"{pattern} {analysis}".lower()
        return any(keyword in combined for keyword in critical_keywords)

    def _escalate_to_ceo(
        self, pattern: str, agent_analysis: str, recommendations: List[str]
    ) -> Optional[str]:
        """Escalate critical issue to CEO for decision."""
        try:
            prompt = f"""
You are the CEO/CTO of this system. A critical issue has been escalated to you.

CRITICAL PATTERN: {pattern}

AGENT ANALYSIS:
{agent_analysis[:1000]}

TEAM RECOMMENDATIONS:
{chr(10).join(f"- {r}" for r in recommendations[:5])}

As CEO, you must:
1. Assess the business impact
2. Make a clear decision
3. Specify exactly what should be done
4. Set timeline and priority

Format your response as:
DECISION: [Your decision]
RATIONALE: [Why]
ACTIONS:
- [Action 1]
- [Action 2]
- [Action 3]
TIMELINE: [When]
PRIORITY: [Critical/High/Medium/Low]
"""

            logger.debug("Calling CEO for decision...")
            response = self.client.call(prompt, agent="general", timeout=90)

            if response:
                logger.debug(f"CEO response: {response[:200]}...")

            return response

        except Exception as e:
            logger.error(f"❌ CEO escalation failed: {e}")
            return None

    def _extract_actions(self, decision: str) -> List[str]:
        """Extract actionable items from CEO decision."""
        actions = []

        # Simple parsing: look for lines with hyphens
        for line in decision.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                actions.append(line[2:])
            elif line.startswith("* "):
                actions.append(line[2:])
            elif line.startswith("Action "):
                actions.append(line)

        # If no structured actions found, use whole decision
        if not actions:
            actions = [decision[:200] + "..."]

        return actions

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get history of executed workflows."""
        return self.execution_log.copy()


def main():
    """Test agent execution engine."""
    engine = AgentExecutionEngine()

    # Test pattern
    pattern = "Declining activity trend detected"
    agent = "researcher"
    recommendations = [
        "Investigate root cause of activity decline",
        "Check if users are disengaged",
        "Review recent system changes",
    ]
    context = {
        "activity_score": 0,
        "recent_learnings": 0,
        "timestamp": "2026-01-30T13:00:00",
        "previous_activity": 5,
    }

    print("\n" + "=" * 70)
    print("🤖 Agent Execution Engine - Test Run")
    print("=" * 70)

    result = engine.execute_pattern_response(
        pattern=pattern,
        agent_to_call=agent,
        recommendations=recommendations,
        context=context,
    )

    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(json.dumps(result, indent=2)[:500] + "...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
