#!/usr/bin/env python3
"""
Run Watcher with big-pickle (OpenCode local model)

Simple runner that:
1. Generates watcher prompt from watcher_loop.py
2. Sends to big-pickle via CLI
3. Records result to event_chronicle
4. Logs to .coordination/watcher-log.md

No modifications to existing watcher code - just swap the model.

Usage:
    python run_with_bigpickle.py                # Single pass
    python run_with_bigpickle.py --loop 30      # Continuous (30s interval)
    python run_with_bigpickle.py --help         # Help
"""

import subprocess
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Tuple

# Import watcher prompt generation
from watcher_loop import gather_state, output_watcher_prompt

try:
    from elf_paths import get_base_path
except ImportError:
    def get_base_path():
        return Path.home() / ".claude" / "emergent-learning"


COORD_DIR = get_base_path() / ".coordination"
DB_PATH = get_base_path() / "memory" / "index.db"
WATCHER_LOG = COORD_DIR / "watcher-log.md"
STOP_FILE = COORD_DIR / "watcher-stop"


def call_bigpickle(prompt: str) -> Tuple[str, bool]:
    """Send prompt to big-pickle and get response."""
    try:
        result = subprocess.run(
            ["claude", "--print", "--model", "opencode/big-pickle"],
            input=prompt.encode(),
            capture_output=True,
            timeout=120,
        )
        return result.stdout.decode(), result.returncode == 0
    except Exception as e:
        return f"Error calling big-pickle: {e}", False


def log_to_file(message: str):
    """Log to watcher-log.md"""
    try:
        timestamp = datetime.now().isoformat()
        with open(WATCHER_LOG, "a") as f:
            f.write(f"{timestamp} | {message}\n")
    except Exception:
        pass


def record_to_chronicle(event_type: str, status: str, summary: str, data=None):
    """Record event to event_chronicle"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO event_chronicle (timestamp, event_type, source, source_id, status, summary, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            event_type,
            'watcher',
            'bigpickle-watcher',
            status,
            summary,
            json.dumps(data) if data else None,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to record to chronicle: {e}", file=sys.stderr)


def run_single_pass() -> int:
    """Run one watcher monitoring pass"""
    print(f"[{datetime.now().isoformat()}] Starting watcher pass with big-pickle...", file=sys.stderr)
    
    # Generate prompt using existing watcher code
    try:
        import io
        from contextlib import redirect_stdout
        
        # Capture the prompt output
        f = io.StringIO()
        with redirect_stdout(f):
            output_watcher_prompt()
        prompt = f.getvalue()
    except Exception as e:
        print(f"Error generating prompt: {e}", file=sys.stderr)
        return 2
    
    # Send to big-pickle
    response, success = call_bigpickle(prompt)
    
    if not success:
        print(f"Error from big-pickle: {response}", file=sys.stderr)
        record_to_chronicle(
            event_type='watcher_error',
            status='critical',
            summary=f'Big-pickle failed: {response[:100]}'
        )
        return 2
    
    # Print response
    print(response)
    
    # Parse status from response
    status = 'nominal'
    if 'STATUS: error' in response or 'STATUS: stale' in response:
        status = 'warning'
    elif 'error' in response.lower():
        status = 'critical'
    
    # Log results
    summary = response.split('\n')[0][:100] if response else 'Pass completed'
    log_to_file(f"Pass completed: {summary}")
    
    # Record to chronicle
    record_to_chronicle(
        event_type='watcher_cycle',
        status=status,
        summary=f'Watcher pass: {summary}',
        data={'response_lines': len(response.split('\n'))}
    )
    
    print(f"[{datetime.now().isoformat()}] Pass complete (status: {status})", file=sys.stderr)
    
    return 0


def run_continuous(interval: int = 30):
    """Run monitoring in continuous loop"""
    print(f"[{datetime.now().isoformat()}] Starting continuous watcher (interval: {interval}s)", file=sys.stderr)
    log_to_file(f"Watcher started in continuous mode (interval: {interval}s)")
    
    try:
        import time
        pass_count = 0
        
        while True:
            if STOP_FILE.exists():
                print(f"[{datetime.now().isoformat()}] Stop signal detected", file=sys.stderr)
                log_to_file("Stop signal detected - exiting")
                break
            
            pass_count += 1
            print(f"\n[{datetime.now().isoformat()}] === Pass #{pass_count} ===", file=sys.stderr)
            
            exit_code = run_single_pass()
            
            if exit_code != 0:
                print(f"Warning: Pass {pass_count} exited with code {exit_code}", file=sys.stderr)
            
            print(f"[{datetime.now().isoformat()}] Sleeping {interval}s...", file=sys.stderr)
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().isoformat()}] Stopped by user (Ctrl+C)", file=sys.stderr)
        log_to_file("Stopped by user")
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        log_to_file(f"ERROR: {e}")
        return 1
    
    return 0


def main():
    """CLI entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print(__doc__)
            return 0
        elif sys.argv[1] == '--loop':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            return run_continuous(interval)
    
    # Default: single pass
    return run_single_pass()


if __name__ == '__main__':
    sys.exit(main())
