#!/usr/bin/env python3
"""
Add comprehensive logging to all three functions
"""


def patch_post_tool_learning():
    """Add logging to post_tool_learning.py"""
    with open("post_tool_learning.py", "r") as f:
        content = f.read()

    # Add logging calls throughout the main function
    replacements = [
        # At the very start
        (
            "hook_input = get_hook_input()",
            'hook_input = get_hook_input()\n    try:\n        from ptl_logger import log_info\n        log_info(f"Hook called with tool: {hook_input.get("tool_name", "unknown")}")\n    except:\n        pass',
        ),
        # Success at the end
        (
            "output_result({})",
            'try:\n        from ptl_logger import log_success\n        log_success("Hook completed successfully")\n    except:\n        pass\n    output_result({})',
        ),
        # Error handling
        (
            'except Exception as e:\n        sys.stderr.write(f"Warning: Failed to log session: {e}\\n")',
            'except Exception as e:\n        sys.stderr.write(f"Warning: Failed to log session: {e}\\n")\n        try:\n            from ptl_logger import log_error\n            log_error(f"Session logging failed: {e}")\n        except:\n            pass',
        ),
        # Validation success
        (
            'sys.stderr.write(f"[VALIDATION] Validated {len(heuristic_ids)} heuristics (success)\\n")',
            'sys.stderr.write(f"[VALIDATION] Validated {len(heuristic_ids)} heuristics (success)\\n")\n            try:\n                from ptl_logger import log_success\n                log_success(f"Validated {len(heuristic_ids)} heuristics")\n            except:\n                pass',
        ),
        # Failure recording
        (
            'sys.stderr.write(f"AUTO-RECORDED FAILURE: {env["FAILURE_TITLE"]}\\n")',
            'sys.stderr.write(f"AUTO-RECORDED FAILURE: {env["FAILURE_TITLE"]}\\n")\n                        try:\n                            from ptl_logger import log_info\n                            log_info(f"Auto-recorded failure: {env["FAILURE_TITLE"]}")\n                        except:\n                            pass',
        ),
    ]

    for old, new in replacements:
        if old in content and new not in content:
            content = content.replace(old, new)

    with open("post_tool_learning.py", "w") as f:
        f.write(content)
    print("✓ post_tool_learning.py patched")


def patch_record_pheromone():
    """Add logging to record_pheromone.py"""
    with open("record_pheromone.py", "r") as f:
        content = f.read()

    # Add logging at key points
    replacements = [
        (
            "def main():",
            "def main():\n    try:\n        from rp_logger import log_start, log_success, log_error, log_info\n        log_start()\n    except:\n        pass",
        ),
        (
            "if len(sys.argv) < 2:\n        return 0",
            'if len(sys.argv) < 2:\n        try:\n            from rp_logger import log_error\n            log_error("No arguments provided")\n        except:\n            pass\n        return 0',
        ),
        (
            "recorded_count += 1\n    \n    return 0",
            'recorded_count += 1\n        \n    try:\n        from rp_logger import log_success\n        log_success(f"Recorded {recorded_count} trails")\n    except:\n        pass\n    \n    return 0',
        ),
        (
            "except Exception as e:\n        # Silently fail - pheromone trails are non-critical\n        return False",
            'except Exception as e:\n        # Silently fail - pheromone trails are non-critical\n        try:\n            from rp_logger import log_error\n            log_error(f"Failed to record trail: {e}")\n        except:\n            pass\n        return False',
        ),
    ]

    for old, new in replacements:
        if old in content and new not in content:
            content = content.replace(old, new)

    with open("record_pheromone.py", "w") as f:
        f.write(content)
    print("✓ record_pheromone.py patched")


def patch_sync_golden_rules():
    """Add logging to sync-golden-rules.py"""
    with open("../post_tool_use/sync-golden-rules.py", "r") as f:
        content = f.read()

    # Add logging at key points
    replacements = [
        (
            "def run():",
            "def run():\n    try:\n        from sgr_logger import log_start, log_success, log_error, log_info\n        log_start()\n    except:\n        pass",
        ),
        (
            "if sync_golden_rules():",
            'if sync_golden_rules():\n            try:\n                from sgr_logger import log_success\n                log_success("Synced golden-rules.md to database")\n            except:\n                pass',
        ),
        (
            'print(f"[SYNC] {result}")',
            'try:\n            from sgr_logger import log_info\n            log_info(result)\n        except:\n            pass\n        print(f"[SYNC] {result}")',
        ),
        (
            'except Exception as e:\n        print(f"[WARN] Golden rules sync failed: {e}")',
            'except Exception as e:\n        print(f"[WARN] Golden rules sync failed: {e}")\n        try:\n            from sgr_logger import log_error\n            log_error(f"Golden rules sync failed: {e}")\n        except:\n            pass',
        ),
    ]

    for old, new in replacements:
        if old in content and new not in content:
            content = content.replace(old, new)

    with open("../post_tool_use/sync-golden-rules.py", "w") as f:
        f.write(content)
    print("✓ sync-golden-rules.py patched")


if __name__ == "__main__":
    patch_post_tool_learning()
    patch_record_pheromone()
    patch_sync_golden_rules()
    print("\n✅ All functions have been patched with logging!")
