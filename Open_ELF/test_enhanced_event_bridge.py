#!/usr/bin/env python3
"""
Test Script for Enhanced Event Bridge
=====================================

Tests the enhanced event bridge functionality and orchestrator API.
"""

import asyncio
import sys
from pathlib import Path

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent))

from core.central_orchestrator import (
    ask_orchestrator,
    OrchestratorRequest,
    OrchestratorResponse,
    initialize_central_orchestrator,
    get_central_orchestrator,
)
from core.openelf_logging import setup_logging, get_logger

# Setup logging
setup_logging("test_enhanced_event_bridge", level="INFO")
logger = get_logger("test_enhanced_event_bridge")


async def test_basic_orchestrator():
    """Test basic orchestrator functionality."""
    logger.info("🧪 Testing basic orchestrator functionality...")

    # Initialize orchestrator
    await initialize_central_orchestrator()

    # Test health check
    response = await ask_orchestrator(
        component="test_component",
        request_type="health_check",
        data={"component": "database"},
    )

    logger.info(f"✅ Health check response: {response.response_type}")
    logger.info(f"   Status: {response.data.get('status', 'unknown')}")
    logger.info(f"   Confidence: {response.confidence}")

    # Test mission submission
    response = await ask_orchestrator(
        component="test_component",
        request_type="mission_submission",
        data={
            "agent_type": "researcher",
            "mission": "Test mission for enhanced event bridge",
        },
    )

    logger.info(f"✅ Mission submission response: {response.response_type}")
    if response.response_type == "mission_accepted":
        logger.info(f"   Mission ID: {response.data.get('mission_id', 'unknown')}")

    # Test coordination
    response = await ask_orchestrator(
        component="test_component",
        request_type="coordination",
        data={"components": ["database", "filesystem"], "type": "test_coordination"},
    )

    logger.info(f"✅ Coordination response: {response.response_type}")
    logger.info(f"   Coordinated: {response.data.get('coordinated', False)}")

    # Test decision making
    response = await ask_orchestrator(
        component="test_component",
        request_type="decision",
        data={
            "context": {"test": "simple_decision"},
            "options": ["option1", "option2", "option3"],
        },
    )

    logger.info(f"✅ Decision response: {response.response_type}")
    logger.info(f"   Decision: {response.data.get('decision', 'unknown')}")

    return True


async def test_error_handling():
    """Test orchestrator error handling."""
    logger.info("🧪 Testing error handling...")

    # Test unknown request type
    response = await ask_orchestrator(
        component="test_component",
        request_type="unknown_type",
        data={"test": "error_handling"},
    )

    logger.info(f"✅ Error handling response: {response.response_type}")
    logger.info(f"   Error: {response.data.get('error', 'no_error')}")

    return True


async def test_performance():
    """Test orchestrator performance with multiple requests."""
    logger.info("🧪 Testing performance with multiple requests...")

    import time

    start_time = time.time()

    # Create multiple concurrent requests
    tasks = []
    for i in range(5):
        task = ask_orchestrator(
            component=f"test_component_{i}",
            request_type="health_check",
            data={"component": f"test_{i}"},
        )
        tasks.append(task)

    # Execute concurrently
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    duration = end_time - start_time

    successful_responses = 0
    for response in responses:
        if isinstance(response, OrchestratorResponse):
            successful_responses += 1

    logger.info(f"✅ Performance test completed")
    logger.info(f"   Requests: {len(tasks)}")
    logger.info(f"   Successful: {successful_responses}")
    logger.info(f"   Duration: {duration:.2f} seconds")
    logger.info(f"   Avg time per request: {duration / len(tasks):.2f} seconds")

    return successful_responses == len(tasks)


async def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("🧪 Enhanced Event Bridge Test Suite")
    logger.info("=" * 60)

    tests = [
        ("Basic Functionality", test_basic_orchestrator),
        ("Error Handling", test_error_handling),
        ("Performance", test_performance),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            logger.info(f"\n📋 Running test: {test_name}")
            result = await test_func()
            results[test_name] = result
            logger.info(f"✅ {test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"   {test_name}: {status}")

    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("✅ All tests passed! Enhanced Event Bridge is ready.")
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Review logs for details.")

    return passed == total


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())

    # Exit with appropriate code
    sys.exit(0 if success else 1)
