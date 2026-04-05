"""Tests for goals CLI commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()

_G1 = "g1000000-0000-0000-0000-000000000001"


class TestGoalsList:
    """Test hs goals list command."""

    def test_goals_list_calls_correct_endpoint(self, sample_goals_list):
        """Goals list makes GET /api/goals."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_goals_list
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.goals.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["goals", "list"])

            assert result.exit_code == 0
            call_url = client.get.call_args[0][0]
            assert "/api/goals" in call_url

    def test_goals_list_with_status_filter(self, sample_goals_list):
        """Goals list passes --status as query param."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_goals_list
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.goals.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["goals", "list", "--status", "active"])

            assert result.exit_code == 0
            params = client.get.call_args[1].get("params", {})
            assert params.get("status") == "active"

    def test_goals_list_displays_goals(self, sample_goals_list):
        """Goals list displays goal titles and progress."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_goals_list
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.goals.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["goals", "list"])

            assert "Squat 300lbs" in result.output


class TestGoalsShow:
    """Test hs goals show command."""

    def test_goals_show_calls_correct_endpoint(self):
        """Goals show makes GET /api/goals/{id}."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": _G1,
            "title": "Squat 300lbs",
            "description": "Get stronger",
            "plan": "## Training Plan\n- Back squat 3x5 MWF",
            "target_type": "result",
            "target_id": "et1",
            "target_value": 300.0,
            "start_value": 225.0,
            "current_value": 275.0,
            "lower_is_better": False,
            "status": "active",
            "deadline": "2024-06-01",
            "progress": 66.7,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-15T00:00:00",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.goals.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["goals", "show", _G1])

            assert result.exit_code == 0
            call_url = client.get.call_args[0][0]
            assert f"/api/goals/{_G1}" in call_url
            assert "Squat 300lbs" in result.output
