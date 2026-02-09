"""
Pattern Response Handler

Handles responses to detected patterns by creating heuristics, recommending agents, and generating actionable items.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import ELF utilities
from event_chronicle import get_chronicle

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PatternResponseHandler")


class PatternResponseHandler:
    """Handles responses to detected patterns in the ELF system.

    This component takes detected patterns and generates appropriate responses
    including recording heuristics, recommending agents, and creating actionable items.
    """

    def __init__(self, elf_home: Path):
        """Initialize with ELF home directory."""
        self.elf_home = Path(elf_home)
        self.heuristics_dir = self.elf_home / "memory" / "heuristics"
        self.heuristics_dir.mkdir(parents=True, exist_ok=True)

    def handle_pattern(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a detected pattern and generate appropriate response.

        Args:
            pattern: The detected pattern string
            context: Additional context data

        Returns:
            Dict containing response details
        """
        result = {
            "pattern": pattern,
            "learning_recorded": False,
            "agent_called": None,
            "recommendations": [],
            "context": context,
        }

        try:
            # Record as heuristic
            heuristic_id = self._record_heuristic(pattern, context)
            result["learning_recorded"] = True

            # Recommend agents based on pattern
            agent_recommendation = self._recommend_agent(pattern)
            if agent_recommendation:
                result["agent_called"] = agent_recommendation

            # Generate recommendations
            recommendations = self._generate_recommendations(pattern, context)
            result["recommendations"] = recommendations

            # Log to chronicle
            get_chronicle().log_event(
                "pattern_responded",
                "pattern_response_handler",
                {
                    "pattern": pattern,
                    "heuristic_id": heuristic_id,
                    "agent_recommendation": agent_recommendation,
                    "recommendations": recommendations,
                    "context": context,
                },
            )

            logger.info(f"✅ Pattern handled: {pattern}")

        except Exception as e:
            logger.error(f"❌ Error handling pattern {pattern}: {str(e)}")
            result["error"] = str(e)

        return result

    def _record_heuristic(self, pattern: str, context: Dict[str, Any]) -> str:
        """Record a pattern as a system heuristic."""

        # Extract heuristic details from pattern
        heuristic_id = f"heuristic_{int(datetime.now().timestamp())}"
        timestamp = datetime.now().isoformat()

        # Create heuristic content
        heuristic_content = f"""# {pattern}

**Domain**: pattern-detection
**Severity**: 2
**Tags**: {{"pattern-recommendation"}}
**Date**: {timestamp.split("T")[0]}

## Summary

System detected pattern: {pattern}

## What Happened

The system detected the pattern "{pattern}" during monitoring.

## Root Cause

This pattern represents a recurring theme in system behavior that should be documented.

## Impact

Documenting this pattern helps prevent future occurrences and improves system learning.

## Prevention

This pattern has been recorded as a heuristic for future reference and system learning.

## Related

- **Experiments**: None
- **Heuristics**: {heuristic_id}
- **Similar Failures**: None
"""

        # Write heuristic file
        heuristic_file = self.heuristics_dir / f"{heuristic_id}.md"
        with open(heuristic_file, "w", encoding="utf-8") as f:
            f.write(heuristic_content)

        return heuristic_id

    def _recommend_agent(self, pattern: str) -> Optional[str]:
        """Recommend an agent to handle the pattern."""

        # Extract keywords from pattern
        pattern_lower = pattern.lower()

        if "circular import" in pattern_lower:
            return "architect"
        elif "performance" in pattern_lower:
            return "performance-engineer"
        elif "error" in pattern_lower or "failure" in pattern_lower:
            return "researcher"
        elif "activity" in pattern_lower or "trend" in pattern_lower:
            return "learning-extractor"
        else:
            return "researcher"  # default

    def _generate_recommendations(
        self, pattern: str, context: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations for the pattern."""
        recommendations = []

        pattern_lower = pattern.lower()

        if "circular import" in pattern_lower:
            recommendations.append("Identify import chain causing circular dependency")
            recommendations.append(
                "Refactor to use lazy imports or dependency inversion"
            )
            recommendations.append("Add circular import detection to CI/CD pipeline")
            recommendations.append("Document the fix as a new heuristic")

        elif "performance" in pattern_lower:
            recommendations.append("Profile affected code with cProfile")
            recommendations.append("Identify bottlenecks using flame graphs")
            recommendations.append("Implement caching for repeated operations")
            recommendations.append(
                "Optimize data structures for better access patterns"
            )

        elif "error" in pattern_lower or "failure" in pattern_lower:
            recommendations.append("Add comprehensive error handling and logging")
            recommendations.append("Implement retry logic with exponential backoff")
            recommendations.append("Create automated alert for this error type")
            recommendations.append("Document failure scenario as a known risk")

        elif "activity" in pattern_lower or "trend" in pattern_lower:
            recommendations.append("Analyze cause of declining activity")
            recommendations.append("Check system health metrics")
            recommendations.append("Review recent code deployments")
            recommendations.append("Contact team members who may have affected system")

        else:
            recommendations.append("Document pattern in system knowledge base")
            recommendations.append("Review similar patterns from historical data")
            recommendations.append("Set up monitoring for this pattern recurrence")
            recommendations.append(
                "Consider creating automated response for this pattern"
            )

        return recommendations
