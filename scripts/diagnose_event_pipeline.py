#!/usr/bin/env python3
"""
Diagnostic script for EventBridge tool detection
Tests if the event pipeline is capturing tools correctly
"""

import requests
import json
import time
from datetime import datetime


def check_event_bridge_status():
    """Check EventBridge heartbeat"""
    try:
        with open(
            "/home/bamer/OPC_ELF/.coordination/event-bridge-heartbeat.json"
        ) as f:
            status = json.load(f)

        print("📊 EventBridge Status:")
        print(f"   Running: {status.get('running', False)}")
        print(f"   Events processed: {status.get('events_processed', 0)}")
        print(f"   Last event: {status.get('last_event_time', 'N/A')}")
        print(f"   Health: {status.get('health', 'unknown')}")

        # Check for tool events
        stats = status.get("event_stats", {})
        top_events = stats.get("top_events", {})

        print("\n📈 Event Statistics:")
        for event_type, count in top_events.items():
            print(f"   {event_type}: {count}")

        return status.get("running", False)
    except Exception as e:
        print(f"❌ Error reading status: {e}")
        return False


def check_recent_tools():
    """Check if any tools were detected recently"""
    try:
        # Read event bridge log
        with open(
            "/home/bamer/OPC_ELF/Open_ELF/logs/event_bridge.log"
        ) as f:
            lines = f.readlines()

        # Look for recent tool detections
        recent_tools = []
        for line in reversed(lines[-100:]):  # Last 100 lines
            if "Tool detected" in line:
                recent_tools.append(line.strip())
                if len(recent_tools) >= 5:
                    break

        if recent_tools:
            print("\n🔧 Recent Tool Detections:")
            for tool in recent_tools[:5]:
                print(f"   {tool}")
        else:
            print("\n⚠️  No recent tool detections in logs")

        return len(recent_tools) > 0
    except Exception as e:
        print(f"❌ Error checking logs: {e}")
        return False


def check_sessions():
    """Check active sessions"""
    try:
        response = requests.get("http://localhost:4096/session", timeout=5)
        sessions = response.json()

        print(f"\n🖥️  Active Sessions: {len(sessions)}")

        # Check messages in each session
        total_messages = 0
        total_tools = 0

        for session in sessions[:3]:  # Check first 3 sessions
            session_id = session.get("id", "unknown")
            msg_response = requests.get(
                f"http://localhost:4096/session/{session_id}/message", timeout=5
            )
            messages = msg_response.json()
            total_messages += len(messages)

            # Count tools in messages
            for msg in messages:
                parts = msg.get("parts", [])
                for part in parts:
                    if part.get("type") == "tool_use":
                        total_tools += 1

        print(f"   Total messages: {total_messages}")
        print(f"   Tools in messages: {total_tools}")

        return total_tools > 0
    except Exception as e:
        print(f"❌ Error checking sessions: {e}")
        return False


def main():
    print("=" * 60)
    print("🔍 EVENT PIPELINE DIAGNOSTIC")
    print(f"   Time: {datetime.now().isoformat()}")
    print("=" * 60)

    # Check EventBridge
    running = check_event_bridge_status()

    if not running:
        print("\n🚨 CRITICAL: EventBridge is not running!")
        return 1

    # Check for recent tools
    has_recent_tools = check_recent_tools()

    # Check sessions
    has_tools_in_sessions = check_sessions()

    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print("=" * 60)

    if has_recent_tools:
        print("✅ Tools ARE being detected and logged")
    else:
        print("⚠️  No recent tool detections")
        print("   - Check if agents are actually using tools")
        print("   - Verify EventBridge polling is working")
        print("   - Check OpenCode API accessibility")

    if has_tools_in_sessions:
        print("✅ Tools found in session messages")
    else:
        print("⚠️  No tools found in recent session messages")

    print("\n🔧 Recommended actions:")
    if not has_recent_tools:
        print("   1. Wait 30 seconds and run this script again")
        print("   2. Check EventBridge logs: tail -f Open_ELF/logs/event_bridge.log")
        print(
            "   3. Restart EventBridge: pkill -f event_bridge.py && python3 Open_ELF/orchestrator/event_bridge.py start"
        )
    else:
        print("   ✅ Event pipeline is working!")
        print("   📊 Check dashboard at http://localhost:3001")

    return 0 if has_recent_tools else 1


if __name__ == "__main__":
    exit(main())
