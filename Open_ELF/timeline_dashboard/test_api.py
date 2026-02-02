#!/usr/bin/env python3
"""
Test script for Timeline Dashboard API
"""

import sys
from pathlib import Path

# Add Open_ELF to Python path
open_elf_path = Path(__file__).parent.parent
sys.path.insert(0, str(open_elf_path))


def test_timeline_api():
    """Test the timeline API endpoints"""
    try:
        # Import the timeline API router
        from timeline_dashboard.timeline_api import router

        print("✅ Timeline API router imported successfully!")
        print(f"✅ Router has {len(router.routes)} routes")

        # Print route details
        for route in router.routes:
            print(f"  - {route.methods} {route.path}")

        return True

    except ImportError as e:
        print(f"❌ Failed to import timeline API: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_event_adapter():
    """Test the event adapter functionality"""
    try:
        from timeline_dashboard.event_adapter import (
            get_chronicle_events,
            get_chronicle_stats,
        )

        print("✅ Event adapter imported successfully!")

        # Test getting events
        events = get_chronicle_events(limit=5)
        print(f"✅ Retrieved {len(events)} events from chronicle")

        # Test getting stats
        stats = get_chronicle_stats()
        print(f"✅ Retrieved chronicle stats:")
        print(f"  - Total events: {stats.get('total_events', 0)}")
        print(f"  - Event types: {len(stats.get('event_types', {}))}")
        print(f"  - Sources: {len(stats.get('sources', {}))}")

        return True

    except ImportError as e:
        print(f"❌ Failed to import event adapter: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_event_definitions():
    """Test the event definitions"""
    try:
        from timeline_dashboard.timeline_events import (
            get_event_config,
            format_event_description,
        )

        print("✅ Timeline events imported successfully!")

        # Test getting event config
        config = get_event_config("heuristic_validated")
        print(f"✅ Event config for 'heuristic_validated':")
        print(f"  - Icon: {config.icon}")
        print(f"  - Color: {config.color}")
        print(f"  - Label: {config.label}")

        # Test formatting description
        data = {"heuristic_rule": "Always validate inputs"}
        description = format_event_description("heuristic_validated", data)
        print(f"✅ Formatted description: {description}")

        return True

    except ImportError as e:
        print(f"❌ Failed to import timeline events: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Timeline Dashboard API Test")
    print("=" * 40)

    success = True

    print("\n1. Testing Timeline API...")
    success &= test_timeline_api()

    print("\n2. Testing Event Adapter...")
    success &= test_event_adapter()

    print("\n3. Testing Event Definitions...")
    success &= test_event_definitions()

    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! Timeline Dashboard API is ready.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
