#!/usr/bin/env python3
"""
Simple test script for AgentManager initialization.
"""

import sys
from pathlib import Path

# Add the Open_ELF directory to the path
openelf_dir = Path(__file__).parent / "Open_ELF"
if str(openelf_dir) not in sys.path:
    sys.path.insert(0, str(openelf_dir))


def test_agent_manager_initialization():
    """Test AgentManager initialization."""
    try:
        print("Testing AgentManager initialization...")

        # Import the AgentManager
        from agents.agent_manager import AgentManager

        # Create an instance of AgentManager
        manager = AgentManager()

        print(f"✅ AgentManager initialized successfully!")
        print(f"Agents loaded: {len(manager.agents)}")

        # List the agents
        agent_names = list(manager.agents.keys())
        print(f"Agent names: {agent_names}")

        # Check for researcher specifically
        if "researcher" in manager.agents:
            print("✅ Researcher agent found!")
            researcher_config = manager.agents["researcher"]
            print(f"  - Model: {researcher_config.model}")
            print(f"  - Description: {researcher_config.description}")
        else:
            print("❌ Researcher agent not found")

        return True

    except Exception as e:
        print(f"❌ Error initializing AgentManager: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing AgentManager Initialization")
    print("=" * 50)

    success = test_agent_manager_initialization()

    if success:
        print("\n🎉 Initialization test completed successfully!")
    else:
        print("\n💥 Initialization test failed!")
        sys.exit(1)
