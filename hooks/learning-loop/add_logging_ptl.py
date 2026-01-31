#!/usr/bin/env python3
"""
Add logging calls to post_tool_learning.py main function
"""

import re

# Read the file
with open("post_tool_learning.py", "r") as f:
    content = f.read()

# Add logger import at the top
if "from ptl_logger import" not in content:
    # Find the last import line
    import_lines = content.split("\n")[:25]
    last_import_idx = 0
    for i, line in enumerate(import_lines):
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            last_import_idx = i

    # Insert logger import after the last import
    lines = content.split("\n")
    lines.insert(last_import_idx + 1, "")
    lines.insert(last_import_idx + 2, "# Import logger")
    lines.insert(last_import_idx + 3, "try:")
    lines.insert(
        last_import_idx + 4,
        "    from ptl_logger import log_start, log_success, log_error, log_partial, log_info",
    )
    lines.insert(last_import_idx + 5, "except ImportError:")
    lines.insert(last_import_idx + 6, "    def log_start(): pass")
    lines.insert(last_import_idx + 7, "    def log_success(msg): pass")
    lines.insert(last_import_idx + 8, "    def log_error(msg): pass")
    lines.insert(last_import_idx + 9, "    def log_partial(msg): pass")
    lines.insert(last_import_idx + 10, "    def log_info(msg): pass")

    content = "\n".join(lines)

# Add logging at the beginning of main function
if "def main():" in content and "log_start()" not in content:
    # Find main function and add logging
    main_pattern = r'def main\(\):\s*"""Main hook logic\."""'
    if re.search(main_pattern, content):
        content = re.sub(
            main_pattern,
            'def main():\n    """Main hook logic."""\n    log_start()',
            content,
        )

# Write back
with open("post_tool_learning.py", "w") as f:
    f.write(content)

print("Added logging to post_tool_learning.py")
