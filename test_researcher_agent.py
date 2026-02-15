#!/usr/bin/env python3
"""
Test script for invoking the researcher agent via AgentManager.
"""

import sys
from pathlib import Path

# Add the Open_ELF directory to the path
openelf_dir = Path(__file__).parent / "Open_ELF"
if str(openelf_dir) not in sys.path:
    sys.path.insert(0, str(openelf_dir))


def test_researcher_agent():
    """Test the researcher agent via AgentManager."""
    try:
        # Import the AgentManager
        from agents.agent_manager import get_agent_manager

        # Get the agent manager instance
        print("Initializing AgentManager...")
        manager = get_agent_manager()

        # List available agents
        print(f"Available agents: {manager.list_agents()}")

        # Check if researcher agent is available
        if "researcher" not in manager.agents:
            print("❌ Researcher agent not found!")
            return False

        print("✅ Researcher agent is available")

        # Test the researcher agent with a simple query
        print("Testing researcher agent...")
        result = manager.researcher(
            "What are the key principles of effective software architecture?"
        )

        if result.get("success"):
            print("✅ Researcher agent responded successfully!")
            print(f"Response: {result.get('response')[:500]}...")
            return True
        else:
            print(f"❌ Researcher agent failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Error testing researcher agent: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing Researcher Agent via AgentManager")
    print("=" * 50)

    success = test_researcher_agent()

    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1)
