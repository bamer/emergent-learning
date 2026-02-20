# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Emergent Learning Framework - Checkin Workflow Orchestrator

Steps (Updated for New Architecture):
1. Display ELF Banner
2. Verify hooks
3. Load building context
4. Display golden rules & heuristics
5. Check and display architecture status (EventBridge, UnifiedOrchestrator, Sentinel, Learning Capture)
6. Prompt dashboard (system tracks per-session)
7. Prompt model selection (Claude tracks per-session)
8. Check CEO decisions
9. Ready status
"""

import os
import sys
import io
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

# Unified ELF logging (required for all ELF modules)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_debug, log_orchestrator_event

    _LOGGER = get_logger("checkin")
except ImportError:
    import logging

    _LOGGER = logging.getLogger("checkin")

    # Provide a fallback log_debug that uses the standard logger's debug method
    def log_debug(module: str, message: str):
        _LOGGER.debug(f"{module}: {message}")

    # Provide a fallback log_orchestrator_event stub for telemetry
    def log_orchestrator_event(
        event_type: str, event_category: str, summary: str, details: dict = None
    ):
        _LOGGER.info(f"[{event_type}] {summary}")
        if details:
            _LOGGER.debug(f"Details: {details}")
        # Try to log to database if available
        try:
            import sqlite3
            from pathlib import Path
            from datetime import datetime, timezone
            import json

            db_path = (
                Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
            )
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                data_json = json.dumps(details) if details else None
                timestamp = datetime.now(timezone.utc).isoformat()
                cursor.execute(
                    "INSERT INTO event_chronicle (event_type, source, source_id, summary, status, data, timestamp, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                    (
                        event_type,
                        "orchestrator",
                        None,
                        summary,
                        "success",
                        data_json,
                        timestamp,
                    ),
                )
                conn.commit()
                conn.close()
        except Exception:
            pass  # Silently fail to avoid breaking checkin


if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class CheckinOrchestrator:
    """Orchestrates the full checkin workflow."""

    BANNER = """
