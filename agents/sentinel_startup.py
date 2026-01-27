#!/usr/bin/env python3
"""
Sentinel Startup Script - Phase 2 Implementation

Starts the Dashboard Sentinel agent in continuous monitoring mode.
The Sentinel records all monitoring cycles to the event_chronicle for
dashboard visibility and learning loop integration.

Usage:
    python3 sentinel_startup.py [--interval 30] [--log-level INFO]

Standard ELF Integration:
- Records 'sentinel_cycle' events to event_chronicle table
- Tracks metrics, analysis, and adaptive patterns
- Automatic learning from monitoring history
- Integration with learning loop via event_chronicle
"""

import sys
import logging
import argparse
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard_sentinel import AISentinel


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                Path.home() / ".opencode" / "emergent-learning" / "logs" / "sentinel-startup.log"
            ),
            logging.StreamHandler(),
        ]
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start Dashboard Sentinel in continuous monitoring mode"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Monitoring interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("🚀 PHASE 2: Starting Dashboard Sentinel - Continuous Monitoring Mode")
    logger.info("=" * 70)
    logger.info(f"Interval: {args.interval}s")
    logger.info(f"Log level: {args.log_level}")
    logger.info("Standard ELF Integration: Enabled")
    logger.info("Event Chronicle Recording: Enabled")
    logger.info("=" * 70)
    
    try:
        # Create Sentinel instance
        sentinel = AISentinel(
            name="Dashboard Sentinel - ELF Standard",
            model="haiku"
        )
        
        logger.info("✓ Sentinel initialized")
        logger.info("✓ Starting continuous monitoring loop...")
        logger.info("")
        
        # Start continuous monitoring
        sentinel.start_continuous_monitoring(interval=args.interval)
        
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 70)
        logger.info("⏹️  Sentinel stopped by user")
        logger.info("=" * 70)
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error("=" * 70)
        raise


if __name__ == "__main__":
    main()
