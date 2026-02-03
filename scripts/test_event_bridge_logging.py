#!/usr/bin/env python3
"""
Test script for improved event bridge logging
Simulates different event types to demonstrate the smart logging behavior
"""

import sys
import time
from datetime import datetime

sys.path.insert(0, "/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator")

from event_bridge import EventBridge


def test_event_logging():
    """Test the improved event logging functionality"""

    print("🧪 Testing Improved Event Bridge Logging")
    print("=" * 50)

    # Create event bridge instance
    bridge = EventBridge()

    # Test 1: First occurrence of events (should log immediately)
    print("\n📋 Test 1: First occurrence of different events")
    bridge._record_event("message", "User: Hello, can you help me?")
    bridge._record_event("tool", "Tool: Read | Session: abc123")
    bridge._record_event("error", "Error: File not found")
    bridge._record_event("session", "Session started")

    # Test 2: Repeated events within throttle window (should be throttled)
    print("\n⏱️ Test 2: Repeated events within 5-second throttle")
    for i in range(5):
        bridge._record_event("tool", f"Tool: Write | Session: def456")
        time.sleep(1)

    # Test 3: Wait and log again (should log due to throttle reset)
    print("\n⏰ Test 3: Waiting 6 seconds for throttle reset")
    time.sleep(6)
    bridge._record_event("tool", "Tool: Edit | Session: ghi789")

    # Test 4: Non-important events (should only log on throttle boundary)
    print("\n🔍 Test 4: Non-important events (debug level)")
    for i in range(3):
        bridge._record_event("heartbeat", f"Heartbeat #{i + 1}")
        time.sleep(2)

    # Test 5: Event summary logging (every Nth occurrence)
    print("\n📊 Test 5: Event summary every 10 occurrences")
    for i in range(12):
        bridge._record_event("poll", f"Poll check #{i + 1}")

    # Show final statistics
    print("\n📈 Final Event Statistics:")
    print(f"Total events: {bridge.event_count}")
    print("Event breakdown:")
    for event_type, count in bridge.event_stats.items():
        print(f"  {event_type}: {count}")

    print("\n✅ Test completed!")
    print("Check the event-bridge.log to see the improved logging behavior.")


if __name__ == "__main__":
    test_event_logging()
