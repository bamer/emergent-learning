#!/usr/bin/env python3
"""
ELF path resolution for OpenCode integration.

Provides consistent path resolution across ELF modules.
"""

import os
from pathlib import Path


def get_base_path() -> Path:
    """
    Get the ELF base directory path.
    
    Priority:
    1. ELF_BASE_PATH environment variable
    2. OPENCODE_DIR environment variable + /emergent-learning
    3. ~/.opencode/emergent-learning
    
    Returns:
        Path: The base path for ELF
    """
    # Try explicit ELF_BASE_PATH
    if "ELF_BASE_PATH" in os.environ:
        return Path(os.environ["ELF_BASE_PATH"])
    
    # Try OPENCODE_DIR + emergent-learning
    if "OPENCODE_DIR" in os.environ:
        return Path(os.environ["OPENCODE_DIR"]) / "emergent-learning"
    
    # Default to ~/.opencode/emergent-learning
    return Path.home() / ".opencode" / "emergent-learning"


def get_scripts_path() -> Path:
    """Get the OpenCode scripts directory."""
    opencode_dir = Path.home() / ".opencode"
    return opencode_dir / "scripts"


def get_opencode_dir() -> Path:
    """Get the OpenCode root directory."""
    if "OPENCODE_DIR" in os.environ:
        return Path(os.environ["OPENCODE_DIR"])
    return Path.home() / ".opencode"
