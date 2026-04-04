"""Tests for the CLI main module and help output."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


class TestCLIHelp:
    """Test CLI help and version output."""

    def test_help_contains_ascii_banner(self):
        """hs --help output contains the ASCII art banner."""
        from health_studio_cli.main import app

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Check for parts of the ASCII art banner
        assert "HEALTH" in result.output.upper() or "╦" in result.output

    def test_version_flag(self):
        """hs --version outputs version."""
        from health_studio_cli.main import app

        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_no_args_shows_help(self):
        """hs with no args shows help/banner."""
        from health_studio_cli.main import app

        result = runner.invoke(app, [])

        # Should show help or banner, not crash
        assert result.exit_code == 0


class TestDashboardCommand:
    """Test hs dashboard command."""

    def test_dashboard_calls_correct_endpoint(self, sample_dashboard):
        """Dashboard makes GET /api/dashboard/summary."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_dashboard
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.dashboard.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["dashboard"])

            assert result.exit_code == 0
            call_url = client.get.call_args[0][0]
            assert "/api/dashboard/summary" in call_url

    def test_dashboard_displays_summary(self, sample_dashboard):
        """Dashboard displays summary data from all sections."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_dashboard
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.dashboard.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["dashboard"])

            assert "Morning Thoughts" in result.output
            assert "Squat 300lbs" in result.output
