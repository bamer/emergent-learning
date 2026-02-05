#!/usr/bin/env python3
"""
Test script for Open_ELF core modules
"""

import sys
from pathlib import Path

# Add core module to path
sys.path.insert(0, str(Path(__file__).parent))

from database import DatabaseManager, get_connection, execute_query
from openelf_logging import setup_logging, get_logger, structured_log
from config import get_config, get, set


def test_database():
    """Test database module."""
    print("Testing database module...")

    # Test DatabaseManager
    db_path = Path("/tmp/test_db.db")
    db_manager = DatabaseManager(db_path)

    # Test connection
    conn = db_manager.get_connection()
    print(f"✓ Database connection established: {db_path}")

    # Test query execution
    results = db_manager.execute_query("SELECT 1 as test_value")
    print(f"✓ Query executed successfully: {results}")

    # Test global functions
    conn2 = get_connection(db_path)
    print(f"✓ Global get_connection works")

    results2 = execute_query("SELECT 2 as test_value", db_path=db_path)
    print(f"✓ Global execute_query works: {results2}")

    # Cleanup
    db_manager.close_connections()
    print("✓ Database module tests passed\n")


def test_logging():
    """Test logging module."""
    print("Testing logging module...")

    # Test setup_logging
    logger = setup_logging("test_component")
    logger.info("Test info message")
    logger.debug("Test debug message")
    print("✓ Basic logging works")

    # Test get_logger
    logger2 = get_logger("test_component")
    logger2.warning("Test warning message")
    print("✓ get_logger works")

    # Test structured_log
    structured_log(
        "INFO", "test_structured", "Structured test", user_id=123, action="test"
    )
    print("✓ Structured logging works")

    print("✓ Logging module tests passed\n")


def test_config():
    """Test configuration module."""
    print("Testing configuration module...")

    # Test get_config
    cfg = get_config()
    db_path = cfg.get("database.path")
    print(f"✓ Default database path: {db_path}")

    # Test get function
    log_level = get("logging.level")
    print(f"✓ Default logging level: {log_level}")

    # Test set function
    set("test.setting", "test_value")
    test_value = get("test.setting")
    print(f"✓ Set/get works: {test_value}")

    # Test component configuration
    cfg.add_component("test_component", {"setting1": "value1", "setting2": "value2"})
    comp_setting = cfg["test_component"]["setting1"]
    print(f"✓ Component configuration works: {comp_setting}")

    print("✓ Configuration module tests passed\n")


def main():
    """Run all tests."""
    print("=== Open_ELF Core Modules Test ===\n")

    try:
        test_database()
        test_logging()
        test_config()

        print("✅ All tests passed successfully!")
        print("\nThe core modules are ready for integration into Open_ELF components.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
