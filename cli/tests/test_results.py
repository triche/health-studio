"""Tests for results CLI commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()

_ET1 = "et100000-0000-0000-0000-000000000001"


class TestResultsTypes:
    """Test hs results types command."""

    def test_results_types_calls_correct_endpoint(self, sample_exercise_types):
        """Results types makes GET /api/exercise-types."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_exercise_types
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.results.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["results", "types"])

            assert result.exit_code == 0
            call_url = client.get.call_args[0][0]
            assert "/api/exercise-types" in call_url

    def test_results_types_displays_exercises(self, sample_exercise_types):
        """Results types displays exercise names and categories."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_exercise_types
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.results.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["results", "types"])

            assert "Back Squat" in result.output
            assert "power_lift" in result.output


class TestResultsLog:
    """Test hs results log command."""

    def test_results_log_calls_correct_endpoint(self):
        """Results log makes POST /api/results."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "re1",
            "exercise_type_id": _ET1,
            "value": 275.0,
            "display_value": None,
            "recorded_date": "2024-01-15",
            "is_pr": True,
            "is_rx": False,
            "notes": None,
            "created_at": "2024-01-15T10:00:00",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.results.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["results", "log", _ET1, "275.0"])

            assert result.exit_code == 0
            client.post.assert_called_once()
            call_url = client.post.call_args[0][0]
            assert "/api/results" in call_url
            body = client.post.call_args[1].get("json", {})
            assert body["exercise_type_id"] == _ET1
            assert body["value"] == 275.0

    def test_results_log_with_date_and_notes(self):
        """Results log passes --date and --notes."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "re1",
            "exercise_type_id": _ET1,
            "value": 275.0,
            "display_value": None,
            "recorded_date": "2024-01-10",
            "is_pr": False,
            "is_rx": False,
            "notes": "Felt strong",
            "created_at": "2024-01-15T10:00:00",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.results.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(
                app,
                [
                    "results",
                    "log",
                    _ET1,
                    "275.0",
                    "--date",
                    "2024-01-10",
                    "--notes",
                    "Felt strong",
                ],
            )

            assert result.exit_code == 0
            body = client.post.call_args[1].get("json", {})
            assert body["recorded_date"] == "2024-01-10"
            assert body["notes"] == "Felt strong"


class TestResultsPRs:
    """Test hs results prs command."""

    def test_results_prs_calls_correct_endpoint(self):
        """Results prs makes GET /api/results/prs/{exercise_type_id}."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "re1",
                "exercise_type_id": _ET1,
                "value": 275.0,
                "display_value": None,
                "recorded_date": "2024-01-15",
                "is_pr": True,
                "is_rx": False,
                "notes": None,
                "created_at": "2024-01-15T10:00:00",
            }
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.results.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["results", "prs", _ET1])

            assert result.exit_code == 0
            call_url = client.get.call_args[0][0]
            assert f"/api/results/prs/{_ET1}" in call_url
