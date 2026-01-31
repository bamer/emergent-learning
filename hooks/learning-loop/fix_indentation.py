#!/usr/bin/env python3
"""
Fix indentation in post_tool_learning.py
"""

with open("post_tool_learning.py", "r") as f:
    lines = f.readlines()

# Fix the indentation issue around line 1138
for i, line in enumerate(lines):
    if "try:" in line and i > 1130 and i < 1145:
        # Make sure try block is properly indented
        if not line.startswith("        try:"):
            lines[i] = "        try:\n"
    elif "from ptl_logger import log_success" in line:
        # Fix indentation of import
        if not line.startswith("            from ptl_logger"):
            lines[i] = "            from ptl_logger import log_success\n"
    elif 'log_success("Hook completed successfully")' in line:
        # Fix indentation of function call
        if not line.startswith("            log_success"):
            lines[i] = '            log_success("Hook completed successfully")\n'
    elif "except:" in line and i > 1135 and i < 1145:
        # Fix except indentation
        if not line.startswith("        except:"):
            lines[i] = "        except:\n"
    elif "pass" in line and i > 1135 and i < 1145:
        # Fix pass indentation
        if not line.startswith("            pass"):
            lines[i] = "            pass\n"

with open("post_tool_learning.py", "w") as f:
    f.writelines(lines)

print("✓ Fixed indentation in post_tool_learning.py")
