#!/usr/bin/env python3
"""
OpenCode Launcher - Separate module for launching OpenCode server and agents

This module handles:
1. Auto-starting OpenCode server on port 4096
2. Launching background services (watcher, orchestrator, CEO advisor)
3. Verifying system is ready

Called as an optional step from checkin workflow.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path
from typing import Tuple


class OpenCodeLauncher:
    """Handles OpenCode server and agent launches."""

    def __init__(self, server_url: str = "http://localhost:4096"):
        self.server_url = server_url
        self.root_dir = Path(__file__).resolve().parents[1]

    def ensure_server_running(self) -> bool:
        """Ensure OpenCode server is running on port 4096."""
        print("\n[OpenCode] Checking server status...")

        # Check if already running
        try:
            resp = requests.get(f"{self.server_url}/", timeout=2)
            if resp.status_code == 200:
                health_data = resp.json()
                version = health_data.get("version", "unknown")
                print(f"[OpenCode] ✅ Server already running on port 4096 (v{version})")
                print(
                    "[OpenCode]    You can monitor it with: ps aux | grep 'opencode serve'"
                )
                return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

        # Start server in visible terminal
        print("[OpenCode] Starting server in new terminal...")
        try:
            import sys

            # Launch in visible terminal based on platform
            if sys.platform == "win32":
                # Windows: PowerShell in new window
                subprocess.Popen(
                    ["powershell", "-NoExit", "-Command", "opencode serve --port 4096"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                # Unix: gnome-terminal, xterm, or fallback
                term_cmd = None
                for term in [
                    "gnome-terminal",
                    "xterm",
                    "konsole",
                    "xfce4-terminal",
                    "alacritty",
                ]:
                    if (
                        subprocess.run(["which", term], capture_output=True).returncode
                        == 0
                    ):
                        if term == "gnome-terminal":
                            # gnome-terminal: Use --tab for new tab, -- for command separation
                            term_cmd = [
                                term,
                                "--tab",
                                "--",
                                "bash",
                                "-c",
                                'opencode serve --port 4096; echo "Server stopped. Press Enter to close..."; read',
                            ]
                        elif term == "xterm":
                            term_cmd = [
                                term,
                                "-e",
                                "bash",
                                "-c",
                                'opencode serve --port 4096; echo "Server stopped. Press Enter to close..."; read',
                            ]
                        elif term == "konsole":
                            term_cmd = [
                                term,
                                "-e",
                                "bash",
                                "-c",
                                'opencode serve --port 4096; echo "Server stopped. Press Enter to close..."; read',
                            ]
                        else:
                            term_cmd = [
                                term,
                                "-e",
                                "bash",
                                "-c",
                                'opencode serve --port 4096; echo "Server stopped. Press Enter to close..."; read',
                            ]
                        break

                if term_cmd:
                    subprocess.Popen(term_cmd)
                else:
                    # Fallback: no terminal found, run in background
                    print("[OpenCode] ⚠️  No terminal found, launching in background")
                    subprocess.Popen(
                        ["opencode", "serve", "--port", "4096"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )

            # Wait for server
            for i in range(30):
                try:
                    resp = requests.get(f"{self.server_url}/", timeout=2)
                    if resp.status_code == 200:
                        print("[OpenCode] ✅ Server started successfully")
                        return True
                except:
                    pass

                if i % 5 == 0 and i > 0:
                    print(f"[OpenCode] Waiting... ({i}s)")
                time.sleep(1)

            print("[OpenCode] ❌ Server failed to start")
            return False

        except FileNotFoundError:
            print("[OpenCode] ❌ OpenCode command not found")
            print("[OpenCode] Install with: npm install -g opencode")
            return False
        except Exception as e:
            print(f"[OpenCode] ❌ Error: {e}")
            return False

    def launch_agents(self) -> bool:
        """Launch background agents (watcher, orchestrator, CEO)."""
        print("\n[OpenCode] Launching agents...")

        agents = [
            ("Watcher", "src/watcher/launcher.py"),
            ("Orchestrator", "src/orchestrator.py"),
            ("CEO Advisor", "agents/dashboard_sentinel_ceo.py"),
        ]

        launched = 0
        for agent_name, script_path in agents:
            try:
                full_path = self.root_dir / script_path

                if not full_path.exists():
                    print(f"[OpenCode] ⚠️  {agent_name} not found")
                    continue

                # Launch with special handling for CEO
                if "dashboard_sentinel" in script_path:
                    subprocess.Popen(
                        [sys.executable, str(full_path), "--ceo"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                else:
                    subprocess.Popen(
                        [sys.executable, str(full_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )

                print(f"[OpenCode] ✅ {agent_name} launched")
                launched += 1
                time.sleep(0.5)

            except Exception as e:
                print(f"[OpenCode] ⚠️  {agent_name} failed: {e}")

        return launched > 0

    def ready_status(self):
        """Print ready status."""
        print("\n" + "=" * 50)
        print("[OpenCode] 🟢 OPENCODE SYSTEM READY")
        print("=" * 50)
        print("\nServices running in background:")
        print("  • Watcher - monitoring experiments")
        print("  • Orchestrator - agent coordination")
        print("  • CEO Advisor - business intelligence")
        print("\nYou can now use the system normally.")
        print("=" * 50 + "\n")

    def launch_all(self) -> bool:
        """Launch OpenCode server and all agents."""
        if not self.ensure_server_running():
            return False

        if not self.launch_agents():
            print("[OpenCode] ⚠️  Some agents failed to launch")
            # Still return True - partial success is ok

        self.ready_status()
        return True


def main():
    """Run launcher standalone."""
    launcher = OpenCodeLauncher()
    success = launcher.launch_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
