#!/usr/bin/env python3
"""
Test script for Unified OpenCode Orchestrator
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add orchestrator directory to path
ORCHESTRATOR_DIR = Path(__file__).parent
sys.path.insert(0, str(ORCHESTRATOR_DIR))

from unified_orchestrator import Event, DecisionEngine, AsyncOpenCodeClient


async def test_decision_engine():
    """Test the decision engine with various event types."""
    print("🧪 Testing Decision Engine...")

    # Create a mock client
    client = AsyncOpenCodeClient()
    engine = DecisionEngine(client)

    # Test events
    test_events = [
        Event(
            id="test_1",
            type="tool_failure",
            severity="error",
            source="opencode",
            data={"tool_name": "bash", "error": "Command failed"},
            timestamp=datetime.now(),
        ),
        Event(
            id="test_2",
            type="error",
            severity="critical",
            source="system",
            data={
                "error_type": "database_connection",
                "error_message": "Cannot connect to database",
            },
            timestamp=datetime.now(),
        ),
        Event(
            id="test_3",
            type="system_health",
            severity="warning",
            source="database",
            data={"status": "degraded", "issues": ["high cpu usage"]},
            timestamp=datetime.now(),
        ),
        Event(
            id="test_4",
            type="ceo_escalation",
            severity="critical",
            source="file_system",
            data={"reason": "System performance degradation", "impact": "High"},
            timestamp=datetime.now(),
        ),
    ]

    # Process each event
    for event in test_events:
        print(f"\n📋 Processing {event.type} event...")
        action = await engine.process_event(event)
        print(f"   Action taken: {action}")

    print("\n✅ Decision Engine tests completed")


async def test_orchestrator_startup():
    """Test that orchestrator can start."""
    print("\n🚀 Testing Orchestrator Startup...")

    try:
        # This would normally start the full orchestrator
        # For testing, we'll just verify the components can be imported
        from unified_orchestrator import UnifiedOrchestrator

        orchestrator = UnifiedOrchestrator()
        print("✅ Orchestrator class instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ Orchestrator startup failed: {e}")
        return False


async def test_status_endpoint():
    """Test the status endpoint."""
    print("\n📊 Testing Status Endpoint...")

    try:
        import requests

        response = requests.get("http://localhost:9999/status", timeout=1)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Status endpoint accessible")
            print(f"   Running: {status.get('running', 'Unknown')}")
            print(f"   Events processed: {status.get('events_processed', 0)}")
            return True
        else:
            print(f"⚠️ Status endpoint returned HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Status endpoint not accessible: {e}")
        return False


async def create_sample_ceo_escalation():
    """Create a sample CEO escalation file for testing."""
    print("\n📧 Creating sample CEO escalation...")

    CEO_INBOX_DIR = Path.home() / ".opencode" / "emergent-learning" / "ceo-inbox"
    CEO_INBOX_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = CEO_INBOX_DIR / f"test_escalation_{timestamp}.md"

    content = f"""# Test Escalation - System Alert

**Date:** {datetime.now().isoformat()}
**Severity:** critical
**Source:** test_system
**Reason:** This is a test escalation for verifying the unified orchestrator

## Context
This is a simulated escalation to test the CEO inbox monitoring functionality.

## Suggested Resolution
No action required - this is a test.

---
*Created by test_unified_orchestrator.py*
"""

    filename.write_text(content)
    print(f"✅ Created test escalation: {filename.name}")
    return filename


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🤖 Unified OpenCode Orchestrator Test Suite")
    print("=" * 60)

    # Run tests
    await test_decision_engine()
    await test_orchestrator_startup()

    # Test status endpoint
    await test_status_endpoint()

    # Create test escalation
    await create_sample_ceo_escalation()

    print("\n" + "=" * 60)
    print("🏁 Test suite completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
