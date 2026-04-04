"""Tests for journal CLI commands."""

from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

runner = CliRunner()


class TestJournalList:
    """Test hs journal list command."""

    def test_journal_list_calls_correct_endpoint(self, sample_journal_list):
        """Journal list makes GET /api/journals."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_journal_list
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.journal.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["journal", "list"])

            assert result.exit_code == 0
            client.get.assert_called_once()
            call_url = client.get.call_args[0][0]
            assert "/api/journals" in call_url

    def test_journal_list_with_since_param(self, sample_journal_list):
        """Journal list passes --since as date_from param."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_journal_list
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.journal.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["journal", "list", "--since", "2024-01-01"])

            assert result.exit_code == 0
            call_kwargs = client.get.call_args
            # Check that date_from is passed as a query param
            params = call_kwargs[1].get(
                "params", call_kwargs[0][1] if len(call_kwargs[0]) > 1 else {}
            )
            assert params.get("date_from") == "2024-01-01"

    def test_journal_list_with_limit_param(self, sample_journal_list):
        """Journal list passes --limit as per_page param."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_journal_list
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.journal.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["journal", "list", "--limit", "5"])

            assert result.exit_code == 0
            call_kwargs = client.get.call_args
            params = call_kwargs[1].get("params", {})
            assert params.get("per_page") == 5

    def test_journal_list_displays_entries(self, sample_journal_list):
        """Journal list displays entry titles and dates."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_journal_list
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.journal.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["journal", "list"])

            assert "Morning Thoughts" in result.output
            assert "2024-01-15" in result.output


class TestJournalShow:
    """Test hs journal show command."""

    def test_journal_show_calls_correct_endpoint(self):
        """Journal show makes GET /api/journals/{id}."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "j1",
            "title": "Morning Thoughts",
            "content": "# Hello\nSome content",
            "entry_date": "2024-01-15",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T10:00:00",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.journal.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["journal", "show", "j1"])

            assert result.exit_code == 0
            call_url = client.get.call_args[0][0]
            assert "/api/journals/j1" in call_url


class TestJournalCreate:
    """Test hs journal create command."""

    def test_journal_create_from_file(self, tmp_path):
        """Journal create --file reads file and sends content to API."""
        from health_studio_cli.main import app

        md_file = tmp_path / "entry.md"
        md_file.write_text("# My Entry\nSome content here")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "j-new",
            "title": "Test Entry",
            "content": "# My Entry\nSome content here",
            "entry_date": "2024-01-15",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T10:00:00",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.journal.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(
                app,
                ["journal", "create", "--title", "Test Entry", "--file", str(md_file)],
            )

            assert result.exit_code == 0
            client.post.assert_called_once()
            call_args = client.post.call_args
            body = call_args[1].get("json", {})
            assert body["title"] == "Test Entry"
            assert "# My Entry" in body["content"]


class TestJournalErrorHandling:
    """Test error handling for journal commands."""

    def test_api_error_shows_user_friendly_message(self):
        """API error responses are displayed as user-friendly messages."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Journal entry not found"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )

        with patch("health_studio_cli.commands.journal.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["journal", "show", "nonexistent"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower() or "error" in result.output.lower()
