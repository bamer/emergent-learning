#!/usr/bin/env python3
"""
Quick test for researcher agent with timeout handling.
"""

import sys
import json
import subprocess
from pathlib import Path


def test_researcher_via_sdk():
    """Test researcher agent via SDK client directly."""
    try:
        print("Testing researcher agent via SDK client...")

        # Test session list first
        sdk_path = "/home/bamer/.opencode/emergent-learning/Open_ELF/agents/opencode_sdk_client.mjs"

        # Create request for session list
        request_data = {
            "action": "session_list",
            "baseUrl": "http://localhost:4096",
            "payload": {"directory": "/home/bamer/.opencode/emergent-learning"},
        }

        # Run the SDK client
        result = subprocess.run(
            ["bun", sdk_path],
            input=json.dumps(request_data),
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        if result.returncode != 0:
            print(f"❌ SDK client failed: {result.stderr}")
            return False

        response = json.loads(result.stdout)
        if not response.get("success"):
            print(f"❌ SDK request failed: {response.get('error')}")
            return False

        print("✅ SDK client working correctly")
        sessions = response.get("data", [])
        researcher_session = None

        # Find researcher session
        for session in sessions:
            if "Researcher" in session.get("title", ""):
                researcher_session = session
                break

        if not researcher_session:
            print("❌ No researcher session found")
            return False

        print(f"✅ Found researcher session: {researcher_session['title']}")
        return True

    except subprocess.TimeoutExpired:
        print("❌ SDK client timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing SDK: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Quick Researcher Agent Test")
    print("=" * 40)

    success = test_researcher_via_sdk()

    if success:
        print("\n🎉 SDK test completed successfully!")
    else:
        print("\n💥 SDK test failed!")
        sys.exit(1)
