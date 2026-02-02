#!/usr/bin/env python3
"""
Log rotation utility for ELF system
Prevents log files from growing too large by rotating and compressing old logs
"""

import gzip
import os
import shutil
from pathlib import Path
from datetime import datetime


class LogRotator:
    """Handles log file rotation with compression and retention policies"""

    def __init__(self, log_dir: str, max_size_mb: int = 10, max_files: int = 5):
        self.log_dir = Path(log_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        self.max_files = max_files
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def should_rotate(self, log_file: Path) -> bool:
        """Check if a log file should be rotated based on size"""
        if not log_file.exists():
            return False
        return log_file.stat().st_size > self.max_size_bytes

    def rotate_log(self, log_file: Path) -> None:
        """Rotate a single log file with compression and cleanup"""
        if not self.should_rotate(log_file):
            return

        print(
            f"[LogRotator] Rotating {log_file.name} (size: {log_file.stat().st_size / 1024 / 1024:.1f}MB)"
        )

        # Find the next rotation number
        rotation_num = 1
        while (log_file.parent / f"{log_file.stem}.{rotation_num}.gz").exists():
            rotation_num += 1

        # Compress current log to rotation file
        rotated_file = log_file.parent / f"{log_file.stem}.{rotation_num}.gz"

        with open(log_file, "rb") as f_in:
            with gzip.open(rotated_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Clear the original log file
        log_file.write_text("")

        # Cleanup old rotation files beyond max_files
        self.cleanup_old_rotations(log_file.stem)

        print(
            f"[LogRotator] Rotated to {rotated_file.name} ({rotated_file.stat().st_size / 1024 / 1024:.1f}MB compressed)"
        )

    def cleanup_old_rotations(self, log_name: str) -> None:
        """Remove old rotation files beyond the retention limit"""
        rotation_files = []
        for i in range(1, 100):  # Look for up to 99 rotations
            rotated_file = self.log_dir / f"{log_name}.{i}.gz"
            if rotated_file.exists():
                rotation_files.append(rotated_file)

        # Sort by modification time (newest first)
        rotation_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Remove files beyond the retention limit
        for old_file in rotation_files[self.max_files :]:
            old_file.unlink()
            print(f"[LogRotator] Deleted old rotation: {old_file.name}")

    def rotate_all_logs(self) -> None:
        """Rotate all log files in the directory"""
        for log_file in self.log_dir.glob("*.log"):
            self.rotate_log(log_file)

    def get_log_status(self) -> dict:
        """Get status of all log files"""
        status = {"total_size_mb": 0, "files": [], "rotations": []}

        for log_file in self.log_dir.glob("*.log"):
            size_mb = log_file.stat().st_size / 1024 / 1024
            status["total_size_mb"] += size_mb
            status["files"].append(
                {
                    "name": log_file.name,
                    "size_mb": round(size_mb, 2),
                    "needs_rotation": self.should_rotate(log_file),
                }
            )

        for rotated_file in self.log_dir.glob("*.gz"):
            size_mb = rotated_file.stat().st_size / 1024 / 1024
            status["rotations"].append(
                {"name": rotated_file.name, "size_mb": round(size_mb, 2)}
            )

        return status


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python log_rotation.py <action> [log_dir]")
        print("Actions: rotate, status")
        return

    action = sys.argv[1]
    log_dir = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "/home/bamer/.opencode/emergent-learning/Open_ELF/logs"
    )

    rotator = LogRotator(log_dir, max_size_mb=10, max_files=5)

    if action == "rotate":
        print(f"[LogRotator] Rotating logs in {log_dir}")
        rotator.rotate_all_logs()
        print("[LogRotator] Rotation complete")

    elif action == "status":
        status = rotator.get_log_status()
        print(f"[LogRotator] Log Status for {log_dir}:")
        print(f"  Total size: {status['total_size_mb']:.1f}MB")
        print(f"  Active log files: {len(status['files'])}")
        print(f"  Rotation files: {len(status['rotations'])}")

        for file_info in status["files"]:
            rotation_indicator = " ⚠️" if file_info["needs_rotation"] else ""
            print(
                f"    {file_info['name']}: {file_info['size_mb']:.1f}MB{rotation_indicator}"
            )


if __name__ == "__main__":
    main()
