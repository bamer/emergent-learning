#!/usr/bin/env python3
"""
Open_ELF Shared Utility Library
Consolidates common utility functions used across the codebase
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class PathUtils:
    """Path resolution and file operation utilities."""

    @staticmethod
    def resolve_path(path: Union[str, Path]) -> Path:
        """Resolve a path, expanding environment variables and user home."""
        if isinstance(path, str):
            path = Path(os.path.expanduser(os.path.expandvars(path)))
        return path.resolve()

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure a directory exists, creating it if necessary."""
        path = PathUtils.resolve_path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def find_files(pattern: str, root_dir: Union[str, Path] = None) -> List[Path]:
        """Find files matching pattern recursively."""
        if root_dir is None:
            root_dir = Path.cwd()
        else:
            root_dir = PathUtils.resolve_path(root_dir)

        return list(root_dir.rglob(pattern))


class DataUtils:
    """Data validation and transformation utilities."""

    @staticmethod
    def safe_json_loads(data: str, default: Any = None) -> Any:
        """Safely parse JSON with fallback."""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def hash_string(data: str) -> str:
        """Create SHA256 hash of a string."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe filesystem use."""
        # Remove or replace unsafe characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
        # Limit length
        return sanitized[:255]


class TimeUtils:
    """Time and date utilities."""

    @staticmethod
    def timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"


class ValidationUtils:
    """Data validation utilities."""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format."""
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_dict_structure(data: Dict, structure: Dict) -> bool:
        """Validate dictionary structure against expected schema."""
        for key, expected_type in structure.items():
            if key not in data:
                return False
            if not isinstance(data[key], expected_type):
                return False
        return True


class FileUtils:
    """File operation utilities."""

    @staticmethod
    def read_file_safe(
        path: Union[str, Path], encoding: str = "utf-8"
    ) -> Optional[str]:
        """Safely read file content with error handling."""
        try:
            path = PathUtils.resolve_path(path)
            if path.exists() and path.is_file():
                return path.read_text(encoding=encoding)
        except Exception:
            pass
        return None

    @staticmethod
    def write_file_safe(
        path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> bool:
        """Safely write file content with error handling."""
        try:
            path = PathUtils.resolve_path(path)
            PathUtils.ensure_directory(path.parent)
            path.write_text(content, encoding=encoding)
            return True
        except Exception:
            return False


# Public API functions for backward compatibility


def resolve_path(path: Union[str, Path]) -> Path:
    """Resolve path with environment expansion."""
    return PathUtils.resolve_path(path)


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    return PathUtils.ensure_directory(path)


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON."""
    return DataUtils.safe_json_loads(data, default)


def timestamp() -> str:
    """Get current timestamp."""
    return TimeUtils.timestamp()


def read_file_safe(path: Union[str, Path], encoding: str = "utf-8") -> Optional[str]:
    """Safely read file."""
    return FileUtils.read_file_safe(path, encoding)


def write_file_safe(
    path: Union[str, Path], content: str, encoding: str = "utf-8"
) -> bool:
    """Safely write file."""
    return FileUtils.write_file_safe(path, content, encoding)


# Example usage
if __name__ == "__main__":
    # Test path resolution
    test_path = resolve_path("~/test/file.txt")
    print(f"Resolved path: {test_path}")

    # Test directory creation
    dir_path = ensure_directory("/tmp/test/directory")
    print(f"Directory ensured: {dir_path}")

    # Test JSON parsing
    json_data = safe_json_loads('{"test": "value"}')
    print(f"JSON parsed: {json_data}")

    # Test timestamp
    print(f"Current timestamp: {timestamp()}")