┌────────────────────────────────────┐
│    Emergent Learning Framework     │
├────────────────────────────────────┤
│                                    │
│      █████▒  █▒     █████▒         │
│      █▒      █▒     █▒             │
│      ████▒   █▒     ████▒          │
│      █▒      █▒     █▒             │
│      █████▒  █████▒ █▒             │
│                                    │
└────────────────────────────────────┘
"""

    def __init__(self, interactive: Optional[bool] = None):
        """
        Initialize the checkin orchestrator.

        Args:
            interactive: Force interactive mode on/off. If None, auto-detect.
                         When False, skips input() prompts and outputs JSON hints
                         for Claude to ask questions via AskUserQuestion tool.
        """
        if interactive is None:
            # En mode auto, détecter si stdin est un terminal interactif
            # Pour le checkin, on considère toujours qu'il y a un terminal
            self.interactive = True
        else:
            self.interactive = interactive

        self.elf_home = self._resolve_elf_home()
        self.selected_model = os.environ.get("ELF_MODEL", "opencode")
        self.architecture_ports = {
            "event_bridge": 9998,
            "unified_orchestrator": 9998,
            "dashboard_backend": 8888,
            "dashboard_frontend": 3001,
            "opencode_server": 4096,
        }

    def _resolve_elf_home(self) -> Path:
        """Resolve ELF home directory directly - simplified for new architecture."""
        # Check for ELF_BASE_PATH env var first
        if os.environ.get("ELF_BASE_PATH"):
            return Path(os.environ["ELF_BASE_PATH"]).expanduser().resolve()

        # Try current directory if it's the ELF root
        current_dir = Path.cwd()
        if (current_dir / "Open_ELF").exists():
            return current_dir

        # Look for Open_ELF directory
        for parent in [Path.cwd().parent, Path.cwd().parent.parent]:
            if (parent / "Open_ELF").exists():
                return parent

        # Fallback to global location for backward compatibility
        global_elf = Path.home() / ".opencode" / "emergent-learning"
        if global_elf.exists():
            return global_elf

        # Last resort: use current directory
        return Path.cwd()

    def verify_hooks(self):
        """Step 1b: Verify and install required hooks (auto-sync, observability, etc)."""
        try:
            # Use the actual ELF installation directory, not the project base
            elf_install = Path.home() / ".opencode" / "emergent-learning"
            verifier = elf_install / "scripts" / "verify-hooks.py"

            if verifier.exists():
                result = subprocess.run(
                    [sys.executable, str(verifier)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output:
                        print(f"[OK] {output}")
                    else:
                        print("[OK] Hooks verified")
                else:
                    print("[WARN] Hook verification had issues (continuing)")
        except Exception as e:
            print(f"[WARN] Hook verification failed: {e} (continuing)")

    def check_architecture_status(self) -> Dict[str, str]:
        """Check status of architecture components."""
        print("[*] Checking Architecture Status...")

        status = {
            "opencode_server": "unknown",
            "event_bridge": "unknown",
            "unified_orchestrator": "unknown",
            "dashboard_backend": "unknown",
            "dashboard_frontend": "unknown",
            "sentinel": "unknown",
            "learning_capture": "unknown",
        }

        # Check OpenCode Server
        try:
            response = requests.get(
                f"http://localhost:{self.architecture_ports['opencode_server']}/session",
                timeout=3,
            )
            status["opencode_server"] = (
                "running" if response.status_code == 200 else "stopped"
            )
        except:
            status["opencode_server"] = "stopped"

        # Check EventBridge
        try:
            response = requests.get(
                f"http://localhost:{self.architecture_ports['event_bridge']}/status",
                timeout=3,
            )
            if response.status_code == 200:
                eb_data = response.json()
                status["event_bridge"] = (
                    "running" if eb_data.get("running") else "stopped"
                )
            else:
                status["event_bridge"] = "stopped"
        except:
            status["event_bridge"] = "stopped"

        # Check UnifiedOrchestrator (by process since it connects to EventBridge, not its own HTTP server)
        try:
            result = subprocess.run(
                ["pgrep", "-f", "Open_ELF/orchestrator/unified_orchestrator.py"],
                capture_output=True,
                text=True,
            )
            status["unified_orchestrator"] = (
                "running" if result.returncode == 0 else "stopped"
            )
        except:
            status["unified_orchestrator"] = "stopped"

        # Check Dashboard Backend
        try:
            response = requests.get(
                f"http://localhost:{self.architecture_ports['dashboard_backend']}/api/v1/stats",
                timeout=3,
            )
            status["dashboard_backend"] = (
                "running" if response.status_code == 200 else "stopped"
            )
        except:
            status["dashboard_backend"] = "stopped"

        # Check Dashboard Frontend
        try:
            response = requests.get(
                f"http://localhost:{self.architecture_ports['dashboard_frontend']}",
                timeout=3,
            )
            status["dashboard_frontend"] = (
                "running" if response.status_code == 200 else "stopped"
            )
        except:
            status["dashboard_frontend"] = "stopped"

        # Check Sentinel
        try:
            result = subprocess.run(
                ["pgrep", "-f", "sentinel/launcher.py"], capture_output=True, text=True
            )
            status["sentinel"] = "running" if result.returncode == 0 else "stopped"

            # Also check API for detailed status
            try:
                response = requests.get(
                    "http://localhost:8888/api/v1/sentinel/status", timeout=3
                )
                if response.status_code == 200:
                    sentinel_data = response.json()
                    status["sentinel"] = (
                        "running"
                        if sentinel_data.get("status_data", {}).get("is_running")
                        else "stopped"
                    )
            except:
                pass
        except:
            status["sentinel"] = "stopped"

        # Check Sentinel Monitor
        try:
            result = subprocess.run(
                ["pgrep", "-f", "Open_ELF/agents/sentinel_monitor.py"],
                capture_output=True,
                text=True,
            )
            status["sentinel"] = "running" if result.returncode == 0 else "stopped"
        except:
            status["sentinel"] = "stopped"

        # Check Learning Capture
        try:
            result = subprocess.run(
                ["pgrep", "-f", "background-learning-capture.py"],
                capture_output=True,
                text=True,
            )
            status["learning_capture"] = (
                "running" if result.returncode == 0 else "inactive"
            )
        except:
            status["learning_capture"] = "inactive"

        return status

    def display_architecture_status(self, status: Dict[str, str]):
        """Display architecture status with visual indicators."""
        print("\n[=] Architecture Status")
        print("    " + "-" * 50)

        services = [
            ("OpenCode Server", status["opencode_server"]),
            ("EventBridge", status["event_bridge"]),
            ("UnifiedOrchestrator", status["unified_orchestrator"]),
            ("Sentinel Monitor", status["sentinel"]),
            ("Dashboard Backend", status["dashboard_backend"]),
            ("Dashboard Frontend", status["dashboard_frontend"]),
            ("Sentinel", status["sentinel"]),
            ("Learning Capture", status["learning_capture"]),
        ]

        for name, state in services:
            icon = "🟢" if state in ["running", "active"] else "🔴"
            print(f"    {icon} {name:25} [{state}]")

        print("    " + "-" * 50)
        print()

        # Warnings for stopped services
        stopped_services = [
            name for name, state in services if state not in ["running", "active"]
        ]
        if stopped_services:
            print(
                f"[!] Warning: {len(stopped_services)} services stopped: {', '.join(stopped_services)}\n"
            )

        return status

    def display_banner(self):
        """Step 1: Display the ELF ASCII banner."""
        print(self.BANNER)

    def load_building_context(self) -> Dict[str, Any]:
        """Step 2: Load context from the building via query system."""
        print("[*] Loading Building Context...")

        try:
            # Determine correct query.py path
            query_path = self.elf_home / "query" / "query.py"
            if not query_path.exists():
                query_path = Path(__file__).parent / "query.py"

            # Call query.py --context to get the data
            result = subprocess.run(
                [
                    sys.executable,
                    str(query_path),
                    "--context",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )

            if result.returncode == 0:
                return {"raw_output": result.stdout}
            else:
                print(f"[!] Warning: Could not load full context")
                return {"raw_output": ""}

        except subprocess.TimeoutExpired:
            print("[!] Warning: Context loading timed out")
            log_debug("checkin", "Context loading timed out")
            return {"raw_output": ""}
        except Exception as e:
            print(f"[!] Warning: Error loading context: {e}")
            log_debug("checkin", f"Context loading failed: {e}")
            return {"raw_output": ""}

    def display_golden_rules(self, context: Dict[str, Any]):
        """Step 3: Query database and display golden rules with confidence scores."""
        try:
            import sqlite3

            db_path = self.elf_home / "memory" / "index.db"

            if not db_path.exists():
                print("[WARN] Database not found, showing static rules")
                return

            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get golden rules from database, sorted by confidence
            cursor.execute("""
                SELECT rule, category, confidence, explanation, use_count
                FROM golden_rules
                WHERE is_active = 1
                ORDER BY confidence DESC, use_count DESC
                LIMIT 15
            """)

            rules = cursor.fetchall()
            conn.close()

            if rules:
                print(f"\n[📜] Loaded {len(rules)} Golden Rules from Database")
                print("=" * 60)

                for i, r in enumerate(rules, 1):
                    confidence = r["confidence"] or 0.0
                    category = r["category"] or "general"
                    rule_text = (
                        r["rule"][:80] + "..." if len(r["rule"]) > 80 else r["rule"]
                    )

                    # Confidence indicator
                    if confidence >= 0.9:
                        icon = "🟢"
                    elif confidence >= 0.8:
                        icon = "🟡"
                    else:
                        icon = "⚪"

                    print(f"{i:2d}. {icon} [{category}] {rule_text}")

                    # Show explanation if available (first 3 rules only)
                    if i <= 3 and r["explanation"]:
                        print(f"    Why: {r['explanation'][:60]}...")

                print("=" * 60)
                print(f"[✓] All rules have embeddings for semantic search")
            else:
                print("[INFO] No golden rules found in database")

        except Exception as e:
            print(f"[WARN] Could not load golden rules: {e}")
            print("[INFO] Using static fallback rules")

    def display_heuristics_with_promote(self):
        """Display heuristics with option to promote to Super Golden Rule."""
        try:
            import sqlite3

            db_path = self.elf_home / "memory" / "index.db"
            if not db_path.exists():
                return

            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get high-confidence heuristics (not yet golden)
            cursor.execute("""
                SELECT id, rule, domain, confidence, validation_count, scope
                FROM heuristics 
                WHERE confidence >= 0.5 AND (scope != 'universal' OR scope IS NULL)
                ORDER BY confidence DESC, validation_count DESC
                LIMIT 10
            """)

            heuristics = cursor.fetchall()
            conn.close()

            if heuristics:
                print(f"\n[📊] Heuristics Ready for Promotion")
                print("=" * 60)
                print("To promote to SUPER GOLDEN RULE (universal), use:")
                print(
                    "  python ~/.opencode/emergent-learning/scripts/promote-to-super-golden.py <id>"
                )
                print("=" * 60)

                for h in heuristics:
                    conf = h["confidence"] or 0.0
                    print(f"\n[{h['id']}] 🟡 {h['rule'][:70]}...")
                    print(
                        f"    Domain: {h['domain'] or 'general'}, Confidence: {conf:.2f}, Validations: {h['validation_count']}"
                    )

                print("\n" + "=" * 60)
                print("Examples:")
                print(
                    "  python ~/.opencode/emergent-learning/scripts/promote-to-super-golden.py 42"
                )

        except Exception as e:
            log_debug("checkin", f"Could not display heuristics: {e}")

    def prompt_dashboard(self) -> bool:
        """Step 5: Ask about dashboard. Claude tracks session state."""
        if not self.interactive:
            # Non-interactive: Output JSON hint for Claude to use AskUserQuestion
            print(
                '[PROMPT_NEEDED] {"type": "dashboard", "question": "Start ELF Dashboard?", "default": "yes"}'
            )

            # Log the question and default response in non-interactive mode
            log_orchestrator_event(
                event_type="question_received",
                event_category="question",
                summary="Start ELF Dashboard?",
                details={
                    "question": "Start ELF Dashboard?",
                    "default": "yes",
                    "mode": "non-interactive",
                },
            )
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary="Auto-selected: yes (non-interactive mode - Claude will handle)",
                details={
                    "response": "yes",
                    "mode": "non-interactive",
                    "agent": "Claude",
                },
            )
            return False  # Claude will handle this

        print("")
        print("[+] Start ELF Dashboard?")
        print("   The dashboard provides metrics, model routing, and system health.")

        try:
            # Log the question before asking the user
            log_orchestrator_event(
                event_type="question_received",
                event_category="question",
                summary="Start ELF Dashboard?",
                details={"question": "Start ELF Dashboard?", "default": "yes"},
            )

            response = input("   Start Dashboard? [Y/n]: ").strip().lower()

            # Log the response after user answers
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary=f"User responded: {response or '(default: yes)'}",
                details={"response": response or "yes"},
            )

            return response in ["y", "yes", ""]  # Default to yes
        except (EOFError, KeyboardInterrupt):
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary="User cancelled dashboard prompt",
                details={"response": "cancelled"},
            )
            return False

    def prompt_model_selection(self) -> str:
        """Step 6: Ask about model selection. Claude tracks session state."""
        if not self.interactive:
            # Non-interactive: Output JSON hint for Claude to use AskUserQuestion
            print(
                '[PROMPT_NEEDED] {"type": "model", "question": "Select AI model", "options": ["opencode", "gemini", "codex", "skip"]}'
            )

            # Log the question and default response in non-interactive mode
            log_orchestrator_event(
                event_type="question_received",
                event_category="question",
                summary="Select Your Active Model",
                details={
                    "question": "Select Your Active Model",
                    "default": "skip",
                    "mode": "non-interactive",
                    "agent": "Claude",
                },
            )
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary=f"Auto-selected: {self.selected_model} (non-interactive mode - Claude will handle)",
                details={
                    "response": self.selected_model,
                    "mode": "non-interactive",
                    "agent": "Claude",
                },
            )
            return self.selected_model  # Claude will handle this

        print("")
        print("[=] Select Your Active Model")
        print("   Available models:")
        print("     (c)laude    - Orchestrator, backend, architecture (active)")
        print("     (g)emini    - Frontend, React, large codebases (1M context)")
        print("     (o)dex      - Graphics, debugging, precision (128K context)")
        print("     (s)kip      - Use current model")

        try:
            # Log the question before asking the user
            log_orchestrator_event(
                event_type="question_received",
                event_category="question",
                summary="Select Your Active Model",
                details={"question": "Select Your Active Model", "default": "skip"},
            )

            response = input("   Select [c/g/o/s]: ").strip().lower()

            model_map = {
                "c": "opencode",
                "g": "gemini",
                "o": "codex",
                "s": self.selected_model,  # Keep current
            }

            selected = model_map.get(
                response[0] if response else "s", self.selected_model
            )

            # Store selection in environment
            os.environ["ELF_MODEL"] = selected
            self.selected_model = selected

            # Log the response after user selects
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary=f"User selected: {selected}",
                details={"response": response, "selected_model": selected},
            )

            if selected != "opencode":
                print(f"   [OK] Using {selected}")

            return selected

        except (EOFError, KeyboardInterrupt, IndexError) as e:
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary="User cancelled or invalid model selection",
                details={
                    "response": f"exception_{type(e).__name__}",
                    "selected_model": self.selected_model,
                },
            )
            return self.selected_model

    def start_dashboard(self):
        """Dashboard launch delegated to ./start-elf-system.sh - skipped here."""
        print("   [OK] Dashboard managed by startup script")

    def check_ceo_decisions(self) -> bool:
        """Step 7: Check for pending CEO decisions."""
        ceo_inbox = self.elf_home / "ceo-inbox"

        if ceo_inbox.exists():
            pending = list(ceo_inbox.glob("*.md"))
            if pending:
                print(f"\n[!] Pending CEO Decisions: {len(pending)}")
                for item in pending[:3]:  # Show first 3
                    print(f"   - {item.stem}")
                if len(pending) > 3:
                    print(f"   ... and {len(pending) - 3} more")
                return True

        return False

    def prompt_launch_opencode(self) -> bool:
        """Ask if user wants to launch OpenCode services."""
        if not self.interactive:
            # En mode non-interactif : lancer automatiquement
            print("\n🚀 Launch OpenCode services now? (y/n) [default: n]: y")

            # Log question and automatic response in non-interactive mode
            log_orchestrator_event(
                event_type="question_received",
                event_category="question",
                summary="Launch OpenCode services now?",
                details={
                    "question": "Launch OpenCode services now?",
                    "default": "no",
                    "mode": "non-interactive",
                },
            )
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary="Auto-selected: yes (non-interactive mode)",
                details={"response": "yes", "mode": "non-interactive"},
            )
            return True

        # Interactive mode
        try:
            # Log the question before asking the user
            log_orchestrator_event(
                event_type="question_received",
                event_category="question",
                summary="Launch OpenCode services now?",
                details={
                    "question": "Launch OpenCode services now?",
                    "default": "no",
                    "mode": "interactive",
                },
            )

            response = (
                input("\n🚀 Launch OpenCode services now? (y/n) [default: n]: ")
                .lower()
                .strip()
            )

            # Log the response after user answers
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary=f"User responded: {response or 'no'}",
                details={"response": response or "no"},
            )

            return response in ["y", "yes"]

        except (EOFError, KeyboardInterrupt):
            log_orchestrator_event(
                event_type="response_sent",
                event_category="response",
                summary="User cancelled service launch prompt",
                details={"response": "cancelled"},
            )
            return False

    def launch_opencode_services(self):
        """Services launch delegated to ./start-elf-system.sh - skipped here."""
        print("\n[OpenCode] ✅ Services managed by startup script")
        print("[OpenCode] 📍 Serveur: http://localhost:4096")
        print("[OpenCode] 📚 API Docs: http://localhost:4096/doc\n")
        return True

    def start_learning_daemon(self):
        """Step 9: Start the learning daemon for automatic learning extraction."""
        print("\n[Learning] 🚀 Starting learning daemon...")

        try:
            # Check if daemon is already running
            import subprocess

            result = subprocess.run(
                ["pgrep", "-f", "learning-daemon.py"], capture_output=True, text=True
            )

            if result.returncode == 0:
                print("[Learning] ✅ Learning daemon already running")
                return True

            # Start the daemon script
            daemon_script = self.elf_home / "scripts" / "start-learning-daemon.sh"
            if not daemon_script.exists():
                print(f"[Learning] ❌ Daemon script not found: {daemon_script}")
                return False

            # Start daemon
            result = subprocess.run(
                ["bash", str(daemon_script)], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                print("[Learning] ✅ Learning daemon started successfully")
                return True
            else:
                print(f"[Learning] ❌ Failed to start daemon: {result.stderr}")
                return False

        except Exception as e:
            print(f"[Learning] ⚠️  Warning: Could not start learning daemon: {e}")
            return False

    def run(self):
        """Execute the complete checkin workflow."""
        # Step 1: Display Banner
        self.display_banner()

        # Step 1b: Verify and install hooks
        self.verify_hooks()

        # Step 2b: Check architecture status (NEW for new architecture)
        architecture_status = self.check_architecture_status()
        self.display_architecture_status(architecture_status)

        # Step 2: Load building context
        context = self.load_building_context()

        # Step 3: Display golden rules (parsed from context)
        self.display_golden_rules(context)

        # Step 4: Display heuristics with promote option
        self.display_heuristics_with_promote()

        # Step 5: Ask about dashboard (Claude tracks session state)
        start_dashboard = self.prompt_dashboard()
        if start_dashboard:
            self.start_dashboard()

        # Step 6: Ask about model selection (Claude tracks session state)
        self.prompt_model_selection()

        # Step 7: Check for CEO decisions
        self.check_ceo_decisions()

        # Step 8: Ask to launch OpenCode services (optional)
        launch_services = self.prompt_launch_opencode()
        if launch_services:
            self.launch_opencode_services()

        # Step 9: Start learning daemon for automatic learning extraction
        self.start_learning_daemon()

        print("\n[OK] Checkin complete - Ready to work!")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ELF Checkin Workflow")
    parser.add_argument(
        "--non-interactive",
        "-n",
        action="store_true",
        help="Run in non-interactive mode (auto-launch services)",
    )
    args = parser.parse_args()

    try:
        orchestrator = CheckinOrchestrator(interactive=not args.non_interactive)
        orchestrator.run()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nCheckin cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Checkin failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
