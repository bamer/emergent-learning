#!/usr/bin/env python3
"""
auto_spawn.py - Autonomous watcher spawning mechanism

Runs in background as a persistent process. Checks at intervals whether
a watcher should be active and spawns one if needed.

Integrates with ELF_superpowers.js hook system to auto-spawn watchers
when OpenCode detects user activity.
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import json

def get_elf_home() -> Path:
    """Resolve ELF home."""
    try:
        from elf_paths import get_base_path
        return get_base_path()
    except:
        return Path.home() / ".opencode" / "emergent-learning"

def should_spawn_watcher() -> bool:
    """
    Determine if a new watcher should be spawned.
    
    Conditions:
    - No watcher running currently
    - More than 30 seconds since last watcher finished
    - User has active OpenCode session
    """
    elf_home = get_elf_home()
    pid_file = elf_home / ".watcher.pid"
    
    # Check if watcher is already running
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            # Check if process exists
            subprocess.run(['kill', '-0', str(pid)], check=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Process exists, don't spawn
            return False
        except (ValueError, subprocess.CalledProcessError):
            # PID file invalid or process doesn't exist
            pid_file.unlink(missing_ok=True)
    
    # Check last watcher finish time
    watcher_log = elf_home / "logs" / "watcher.log"
    if watcher_log.exists():
        try:
            stat = watcher_log.stat()
            last_run = datetime.fromtimestamp(stat.st_mtime)
            if datetime.now() - last_run < timedelta(seconds=30):
                # Too soon since last run
                return False
        except:
            pass
    
    return True

def spawn_watcher() -> bool:
    """
    Spawn a new watcher process in the background.
    
    Returns: True if spawned successfully
    """
    elf_home = get_elf_home()
    watcher_script = elf_home / "watcher" / "run_with_bigpickle.py"
    
    if not watcher_script.exists():
        print(f"Watcher script not found: {watcher_script}", file=sys.stderr)
        return False
    
    try:
        # Spawn watcher in background
        process = subprocess.Popen(
            [sys.executable, str(watcher_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(elf_home)
        )
        
        # Store PID
        pid_file = elf_home / ".watcher.pid"
        pid_file.write_text(str(process.pid))
        
        print(f"✓ Spawned watcher (PID {process.pid})")
        return True
        
    except Exception as e:
        print(f"✗ Failed to spawn watcher: {e}", file=sys.stderr)
        return False

def log_spawn_event(success: bool):
    """Log spawn attempt to watcher log."""
    elf_home = get_elf_home()
    log_file = elf_home / "logs" / "watcher.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    status = "SUCCESS" if success else "FAILED"
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] AUTO_SPAWN: {status}\n")

def run_once():
    """Single spawn check."""
    if should_spawn_watcher():
        success = spawn_watcher()
        log_spawn_event(success)
        return success
    return False

def run_daemon(interval: int = 60):
    """
    Run as daemon, checking and spawning watchers periodically.
    
    Args:
        interval: Seconds between spawn checks
    """
    print("🔄 Watcher auto-spawn daemon started")
    print(f"   Checking every {interval} seconds")
    print(f"   Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(interval)
            run_once()
    except KeyboardInterrupt:
        print("\n✓ Watcher auto-spawn daemon stopped")
        sys.exit(0)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Autonomous watcher spawning mechanism"
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon (continuous)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (for daemon mode)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Single spawn check and exit'
    )
    
    args = parser.parse_args()
    
    if args.daemon:
        run_daemon(interval=args.interval)
    else:
        # Default: single check
        success = run_once()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
