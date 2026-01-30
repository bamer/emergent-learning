#!/usr/bin/env python3
"""
Pattern Response Handler - React to detected patterns

When Sentinel detects patterns:
1. Record pattern as learning
2. Decide which agent to call
3. Execute agent analysis
4. Record recommendations
5. Update heuristics
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PatternResponseHandler:
    """Handle responses to detected patterns."""
    
    def __init__(self, elf_home: Path = None, db_path: str = None):
        if elf_home is None:
            elf_home = Path.home() / ".opencode" / "emergent-learning"
        
        self.elf_home = elf_home
        self.db_path = db_path or str(elf_home / "memory" / "index.db")
    
    def handle_pattern(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a detected pattern.
        
        Args:
            pattern: Pattern description (e.g., "Declining activity trend detected")
            context: Context data (metrics, analysis, etc.)
        
        Returns:
            Response with actions taken
        """
        logger.info(f"🔍 Handling pattern: {pattern}")
        
        result = {
            "pattern": pattern,
            "timestamp": datetime.now().isoformat(),
            "learning_recorded": False,
            "agent_called": None,
            "recommendations": [],
            "actions_taken": []
        }
        
        # Step 1: Record as learning
        if self._record_pattern_as_learning(pattern, context):
            result["learning_recorded"] = True
            logger.info(f"✓ Pattern recorded as learning")
        
        # Step 2: Determine which agent should analyze
        agent = self._determine_agent(pattern)
        if agent:
            result["agent_called"] = agent
            logger.info(f"📞 Should call agent: {agent}")
            
            # In a real system, would call the agent here
            # For now, just log it
        
        # Step 3: Generate recommendations based on pattern type
        recommendations = self._generate_recommendations(pattern, context)
        result["recommendations"] = recommendations
        
        for rec in recommendations:
            logger.info(f"💡 Recommendation: {rec}")
        
        # Step 4: Record event to chronicle
        self._record_to_chronicle(pattern, context, recommendations)
        
        return result
    
    def _record_pattern_as_learning(
        self, 
        pattern: str, 
        context: Dict[str, Any]
    ) -> bool:
        """Record pattern as a heuristic in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Determine confidence based on pattern type
            confidence = self._estimate_confidence(pattern)
            
            # Record as heuristic (more appropriate for patterns)
            cursor.execute("""
                INSERT INTO heuristics 
                (domain, rule, explanation, source_type, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "system-patterns",        # domain
                pattern,                  # rule
                "Pattern detected by Sentinel monitoring",  # explanation
                "observation",            # source_type (must be one of: failure, success, observation, NULL)
                confidence                # confidence
            ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to record pattern as heuristic: {e}")
            return False
    
    def _determine_agent(self, pattern: str) -> Optional[str]:
        """Determine which agent should analyze this pattern."""
        pattern_lower = pattern.lower()
        
        # Map patterns to agents
        mappings = {
            "declining": "researcher",      # Investigate why activity is declining
            "instability": "architect",     # Design solution for stability
            "anomaly": "skeptic",           # Question & validate anomaly
            "cycle": "researcher",          # Research cyclical patterns
            "error": "skeptic",             # Critical analysis of error
            "surge": "architect",           # Plan for scaling
            "trend": "researcher",          # Research trend implications
            "unusual": "creative",          # Generate creative solutions
        }
        
        for keyword, agent in mappings.items():
            if keyword in pattern_lower:
                return agent
        
        return None
    
    def _estimate_confidence(self, pattern: str) -> float:
        """Estimate confidence level for this pattern."""
        # Declining/cyclical patterns are usually high confidence
        # Anomalies/surges are medium confidence
        # Unusual patterns are lower confidence
        
        pattern_lower = pattern.lower()
        
        if "declining" in pattern_lower or "cycle" in pattern_lower:
            return 0.8
        elif "instability" in pattern_lower:
            return 0.7
        elif "anomaly" in pattern_lower:
            return 0.6
        else:
            return 0.5
    
    def _generate_recommendations(
        self, 
        pattern: str, 
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on pattern."""
        recommendations = []
        pattern_lower = pattern.lower()
        
        if "declining" in pattern_lower:
            recommendations.extend([
                "Investigate root cause of activity decline",
                "Check if users are disengaged",
                "Review recent system changes",
                "Consider running user survey or analysis"
            ])
        
        elif "instability" in pattern_lower:
            recommendations.extend([
                "Implement stability improvements",
                "Add monitoring and alerting",
                "Consider redundancy/failover",
                "Review infrastructure capacity"
            ])
        
        elif "cycle" in pattern_lower:
            recommendations.extend([
                "Confirm cyclical pattern continues",
                "Plan resources around cycle",
                "Optimize for peak times",
                "Automate cycle-based actions"
            ])
        
        else:
            recommendations.extend([
                "Monitor for pattern continuation",
                "Investigate underlying causes",
                "Plan mitigation if needed"
            ])
        
        return recommendations
    
    def _record_to_chronicle(
        self,
        pattern: str,
        context: Dict[str, Any],
        recommendations: List[str]
    ) -> bool:
        """Record pattern analysis to event chronicle."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            summary = f"Pattern detected: {pattern}"
            # Safely convert context to string
            context_str = "; ".join([f"{k}={v}" for k, v in list(context.items())[:5]])
            data = json.dumps({
                "pattern": pattern,
                "recommendations": recommendations,
                "context": context_str
            })
            
            cursor.execute("""
                INSERT INTO event_chronicle 
                (timestamp, event_type, source, status, summary, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "pattern_detected",
                "sentinel",
                "analyzed",
                summary,
                data
            ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to record to chronicle: {e}")
            return False


def main():
    """Test the pattern response handler."""
    handler = PatternResponseHandler()
    
    # Test patterns
    test_patterns = [
        "Declining activity trend detected",
        "Service instability detected",
        "Cyclical pattern detected: Activity cycle of 10 intervals detected",
    ]
    
    for pattern in test_patterns:
        print(f"\n{'='*70}")
        result = handler.handle_pattern(
            pattern,
            {"metrics": {"activity_score": 1}, "timestamp": datetime.now()}
        )
        
        print(f"Pattern: {pattern}")
        print(f"Learning recorded: {result['learning_recorded']}")
        print(f"Agent to call: {result['agent_called']}")
        print(f"Recommendations:")
        for rec in result['recommendations']:
            print(f"  - {rec}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
