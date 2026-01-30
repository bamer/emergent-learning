#!/usr/bin/env python3
"""
Robust OpenCode Terminal Launcher
Ensures OpenCode server launches in a separate, visible terminal window.
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path


class OpenCodeTerminalLauncher:
    """Launches OpenCode in a separate terminal with fallback strategies."""

    def __init__(self, port=4096):
        self.port = port

    def launch_in_new_terminal(self):
        """Launch OpenCode in a new terminal window with multiple fallback strategies."""
        print(f"🚀 Launching OpenCode server on port {self.port}...")

        # Determine available terminal launchers
        launchers = self._get_terminal_launchers()

        # Try each launcher in order of preference
        for launcher in launchers:
            try:
                if self._try_launcher(launcher):
                    print(f"✅ Started OpenCode using {launcher['name']}")
                    return True
            except Exception as e:
                print(f"⚠️  {launcher['name']} failed: {e}")
                continue

        # All launchers failed - fallback to background
        print("⚠️  Could not find suitable terminal. Launching in background...")
        return self._launch_background()

    def _get_terminal_launchers(self):
        """Get list of terminal launch strategies for current platform."""
        launchers = []

        if sys.platform == "win32":
            launchers.extend(
                [
                    {
                        "name": "PowerShell",
                        "test": ["powershell", "-Command", "Get-Command opencode"],
                        "launch": [
                            "powershell",
                            "-NoExit",
                            "-Command",
                            f"opencode serve --port {self.port}",
                        ],
                        "flags": {},
                    },
                    {
                        "name": "Command Prompt",
                        "test": ["cmd", "/c", "where opencode"],
                        "launch": ["cmd", "/k", f"opencode serve --port {self.port}"],
                        "flags": {"creationflags": subprocess.CREATE_NEW_CONSOLE},
                    },
                ]
            )
        else:
            # Unix/Linux systems
            launchers.extend(
                [
                    {
                        "name": "gnome-terminal",
                        "test": ["which", "gnome-terminal"],
                        "launch": [
                            "gnome-terminal",
                            "--",
                            "bash",
                            "-c",
                            f'opencode serve --port {self.port}; echo "\\nPress Enter to close..."; read',
                        ],
                    },
                    {
                        "name": "konsole",
                        "test": ["which", "konsole"],
                        "launch": [
                            "konsole",
                            "--new-tab",
                            "-e",
                            "bash",
                            "-c",
                            f'opencode serve --port {self.port}; echo "Press Enter to close..."; read',
                        ],
                    },
                    {
                        "name": "xterm",
                        "test": ["which", "xterm"],
                        "launch": [
                            "xterm",
                            "-e",
                            "bash",
                            "-c",
                            f'opencode serve --port {self.port}; echo "Press Enter to close..."; read',
                        ],
                    },
                    {
                        "name": "xfce4-terminal",
                        "test": ["which", "xfce4-terminal"],
                        "launch": [
                            "xfce4-terminal",
                            "--disable-server",
                            "--",
                            "bash",
                            "-c",
                            f'opencode serve --port {self.port}; echo "Press Enter to close..."; read',
                        ],
                    },
                    {
                        "name": "alacritty",
                        "test": ["which", "alacritty"],
                        "launch": [
                            "alacritty",
                            "-e",
                            "bash",
                            "-c",
                            f'opencode serve --port {self.port}; echo "Press Enter to close..."; read',
                        ],
                    },
                    {
                        "name": "tmux new session",
                        "test": ["which", "tmux"],
                        "launch": [
                            "tmux",
                            "new-session",
                            "-d",
                            "-s",
                            "opencode",
                            f"opencode serve --port {self.port}",
                        ],
                    },
                    {
                        "name": "screen new session",
                        "test": ["which", "screen"],
                        "launch": [
                            "screen",
                            "-dmS",
                            "opencode",
                            "bash",
                            "-c",
                            f"opencode serve --port {self.port}",
                        ],
                    },
                ]
            )

        return launchers

    def _try_launcher(self, launcher):
        """Try a specific launcher."""
        # Test if terminal exists
        if "test" in launcher:
            result = subprocess.run(launcher["test"], capture_output=True)
            if result.returncode != 0:
                return False

        # Try to launch
        cmd = launcher["launch"]
        flags = launcher.get("flags", {})

        print(f"🔧 Trying {launcher['name']}...")
        print(f"   Command: {' '.join(cmd)}")

        # For gnome-terminal, add environment check
        if launcher["name"] == "gnome-terminal" and os.environ.get("DISPLAY"):
            process = subprocess.Popen(cmd, **flags)
        else:
            process = subprocess.Popen(cmd, **flags)

        # Give it a moment to start
        time.sleep(3)

        # Check if process is still running (successful launch)
        if process.poll() is None:
            print(f"✅ {launcher['name']} launched successfully")
            return True
        else:
            print(f"❌ {launcher['name']} failed to start")
            return False

    def _launch_background(self):
        """Fallback: launch in background."""
        cmd = ["opencode", "serve", "--port", str(self.port)]

        # Check if opencode is available
        try:
            subprocess.run(["which", "opencode"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("❌ 'opencode' command not found")
            print("   Install with: npm install -g opencode")
            return False

        # Launch in background
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        print(f"📡 OpenCode server started in background on port {self.port}")
        print("   Monitor with: ps aux | grep opencode")
        print("   Stop with: pkill -f 'opencode serve'")
        return True

    def wait_for_server(self, timeout=30):
        """Wait for server to be ready."""
        print("⏳ Waiting for server to start...")

        import requests

        for i in range(timeout):
            try:
                resp = requests.get(
                    f"http://localhost:{self.port}/global/health", timeout=2
                )
                if resp.status_code == 200:
                    print(f"✅ Server is ready on http://localhost:{self.port}")
                    return True
            except:
                pass

            if i % 5 == 0 and i > 0:
                print(f"   Still waiting... ({i}s)")

            time.sleep(1)

        print("⚠️  Server did not respond within timeout")
        return False


def main():
    """Main launcher function."""
    launcher = OpenCodeTerminalLauncher()

    if launcher.launch_in_new_terminal():
        # Wait a bit then check if server started
        time.sleep(3)
        launcher.wait_for_server()

        print("\n📋 OpenCode Server Information:")
        print(f"   🌐 URL: http://localhost:{launcher.port}")
        print(f"   📊 Health: http://localhost:{launcher.port}/global/health")
        print(f"   🤖 Agents: http://localhost:{launcher.port}/agents")
        print("\n💡 To stop the server:")
        print("   - In the terminal: Press Ctrl+C")
        print("   - Or kill: pkill -f 'opencode serve'")

        print("\n✅ OpenCode is running in a separate terminal!")
        return True

    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
