"""Tests for ID prefix resolution."""

from unittest.mock import MagicMock, patch

import pytest
from click.exceptions import Exit

from health_studio_cli.resolve import resolve_id


class TestResolveId:
    """Test resolve_id prefix matching."""

    def test_full_uuid_returned_as_is(self):
        """A full UUID is returned without making any API call."""
        full_id = "c1793db1-1234-5678-9abc-def012345678"
        client = MagicMock()

        result = resolve_id(client, full_id, "/api/metric-types")

        assert result == full_id
        client.get.assert_not_called()

    def test_prefix_resolves_to_full_id(self):
        """An 8-char prefix resolves to the matching full UUID."""
        client = MagicMock()
        response = MagicMock()
        response.json.return_value = [
            {"id": "c1793db1-1111-2222-3333-444455556666", "name": "Sleep"},
            {"id": "bd5dcaf5-aaaa-bbbb-cccc-ddddeeee0000", "name": "Steps"},
        ]
        response.raise_for_status = MagicMock()
        client.get.return_value = response

        result = resolve_id(client, "c1793db1", "/api/metric-types")

        assert result == "c1793db1-1111-2222-3333-444455556666"
        client.get.assert_called_once_with("/api/metric-types")

    def test_prefix_shorter_than_8_chars(self):
        """A prefix shorter than 8 chars also resolves."""
        client = MagicMock()
        response = MagicMock()
        response.json.return_value = [
            {"id": "c1793db1-1111-2222-3333-444455556666", "name": "Sleep"},
            {"id": "bd5dcaf5-aaaa-bbbb-cccc-ddddeeee0000", "name": "Steps"},
        ]
        response.raise_for_status = MagicMock()
        client.get.return_value = response

        result = resolve_id(client, "c179", "/api/metric-types")

        assert result == "c1793db1-1111-2222-3333-444455556666"

    def test_no_match_exits_with_error(self):
        """No matching ID causes a SystemExit (typer.Exit)."""
        client = MagicMock()
        response = MagicMock()
        response.json.return_value = [
            {"id": "c1793db1-1111-2222-3333-444455556666", "name": "Sleep"},
        ]
        response.raise_for_status = MagicMock()
        client.get.return_value = response

        with pytest.raises(Exit):
            resolve_id(client, "xxxxxxxx", "/api/metric-types")

    def test_ambiguous_prefix_exits_with_error(self):
        """An ambiguous prefix (matches multiple) causes a SystemExit."""
        client = MagicMock()
        response = MagicMock()
        response.json.return_value = [
            {"id": "c1793db1-1111-2222-3333-444455556666", "name": "Sleep"},
            {"id": "c1793db1-aaaa-bbbb-cccc-ddddeeee0000", "name": "Weight"},
        ]
        response.raise_for_status = MagicMock()
        client.get.return_value = response

        with pytest.raises(Exit):
            resolve_id(client, "c1793db1", "/api/metric-types")

    def test_paginated_response_uses_items_key(self):
        """Paginated responses (with 'items' key) are handled."""
        client = MagicMock()
        response = MagicMock()
        response.json.return_value = {
            "items": [
                {"id": "g1abcdef-1111-2222-3333-444455556666", "title": "Goal A"},
                {"id": "g2abcdef-aaaa-bbbb-cccc-ddddeeee0000", "title": "Goal B"},
            ],
            "total": 2,
        }
        response.raise_for_status = MagicMock()
        client.get.return_value = response

        result = resolve_id(client, "g1abcdef", "/api/goals")

        assert result == "g1abcdef-1111-2222-3333-444455556666"


class TestResolveIdInMetricsCommands:
    """Test that metrics commands resolve prefix IDs before API calls."""

    def test_metrics_trend_resolves_prefix(self):
        """hs metrics trend resolves an 8-char prefix to the full UUID."""
        from typer.testing import CliRunner

        from health_studio_cli.main import app

        runner = CliRunner()

        full_uuid = "c1793db1-1111-2222-3333-444455556666"

        # Mock for the types lookup (resolve step)
        types_response = MagicMock()
        types_response.json.return_value = [
            {"id": full_uuid, "name": "Sleep", "unit": "minutes"},
        ]
        types_response.raise_for_status = MagicMock()

        # Mock for the trend call
        trend_response = MagicMock()
        trend_response.status_code = 200
        trend_response.json.return_value = {
            "metric_type_id": full_uuid,
            "metric_name": "Sleep",
            "unit": "minutes",
            "data": [{"recorded_date": "2026-04-01", "value": 450.0}],
        }
        trend_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.metrics.get_client") as mock_get_client:
            client = MagicMock()
            client.get.side_effect = [types_response, trend_response]
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["metrics", "trend", "c1793db1"])

            assert result.exit_code == 0
            # The trend API call should use the FULL UUID
            trend_call = client.get.call_args_list[1]
            assert full_uuid in trend_call[0][0]

    def test_metrics_log_resolves_prefix(self):
        """hs metrics log resolves an 8-char prefix to the full UUID."""
        from typer.testing import CliRunner

        from health_studio_cli.main import app

        runner = CliRunner()

        full_uuid = "c1793db1-1111-2222-3333-444455556666"

        # Mock for the types lookup (resolve step)
        types_response = MagicMock()
        types_response.json.return_value = [
            {"id": full_uuid, "name": "Sleep", "unit": "minutes"},
        ]
        types_response.raise_for_status = MagicMock()

        # Mock for the log call
        log_response = MagicMock()
        log_response.status_code = 201
        log_response.json.return_value = {
            "id": "entry-1",
            "metric_type_id": full_uuid,
            "value": 450.0,
            "recorded_date": "2026-04-01",
        }
        log_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.metrics.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = types_response
            client.post.return_value = log_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["metrics", "log", "c1793db1", "450.0"])

            assert result.exit_code == 0
            body = client.post.call_args[1]["json"]
            assert body["metric_type_id"] == full_uuid


