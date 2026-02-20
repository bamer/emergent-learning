#!/usr/bin/env python3
"""
Test script for Open_ELF Orchestrator
"""

import sys

sys.path.insert(0, "/home/bamer/OPC_ELF/Open_ELF/orchestrator")

from orchestrator import UnifiedOrchestrator, OpenCodeClient


def test_opencode_connection():
    """Test connection to OpenCode server."""
    print("Testing OpenCode connection...")
    client = OpenCodeClient()

    if client.health_check():
        print("✅ OpenCode server is accessible")
        return True
    else:
        print("❌ OpenCode server not accessible")
        print("   Start it with: opencode serve --port 4096")
        return False


def test_orchestrator_init():
    """Test orchestrator initialization."""
    print("\nTesting orchestrator initialization...")

    try:
        orch = UnifiedOrchestrator()
        print("✅ Orchestrator created successfully")

        # Don't actually start it in test mode
        # Just verify the structure
        print(f"✅ Client initialized: {orch.client.base_url}")
        print(f"✅ Sessions dict ready: {len(orch.sessions)} sessions")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_heuristic_extraction():
    """Test heuristic extraction."""
    print("\nTesting heuristic extraction...")

    from orchestrator import HeuristicExtractor

    test_response = """
    I've analyzed the code and found several issues.
    
    [LEARNED:architecture] Always validate user input before processing
    [HEURISTIC:security] Use parameterized queries to prevent SQL injection
    [PATTERN:performance] Cache frequently accessed data to reduce DB calls
    
    The solution involves refactoring the authentication layer.
    """

    heuristics = HeuristicExtractor.extract(test_response)

    print(f"✅ Extracted {len(heuristics)} heuristics:")
    for h in heuristics:
        print(f"   - {h[:80]}...")

    return len(heuristics) == 3


def test_agent_selector():
    """Test agent auto-selection."""
    print("\nTesting agent auto-selection...")

    from orchestrator import AgentSelector

    test_cases = [
        ("Design a new API endpoint for authentication", "architect"),
        ("Investigate why the database is slow", "researcher"),
        ("Review the security of our payment system", "skeptic"),
        ("Create innovative features for the dashboard", "creative"),
        ("Decide which technology to use for the backend", "ceo"),
    ]

    all_passed = True
    for mission, expected in test_cases:
        selected = AgentSelector.select_agent(mission)
        confidence = AgentSelector.get_agent_confidence(mission, selected)
        status = "✅" if selected == expected else "❌"
        print(
            f"   {status} '{mission[:40]}...' → {selected} (confidence: {confidence:.2f})"
        )
        if selected != expected:
            all_passed = False

    return all_passed


def test_mission_analyzer():
    """Test mission analysis and swarm detection."""
    print("\nTesting mission analyzer...")

    from orchestrator import MissionAnalyzer

    # Test swarm detection
    swarm_missions = [
        "swarm: Design and implement a new feature",
        "parallel investigation of the codebase",
        "multi-agent analysis needed",
    ]

    normal_missions = [
        "Design a new API endpoint",
        "Fix the bug in the login system",
    ]

    print("   Testing swarm detection:")
    for mission in swarm_missions:
        is_swarm = MissionAnalyzer.is_swarm_mission(mission)
        status = "✅" if is_swarm else "❌"
        print(f"     {status} '{mission[:40]}...' → swarm={is_swarm}")
        if not is_swarm:
            return False

    for mission in normal_missions:
        is_swarm = MissionAnalyzer.is_swarm_mission(mission)
        status = "✅" if not is_swarm else "❌"
        print(f"     {status} '{mission[:40]}...' → swarm={is_swarm}")
        if is_swarm:
            return False

    # Test mission decomposition
    print("   Testing mission decomposition:")
    mission = "Design and implement a new authentication system"
    subtasks = MissionAnalyzer.decompose_mission(mission)
    print(f"     ✅ Decomposed into {len(subtasks)} subtasks:")
    for i, subtask in enumerate(subtasks, 1):
        print(f"        {i}. [{subtask['agent']}] {subtask['task'][:50]}...")

    return len(subtasks) >= 2


def main():
    """Run all tests."""
    print("=" * 70)
    print("Open_ELF Orchestrator Test Suite")
    print("=" * 70)

    tests = [
        ("OpenCode Connection", test_opencode_connection),
        ("Orchestrator Init", test_orchestrator_init),
        ("Heuristic Extraction", test_heuristic_extraction),
        ("Agent Auto-Selection", test_agent_selector),
        ("Mission Analyzer", test_mission_analyzer),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 70)
    print("Test Results:")
    print("=" * 70)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
