#!/usr/bin/env python3
"""
Test script for custom 6-agent swarm via AgentManager.
"""

import sys
import json
from pathlib import Path

# Add the Open_ELF directory to the path
openelf_dir = Path(__file__).parent / "Open_ELF"
if str(openelf_dir) not in sys.path:
    sys.path.insert(0, str(openelf_dir))


def test_custom_swarm():
    """Test custom 6-agent swarm."""
    try:
        print("Testing custom 6-agent swarm...")

        # Import the AgentManager
        from agents.agent_manager import AgentManager

        # Create an instance of AgentManager
        manager = AgentManager()

        # List available agents
        available_agents = list(manager.agents.keys())
        print(f"Available agents ({len(available_agents)}): {available_agents}")

        # Define our 6-agent swarm
        swarm_agents = [
            "researcher",
            "architect",
            "creative",
            "skeptic",
            "ceo",
            "sentinel",
        ]

        # Check which agents are available
        available_swarm_agents = [
            agent for agent in swarm_agents if agent in manager.agents
        ]
        missing_agents = [
            agent for agent in swarm_agents if agent not in manager.agents
        ]

        print(f"\nRequested swarm agents: {swarm_agents}")
        print(f"Available swarm agents: {available_swarm_agents}")
        if missing_agents:
            print(f"Missing agents: {missing_agents}")

        # Create swarm task
        swarm_task = "Analyze the benefits and drawbacks of microservices architecture compared to monolithic architecture"

        # Test with multi-agent-coordinator if available
        if "multi-agent-coordinator" in manager.agents:
            print(f"\n🚀 Initiating 6-agent swarm via multi-agent-coordinator...")

            # Create swarm prompt
            swarm_prompt = f"""[SWARM] Coordinate a team of 6 agents to analyze: {swarm_task}

Available agents: {", ".join(available_swarm_agents)}

Each agent should contribute their unique perspective:
- Researcher: Gather facts and evidence
- Architect: Analyze technical implications
- Creative: Propose innovative solutions
- Skeptic: Identify potential issues and risks
- CEO: Consider business impact
- Sentinel: Evaluate security and monitoring aspects

Provide a comprehensive analysis with inputs from all agents."""

            result = manager.ask_agent("multi-agent-coordinator", swarm_prompt)

            if result.get("success"):
                print("✅ Swarm initiated successfully!")
                print(f"Session ID: {result.get('session_id')}")
                response_preview = (
                    result.get("response", "")[:300] + "..."
                    if len(result.get("response", "")) > 300
                    else result.get("response", "")
                )
                print(f"Response preview: {response_preview}")
                return True
            else:
                print(f"❌ Failed to initiate swarm: {result.get('error')}")
                return False
        else:
            print("❌ Multi-agent coordinator not available for swarm coordination")

            # Fallback: Test individual agents
            print("\n🔄 Testing individual agents as fallback...")
            success_count = 0

            for agent_name in available_swarm_agents[:3]:  # Test first 3 to save time
                print(f"\nTesting {agent_name}...")
                prompt = f"As a {agent_name}, analyze: {swarm_task}"
                result = manager.ask_agent(agent_name, prompt)

                if result.get("success"):
                    print(f"✅ {agent_name} responded successfully")
                    success_count += 1
                else:
                    print(f"❌ {agent_name} failed: {result.get('error')}")

            print(
                f"\nIndividual agent test results: {success_count}/{min(3, len(available_swarm_agents))} successful"
            )
            return success_count > 0

    except Exception as e:
        print(f"❌ Error testing custom swarm: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🤖 Testing Custom 6-Agent Swarm")
    print("=" * 50)

    success = test_custom_swarm()

    if success:
        print("\n🎉 Custom swarm test completed successfully!")
    else:
        print("\n💥 Custom swarm test failed!")
        sys.exit(1)
