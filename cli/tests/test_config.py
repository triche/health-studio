"""Tests for CLI configuration management."""

import stat

import pytest


class TestConfigInit:
    """Test hs config init command."""

    def test_config_init_creates_toml_file(self, tmp_path):
        """Config init creates a TOML file with correct structure."""
        from health_studio_cli.config import create_config

        config_dir = tmp_path / ".health-studio"
        config_file = config_dir / "config.toml"

        create_config(
            config_dir=config_dir,
            base_url="http://localhost:8000",
            api_key="hs_testkey1234567890abcdefghijklmno",
        )

        assert config_file.exists()
        content = config_file.read_text()
        assert "[server]" in content
        assert 'base_url = "http://localhost:8000"' in content
        assert "[auth]" in content
        assert 'api_key = "hs_testkey1234567890abcdefghijklmno"' in content

    def test_config_init_sets_600_permissions(self, tmp_path):
        """Config file is created with 600 permissions (owner-only read/write)."""
        from health_studio_cli.config import create_config

        config_dir = tmp_path / ".health-studio"
        config_file = config_dir / "config.toml"

        create_config(
            config_dir=config_dir,
            base_url="http://localhost:8000",
            api_key="hs_testkey1234567890abcdefghijklmno",
        )

        file_stat = config_file.stat()
        file_mode = stat.S_IMODE(file_stat.st_mode)
        assert file_mode == 0o600

    def test_config_init_creates_directory(self, tmp_path):
        """Config init creates the config directory if it doesn't exist."""
        from health_studio_cli.config import create_config

        config_dir = tmp_path / ".health-studio"
        assert not config_dir.exists()

        create_config(
            config_dir=config_dir,
            base_url="http://localhost:8000",
            api_key="hs_testkey1234567890abcdefghijklmno",
        )

        assert config_dir.exists()


class TestConfigRead:
    """Test reading configuration."""

    def test_read_config_from_file(self, tmp_config_file):
        """Read config from a TOML file."""
        from health_studio_cli.config import read_config

        config = read_config(config_path=tmp_config_file)

        assert config["base_url"] == "http://localhost:8000"
        assert config["api_key"] == "hs_testkey1234567890abcdefghijklmno"

    def test_env_var_overrides_config_file(self, tmp_config_file, mock_env_api_key):
        """Environment variable takes precedence over config file."""
        from health_studio_cli.config import read_config

        config = read_config(config_path=tmp_config_file)

        assert config["api_key"] == "hs_envkey1234567890abcdefghijklmno"

    def test_env_var_used_when_no_config_file(self, tmp_path, mock_env_api_key):
        """Falls back to env var when config file is absent."""
        from health_studio_cli.config import read_config

        nonexistent = tmp_path / "nonexistent" / "config.toml"
        config = read_config(config_path=nonexistent)

        assert config["api_key"] == "hs_envkey1234567890abcdefghijklmno"

    def test_missing_config_and_no_env_raises(self, tmp_path):
        """Raises error when neither config file nor env var exists."""
        from health_studio_cli.config import ConfigError, read_config

        nonexistent = tmp_path / "nonexistent" / "config.toml"
        with pytest.raises(ConfigError):
            read_config(config_path=nonexistent)


class TestConfigShow:
    """Test hs config show output."""

    def test_config_show_masks_api_key(self, tmp_config_file):
        """Config show masks the API key except prefix."""
        from health_studio_cli.config import format_config_for_display

        config = {
            "base_url": "http://localhost:8000",
            "api_key": "hs_testkey1234567890abcdefghijklmno",
        }
        display = format_config_for_display(config)

        assert "http://localhost:8000" in display
        assert "hs_testk" in display
        assert "hs_testkey1234567890abcdefghijklmno" not in display
        assert "****" in display


class TestConfigSet:
    """Test hs config set."""

    def test_config_set_updates_value(self, tmp_config_file):
        """Config set updates a specific value in the config file."""
        from health_studio_cli.config import read_config, set_config_value

        set_config_value(
            config_path=tmp_config_file, key="server.base_url", value="http://myhost:9000"
        )

        config = read_config(config_path=tmp_config_file)
        assert config["base_url"] == "http://myhost:9000"
