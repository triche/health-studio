"""Tests for export/import CLI commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def _mock_client_get(response_data, status_code=200, content_type="application/json"):
    """Helper to create a mock client with a GET response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = {"content-type": content_type}
    mock_response.raise_for_status = MagicMock()
    if isinstance(response_data, str):
        mock_response.text = response_data
        mock_response.content = response_data.encode()
    else:
        mock_response.json.return_value = response_data
        mock_response.content = b"{}"
    return mock_response


class TestExportJson:
    def test_export_json_calls_correct_endpoint(self, tmp_path):
        from health_studio_cli.main import app

        mock_response = _mock_client_get({"version": 1, "metric_types": []})
        mock_response.json.return_value = {"version": 1, "metric_types": []}

        with patch("health_studio_cli.commands.export_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            out_file = tmp_path / "backup.json"
            result = runner.invoke(app, ["export", "json", str(out_file)])

            assert result.exit_code == 0
            client.get.assert_called_once()
            assert "/api/export/json" in client.get.call_args[0][0]

    def test_export_json_writes_file(self, tmp_path):
        from health_studio_cli.main import app

        export_data = {"version": 1, "metric_types": [{"id": "1", "name": "Weight"}]}
        mock_response = _mock_client_get(export_data)

        with patch("health_studio_cli.commands.export_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            out_file = tmp_path / "backup.json"
            result = runner.invoke(app, ["export", "json", str(out_file)])

            assert result.exit_code == 0
            assert out_file.exists()


class TestExportCsv:
    def test_export_csv_calls_correct_endpoint(self, tmp_path):
        from health_studio_cli.main import app

        mock_response = _mock_client_get("id,name,unit\n1,Weight,lbs\n", content_type="text/csv")

        with patch("health_studio_cli.commands.export_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            out_file = tmp_path / "metrics.csv"
            result = runner.invoke(app, ["export", "csv", "metric_types", str(out_file)])

            assert result.exit_code == 0
            assert "/api/export/csv/metric_types" in client.get.call_args[0][0]

    def test_export_csv_writes_file(self, tmp_path):
        from health_studio_cli.main import app

        csv_content = "id,name,unit\n1,Weight,lbs\n"
        mock_response = _mock_client_get(csv_content, content_type="text/csv")

        with patch("health_studio_cli.commands.export_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            out_file = tmp_path / "metrics.csv"
            result = runner.invoke(app, ["export", "csv", "metric_types", str(out_file)])

            assert result.exit_code == 0
            assert out_file.exists()
            assert "Weight" in out_file.read_text()


class TestExportMarkdown:
    def test_export_markdown_calls_correct_endpoint(self, tmp_path):
        from health_studio_cli.main import app

        md_content = "# Day One\n_Date: 2025-01-01_\nContent here\n---\n"
        mock_response = _mock_client_get(md_content, content_type="text/markdown")

        with patch("health_studio_cli.commands.export_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            out_file = tmp_path / "journals.md"
            result = runner.invoke(app, ["export", "markdown", str(out_file)])

            assert result.exit_code == 0
            assert "/api/export/journals/markdown" in client.get.call_args[0][0]
            assert out_file.exists()


class TestImportJson:
    def test_import_json_calls_correct_endpoint(self, tmp_path):
        from health_studio_cli.main import app

        # Create a valid JSON file
        import_file = tmp_path / "backup.json"
        import_file.write_text('{"version": 1, "metric_types": []}')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "metric_types": 0,
            "metric_entries": 0,
            "exercise_types": 0,
            "result_entries": 0,
            "journal_entries": 0,
            "goals": 0,
            "skipped": 0,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.import_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["import", "json", str(import_file)])

            assert result.exit_code == 0
            client.post.assert_called_once()
            assert "/api/import/json" in client.post.call_args[0][0]

    def test_import_json_displays_results(self, tmp_path):
        from health_studio_cli.main import app

        import_file = tmp_path / "backup.json"
        payload = '{"version": 1, "metric_types": [{"id":"1","name":"W","unit":"lbs"}]}'
        import_file.write_text(payload)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "metric_types": 1,
            "metric_entries": 0,
            "exercise_types": 0,
            "result_entries": 0,
            "journal_entries": 0,
            "goals": 0,
            "skipped": 0,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.import_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["import", "json", str(import_file)])

            assert result.exit_code == 0
            assert "metric_types" in result.output


class TestImportCsv:
    def test_import_csv_calls_correct_endpoint(self, tmp_path):
        from health_studio_cli.main import app

        csv_file = tmp_path / "metrics.csv"
        csv_file.write_text("metric_type_id,value,recorded_date\nmt1,180.5,2025-01-01\n")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"imported": 1}
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.import_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["import", "csv", "metric_entries", str(csv_file)])

            assert result.exit_code == 0
            client.post.assert_called_once()
            assert "/api/import/csv/metric_entries" in client.post.call_args[0][0]

    def test_import_csv_displays_count(self, tmp_path):
        from health_studio_cli.main import app

        csv_file = tmp_path / "metrics.csv"
        csv_file.write_text("metric_type_id,value,recorded_date\nmt1,180.5,2025-01-01\n")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"imported": 1}
        mock_response.raise_for_status = MagicMock()

        with patch("health_studio_cli.commands.import_cmd.get_client") as mock_get_client:
            client = MagicMock()
            client.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=client)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(app, ["import", "csv", "metric_entries", str(csv_file)])

            assert result.exit_code == 0
            assert "1" in result.output

    def test_import_csv_nonexistent_file(self):
        from health_studio_cli.main import app

        result = runner.invoke(app, ["import", "csv", "metric_entries", "/nonexistent/file.csv"])
        assert result.exit_code != 0
