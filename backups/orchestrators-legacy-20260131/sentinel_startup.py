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
import atexit
import os
import fcntl
import time
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

LOCK_FILE = Path.home() / ".opencode" / ".sentinel.lock"
_lock_fd = None


def acquire_lock() -> bool:
    """Acquire exclusive lock to prevent duplicate sentinel processes."""
    global _lock_fd
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        _lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(_lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()
        return True
    except (IOError, OSError):
        if _lock_fd:
            _lock_fd.close()
        return False


def release_lock():
    """Release the lock file."""
    global _lock_fd
    if _lock_fd:
        try:
            fcntl.flock(_lock_fd.fileno(), fcntl.LOCK_UN)
            _lock_fd.close()
            LOCK_FILE.unlink(missing_ok=True)
        except Exception:
            pass


from orchestrator import AgentOrchestrator


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                Path.home()
                / ".opencode"
                / "emergent-learning"
                / "logs"
                / "sentinel-startup.log"
            ),
            logging.StreamHandler(),
        ],
    )


def main():
    """Main entry point - Start ELF Orchestrator with proper agent roles."""
    if not acquire_lock():
        print("❌ Another ELF instance is already running. Exiting.")
        sys.exit(1)
    atexit.register(release_lock)

    parser = argparse.ArgumentParser(
        description="Start ELF Agent Orchestrator - Central Coordination System"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Monitoring interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("🚀 ELF Agent Orchestrator - Starting Central Coordination")
    logger.info("=" * 70)
    logger.info(f"Monitoring interval: {args.interval}s")
    logger.info(f"Log level: {args.log_level}")
    logger.info("✅ Orchestrator: 🎯 Central coordination")
    logger.info("✅ Sentinel: 🔍 Monitoring (not CEO)")
    logger.info("✅ CEO: 👑 Executive decisions (on-demand)")
    logger.info("✅ Other agents: Available on-demand")
    logger.info("=" * 70)

    try:
        # Create Orchestrator instance (replaces Sentinel-only approach)
        orchestrator = AgentOrchestrator()

        logger.info("✓ Orchestrator initialized")
        logger.info("✓ Starting agent coordination system...")
        logger.info("")

        # Start orchestrator (will auto-start Sentinel and other agents)
        orchestrator.start_orchestrator()

        # Keep running with monitoring
        while True:
            time.sleep(args.interval)

            # Show status every 10 cycles
            if hasattr(orchestrator, "_status_counter"):
                orchestrator._status_counter += 1
            else:
                orchestrator._status_counter = 1

            if orchestrator._status_counter % 10 == 0:
                status = orchestrator.get_agent_status()
                active_agents = [
                    a for a in status["agents"].values() if a["status"] == "running"
                ]
                active_count = len(active_agents)
                active_names = [agent["name"] for agent in active_agents]
                logger.info(
                    f"📊 Status: {active_count} agents active ({', '.join(active_names)})"
                )

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 70)
        logger.info("⏹️  ELF Orchestrator stopped by user")
        logger.info("=" * 70)
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error("=" * 70)
        raise


if __name__ == "__main__":
    main()
