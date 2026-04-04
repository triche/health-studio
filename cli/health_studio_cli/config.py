"""Configuration management for Health Studio CLI.

Reads/writes ~/.health-studio/config.toml and supports env var overrides.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

import tomli_w


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


DEFAULT_CONFIG_DIR = Path.home() / ".health-studio"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.toml"


def create_config(
    *,
    config_dir: Path = DEFAULT_CONFIG_DIR,
    base_url: str,
    api_key: str,
) -> Path:
    """Create a new config file with the given values.

    Returns the path to the created config file.
    """
    config_dir.mkdir(parents=True, exist_ok=True)
    config_dir.chmod(0o700)

    config_file = config_dir / "config.toml"
    data = {
        "server": {"base_url": base_url},
        "auth": {"api_key": api_key},
    }
    config_file.write_text(tomli_w.dumps(data))
    config_file.chmod(0o600)
    return config_file


def read_config(*, config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, str]:
    """Read configuration from file and environment.

    Env var HEALTH_STUDIO_API_KEY overrides the file value.
    Raises ConfigError if no API key is available.
    """
    config: dict[str, str] = {}

    if config_path.exists():
        with config_path.open("rb") as f:
            raw = tomllib.load(f)
        config["base_url"] = raw.get("server", {}).get("base_url", "http://localhost:8000")
        config["api_key"] = raw.get("auth", {}).get("api_key", "")

    # Env var overrides
    env_key = os.environ.get("HEALTH_STUDIO_API_KEY")
    if env_key:
        config["api_key"] = env_key

    if not config.get("api_key"):
        raise ConfigError(
            "No API key configured. Run 'hs config init' or set HEALTH_STUDIO_API_KEY."
        )

    config.setdefault("base_url", "http://localhost:8000")
    return config


def format_config_for_display(config: dict[str, str]) -> str:
    """Format config for display, masking the API key."""
    api_key = config.get("api_key", "")
    masked_key = api_key[:8] + "****" if len(api_key) > 8 else "****"

    lines = [
        f"Base URL: {config.get('base_url', 'not set')}",
        f"API Key:  {masked_key}",
    ]
    return "\n".join(lines)


def set_config_value(*, config_path: Path = DEFAULT_CONFIG_PATH, key: str, value: str) -> None:
    """Update a single config value. Key format: 'section.key' (e.g. 'server.base_url')."""
    if config_path.exists():
        with config_path.open("rb") as f:
            data = tomllib.load(f)
    else:
        data = {}

    parts = key.split(".", 1)
    if len(parts) == 2:
        section, field = parts
        if section not in data:
            data[section] = {}
        data[section][field] = value
    else:
        data[key] = value

    config_path.write_text(tomli_w.dumps(data))
    config_path.chmod(0o600)
