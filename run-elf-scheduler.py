#!/usr/bin/env python3
"""
ELF System Runner - Starts all ELF components

This script starts the complete ELF monitoring system:
- EventBridge (event routing)
- LearningProcessor (learning and trails)
- Tiered Scheduler (Sentinel/Orchestrator/CEO agents)

Usage:
    python3 run-elf-scheduler.py start    # Start all components
    python3 run-elf-scheduler.py status   # Show status
    python3 run-elf-scheduler.py stop     # Stop all components
"""

import sys
import signal
import subprocess
import time
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent

# Import centralized logging
try:
    from Open_ELF.utils.elf_logging import get_logger

    logger = get_logger("elf_runner")
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("elf_runner")


class ELFRunner:
    """Runner for all ELF system components."""

    def __init__(self):
        self.processes = {}

    def start(self):
        """Start all ELF components."""
        logger.info("=" * 60)
        logger.info("🚀 Starting ELF System")
        logger.info("=" * 60)

        # Start EventBridge
        self._start_process(
            name="event_bridge",
            script=ELF_DIR / "core" / "event_bridge_v2.py",
            args=["start"],
        )

        # Start Tiered Scheduler (Sentinel/Orchestrator/CEO)
        self._start_process(
            name="scheduler",
            script=ELF_DIR / "Open_ELF" / "monitor" / "scheduler.py",
            args=["start"],
        )

        logger.info("=" * 60)
        logger.info("✅ ELF System started")
        logger.info("   EventBridge: Port 9998")
        logger.info("   Scheduler: Sentinel (15min), Orchestrator (30min), CEO (60min)")
        logger.info("=" * 60)

        # Wait for processes
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def _start_process(self, name: str, script: Path, args: list):
        """Start a process in the background."""
        if not script.exists():
            logger.warning(f"⚠️  {name} script not found: {script}")
            return

        logger.info(f"   Starting {name}...")

        proc = subprocess.Popen(
            [sys.executable, str(script)] + args,
            cwd=str(ELF_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.processes[name] = proc
        logger.info(f"   ✅ {name} started (PID: {proc.pid})")

    def status(self):
        """Show status of all components."""
        print("\n" + "=" * 60)
        print("   ELF System Status")
        print("=" * 60)

        for name, proc in self.processes.items():
            status = "🟢 Running" if proc.poll() is None else "🔴 Stopped"
            print(f"   {status} {name}")

        # Check EventBridge HTTP status
        try:
            import requests

            r = requests.get("http://localhost:9998/status", timeout=2)
            print(f"   🟢 EventBridge HTTP: responding")
        except:
            print(f"   🔴 EventBridge HTTP: not responding")

        print("=" * 60)

    def stop(self):
        """Stop all ELF components."""
        logger.info("👋 Stopping ELF System...")

        for name, proc in self.processes.items():
            if proc.poll() is None:
                logger.info(f"   Stopping {name}...")
                proc.terminate()
                proc.wait(timeout=5)
                logger.info(f"   ✅ {name} stopped")

        # Kill any remaining processes
        subprocess.run(["pkill", "-f", "event_bridge_v2"], capture_output=True)
        subprocess.run(["pkill", "-f", "scheduler.py"], capture_output=True)

        logger.info("✅ ELF System stopped")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ELF System Runner")
    parser.add_argument(
        "command",
        choices=["start", "status", "stop"],
        help="start: Run all components, status: Show status, stop: Stop all",
    )

    args = parser.parse_args()

    runner = ELFRunner()

    if args.command == "start":
        runner.start()
    elif args.command == "status":
        runner.status()
    elif args.command == "stop":
        runner.stop()


if __name__ == "__main__":
    main()
