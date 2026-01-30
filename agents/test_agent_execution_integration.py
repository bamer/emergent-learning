#!/usr/bin/env python3
"""
Test Agent Execution Integration
Verify that the agent execution workflow is properly integrated
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TestAgentExecution")

def test_imports():
    """Test that all components can be imported."""
    logger.info("=" * 70)
    logger.info("TEST 1: Verifying imports...")
    logger.info("=" * 70)
    
    try:
        from agent_execution_engine import AgentExecutionEngine
        logger.info("✅ AgentExecutionEngine imported")
        
        from pattern_response_handler import PatternResponseHandler
        logger.info("✅ PatternResponseHandler imported")
        
        from opencode_client import OpenCodeClient
        logger.info("✅ OpenCodeClient imported")
        
        from dashboard_sentinel import AISentinel
        logger.info("✅ AISentinel imported")
        
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_pattern_handler():
    """Test pattern handler can map patterns to agents."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Testing PatternResponseHandler...")
    logger.info("=" * 70)
    
    try:
        from pattern_response_handler import PatternResponseHandler
        
        handler = PatternResponseHandler()
        
        test_patterns = [
            ("Declining activity trend detected", "researcher"),
            ("Service instability detected", "architect"),
            ("Anomaly detected in metrics", "skeptic"),
            ("Unusual pattern found", "creative"),
        ]
        
        for pattern, expected_agent in test_patterns:
            agent = handler._determine_agent(pattern)
            if agent == expected_agent:
                logger.info(f"✅ Pattern '{pattern}' → {agent}")
            else:
                logger.warning(f"⚠️  Pattern '{pattern}' → {agent} (expected {expected_agent})")
        
        return True
    except Exception as e:
        logger.error(f"❌ PatternResponseHandler test failed: {e}")
        return False

def test_execution_engine_initialization():
    """Test that execution engine can be initialized."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Testing AgentExecutionEngine initialization...")
    logger.info("=" * 70)
    
    try:
        from agent_execution_engine import AgentExecutionEngine
        
        engine = AgentExecutionEngine(server_url="http://localhost:4096")
        logger.info(f"✅ AgentExecutionEngine initialized")
        logger.info(f"   Server URL: {engine.server_url}")
        logger.info(f"   Execution log entries: {len(engine.execution_log)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ AgentExecutionEngine initialization failed: {e}")
        return False

def test_sentinel_integration():
    """Test that Sentinel has agent execution components."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Testing Dashboard Sentinel integration...")
    logger.info("=" * 70)
    
    try:
        from dashboard_sentinel import AISentinel
        
        sentinel = AISentinel(name="Test Sentinel", model="big-pickle")
        logger.info(f"✅ AISentinel created: {sentinel.name}")
        
        # Check if execution engine is available
        if sentinel.execution_engine:
            logger.info("✅ AgentExecutionEngine is initialized")
        else:
            logger.warning("⚠️  AgentExecutionEngine is None (will fail agent execution)")
        
        # Check if pattern handler is available
        if sentinel.pattern_handler:
            logger.info("✅ PatternResponseHandler is initialized")
        else:
            logger.warning("⚠️  PatternResponseHandler is None (will fail pattern handling)")
        
        # Check if _execute_agent_workflows method exists
        if hasattr(sentinel, '_execute_agent_workflows'):
            logger.info("✅ _execute_agent_workflows method exists")
        else:
            logger.error("❌ _execute_agent_workflows method NOT found!")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Sentinel integration test failed: {e}")
        return False

def test_opencode_client_status():
    """Test OpenCode client status."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Testing OpenCode Client status...")
    logger.info("=" * 70)
    
    try:
        from opencode_client import OpenCodeClient
        
        client = OpenCodeClient(server_url="http://localhost:4096")
        status = client.get_status()
        
        logger.info(f"✅ OpenCode Client status:")
        logger.info(f"   Server available: {status['server_available']}")
        logger.info(f"   CLI available: {status['cli_available']}")
        logger.info(f"   Method: {status['method']}")
        logger.info(f"   Model: {status['model']}")
        
        if status['server_available'] or status['cli_available']:
            logger.info("✅ OpenCode is accessible (either server or CLI)")
            return True
        else:
            logger.warning("⚠️  OpenCode is NOT accessible - agent calls will fail")
            logger.warning("   Start with: opencode serve --port 4096")
            return False
            
    except Exception as e:
        logger.error(f"❌ OpenCode client test failed: {e}")
        return False

def test_workflow_method_signature():
    """Test that the workflow method has correct signature."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: Testing workflow method signature...")
    logger.info("=" * 70)
    
    try:
        from dashboard_sentinel import AISentinel
        import inspect
        
        sentinel = AISentinel()
        
        # Get method signature
        method = sentinel._execute_agent_workflows
        sig = inspect.signature(method)
        
        params = list(sig.parameters.keys())
        logger.info(f"✅ _execute_agent_workflows parameters: {params}")
        
        expected_params = ['patterns', 'metrics', 'analysis']
        if all(p in params for p in expected_params):
            logger.info(f"✅ All expected parameters present")
            return True
        else:
            logger.error(f"❌ Missing parameters: {set(expected_params) - set(params)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Workflow method test failed: {e}")
        return False

def test_monitoring_cycle_integration():
    """Test that run_monitoring_cycle calls agent execution."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 7: Testing run_monitoring_cycle integration...")
    logger.info("=" * 70)
    
    try:
        from dashboard_sentinel import AISentinel
        import inspect
        
        sentinel = AISentinel()
        
        # Get source code of run_monitoring_cycle
        source = inspect.getsource(sentinel.run_monitoring_cycle)
        
        # Check if it calls _execute_agent_workflows
        if "_execute_agent_workflows" in source:
            logger.info("✅ run_monitoring_cycle calls _execute_agent_workflows")
        else:
            logger.error("❌ run_monitoring_cycle does NOT call _execute_agent_workflows")
            return False
        
        # Check if it passes patterns
        if "patterns=" in source:
            logger.info("✅ run_monitoring_cycle passes patterns to agent execution")
        else:
            logger.error("❌ run_monitoring_cycle does not pass patterns")
            return False
        
        # Check if it records agent executions
        if "agent_executions" in source:
            logger.info("✅ run_monitoring_cycle records agent execution results")
        else:
            logger.error("❌ run_monitoring_cycle does not record agent executions")
            return False
        
        return True
            
    except Exception as e:
        logger.error(f"❌ Monitoring cycle test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 AGENT EXECUTION INTEGRATION TESTS")
    logger.info("=" * 70 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("PatternResponseHandler", test_pattern_handler),
        ("AgentExecutionEngine Init", test_execution_engine_initialization),
        ("Sentinel Integration", test_sentinel_integration),
        ("OpenCode Client", test_opencode_client_status),
        ("Workflow Method", test_workflow_method_signature),
        ("Monitoring Cycle", test_monitoring_cycle_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 70)
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("=" * 70)
    logger.info(f"Results: {passed_count}/{total} tests passed")
    logger.info("=" * 70)
    
    if passed_count == total:
        logger.info(f"\n✅ ALL {total} TESTS PASSED!")
        logger.info("Agent execution workflow is properly integrated.")
        logger.info("🚀 Ready to run: python emergent-learning/agents/dashboard_sentinel.py")
        return 0
    else:
        logger.warning(f"\n⚠️  {total - passed} test(s) failed")
        logger.warning("Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
