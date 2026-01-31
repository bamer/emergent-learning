#!/usr/bin/env python3
"""
Minimal fix for record_pheromone.py to handle dict input
"""


def fix_dict_input():
    """Fix extract_file_paths to handle dict input from hooks"""
    with open("record_pheromone.py", "r") as f:
        content = f.read()

    # Replace the function to handle dict input
    old_function = '''def extract_file_paths(tool_name: str, tool_input: str) -> list:
    """
    Extract file paths from tool input.
    
    Different tools have different input formats:
    - Read: file path directly
    - Grep: --path followed by path, or pattern and path
    - Bash: might contain file operations (cat, ls, etc.)
    - edit_file/create_file: path parameter
    """
    paths = set()
    
    if tool_name in ['Read', 'create_file', 'edit_file']:
        # First argument is usually path
        parts = tool_input.strip().split()
        if parts:
            path_str = parts[0]
            if path_str.startswith('/') or path_str.startswith('.'):
                paths.add(path_str)
    
    elif tool_name == 'Grep':
        # Look for --path parameter
        if '--path' in tool_input:
            match = re.search(r'--path\s+([^\s]+)', tool_input)
            if match:
                paths.add(match.group(1))
    
    elif tool_name == 'Bash':
        # Extract file paths from common commands
        # cat, ls, find, grep, rm, touch, mv, cp, etc.
        patterns = [
            r'\b(?:cat|ls|find|grep|rm|touch|mv|cp)\s+([^\s|;>]+)',
            r'(?:^|\s)(/[^\s|;>]+)',  # Absolute paths
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, tool_input)
            for match in matches:
                path_str = match.group(1) if match.lastindex else match.group(0)
                if path_str and not path_str in ['|', ';', '>']:
                    paths.add(path_str)
    
    return list(paths)'''

    new_function = '''def extract_file_paths(tool_name: str, tool_input) -> list:
    """
    Extract file paths from tool input.
    
    Handle both dict input (from hooks) and string input (legacy).
    """
    paths = set()
    
    # Handle dict input (from ELF hooks)
    if hasattr(tool_input, 'get'):
        if tool_name in ['Read', 'Edit', 'Write', 'create_file', 'edit_file']:
            # Extract file_path from dict
            file_path = tool_input.get('file_path') or tool_input.get('path', '')
            if file_path:
                paths.add(file_path)
        
        elif tool_name == 'Grep':
            # Extract path from dict
            path = tool_input.get('path', '')
            if path:
                paths.add(path)
            # Also check in pattern parameter
            pattern = tool_input.get('pattern', '')
            if '/' in pattern:  # Unix paths in pattern
                paths.add(pattern)
        
        elif tool_name == 'Bash':
            # Extract from command string
            command = tool_input.get('command', '')
            # cat, ls, find, grep, rm, touch, mv, cp, etc.
            bash_patterns = [
                r'\\b(?:cat|ls|find|grep|rm|touch|mv|cp)\\s+([^\\s|;>]+)',
                r'(?:^|\\s)(/[^\\s|;>]+)',  # Absolute paths
            ]
            for bash_pattern in bash_patterns:
                matches = re.finditer(bash_pattern, command)
                for match in matches:
                    path_str = match.group(1) if match.lastindex else match.group(0)
                    if path_str and not path_str in ['|', ';', '>']:
                        paths.add(path_str)
    
    # Handle string input (legacy/direct calls)
    elif isinstance(tool_input, str):
        if tool_name in ['Read', 'create_file', 'edit_file']:
            # First argument is usually path
            parts = tool_input.strip().split()
            if parts:
                path_str = parts[0]
                if path_str.startswith('/') or path_str.startswith('.'):
                    paths.add(path_str)
        
        elif tool_name == 'Grep':
            # Look for --path parameter
            if '--path' in tool_input:
                match = re.search(r'--path\\s+([^\\s]+)', tool_input)
                if match:
                    paths.add(match.group(1))
        
        elif tool_name == 'Bash':
            # Extract file paths from common commands
            # cat, ls, find, grep, rm, touch, mv, cp, etc.
            patterns = [
                r'\\b(?:cat|ls|find|grep|rm|touch|mv|cp)\\s+([^\\s|;>]+)',
                r'(?:^|\\s)(/[^\\s|;>]+)',  # Absolute paths
            ]
            for pattern in patterns:
                matches = re.finditer(pattern, tool_input)
                for match in matches:
                    path_str = match.group(1) if match.lastindex else match.group(0)
                    if path_str and not path_str in ['|', ';', '>']:
                        paths.add(path_str)
    
    return list(paths)'''

    content = content.replace(old_function, new_function)

    with open("record_pheromone.py", "w") as f:
        f.write(content)

    print("✅ Fixed extract_file_paths to handle dict input")


if __name__ == "__main__":
    fix_dict_input()
