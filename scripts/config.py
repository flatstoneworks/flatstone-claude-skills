#!/usr/bin/env python3
"""
Configuration module for Claude Skills.

Handles loading configuration from:
1. Environment variables (highest priority)
2. Config file (~/.config/claude-skills/config.json)
3. Default values (lowest priority)

Environment Variables:
    CLAUDE_SKILLS_WORKSPACE  - Base workspace directory
    CLAUDE_SKILLS_CATALOG    - Path to CATALOG.md
    CLAUDE_SKILLS_CONFIG     - Path to config file (override default location)
"""

import json
import os
from pathlib import Path
from typing import Optional

# Default config directory (XDG standard)
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "claude-skills"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


class Config:
    """Configuration manager for Claude Skills."""

    def __init__(self):
        self._config = {}
        self._load()

    def _load(self):
        """Load configuration from file and environment."""
        # Load from config file
        config_file = Path(os.environ.get("CLAUDE_SKILLS_CONFIG", DEFAULT_CONFIG_FILE))

        if config_file.exists():
            try:
                with open(config_file) as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {config_file}: {e}")
                self._config = {}

        # Environment variables override config file
        if os.environ.get("CLAUDE_SKILLS_WORKSPACE"):
            self._config["workspace"] = os.environ["CLAUDE_SKILLS_WORKSPACE"]

        if os.environ.get("CLAUDE_SKILLS_CATALOG"):
            self._config["catalog_file"] = os.environ["CLAUDE_SKILLS_CATALOG"]

    @property
    def workspace(self) -> Path:
        """Get the workspace directory."""
        if "workspace" in self._config:
            return Path(self._config["workspace"]).expanduser()

        # Default: try to find workspace by looking for CATALOG.md
        # Start from current directory and walk up
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / "CATALOG.md").exists():
                return parent
            if (parent / ".claude-skills").exists():
                return parent

        # Fallback to home directory
        return Path.home()

    @property
    def catalog_file(self) -> Path:
        """Get the path to CATALOG.md."""
        if "catalog_file" in self._config:
            return Path(self._config["catalog_file"]).expanduser()
        return self.workspace / "CATALOG.md"

    @property
    def scripts_dir(self) -> Path:
        """Get the scripts directory."""
        if "scripts_dir" in self._config:
            return Path(self._config["scripts_dir"]).expanduser()
        return self.workspace / "scripts"

    @property
    def categories(self) -> dict:
        """Get project categories with their base ports."""
        default_categories = {
            "WORK": {"base": 3000, "description": "Work projects"},
            "PERSONAL": {"base": 4000, "description": "Personal projects"},
            "EXPERIMENTS": {"base": 5000, "description": "Experimental projects"},
            "TOOLS": {"base": None, "description": "Tools and utilities (no ports)"},
        }
        return self._config.get("categories", default_categories)

    @property
    def hostname(self) -> str:
        """Get the hostname to use in URLs."""
        return self._config.get("hostname", "localhost")

    @property
    def project_dirs(self) -> list:
        """Get directories to scan for projects."""
        if "project_dirs" in self._config:
            return [Path(p).expanduser() for p in self._config["project_dirs"]]
        return [self.workspace]

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self._config.get(key, default)

    def save(self, config_file: Optional[Path] = None):
        """Save current configuration to file."""
        config_file = config_file or DEFAULT_CONFIG_FILE
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w') as f:
            json.dump(self._config, f, indent=2)

        print(f"Configuration saved to {config_file}")

    @classmethod
    def init_config(cls, workspace: str, hostname: str = "localhost",
                    categories: Optional[dict] = None) -> "Config":
        """Initialize a new configuration."""
        config = cls()
        config._config = {
            "workspace": str(workspace),
            "hostname": hostname,
            "categories": categories or {
                "WORK": {"base": 3000, "description": "Work projects"},
                "PERSONAL": {"base": 4000, "description": "Personal projects"},
                "EXPERIMENTS": {"base": 5000, "description": "Experimental projects"},
                "TOOLS": {"base": None, "description": "Tools and utilities (no ports)"},
            },
            "project_dirs": [str(workspace)],
        }
        return config

    def __repr__(self):
        return f"Config(workspace={self.workspace}, catalog={self.catalog_file})"


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config():
    """Reload the configuration."""
    global _config
    _config = Config()
    return _config


# Convenience functions
def get_workspace() -> Path:
    """Get the workspace directory."""
    return get_config().workspace


def get_catalog_file() -> Path:
    """Get the catalog file path."""
    return get_config().catalog_file


def get_hostname() -> str:
    """Get the hostname for URLs."""
    return get_config().hostname


def get_categories() -> dict:
    """Get the project categories."""
    return get_config().categories


if __name__ == "__main__":
    # Print current configuration
    config = get_config()
    print(f"Workspace: {config.workspace}")
    print(f"Catalog: {config.catalog_file}")
    print(f"Hostname: {config.hostname}")
    print(f"Categories: {list(config.categories.keys())}")
