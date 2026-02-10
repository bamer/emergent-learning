#!/usr/bin/env python3
"""
Trigger AI analysis of system state and output results.
"""

import sys
import os

# Add the project root to the path so we can import Open_ELF modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    print("🔍 Triggering deep analysis of system state...")
    try:
        from Open_ELF.orchestrator.unified_orchestrator import get_orchestrator

        orchestrator = get_orchestrator()
        # Directly call the AI analysis method
        result = orchestrator._analyze_with_ai()
        print("📊 Analysis result:", result)
        if result and "response" in result:
            print("🗣 AgentManager response:", result["response"])
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
