#!/usr/bin/env python3
"""
Async Log Watcher - Real-time log surveillance with automatic rotation
Monitors file sizes and triggers rotation when thresholds are exceeded
"""

import asyncio
import os
import sys
import time
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import aiofiles
import aiofiles.os

# Configuration
LOG_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")
ROTATION_SCRIPT = "/home/bamer/.opencode/emergent-learning/scripts/auto_log_rotation.py"
WATCH_CONFIG = "/home/bamer/.opencode/emergent-learning/scripts/watch_config.json"
STATUS_FILE = Path("/home/bamer/.opencode/emergent-learning/logs/sentinel_status.json")

# Default thresholds (size in MB)
DEFAULT_THRESHOLDS = {
    "event-bridge.log": {"size_mb": 1, "interval_minutes": 5},  # Very active log
    "sentinel.log": {"size_mb": 2, "interval_minutes": 10},
    "orchestrator.log": {"size_mb": 2, "interval_minutes": 15},
    "backend.log": {"size_mb": 3, "interval_minutes": 20},
    "opencode-server.log": {"size_mb": 3, "interval_minutes": 20},
    "frontend.log": {"size_mb": 2, "interval_minutes": 15},
    "researcher.log": {"size_mb": 2, "interval_minutes": 15},
    "architect.log": {"size_mb": 2, "interval_minutes": 15},
    "creative.log": {"size_mb": 2, "interval_minutes": 15},
    "ceo.log": {"size_mb": 1, "interval_minutes": 10},
}

# Global thresholds
GLOBAL_SIZE_THRESHOLD_MB = 5  # Rotation if ENTIRE directory exceeds this size
GLOBAL_FILE_COUNT_THRESHOLD = 15  # Rotation if more than 15 active files


