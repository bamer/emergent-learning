#!/usr/bin/env python3
"""
Test script to debug OpenCode AI integration
"""

import asyncio
import httpx
import json
from pathlib import Path

ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")


async def test_opencode_integration():
    """Test OpenCode AI integration step by step"""
    base_url = "http://localhost:4096"
    timeout = 600

    async with httpx.AsyncClient(timeout=timeout) as client:
        print("🔍 Testing OpenCode connection...")

        # 1. Check sessions
        print("\n1. Listing existing sessions:")
        response = await client.get(f"{base_url}/session")
        if response.status_code == 200:
            sessions = response.json()
            print(f"Found {len(sessions)} sessions")
            for session in sessions[:5]:  # Show first 5
                print(f"  - {session.get('id', 'N/A')}: {session.get('title', 'N/A')}")
        else:
            print(f"❌ Failed to get sessions: {response.status_code}")

        # 2. Create new session
        print("\n2. Creating new AI session:")
        session_title = "ELF AI Analysis Session - nvidia/minimaxai/minimax-m2"
        response = await client.post(
            f"{base_url}/session",
            json={
                "title": session_title,
                "directory": str(ELF_DIR),
            },
        )

        if response.status_code in [200, 201]:
            session_data = response.json()
            session_id = session_data.get("id")
            print(f"✅ Created session: {session_id}")

            # 3. Send test message
            print("\n3. Sending test message:")
            test_prompt = """ELF System Analysis Request from SENTINEL_MONITOR Agent

Services Status:
- status_server: ✅ Operational
- event_bridge: ✅ Operational  
- elf_watcher: ✅ Operational
- unified_orchestrator: ✅ Operational
- sentinel_monitor: ✅ Operational

Please provide a brief analysis of system health from the SENTINEL_MONITOR perspective."""

            response = await client.post(
                f"{base_url}/session/{session_id}/message",
                json={
                    "parts": [{"type": "text", "text": test_prompt}],
                    "model": {
                        "providerID": "nvidia",
                        "modelID": "minimaxai/minimax-m2",
                    },
                },
            )

            if response.status_code == 200:
                result = response.json()
                parts = result.get("parts", [])

                # Extract AI response
                for part in parts:
                    if part.get("type") == "text" and part.get("role") == "assistant":
                        text = part.get("text", "")
                        if len(text) > 100:
                            print(f"✅ AI Response (first 200 chars): {text[:200]}...")
                        else:
                            print(f"✅ AI Response: {text}")
                        break
                else:
                    print("❌ No assistant text found in response")
            else:
                print(f"❌ Message failed: {response.status_code}")
                print(response.text)
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(test_opencode_integration())
