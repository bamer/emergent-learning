#!/usr/bin/env python3
"""
Simple ELF Checkin with guaranteed OpenCode prompt.

This ensures users always see the OpenCode launch prompt
and provides easy launch option.
"""

import os
import sys
import subprocess
from pathlib import Path


def display_banner():
    """Display ELF banner."""
    print("""
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
    """)


def check_opencode_status():
    """Check if OpenCode server is running."""
    try:
        import requests

        resp = requests.get("http://localhost:4096/global/health", timeout=2)
        return resp.status_code == 200
    except:
        return False


def prompt_opencode_launch(interactive=True):
    """Prompt and handle OpenCode launch."""
    print("\n🚀 OpenCode Services")

    if check_opencode_status():
        print("✅ OpenCode server is already running on http://localhost:4096")
        return

    print("OpenCode provides agent orchestration for ELF.")
    print("Launch now to enable multi-agent workflows?")

    if not interactive:
        print("⚠️  Non-interactive mode - skipping launch prompt")
        return

    try:
        response = (
            input("Launch OpenCode services? (y/n) [default: y]: ").lower().strip()
        )
        if response in ["", "y", "yes"]:
            launch_opencode()
        else:
            print("⏭ Skipping OpenCode launch")
    except KeyboardInterrupt:
        print("\n✋ Cancelled")


def launch_opencode():
    """Launch OpenCode services in a separate terminal window."""
    print("\n🔧 Starting OpenCode in separate terminal...")

    # Try GNOME-specific launcher first (most reliable)
    gnome_script = Path(__file__).parent.parent / "scripts" / "launch-opencode-gnome.sh"

    if gnome_script.exists():
        try:
            subprocess.run(["bash", str(gnome_script)], check=True)
            print("✅ OpenCode started in new terminal window!")
            print("📋 You can monitor and close it independently.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ GNOME launcher failed: {e}")

    # Fallback to background launch
    print("   Falling back to background launch...")
    try:
        subprocess.run(["opencode", "serve", "--port", "4096"], check=True)
        print("✅ OpenCode started in background")
        print("   Stop with: pkill -f 'opencode serve'")
        return True
    except subprocess.CalledProcessError:
        print("❌ Opencode not found. Install with: npm install -g opencode")
        return False
    else:
        print("❌ Terminal launcher script not found")
        return False


def check_dashboard_status():
    """Check if dashboard is running."""
    try:
        import requests

        # Try both old and new API paths for compatibility
        for path in ["/api/heuristics?limit=1", "/api/v1/heuristics?limit=1"]:
            try:
                resp = requests.get(f"http://localhost:3001{path}", timeout=2)
                if resp.status_code == 200:
                    return True
            except:
                continue
        return False
    except:
        return False


def main():
    """Simple checkin flow."""
    display_banner()

    print("🔍 System Status:")

    # Check dashboard
    if check_dashboard_status():
        print("  ✅ Dashboard: Running on http://localhost:3001")
    else:
        print("  ⚠️  Dashboard: Not detected on http://localhost:3001")
        print("      Start with: bash dashboard-app/run-dashboard.sh")

    # Check OpenCode
    opencode_running = check_opencode_status()
    if opencode_running:
        print("  ✅ OpenCode: Running on http://localhost:4096")
    else:
        print("  ⚠️  OpenCode: Not running")
        prompt_opencode_launch(interactive=True)

    print("\n📚 Golden Rules: Available via query system")
    print("   Use: python query/query.py --context")

    print("\n✅ ELF Checkin Complete!")

    if opencode_running:
        print("🎯 Full system ready - agents + dashboard + learning")


if __name__ == "__main__":
    main()