class AsyncLogWatcher:
    """Async log sentinel with improved I/O performance."""

    def __init__(self):
        self.log_dir = LOG_DIR
        self.config_file = Path(WATCH_CONFIG)
        self.status_file = STATUS_FILE
        self.running = True
        self.load_config()
        self.last_check = {}

    def load_config(self):
        """Load or create threshold configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.thresholds = config.get("thresholds", DEFAULT_THRESHOLDS)
                    self.global_size_mb = config.get(
                        "global_size_mb", GLOBAL_SIZE_THRESHOLD_MB
                    )
                    self.global_file_count = config.get(
                        "global_file_count", GLOBAL_FILE_COUNT_THRESHOLD
                    )
            except Exception as e:
                print(f"[Watch] Error loading config: {e}")
                self.thresholds = DEFAULT_THRESHOLDS.copy()
                self.global_size_mb = GLOBAL_SIZE_THRESHOLD_MB
                self.global_file_count = GLOBAL_FILE_COUNT_THRESHOLD
        else:
            # Create default config
            self.thresholds = DEFAULT_THRESHOLDS.copy()
            self.global_size_mb = GLOBAL_SIZE_THRESHOLD_MB
            self.global_file_count = GLOBAL_FILE_COUNT_THRESHOLD
            asyncio.create_task(self.save_config())

    async def save_config(self):
        """Save configuration asynchronously"""
        try:
            config = {
                "thresholds": self.thresholds,
                "global_size_mb": self.global_size_mb,
                "global_file_count": self.global_file_count,
                "last_updated": datetime.now().isoformat(),
            }
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.config_file, "w") as f:
                await f.write(json.dumps(config, indent=2))
            print(f"[Watch] Configuration saved: {self.config_file}")
        except Exception as e:
            print(f"[Watch] Error saving config: {e}")

    async def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB asynchronously"""
        try:
            stat = await aiofiles.os.stat(file_path)
            return stat.st_size / (1024 * 1024)
        except Exception as e:
            print(f"[Watch] Error getting size for {file_path}: {e}")
            return 0.0

    def should_check_file(self, file_name: str) -> bool:
        """Check if file should be checked according to configured interval"""
        if file_name not in self.last_check:
            return True

        last_check_time = self.last_check[file_name]
        interval_minutes = self.thresholds.get(file_name, {}).get(
            "interval_minutes", 15
        )

        time_since_check = (datetime.now() - last_check_time).total_seconds() / 60
        return time_since_check >= interval_minutes

    async def get_directory_stats(self) -> Dict:
        """Get directory statistics asynchronously"""
        try:
            # Use async operations to list files
            log_files = []
            async for entry in aiofiles.os.scandir(self.log_dir):
                if entry.name.endswith(".log") and entry.is_file():
                    log_files.append(Path(entry.path))

            # Get stats for each file concurrently
            active_files = []
            file_tasks = []
            for f in log_files:
                file_tasks.append(self._get_file_info_async(f))

            file_infos = await asyncio.gather(*file_tasks, return_exceptions=True)

            for file_info in file_infos:
                if isinstance(file_info, dict) and file_info.get("size", 0) > 0:
                    active_files.append(file_info)

            total_size = sum(f["size_mb"] for f in active_files)

            return {
                "total_files": len(log_files),
                "active_files": len(active_files),
                "total_size_mb": total_size,
                "files": active_files,
            }
        except Exception as e:
            print(f"[Watch] Error getting directory stats: {e}")
            return {
                "error": str(e),
                "total_files": 0,
                "active_files": 0,
                "total_size_mb": 0,
            }

    async def _get_file_info_async(self, file_path: Path) -> Dict:
        """Get file information asynchronously"""
        try:
            stat = await aiofiles.os.stat(file_path)
            size_mb = stat.st_size / (1024 * 1024)

            return {
                "name": file_path.name,
                "path": str(file_path),
                "size_mb": size_mb,
                "size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        except Exception as e:
            print(f"[Watch] Error getting info for {file_path}: {e}")
            return {"name": file_path.name, "error": str(e)}

    def check_global_thresholds(self, stats: Dict) -> List[str]:
        """Check global thresholds and return rotation reasons"""
        reasons = []

        if stats.get("total_size_mb", 0) > self.global_size_mb:
            reasons.append(
                f"Global size: {stats['total_size_mb']:.2f}MB > {self.global_size_mb}MB"
            )

        if stats.get("active_files", 0) > self.global_file_count:
            reasons.append(
                f"File count: {stats['active_files']} > {self.global_file_count}"
            )

        return reasons

    async def check_file_thresholds(self, file_path: Path) -> List[str]:
        """Check specific file thresholds asynchronously"""
        file_name = file_path.name
        size_mb = await self.get_file_size_mb(file_path)

        reasons = []

        if file_name in self.thresholds:
            threshold = self.thresholds[file_name]
            size_limit = threshold.get("size_mb", 2)

            if size_mb > size_limit:
                reasons.append(f"File {file_name}: {size_mb:.2f}MB > {size_limit}MB")

        return reasons

    async def trigger_rotation(self, reason: str) -> bool:
        """Trigger log rotation asynchronously"""
        try:
            print(f"[Watch] 🚨 TRIGGER ROTATION: {reason}")

            # Run rotation in subprocess (still sync, but non-blocking)
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                ROTATION_SCRIPT,
                "run",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)

            if process.returncode == 0:
                print(f"[Watch] ✅ Rotation successful")
                await self.log_event("rotation_success", reason, stdout.decode())
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                print(f"[Watch] ❌ Rotation failed: {error_msg}")
                await self.log_event("rotation_failed", reason, error_msg)
                return False

        except asyncio.TimeoutError:
            print(f"[Watch] ⏰ Rotation timeout after 30 seconds")
            await self.log_event("rotation_timeout", reason, "Process timeout")
            return False
        except Exception as e:
            print(f"[Watch] ❌ Rotation error: {e}")
            await self.log_event("rotation_error", reason, str(e))
            return False

    async def log_event(self, event_type: str, reason: str, details: str):
        """Log events asynchronously"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "reason": reason,
                "details": details,
            }

            self.status_file.parent.mkdir(parents=True, exist_ok=True)

            # Read existing events
            events = []
            if self.status_file.exists():
                async with aiofiles.open(self.status_file, "r") as f:
                    content = await f.read()
                    if content.strip():
                        events = json.loads(content).get("events", [])

            # Add new event (keep only last 100)
            events.append(event)
            events = events[-100:]

            # Write back
            status_data = {
                "last_updated": datetime.now().isoformat(),
                "events": events,
            }

            async with aiofiles.open(self.status_file, "w") as f:
                await f.write(json.dumps(status_data, indent=2))

        except Exception as e:
            print(f"[Watch] Error logging event: {e}")

    async def check_and_rotate(self):
        """Main check and rotation logic"""
        try:
            # Get directory stats asynchronously
            stats = await self.get_directory_stats()

            # Check global thresholds
            global_reasons = self.check_global_thresholds(stats)
            if global_reasons:
                for reason in global_reasons:
                    await self.trigger_rotation(reason)
                return

            # Check individual files concurrently
            file_tasks = []
            for file_info in stats.get("files", []):
                file_path = Path(file_info["path"])
                file_name = file_path.name

                if self.should_check_file(file_name):
                    file_tasks.append(self._check_single_file(file_path))

            if file_tasks:
                results = await asyncio.gather(*file_tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, list) and result:  # List of reasons
                        for reason in result:
                            await self.trigger_rotation(reason)

        except Exception as e:
            print(f"[Watch] Error in check_and_rotate: {e}")

    async def _check_single_file(self, file_path: Path) -> List[str]:
        """Check a single file for threshold violations"""
        self.last_check[file_path.name] = datetime.now()
        return await self.check_file_thresholds(file_path)

    async def run(self):
        """Main async run loop"""
        print(f"[Watch] 🚀 Starting async log sentinel...")
        print(f"[Watch] 📁 Monitoring: {self.log_dir}")
        print(
            f"[Watch] ⚙️ Global thresholds: {self.global_size_mb}MB, {self.global_file_count} files"
        )

        while self.running:
            try:
                await self.check_and_rotate()
                # Check every minute
                await asyncio.sleep(60)
            except Exception as e:
                print(f"[Watch] Error in main loop: {e}")
                await asyncio.sleep(10)  # Brief pause before retrying

        print(f"[Watch] 👋 Shutting down...")

    def stop(self):
        """Stop the sentinel"""
        self.running = False


async def main():
    """Main entry point"""
    sentinel = AsyncLogWatcher()

    def signal_handler(signum, frame):
        print(f"\n[Watch] Received signal {signum}")
        sentinel.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await sentinel.run()


if __name__ == "__main__":
    asyncio.run(main())
