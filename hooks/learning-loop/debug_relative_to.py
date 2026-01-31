#!/usr/bin/env python3
"""
Debug file_path_obj.relative_to() issue
"""

from pathlib import Path

# Test paths
test_paths = [
    "/home/bamer/.opencode/emergent-learning/README.md",
    "./README.md",
    "README.md",
    "/home/bamer/.opencode/emergent-learning/hooks/learning-loop/post_tool_learning.py",
]

elf_home = Path.home() / ".opencode" / "emergent-learning"

print(f"ELF home: {elf_home}")
print()

for test_path in test_paths:
    file_path_obj = Path(test_path).expanduser().resolve()
    print(f"Testing: {file_path_obj}")

    try:
        relative = file_path_obj.relative_to(elf_home)
        print(f"  -> Relative: {relative}")
        print(f"  -> IS IN ELF: ✅")
    except ValueError as e:
        print(f"  -> ValueError: {e}")
        print(f"  -> NOT IN ELF: ❌")
    print()
