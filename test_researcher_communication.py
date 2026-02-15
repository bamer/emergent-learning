#!/usr/bin/env python3
"""
Test script for communicating with the researcher agent via AgentManager.
"""

import sys
from pathlib import Path

# Add the Open_ELF directory to the path
openelf_dir = Path(__file__).parent / "Open_ELF"
if str(openelf_dir) not in sys.path:
    sys.path.insert(0, str(openelf_dir))


def test_researcher_communication():
    """Test communication with the researcher agent."""
    try:
        print("Testing communication with researcher agent...")

        # Import the AgentManager
        from agents.agent_manager import AgentManager

        # Create an instance of AgentManager
        manager = AgentManager()

        # Check if researcher agent is available
        if "researcher" not in manager.agents:
            print("❌ Researcher agent not found!")
            return False

        print("✅ Researcher agent is available")
        researcher_config = manager.agents["researcher"]
        print(f"  - Model: {researcher_config.model}")
        print(f"  - Description: {researcher_config.description}")

        # Test communication with a simple query
        print("\nSending test query to researcher agent...")
        result = manager.ask_agent("researcher", "What is 2+2?")

        print(f"Request successful: {result.get('success')}")
        if result.get("success"):
            print(f"Response: {result.get('response')}")
            print(f"Session ID: {result.get('session_id')}")
            return True
        else:
            print(f"Error: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Error communicating with researcher agent: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing Researcher Agent Communication")
    print("=" * 50)

    success = test_researcher_communication()

    if success:
        print("\n🎉 Communication test completed successfully!")
    else:
        print("\n💥 Communication test failed!")
        sys.exit(1)
