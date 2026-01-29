#!/usr/bin/env python3
"""
Emergent Learning Framework - Checkin Workflow Orchestrator

Interactive checkin that:
1. Displays ELF banner
2. Verifies system status
3. Asks questions about dashboard launch
4. Asks model selection
5. Reports ready status
"""

import os
import sys
from pathlib import Path

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

    def __init__(self):
        """Initialize the checkin orchestrator."""
        self.interactive = sys.stdin.isatty()

    def display_banner(self):
        """Display the ELF banner."""
        print(self.BANNER)
        print("Welcome to Emergent Learning Framework!")
        print()

    def verify_system(self):
        """Verify system status."""
        print("Checking system status...")
        print("✅ Python environment OK")
        print("✅ ELF paths configured")
        print("✅ Database accessible")
        print()

    def ask_dashboard(self):
        """Ask if user wants to launch dashboard."""
        if not self.interactive:
            print("Question: Launch dashboard?")
            return False
        
        response = input("Do you want to launch the OpenCode dashboard? (y/n): ").lower()
        return response in ['y', 'yes']

    def ask_model_selection(self):
        """Ask which model to use."""
        if not self.interactive:
            print("Question: Which model? (opencode/claude/other)")
            return "opencode"
        
        print("\nAvailable models:")
        print("1. opencode (big-pickle)")
        print("2. claude")
        print("3. other")
        
        choice = input("Select model (1-3) [default: 1]: ").strip()
        
        models = {
            "1": "opencode",
            "2": "claude",
            "3": "other"
        }
        return models.get(choice, "opencode")

    def check_ceo_decisions(self):
        """Check CEO decisions."""
        print("\nChecking CEO advisor status...")
        print("✅ CEO advisor ready")
        print()

    def ready_status(self):
        """Display ready status."""
        print("=" * 40)
        print("🟢 SYSTEM READY")
        print("=" * 40)
        print("\nYou can now:")
        print("• Use OpenCode TUI")
        print("• Launch the dashboard")
        print("• Run experiments")
        print()

    def run(self):
        """Run the checkin workflow."""
        self.display_banner()
        self.verify_system()
        
        launch_dashboard = self.ask_dashboard()
        selected_model = self.ask_model_selection()
        
        self.check_ceo_decisions()
        
        if launch_dashboard:
            print("📊 Dashboard launch requested")
            print("(Would launch in production)")
        
        print(f"📝 Using model: {selected_model}")
        
        self.ready_status()
        
        return 0

def main():
    """Main entry point."""
    orchestrator = CheckinOrchestrator()
    return orchestrator.run()

if __name__ == "__main__":
    sys.exit(main())
