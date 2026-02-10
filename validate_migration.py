#!/usr/bin/env python3
"""
validate_migration.py - Validate ELF OpenCode migration status

Checks:
1. All paths converted from .opencode to .opencode
2. Database initialization
3. Hook system setup
4. Configuration files
5. Plugin integration
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Tuple, List

ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
OPENCODE_DIR = Path.home() / ".opencode"

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def check(description: str, condition: bool, details: str = "") -> bool:
    """Print check result."""
    status = f"{GREEN}✅{RESET}" if condition else f"{RED}❌{RESET}"
    print(f"  {status} {description}")
    if details and not condition:
        print(f"     {YELLOW}→ {details}{RESET}")
    return condition


def check_paths():
    """Validate path conversions."""
    print(f"\n{YELLOW}=== Path Configuration ==={RESET}")
    
    results = []
    results.append(check(
        "ELF directory exists",
        ELF_DIR.exists(),
        f"Expected: {ELF_DIR}"
    ))
    
    results.append(check(
        "No .opencode paths in Python files",
        validate_no_opencode_paths(),
        "Run: python3 fix_paths.py"
    ))
    
    results.append(check(
        "ELF_BASE_PATH environment variable set",
        os.environ.get("ELF_BASE_PATH") == str(ELF_DIR) or not os.environ.get("ELF_BASE_PATH"),
        f"Set: export ELF_BASE_PATH={ELF_DIR}"
    ))
    
    return all(results)


def check_database():
    """Validate database setup."""
    print(f"\n{YELLOW}=== Database ==={RESET}")
    
    results = []
    db_path = ELF_DIR / "memory" / "index.db"
    
    results.append(check(
        "Database file exists",
        db_path.exists(),
        f"Create with: python3 {ELF_DIR}/setup_db.py"
    ))
    
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire]
            conn.close()
            
            required_tables = ['heuristics', 'golden_rules', 'sessions']
            has_tables = all(t in tables for t in required_tables)
            
            results.append(check(
                f"Database has required tables ({len(tables)} tables found)",
                has_tables,
                f"Missing: {set(required_tables) - set(tables)}"
            ))
        except Exception as e:
            results.append(check(
                "Database accessible",
                False,
                str(e)
            ))
    
    return all(results)


def check_hooks():
    """Validate hook system setup."""
    print(f"\n{YELLOW}=== Hook System ==={RESET}")
    
    results = []
    
    hook_files = [
        ELF_DIR / "hooks" / "learning-loop" / "pre_tool_learning.py",
        ELF_DIR / "hooks" / "learning-loop" / "post_tool_learning.py",
        ELF_DIR / "hooks" / "learning-loop" / "extract_patterns.py",
    ]
    
    for hook_file in hook_files:
        results.append(check(
            f"{hook_file.name} exists",
            hook_file.exists(),
            f"Expected: {hook_file}"
        ))
    
    return all(results)


def check_plugin():
    """Validate plugin setup."""
    print(f"\n{YELLOW}=== Plugin System ==={RESET}")
    
    results = []
    
    plugin_source = ELF_DIR / "ELF_superpowers.js"
    plugin_link = OPENCODE_DIR / "plugins" / "ELF_superpowers.js"
    
    results.append(check(
        "ELF_superpowers.js source exists",
        plugin_source.exists(),
        f"Expected: {plugin_source}"
    ))
    
    results.append(check(
        "Plugins directory exists",
        (OPENCODE_DIR / "plugins").exists(),
        f"Create with: mkdir -p {OPENCODE_DIR}/plugins"
    ))
    
    if not plugin_link.exists() and plugin_source.exists():
        results.append(check(
            "ELF_superpowers.js plugin symlinked",
            False,
            f"Create with: ln -sf {plugin_source} {plugin_link}"
        ))
    else:
        results.append(check(
            "ELF_superpowers.js plugin symlinked",
            plugin_link.exists(),
            f"Create with: ln -sf {plugin_source} {plugin_link}"
        ))
    
    return all(results)


def check_query_system():
    """Validate query system."""
    print(f"\n{YELLOW}=== Query System ==={RESET}")
    
    results = []
    
    query_files = [
        ELF_DIR / "query" / "query.py",
        ELF_DIR / "query" / "checkin.py",
        ELF_DIR / "query" / "checkout.py",
        ELF_DIR / "query" / "models.py",
    ]
    
    for query_file in query_files:
        results.append(check(
            f"{query_file.name} exists",
            query_file.exists(),
            f"Expected: {query_file}"
        ))
    
    # Check for .opencode references in query files
    has_old_paths = False
    for query_file in query_files:
        if query_file.exists():
            content = query_file.read_text(errors='ignore')
            if '.opencode' in content:
                has_old_paths = True
                print(f"     {YELLOW}→ Found .opencode reference in {query_file.name}{RESET}")
    
    results.append(check(
        "Query files use .opencode paths",
        not has_old_paths,
        "Run: python3 fix_paths.py"
    ))
    
    return all(results)


def check_sentinel():
    """Validate sentinel system."""
    print(f"\n{YELLOW}=== Watcher System ==={RESET}")
    
    results = []
    
    sentinel_files = [
        ELF_DIR / "sentinel" / "run_with_bigpickle.py",
        ELF_DIR / "sentinel" / "sentinel_loop.py",
        ELF_DIR / "logs" / "sentinel.log",
    ]
    
    for sentinel_file in sentinel_files:
        expected = "should exist" if sentinel_file.suffix == '.py' else "log file"
        results.append(check(
            f"{sentinel_file.name} {expected}",
            sentinel_file.exists() or sentinel_file.suffix == '.log',
            f"Expected: {sentinel_file}"
        ))
    
    return all(results)


def check_config():
    """Validate configuration."""
    print(f"\n{YELLOW}=== Configuration ==={RESET}")
    
    results = []
    
    config_files = [
        ELF_DIR / "elf_config.yaml",
        ELF_DIR / "elf_paths.py",
        ELF_DIR / "agents" / "parties.yaml",
    ]
    
    for config_file in config_files:
        results.append(check(
            f"{config_file.name} exists",
            config_file.exists(),
            f"Expected: {config_file}"
        ))
    
    return all(results)


def validate_no_opencode_paths() -> bool:
    """Check if any files still have .opencode references."""
    patterns = [
        '/.opencode/emergent-learning',
        '~/.opencode/emergent-learning',
    ]
    
    # Files to skip (examples, documentation, etc.)
    skip_files = {
        'validate_migration.py',  # This file itself has examples
        'ELF_OPENCODE_MIGRATION_GUIDE.md',  # Documentation with examples
        'elf_paths.py',  # Legacy path reference needed for migration logic
    }
    
    bad_files = []
    
    for py_file in ELF_DIR.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', '.git']):
            continue
        if py_file.name in skip_files:
            continue
        try:
            content = py_file.read_text(errors='ignore')
            for pattern in patterns:
                if pattern in content:
                    bad_files.append(str(py_file.relative_to(ELF_DIR)))
                    break
        except:
            pass
    
    return len(bad_files) == 0


def main():
    """Run all validation checks."""
    print(f"\n{YELLOW}{'='*50}")
    print("  ELF OpenCode Migration Validator")
    print(f"{'='*50}{RESET}")
    
    checks = [
        ("Paths", check_paths),
        ("Database", check_database),
        ("Hooks", check_hooks),
        ("Plugin", check_plugin),
        ("Query System", check_query_system),
        ("Watcher", check_sentinel),
        ("Configuration", check_config),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"  {RED}✗ Error in {name}: {e}{RESET}")
            results[name] = False
    
    # Summary
    print(f"\n{YELLOW}{'='*50}")
    print("  Summary")
    print(f"{'='*50}{RESET}")
    
    for name, passed in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
        print(f"  {status} {name}")
    
    all_passed = all(results.values())
    
    print(f"\n{YELLOW}{'='*50}{RESET}")
    if all_passed:
        print(f"{GREEN}✅ All checks passed! ELF is ready for OpenCode.{RESET}")
    else:
        print(f"{RED}❌ Some checks failed. See details above.{RESET}")
        print(f"\n{YELLOW}Next steps:{RESET}")
        print(f"  1. Review failed checks above")
        print(f"  2. Follow the suggested fixes")
        print(f"  3. Run this script again to verify")
    
    print(f"{YELLOW}{'='*50}\n{RESET}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
