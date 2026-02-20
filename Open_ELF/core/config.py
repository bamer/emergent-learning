#!/usr/bin/env python3
"""
Open_ELF Configuration Module
Centralized configuration management for Open_ELF
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class Config:
    """Centralized configuration management for Open_ELF."""

    def __init__(self):
        self._values: Dict[str, Any] = {}
        self._defaults = self._get_defaults()
        self._validators = self._get_validators()
        self._config_path = Path(
            "/home/bamer/OPC_ELF/Open_ELF/core/config.json"
        )

        # Load configuration
        self._load_all()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "database.path": "/home/bamer/OPC_ELF/Open_ELF/data.db",
            "logging.level": "INFO",
            "api.base_url": "http://localhost:8000",
            "component.default": {},
        }

    def _get_validators(self) -> Dict[str, Callable[[Any], bool]]:
        """Get configuration validators."""
        return {
            "database.path": lambda v: isinstance(v, str) and len(v) > 0,
            "logging.level": lambda v: v
            in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "api.base_url": lambda v: isinstance(v, str)
            and (v.startswith("http://") or v.startswith("https://")),
            "component.default": lambda v: isinstance(v, dict),
        }

    def _load_defaults(self):
        """Load default values."""
        self._values.update(self._defaults)

    def _load_env(self):
        """Load configuration from environment variables."""
        for key in self._defaults.keys():
            env_key = f"OPENELF_{key.replace('.', '_').upper()}"
            if env_key in os.environ:
                self._values[key] = os.environ[env_key]

    def _load_json(self):
        """Load configuration from JSON file."""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r") as f:
                    data = json.load(f)
                    self._values.update(data)
            except Exception as e:
                print(f"[WARN] Failed to load config.json: {e}")

    def _validate(self):
        """Validate configuration values."""
        for key, value in self._values.items():
            if key in self._validators:
                if not self._validators[key](value):
                    raise ValueError(f"Invalid value for {key}: {value}")

    def _load_all(self):
        """Load all configuration sources."""
        self._load_defaults()
        self._load_env()
        self._load_json()
        self._validate()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve configuration value."""
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if key in self._validators and not self._validators[key](value):
            raise ValueError(f"Invalid value for {key}: {value}")
        self._values[key] = value

    def reload(self):
        """Reload configuration from sources."""
        self._values.clear()
        self._load_all()

    def __getitem__(self, key: str) -> Any:
        """Dictionary-like access."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        """Dictionary-like assignment."""
        self.set(key, value)

    def add_component(self, name: str, config: Dict[str, Any]):
        """Add component-specific configuration."""
        if name not in self._values:
            self._values[name] = {}
        self._values[name].update(config)


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def get(key: str, default: Any = None) -> Any:
    """Get configuration value."""
    return get_config().get(key, default)


def set(key: str, value: Any):
    """Set configuration value."""
    get_config().set(key, value)


def reload():
    """Reload configuration."""
    get_config().reload()


def add_component(name: str, config: Dict[str, Any]):
    """Add component configuration."""
    get_config().add_component(name, config)


# Example usage
if __name__ == "__main__":
    # Get configuration
    cfg = get_config()
    print(f"Database path: {cfg['database.path']}")
    print(f"Logging level: {cfg['logging.level']}")

    # Set configuration
    cfg["logging.level"] = "DEBUG"
    print(f"Updated logging level: {cfg['logging.level']}")

    # Add component configuration
    cfg.add_component("worker", {"threads": 4, "timeout": 30})
    print(f"Worker threads: {cfg['worker']['threads']}")