class TestResolveIdInResultsCommands:
    """Test that results commands resolve prefix IDs."""

    def test_results_prs_resolves_prefix(self):
        """hs results prs resolves an 8-char prefix to the full UUID."""
        from typer.testing import CliRunner

        from health_studio_cli.main import app

        runner = CliRunner()

        full_uuid = "et1abcde-1111-2222-3333-444455556666"

        types_response = MagicMock()
        types_response.json.return_value = [
            {"id": full_uuid, "name": "Back Squat", "category": "power_lift", "result_unit": "lbs"},
        ]
        types_response.raise_for_status = MagicMock()

        prs_response = MagicMock()
        prs_response.status_code = 200
        prs_response.json.return_value = [
            {"recorded_date": "2026-01-15", "value": 275.0, "is_rx": False, "notes": None},
        ]
        prs_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.results.get_client") as mock_get_client:
            client = MagicMock()
            client.get.side_effect = [types_response, prs_response]
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["results", "prs", "et1abcde"])

            assert result.exit_code == 0
            prs_call = client.get.call_args_list[1]
            assert full_uuid in prs_call[0][0]

    def test_results_log_resolves_prefix(self):
        """hs results log resolves an 8-char prefix to the full UUID."""
        from typer.testing import CliRunner

        from health_studio_cli.main import app

        runner = CliRunner()

        full_uuid = "et1abcde-1111-2222-3333-444455556666"

        types_response = MagicMock()
        types_response.json.return_value = [
            {"id": full_uuid, "name": "Back Squat", "category": "power_lift", "result_unit": "lbs"},
        ]
        types_response.raise_for_status = MagicMock()

        log_response = MagicMock()
        log_response.status_code = 201
        log_response.json.return_value = {
            "id": "re1",
            "exercise_type_id": full_uuid,
            "value": 275.0,
            "recorded_date": "2026-01-15",
            "is_pr": True,
            "is_rx": False,
            "notes": None,
        }
        log_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.results.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = types_response
            client.post.return_value = log_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["results", "log", "et1abcde", "275.0"])

            assert result.exit_code == 0
            body = client.post.call_args[1]["json"]
            assert body["exercise_type_id"] == full_uuid


class TestResolveIdInGoalsCommands:
    """Test that goals show resolves prefix IDs."""

    def test_goals_show_resolves_prefix(self):
        """hs goals show resolves an 8-char prefix to the full UUID."""
        from typer.testing import CliRunner

        from health_studio_cli.main import app

        runner = CliRunner()

        full_uuid = "g1abcdef-1111-2222-3333-444455556666"

        list_response = MagicMock()
        list_response.json.return_value = {
            "items": [
                {"id": full_uuid, "title": "Squat 300", "status": "active", "progress": 66.7},
            ],
            "total": 1,
        }
        list_response.raise_for_status = MagicMock()

        show_response = MagicMock()
        show_response.status_code = 200
        show_response.json.return_value = {
            "id": full_uuid,
            "title": "Squat 300",
            "status": "active",
            "target_value": 300.0,
            "current_value": 275.0,
            "lower_is_better": False,
            "progress": 66.7,
        }
        show_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.goals.get_client") as mock_get_client:
            client = MagicMock()
            client.get.side_effect = [list_response, show_response]
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["goals", "show", "g1abcdef"])

            assert result.exit_code == 0
            show_call = client.get.call_args_list[1]
            assert full_uuid in show_call[0][0]


class TestResolveIdInJournalCommands:
    """Test that journal show resolves prefix IDs."""

    def test_journal_show_resolves_prefix(self):
        """hs journal show resolves an 8-char prefix to the full UUID."""
        from typer.testing import CliRunner

        from health_studio_cli.main import app

        runner = CliRunner()

        full_uuid = "j1abcdef-1111-2222-3333-444455556666"

        list_response = MagicMock()
        list_response.json.return_value = {
            "items": [
                {"id": full_uuid, "title": "Morning Thoughts", "entry_date": "2024-01-15"},
            ],
            "total": 1,
        }
        list_response.raise_for_status = MagicMock()

        show_response = MagicMock()
        show_response.status_code = 200
        show_response.json.return_value = {
            "id": full_uuid,
            "title": "Morning Thoughts",
            "content": "# Hello",
            "entry_date": "2024-01-15",
        }
        show_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.journal.get_client") as mock_get_client:
            client = MagicMock()
            client.get.side_effect = [list_response, show_response]
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["journal", "show", "j1abcdef"])

            assert result.exit_code == 0
            show_call = client.get.call_args_list[1]
            assert full_uuid in show_call[0][0]
