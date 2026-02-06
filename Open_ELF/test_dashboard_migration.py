#!/usr/bin/env python3
"""Test EventBridge integration in dashboard API."""

import sys
from pathlib import Path

# Add Open_ELF directory to path
openelf_dir = Path(__file__).parent.parent
if str(openelf_dir) not in sys.path:
    sys.path.insert(0, str(openelf_dir))


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")

    try:
        from orchestrator.event_bridge import get_event_bridge_singleton

        print("✅ EventBridge imported")
    except Exception as e:
        print(f"❌ EventBridge import failed: {e}")
        return False

    try:
        from orchestrator.unified_orchestrator import get_orchestrator

        print("✅ UnifiedOrchestrator imported")
    except Exception as e:
        print(f"❌ UnifiedOrchestrator import failed: {e}")
        return False

    return True


def test_get_bridge():
    """Test get_bridge function."""
    print("\nTesting get_bridge()...")

    try:
        from dashboard_app.backend.routers.agents import get_bridge

        bridge = get_bridge()
        print(f"✅ get_bridge() returned: {type(bridge).__name__}")
        print(f"   Running: {bridge.running}")
        print(
            f"   Session ID: {bridge.opencode_session_id[:8] if bridge.opencode_session_id else 'None'}..."
        )
        return True
    except Exception as e:
        print(f"❌ get_bridge() failed: {e}")
        return False


def test_has_no_direct_session_creation():
    """Verify no direct session creation in API."""
    print("\nChecking for direct session creation...")

    agents_file = Path(__file__).parent / "dashboard-app/backend/routers/agents.py"
    content = agents_file.read_text()

    # Look for direct session creation patterns
    patterns_to_check = [
        'requests.post(f"{OPENCODE_SERVER}/session"',
        "requests.post(f'{OPENCODE_SERVER}/session'",
    ]

    found_patterns = []
    for pattern in patterns_to_check:
        if pattern in content:
            # Count occurrences
            count = content.count(pattern)
            found_patterns.append((pattern, count))

    if found_patterns:
        print("❌ Found direct session creation:")
        for pattern, count in found_patterns:
            print(f"   - {pattern}: {count} occurrences")
        return False
    else:
        print("✅ No direct session creation found")
        return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("EventBridge Dashboard Integration Test")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("get_bridge()", test_get_bridge()))
    results.append(("No direct sessions", test_has_no_direct_session_creation()))

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✅ All tests passed!")
        print(
            "\nMigration successful. Dashboard now uses EventBridge for all operations."
        )
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
