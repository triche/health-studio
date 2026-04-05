"""Tests for metrics CLI commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()

_MT1 = "mt100000-0000-0000-0000-000000000001"


class TestMetricsTypes:
    """Test hs metrics types command."""

    def test_metrics_types_calls_correct_endpoint(self, sample_metric_types):
        """Metrics types makes GET /api/metric-types."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_metric_types
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.metrics.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["metrics", "types"])

            assert result.exit_code == 0
            call_url = client.get.call_args[0][0]
            assert "/api/metric-types" in call_url

    def test_metrics_types_displays_types(self, sample_metric_types):
        """Metrics types displays type names and units."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_metric_types
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.metrics.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["metrics", "types"])

            assert "Weight" in result.output
            assert "lbs" in result.output


class TestMetricsLog:
    """Test hs metrics log command."""

    def test_metrics_log_calls_correct_endpoint(self):
        """Metrics log makes POST /api/metrics."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "me1",
            "metric_type_id": _MT1,
            "value": 185.0,
            "recorded_date": "2024-01-15",
            "notes": None,
            "created_at": "2024-01-15T10:00:00",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.metrics.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["metrics", "log", _MT1, "185.0"])

            assert result.exit_code == 0
            client.post.assert_called_once()
            call_args = client.post.call_args
            call_url = call_args[0][0]
            assert "/api/metrics" in call_url
            body = call_args[1].get("json", {})
            assert body["metric_type_id"] == _MT1
            assert body["value"] == 185.0

    def test_metrics_log_with_date_and_notes(self):
        """Metrics log passes --date and --notes."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "me1",
            "metric_type_id": _MT1,
            "value": 185.0,
            "recorded_date": "2024-01-10",
            "notes": "Morning weight",
            "created_at": "2024-01-15T10:00:00",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.metrics.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(
                app,
                [
                    "metrics",
                    "log",
                    _MT1,
                    "185.0",
                    "--date",
                    "2024-01-10",
                    "--notes",
                    "Morning weight",
                ],
            )

            assert result.exit_code == 0
            body = client.post.call_args[1].get("json", {})
            assert body["recorded_date"] == "2024-01-10"
            assert body["notes"] == "Morning weight"


class TestMetricsTrend:
    """Test hs metrics trend command."""

    def test_metrics_trend_calls_correct_endpoint(self):
        """Metrics trend makes GET /api/metrics/trends/{type_id}."""
        from health_studio_cli.main import app

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "metric_type_id": _MT1,
            "metric_name": "Weight",
            "unit": "lbs",
            "data": [
                {"recorded_date": "2024-01-10", "value": 186.0},
                {"recorded_date": "2024-01-11", "value": 185.5},
                {"recorded_date": "2024-01-12", "value": 185.0},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.metrics.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["metrics", "trend", _MT1])

            assert result.exit_code == 0
            call_url = client.get.call_args[0][0]
            assert f"/api/metrics/trends/{_MT1}" in call_url
