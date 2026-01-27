#!/usr/bin/env python3
"""
Run Watcher with big-pickle (OpenCode local model)

Two-tier system using big-pickle for both:
1. Tier 1 (Watcher): Detects issues
2. Tier 2 (Handler/CEO): Makes decisions if issues detected

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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import watcher prompt generation
from watcher_loop import gather_state, output_watcher_prompt, output_handler_prompt

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
    """Send prompt to big-pickle and get response via opencode CLI."""
    try:
        # Use correct opencode syntax: opencode --model opencode/big-pickle --prompt "..."
        result = subprocess.run(
            ["opencode", "--model", "opencode/big-pickle", "--prompt", prompt],
            capture_output=True,
            timeout=120,
            text=True,
        )
        
        if result.returncode == 0:
            return result.stdout, True
        else:
            return f"Error: big-pickle returned error code {result.returncode}\n{result.stderr}", False
            
    except subprocess.TimeoutExpired:
        return "Error: big-pickle timed out (>120s). System busy or model response too slow.", False
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


def extract_status_from_response(response: str) -> str:
    """Extract status from watcher response."""
    if 'STATUS: error' in response or 'STATUS: stale' in response:
        return 'warning'
    elif 'error' in response.lower():
        return 'critical'
    return 'nominal'


def needs_escalation(response: str) -> bool:
    """Check if watcher detected issues that need handler escalation."""
    # Look for status that requires intervention
    return any(x in response for x in ['STATUS: error', 'STATUS: stale', 'STATUS: complete', 'intervention_needed'])


def run_handler_pass(escalation_reason: str) -> Tuple[str, bool]:
    """Run handler/CEO tier to make decisions."""
    print(f"[{datetime.now().isoformat()}] Escalating to handler (big-pickle CEO)...", file=sys.stderr)
    
    try:
        import io
        from contextlib import redirect_stdout
        
        # Generate handler prompt
        f = io.StringIO()
        with redirect_stdout(f):
            output_handler_prompt(escalation_reason)
        prompt = f.getvalue()
    except Exception as e:
        print(f"Error generating handler prompt: {e}", file=sys.stderr)
        return f"Error: {e}", False
    
    # Send to big-pickle for decision making
    response, success = call_bigpickle(prompt)
    return response, success


def run_single_pass() -> int:
    """Run one watcher monitoring pass with escalation tier"""
    print(f"[{datetime.now().isoformat()}] === Starting big-pickle watcher (Tier 1) ===", file=sys.stderr)
    
    # TIER 1: Watcher - Generate and analyze
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
        record_to_chronicle(
            event_type='watcher_error',
            status='critical',
            summary=f'Prompt generation failed: {e}'
        )
        return 2
    
    # Send to big-pickle (Tier 1 analysis)
    watcher_response, success = call_bigpickle(prompt)
    
    if not success:
        print(f"Error from big-pickle: {watcher_response}", file=sys.stderr)
        record_to_chronicle(
            event_type='watcher_error',
            status='critical',
            summary=f'Big-pickle Tier 1 failed: {watcher_response[:100]}'
        )
        return 2
    
    # Parse Tier 1 response
    watcher_status = extract_status_from_response(watcher_response)
    print(watcher_response)
    
    # Log Tier 1 results
    summary = watcher_response.split('\n')[0][:100] if watcher_response else 'Analysis completed'
    log_to_file(f"[TIER 1] Watcher analysis: {watcher_status}")
    
    record_to_chronicle(
        event_type='watcher_cycle',
        status=watcher_status,
        summary=f'Watcher (Tier 1): {summary}',
        data={'tier': 1, 'response_lines': len(watcher_response.split('\n'))}
    )
    
    # TIER 2: Check if escalation needed (handler/CEO decision)
    exit_code = 0
    if needs_escalation(watcher_response):
        print(f"\n[{datetime.now().isoformat()}] === Escalating to big-pickle Handler (Tier 2 - CEO) ===", file=sys.stderr)
        
        # Call handler with escalation details
        handler_response, success = run_handler_pass(watcher_response)
        
        if not success:
            print(f"Error from handler: {handler_response}", file=sys.stderr)
            record_to_chronicle(
                event_type='handler_error',
                status='critical',
                summary=f'Big-pickle Tier 2 failed: {handler_response[:100]}'
            )
            return 2
        
        # Print handler response
        print(f"\n{handler_response}")
        
        # Parse handler response
        handler_status = extract_status_from_response(handler_response)
        handler_summary = handler_response.split('\n')[0][:100] if handler_response else 'Decision made'
        
        # Log Tier 2 results
        log_to_file(f"[TIER 2] Handler decision: {handler_status}")
        
        record_to_chronicle(
            event_type='handler_decision',
            status=handler_status,
            summary=f'Handler (Tier 2): {handler_summary}',
            data={'tier': 2, 'escalation_reason': watcher_status, 'response_lines': len(handler_response.split('\n'))}
        )
        
        # Set exit code based on what handler did
        if 'ESCALATE' in handler_response:
            exit_code = 1  # Signal that human decision needed
        else:
            exit_code = 0  # Handler resolved it
    else:
        print(f"[{datetime.now().isoformat()}] No escalation needed (system nominal)", file=sys.stderr)
    
    print(f"[{datetime.now().isoformat()}] === Pass complete (exit code: {exit_code}) ===", file=sys.stderr)
    return exit_code


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
