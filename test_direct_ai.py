#!/usr/bin/env python3
"""
Direct test of OpenCode AI integration with component context
"""

import asyncio
import httpx
import json
from pathlib import Path

ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")


async def test_ai_with_component_context():
    """Test AI integration directly"""
    base_url = "http://localhost:4096"
    timeout = 60

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 1. Create session
            print("Creating AI session...")
            response = await client.post(
                f"{base_url}/session",
                json={
                    "title": "ELF AI Test - Component Context",
                    "directory": str(ELF_DIR),
                },
            )

            if response.status_code not in [200, 201]:
                print(f"❌ Session creation failed: {response.status_code}")
                return

            session_data = response.json()
            session_id = session_data.get("id")
            print(f"✅ Session created: {session_id[:8]}...")

            # 2. Test different components
            components = ["elf_watcher", "unified_orchestrator", "sentinel_monitor"]

            for component in components:
                print(f"\n🧪 Testing component: {component}")

                # Create component-specific prompt
                system_state = {
                    "services": {
                        "status_server": True,
                        "event_bridge": True,
                        "elf_watcher": component == "elf_watcher",
                        "unified_orchestrator": component == "unified_orchestrator",
                        "sentinel_monitor": component == "sentinel_monitor",
                    }
                }

                services_report = "\\n".join(
                    [
                        f"  - {service}: {'✅ Operational' if healthy else '❌ Down'}"
                        for service, healthy in system_state["services"].items()
                    ]
                )

                enhanced_prompt = f"""ELF System Analysis Request from {component.upper()} Agent

Current System State:
{services_report}

You are analyzing system state as the {component} agent. Provide agent-specific insights and recommendations. Be concise but informative."""

                print(f"📤 Sending request for {component}...")
                start_time = asyncio.get_event_loop().time()

                response = await client.post(
                    f"{base_url}/session/{session_id}/message",
                    json={
                        "parts": [{"type": "text", "text": enhanced_prompt}],
                        "model": {
                            "providerID": "nvidia",
                            "modelID": "minimaxai/minimax-m2",
                        },
                    },
                )

                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time

                if response.status_code == 200:
                    result = response.json()
                    parts = result.get("parts", [])

                    # Extract text content from parts
                    text_content = []
                    for part in parts:
                        if part.get("type") == "text" and part.get("text"):
                            text_content.append(part.get("text", ""))

                    ai_response = "\\n".join(text_content)

                    if ai_response.strip():
                        print(f"✅ {component} response ({duration:.1f}s):")
                        if len(ai_response) > 200:
                            print(f"   {ai_response[:200]}...")
                        else:
                            print(f"   {ai_response}")
                    else:
                        print(f"⚠️  {component}: Empty response")
                else:
                    print(f"❌ {component} failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_ai_with_component_context())
