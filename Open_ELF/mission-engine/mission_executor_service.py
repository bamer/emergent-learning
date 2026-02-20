#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO 
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Mission Executor Service - Background daemon that executes missions

This service continuously monitors .coordination/missions/running/ and executes
missions via the Mission Engine. It ensures missions don't get stuck in "running" state.

Usage:
    python mission_executor_service.py

    To run as systemd service:
    sudo cp mission_executor.service /etc/systemd/system/
    sudo systemctl enable --now mission_executor
"""

import sys
import time
import signal
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

try:
    from Open_ELF.mission_engine.mission_engine import MissionEngine, get_mission_engine
    from Open_ELF.mission_engine.models import MissionStatus
    from Open_ELF.dashboard_app.backend.mission_store import MissionStore
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_error, log_warning

    logger = get_logger("mission_executor")
except ImportError as e:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("mission_executor")
    logger.warning(f"Could not import centralized logging: {e}")

# Paths
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
RUNNING_DIR = ELF_DIR / ".coordination" / "missions" / "running"
COMPLETED_DIR = ELF_DIR / ".coordination" / "missions" / "completed"
FAILED_DIR = ELF_DIR / ".coordination" / "missions" / "failed"
LOG_DIR = ELF_DIR / "Open_ELF" / "mission-engine" / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)


class MissionExecutorService:
    """
    Background service that executes missions.

    Monitors the running missions directory and executes them via
    MissionEngine and AgentManager.
    """

    def __init__(self, check_interval: int = 30, timeout_hours: int = 24):
        """
        Initialize the mission executor service.

        Args:
            check_interval: Seconds between checks (default: 30)
            timeout_hours: Max time for a mission to complete (default: 24)
        """
        self.check_interval = check_interval
        self.timeout_hours = timeout_hours
        self.running = False
        self.stop_event: Optional[Any] = None

        # Initialize mission engine
        self.engine = get_mission_engine()
        self.store = MissionStore()

        # Stats
        self.stats = {
            "started": 0,
            "completed": 0,
            "failed": 0,
            "timed_out": 0,
            "errors": 0,
        }

        logger.info("🚀 Mission Executor Service initialized")
        logger.info(f"   Check interval: {check_interval}s")
        logger.info(f"   Mission timeout: {timeout_hours}h")

    def run_mission_from_file(self, mission_file: Path) -> bool:
        """
        Execute a mission from its markdown file.

        Args:
            mission_file: Path to mission markdown file

        Returns:
            True if mission was executed successfully
        """
        try:
            # Parse mission file
            mission = self.store.get_mission(mission_file.stem)
            if not mission:
                logger.error(f"❌ Could not parse mission: {mission_file.name}")
                return False

            # Check if already has session (already started)
            if mission.status == "running" and mission.session_id:
                logger.info(
                    f"🔄 Mission {mission.id} already has session {mission.session_id}"
                )
                return True

            # Check if mission is too old (timeout)
            created_at = datetime.fromisoformat(mission.created_at)
            age = datetime.now() - created_at
            if age > timedelta(hours=self.timeout_hours):
                logger.warning(f"⏰ Mission {mission.id} timed out (age: {age})")
                self.store.fail_mission(
                    mission.id,
                    f"Timeout - mission did not complete in {self.timeout_hours}h",
                )
                self.stats["timed_out"] += 1
                return False

            # Execute mission via MissionEngine
            logger.info(f"🎯 Executing mission: {mission.id}")
            logger.info(f"   Agent: {mission.agent_type}")
            logger.info(f"   Mission: {mission.mission_text[:100]}...")

            result = self.engine.execute_mission(mission.id)

            if result.success:
                logger.info(f"✅ Mission {mission.id} completed")
                self.store.complete_mission(
                    mission.id,
                    result.output or "Completed successfully",
                    result.actions or [],
                )
                self.stats["completed"] += 1
            else:
                logger.error(f"❌ Mission {mission.id} failed: {result.output}")
                self.store.fail_mission(mission.id, result.output or "Execution failed")
                self.stats["failed"] += 1

            return result.success

        except Exception as e:
            logger.error(f"❌ Error executing mission {mission_file.name}: {e}")
            import traceback

            traceback.print_exc()
            self.stats["errors"] += 1
            return False

    def check_and_execute_missions(self):
        """
        Check for running missions and execute them.
        """
        if not RUNNING_DIR.exists():
            return

        mission_files = list(RUNNING_DIR.glob("*.md"))
        logger.debug(f"📋 Found {len(mission_files)} running missions")

        for mission_file in mission_files:
            logger.info(f"🔍 Checking mission: {mission_file.name}")
            self.run_mission_from_file(mission_file)

    def cleanup_stale_missions(self):
        """
        Move very old missions from running to failed.
        """
        if not RUNNING_DIR.exists():
            return

        threshold = datetime.now() - timedelta(days=1)
        stale_count = 0

        for mission_file in RUNNING_DIR.glob("*.md"):
            try:
                stat = mission_file.stat()
                if datetime.fromtimestamp(stat.st_mtime) < threshold:
                    logger.warning(f"🧹 Cleaned up stale mission: {mission_file.name}")

                    # Move to failed directory
                    FAILED_DIR.mkdir(parents=True, exist_ok=True)
                    dest = FAILED_DIR / mission_file.name
                    mission_file.rename(dest)
                    stale_count += 1

                    # Mark as failed in file
                    content = dest.read_text()
                    if "## Error" not in content:
                        error_line = "\n## Error\n```\nStale - mission never completed in 24 hours\n```\n"
                        content = content.replace("## Logs", error_line + "\n## Logs")
                        dest.write_text(content)

            except Exception as e:
                logger.error(f"❌ Error cleaning up {mission_file.name}: {e}")

        if stale_count > 0:
            logger.info(f"🗑️  Cleaned up {stale_count} stale missions")

    def report_stats(self):
        """Report current statistics."""
        logger.info("📊 Mission Executor Stats:")
        for key, value in self.stats.items():
            logger.info(f"   {key}: {value}")

        # Count current state
        if RUNNING_DIR.exists():
            running = len(list(RUNNING_DIR.glob("*.md")))
            logger.info(f"   Currently running: {running}")

        if COMPLETED_DIR.exists():
            completed = len(list(COMPLETED_DIR.glob("*.md")))
            logger.info(f"   Total completed: {completed}")

        if FAILED_DIR.exists():
            failed = len(list(FAILED_DIR.glob("*.md")))
            logger.info(f"   Total failed: {failed}")

        logger.info(f"   Engine stats: {self.engine.get_stats()}")

    def run(self):
        """
        Main run loop.

        Continuously monitors for missions to execute.
        """
        logger.info("✅ Mission Executor Service starting...")
        self.running = True

        # Start mission engine background processing
        logger.info("🔄 Starting MissionEngine background processing...")
        self.engine.start_background_processing()

        try:
            while self.running:
                start_time = time.time()

                # Check for missions
                try:
                    self.check_and_execute_missions()

                    # Periodically cleanup stale missions (every 10 iterations)
                    if hasattr(self, "_iterations"):
                        self._iterations += 1
                    else:
                        self._iterations = 1

                    if self._iterations % 10 == 0:
                        self.cleanup_stale_missions()
                        self.report_stats()

                    # Wait for next check
                    elapsed = time.time() - start_time
                    sleep_time = max(0, self.check_interval - elapsed)
                    time.sleep(sleep_time)

                except KeyboardInterrupt:
                    logger.info("🛑 Mission Executor Service interrupted")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in main loop: {e}")
                    import traceback

                    traceback.print_exc()
                    time.sleep(self.check_interval)

        finally:
            self.shutdown()

    def shutdown(self):
        """Shutdown the service."""
        logger.info("🛑 Shutting down Mission Executor Service...")
        self.running = False

        # Stop mission engine
        if self.engine.running:
            self.engine.stop_background_processing()

        logger.info("✅ Mission Executor Service stopped")
        self.report_stats()


def main():
    """Main entry point."""
    print("""
┌────────────────────────────────────────┐
│   Mission Executor Service v1.0        │
│   Background Mission Execution Daemon  │
└────────────────────────────────────────┘
""")

    service = MissionExecutorService(check_interval=30, timeout_hours=24)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"📶 Received signal {signum}")
        service.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        service.run()
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt")
        service.shutdown()
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        service.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
