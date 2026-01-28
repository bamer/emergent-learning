#!/usr/bin/env python3
"""
fix_paths.py - Convert all hardcoded ~/.claude paths to ~/.opencode paths

Fixes:
  1. Hardcoded path strings in Python files
  2. Path references in documentation
  3. Environment variable defaults
  4. Database path references
  5. Logging and output paths
"""

import os
import re
import sys
from pathlib import Path
from typing import Tuple, List

# Configuration
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
SCRIPT_DIR = Path(__file__).parent

# Patterns to replace
PATH_REPLACEMENTS = [
    # Main path replacements
    (r'Path\.home\(\)\s*/\s*"\.claude"\s*/\s*"emergent-learning"', 
     'Path.home() / ".opencode" / "emergent-learning"'),
    (r"Path\.home\(\)\s*/\s*'\.claude'\s*/\s*'emergent-learning'", 
     "Path.home() / '.opencode' / 'emergent-learning'"),
    
    # String path replacements
    (r'/home/([^/]+)/\.claude/emergent-learning', r'/home/\1/.opencode/emergent-learning'),
    (r'~/.opencode/emergent-learning', '~/.opencode/emergent-learning'),
    (r'"~/.opencode/emergent-learning"', '"~/.opencode/emergent-learning"'),
    (r"'~/.opencode/emergent-learning'", "'~/.opencode/emergent-learning'"),
    
    # Legacy base path
    (r'_LEGACY_BASE = Path\.home\(\) / "\.claude" / "emergent-learning"', 
     '_LEGACY_BASE = Path.home() / ".opencode" / "emergent-learning"  # Legacy only'),
    
    # Database paths
    (r'\.claude/emergent-learning/memory/index\.db', '.opencode/emergent-learning/memory/index.db'),
    
    # Query paths
    (r'\.opencode/emergent-learning/query', '.opencode/emergent-learning/query'),
    (r'\.opencode/emergent-learning/sessions', '.opencode/emergent-learning/sessions'),
]

# Files to skip (binary, git-related, etc.)
SKIP_PATTERNS = [
    r'\.git/',
    r'\.ruff_cache/',
    r'__pycache__/',
    r'\.egg-info/',
    r'\.venv/',
    r'\.coordination/',
    r'\.watcher\.pid',
    r'test-elf-fixes\.js',
    r'\.pyc$',
    r'\.pyo$',
]


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    str_path = str(file_path)
    return any(re.search(pattern, str_path) for pattern in SKIP_PATTERNS)


def convert_file(file_path: Path) -> Tuple[bool, str]:
    """Convert a single file. Returns (changed, message)."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original_content = content
        
        # Apply replacements
        for pattern, replacement in PATH_REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        
        # Check if changed
        if content == original_content:
            return False, f"No changes needed"
        
        # Write back
        file_path.write_text(content, encoding='utf-8')
        return True, f"✅ Updated"
        
    except Exception as e:
        return False, f"❌ Error: {e}"


def find_all_files(start_path: Path = SCRIPT_DIR) -> List[Path]:
    """Recursively find all Python and text files."""
    files = []
    
    for item in start_path.rglob('*'):
        if item.is_file():
            # Include Python, JS, YAML, MD files and other text files
            if item.suffix in {'.py', '.js', '.yaml', '.yml', '.md', '.sh', '.txt', '.sql'}:
                if not should_skip_file(item):
                    files.append(item)
    
    return sorted(files)


def main():
    """Main conversion routine."""
    print("🔧 ELF Path Converter - ~/.claude → ~/.opencode")
    print(f"   Base: {SCRIPT_DIR}\n")
    
    files = find_all_files()
    
    if not files:
        print("No files found to convert")
        return 1
    
    print(f"📁 Found {len(files)} files to scan\n")
    
    changed_count = 0
    
    for file_path in files:
        rel_path = file_path.relative_to(SCRIPT_DIR)
        changed, message = convert_file(file_path)
        
        if changed:
            print(f"   {rel_path}: {message}")
            changed_count += 1
        elif "--verbose" in sys.argv:
            print(f"   {rel_path}: {message}")
    
    print(f"\n✨ Conversion complete!")
    print(f"   Files modified: {changed_count}/{len(files)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
