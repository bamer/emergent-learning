#!/usr/bin/env python3
"""
Enhanced Sentinel with Pattern Learning

Wraps the existing Sentinel to add pattern detection → learning → action flow.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pattern_response_handler import PatternResponseHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SentinelLearning")


class SentinelWithLearning:
    """Sentinel enhanced with pattern-to-learning pipeline."""
    
    def __init__(self):
        self.elf_home = Path.home() / ".opencode" / "emergent-learning"
        self.response_handler = PatternResponseHandler(self.elf_home)
    
    def process_patterns(self, patterns: List[str], context: Dict[str, Any]):
        """
        Process detected patterns through the learning pipeline.
        
        Args:
            patterns: List of detected patterns
            context: Context data (metrics, etc.)
        """
        if not patterns:
            logger.debug("No patterns detected")
            return
        
        logger.info(f"🔍 Processing {len(patterns)} detected patterns")
        
        for pattern in patterns:
            logger.info(f"\n{'='*70}")
            logger.info(f"📍 Pattern: {pattern}")
            
            # Handle pattern through response system
            result = self.response_handler.handle_pattern(pattern, context)
            
            # Log results
            if result['learning_recorded']:
                logger.info(f"✅ Pattern recorded as heuristic")
            
            if result['agent_called']:
                logger.info(f"🤖 Recommended agent: {result['agent_called']}")
                logger.info(f"   (Should be called to analyze further)")
            
            if result['recommendations']:
                logger.info(f"💡 Recommendations:")
                for rec in result['recommendations']:
                    logger.info(f"   - {rec}")
            
            logger.info(f"✓ Pattern response recorded in event_chronicle")


def integrate_with_sentinel():
    """Integration example for real Sentinel."""
    logger.info("""
    🔗 Integration Steps for Real Sentinel:
    
    1. In dashboard_sentinel.py or dashboard_sentinel_ceo.py:
       
       from sentinel_with_learning import SentinelWithLearning
       learning_handler = SentinelWithLearning()
       
    2. After detecting patterns:
       
       patterns = analysis.get("patterns", [])
       learning_handler.process_patterns(patterns, metrics)
    
    3. This will:
       - Record patterns as heuristics in database
       - Recommend which agent to call
       - Generate actionable recommendations
       - Log to event_chronicle for visibility
    """)


if __name__ == "__main__":
    # Test
    handler = SentinelWithLearning()
    
    test_patterns = [
        "Declining activity trend detected",
        "Service instability detected",
        "Cyclical pattern detected: Activity cycle of 10 intervals detected",
    ]
    
    test_context = {
        "timestamp": "2026-01-30T12:45:00",
        "activity_score": 1,
        "service_health": 0.95,
        "metrics": {"latency_ms": 45, "error_rate": 0.02}
    }
    
    print("\n" + "="*70)
    print("🚀 Sentinel with Learning - Test Run")
    print("="*70)
    
    handler.process_patterns(test_patterns, test_context)
    
    print("\n" + "="*70)
    integrate_with_sentinel()
    print("="*70)
