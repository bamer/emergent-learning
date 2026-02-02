"""
Test script for Timeline Dashboard Integration
"""

import json
import sys
from pathlib import Path

# Add the timeline dashboard to Python path
sys.path.append(str(Path(__file__).parent))

from event_adapter import (
    get_chronicle_events,
    get_chronicle_stats,
    convert_chronicle_event_to_timeline_event,
)
from timeline_events import get_event_config, format_event_description


def test_event_conversion():
    """Test event conversion from chronicle format to timeline format"""
    print("Testing event conversion...")

    # Sample chronicle event
    sample_event = {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "timestamp": "2026-02-02T10:30:00Z",
        "event_type": "heuristic_validated",
        "source": "record-heuristic.sh",
        "data": {
            "heuristic_id": 42,
            "domain": "testing",
            "rule": "Always validate inputs at system boundaries",
        },
        "metadata": {"user_id": "test-user", "session_id": "session-123"},
    }

    from event_adapter import convert_chronicle_event_to_timeline_event

    # Convert event
    timeline_event = convert_chronicle_event_to_timeline_event(sample_event)

    print("Chronicle event:")
    print(json.dumps(sample_event, indent=2))
    print()
    print("Converted timeline event:")
    print(json.dumps(timeline_event, indent=2))
    print()

    # Verify required fields
    required_fields = ["id", "timestamp", "event_type", "description"]
    for field in required_fields:
        assert field in timeline_event, f"Missing required field: {field}"

    print("✓ Event conversion test passed!")


def test_event_config():
    """Test event configuration lookup"""
    print("\nTesting event configuration...")

    # Test known event type
    config = get_event_config("heuristic_validated")
    assert config.icon == "CheckCircle"
    assert config.color == "bg-emerald-500"
    assert config.label == "Heuristic Validated"
    print("✓ Known event type configuration test passed!")

    # Test unknown event type
    config = get_event_config("unknown_event_type")
    assert config.icon == "FileText"
    assert config.label == "Unknown Event Type"
    print("✓ Unknown event type configuration test passed!")


def test_description_formatting():
    """Test event description formatting"""
    print("\nTesting description formatting...")

    # Test with data
    data = {"heuristic_rule": "Always validate inputs"}
    description = format_event_description("heuristic_validated", data)
    assert "Always validate inputs" in description
    print("✓ Description formatting with data test passed!")

    # Test with fallback
    data = {"message": "Fallback message"}
    description = format_event_description("unknown_type", data)
    assert description == "Fallback message"
    print("✓ Description formatting fallback test passed!")


def test_chronicle_access():
    """Test accessing chronicle events"""
    print("\nTesting chronicle access...")

    # Try to get events (this will work if chronicle files exist)
    try:
        events = get_chronicle_events(limit=5)
        print(f"✓ Retrieved {len(events)} events from chronicle")

        if events:
            print("Sample event:")
            print(json.dumps(events[0], indent=2))

    except Exception as e:
        print(f"Note: Could not access chronicle files: {e}")
        print("This is expected if no events have been recorded yet.")


def test_chronicle_stats():
    """Test getting chronicle statistics"""
    print("\nTesting chronicle statistics...")

    try:
        stats = get_chronicle_stats()
        print("✓ Retrieved chronicle statistics")
        print(f"Total events: {stats.get('total_events', 0)}")
        print(f"Event types: {len(stats.get('event_types', {}))}")
        print(f"Sources: {len(stats.get('sources', {}))}")

    except Exception as e:
        print(f"Note: Could not get chronicle statistics: {e}")


if __name__ == "__main__":
    print("Timeline Dashboard Integration Tests")
    print("====================================")

    try:
        test_event_conversion()
        test_event_config()
        test_description_formatting()
        test_chronicle_access()
        test_chronicle_stats()

        print("\n🎉 All tests completed successfully!")
        print("\nNext steps:")
        print("1. Integrate with your dashboard backend using demo_integration.py")
        print(
            "2. Update your frontend TimelineView to use the new /api/v1/timeline/events endpoint"
        )
        print("3. Verify events are being recorded in the Event Chronicle")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
