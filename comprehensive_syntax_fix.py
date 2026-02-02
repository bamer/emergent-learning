#!/usr/bin/env python3
"""
Comprehensive syntax fix for dashboard backend files
This script will fix critical syntax errors systematically
"""

import os
import re
import subprocess


def fix_file_syntax(filepath):
    """Fix syntax errors in a single file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix cursor\1 errors
        content = content.replace("cursor\\1", "cursor.fetchall()")

        # Fix incomplete list comprehensions that got split across lines
        content = re.sub(
            r"for r in cursor\.fetchall\(\)\s*$",
            "for r in cursor.fetchall()]",
            content,
            flags=re.MULTILINE,
        )

        # Fix dangling cursor.fetchall() calls
        content = re.sub(
            r"cursor\.fetchall\(\)\s*(\n|$)", "cursor.fetchall()]\\1", content
        )

        # Fix specific patterns that break syntax
        content = re.sub(
            r"\[dict_from_row\(r\) for r in cursor\.fetchall\(\)\s*\n",
            "[dict_from_row(r) for r in cursor.fetchall()]\\n",
            content,
        )

        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed: {os.path.basename(filepath)}")
            return True
        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def test_python_syntax(filepath):
    """Test if a Python file has valid syntax"""
    try:
        result = subprocess.run(
            ["python", "-m", "py_compile", filepath], capture_output=True, text=True
        )
        return result.returncode == 0
    except:
        return False


def fix_dashboard_syntax():
    """Fix all syntax errors in dashboard backend"""

    backend_dir = "/home/bamer/.opencode/emergent-learning/dashboard-app/backend"

    # Get all Python files (excluding venv)
    python_files = []
    for root, dirs, files in os.walk(backend_dir):
        if "venv" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files to check")

    fixed_count = 0
    syntax_errors = []

    for filepath in python_files:
        # Try to fix syntax issues
        if fix_file_syntax(filepath):
            fixed_count += 1

        # Test syntax
        if not test_python_syntax(filepath):
            syntax_errors.append(filepath)

    print(f"\\nFixed {fixed_count} files")
    print(f"Syntax errors remaining in {len(syntax_errors)} files:")

    for filepath in syntax_errors[:5]:  # Show first 5 errors
        print(f"  - {filepath}")

    return len(syntax_errors) == 0


if __name__ == "__main__":
    success = fix_dashboard_syntax()
    print(f"\\nSyntax check: {'PASSED' if success else 'FAILED'}")
