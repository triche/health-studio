"""Tests for export/import endpoints."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_data(client: TestClient) -> dict:
    """Seed a variety of data and return references."""
    # Create metric types
    mt = client.post("/api/metric-types", json={"name": "Weight", "unit": "lbs"}).json()

    # Create metric entries
    me1 = client.post(
        "/api/metrics",
        json={
            "metric_type_id": mt["id"],
            "value": 180.5,
            "recorded_date": "2025-01-01",
            "notes": "Morning weigh-in",
        },
    ).json()
    me2 = client.post(
        "/api/metrics",
        json={
            "metric_type_id": mt["id"],
            "value": 179.0,
            "recorded_date": "2025-01-02",
        },
    ).json()

    # Create exercise types
    et = client.post(
        "/api/exercise-types",
        json={"name": "Back Squat", "category": "Strength", "result_unit": "lbs"},
    ).json()

    # Create result entries
    re1 = client.post(
        "/api/results",
        json={
            "exercise_type_id": et["id"],
            "value": 225.0,
            "recorded_date": "2025-01-01",
            "notes": "3x5",
        },
    ).json()

    # Create journal entries
    je1 = client.post(
        "/api/journals",
        json={
            "title": "Day One",
            "content": "Started tracking **everything**.",
            "entry_date": "2025-01-01",
        },
    ).json()
    je2 = client.post(
        "/api/journals",
        json={
            "title": "Day Two",
            "content": "Feeling good.\n\n- Ate well\n- Slept 8h",
            "entry_date": "2025-01-02",
        },
    ).json()

    # Create goals
    goal = client.post(
        "/api/goals",
        json={
            "title": "Lose 10 lbs",
            "description": "Get to 170",
            "target_type": "metric",
            "target_id": mt["id"],
            "target_value": 170.0,
            "start_value": 180.0,
            "lower_is_better": True,
        },
    ).json()

    return {
        "metric_types": [mt],
        "metric_entries": [me1, me2],
        "exercise_types": [et],
        "result_entries": [re1],
        "journal_entries": [je1, je2],
        "goals": [goal],
    }


# ===========================================================================
# JSON Export
# ===========================================================================


class TestJsonExport:
    def test_json_export_empty_db(self, authed_client: TestClient):
        resp = authed_client.get("/api/export/json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == 1
        assert data["metric_types"] == []
        assert data["metric_entries"] == []
        assert data["exercise_types"] == []
        assert data["result_entries"] == []
        assert data["journal_entries"] == []
        assert data["goals"] == []

    def test_json_export_with_data(self, authed_client: TestClient):
        _seed_data(authed_client)
        resp = authed_client.get("/api/export/json")
        assert resp.status_code == 200
        data = resp.json()

        assert data["version"] == 1
        assert len(data["metric_types"]) == 1
        assert data["metric_types"][0]["name"] == "Weight"
        assert len(data["metric_entries"]) == 2
        assert len(data["exercise_types"]) == 1
        assert len(data["result_entries"]) == 1
        assert len(data["journal_entries"]) == 2
        assert len(data["goals"]) == 1

    def test_json_export_content_disposition(self, authed_client: TestClient):
        resp = authed_client.get("/api/export/json")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert "health-studio-export" in resp.headers.get("content-disposition", "")

    def test_json_export_requires_auth(self, client: TestClient):
        resp = client.get("/api/export/json")
        assert resp.status_code == 401


# ===========================================================================
# CSV Export
# ===========================================================================


class TestCsvExport:
    def test_csv_export_metric_types(self, authed_client: TestClient):
        _seed_data(authed_client)
        resp = authed_client.get("/api/export/csv/metric_types")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "Weight"
        assert rows[0]["unit"] == "lbs"

    def test_csv_export_metric_entries(self, authed_client: TestClient):
        _seed_data(authed_client)
        resp = authed_client.get("/api/export/csv/metric_entries")
        assert resp.status_code == 200
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 2

    def test_csv_export_exercise_types(self, authed_client: TestClient):
        _seed_data(authed_client)
        resp = authed_client.get("/api/export/csv/exercise_types")
        assert resp.status_code == 200
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "Back Squat"

    def test_csv_export_result_entries(self, authed_client: TestClient):
        _seed_data(authed_client)
        resp = authed_client.get("/api/export/csv/result_entries")
        assert resp.status_code == 200
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 1

    def test_csv_export_journal_entries(self, authed_client: TestClient):
        _seed_data(authed_client)
        resp = authed_client.get("/api/export/csv/journal_entries")
        assert resp.status_code == 200
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 2

    def test_csv_export_goals(self, authed_client: TestClient):
        _seed_data(authed_client)
        resp = authed_client.get("/api/export/csv/goals")
        assert resp.status_code == 200
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 1

    def test_csv_export_invalid_entity(self, authed_client: TestClient):
        resp = authed_client.get("/api/export/csv/invalid_thing")
        assert resp.status_code == 400

    def test_csv_export_empty(self, authed_client: TestClient):
        resp = authed_client.get("/api/export/csv/metric_types")
        assert resp.status_code == 200
        lines = resp.text.strip().split("\n")
        # Should still have header row
        assert len(lines) == 1

    def test_csv_export_requires_auth(self, client: TestClient):
        resp = client.get("/api/export/csv/metric_types")
        assert resp.status_code == 401


# ===========================================================================
# Markdown Export (journals)
# ===========================================================================


class TestMarkdownExport:
    def test_markdown_export_journals(self, authed_client: TestClient):
        _seed_data(authed_client)
        resp = authed_client.get("/api/export/journals/markdown")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/markdown")
        text = resp.text
        assert "# Day One" in text
        assert "# Day Two" in text
        assert "Started tracking **everything**." in text

    def test_markdown_export_empty(self, authed_client: TestClient):
        resp = authed_client.get("/api/export/journals/markdown")
        assert resp.status_code == 200
        # Should still return valid markdown, just empty or with a header
        assert resp.text is not None

    def test_markdown_export_requires_auth(self, client: TestClient):
        resp = client.get("/api/export/journals/markdown")
        assert resp.status_code == 401


# ===========================================================================
# JSON Import
# ===========================================================================


class TestJsonImport:
    def test_json_import_full_backup(self, authed_client: TestClient):
        # Export, then re-import into empty DB
        seed = _seed_data(authed_client)
        resp = authed_client.get("/api/export/json")
        exported = resp.json()

        # Wipe all data via individual deletes
        for je in seed["journal_entries"]:
            authed_client.delete(f"/api/journals/{je['id']}")
        for re_ in seed["result_entries"]:
            authed_client.delete(f"/api/results/{re_['id']}")
        for me in seed["metric_entries"]:
            authed_client.delete(f"/api/metrics/{me['id']}")
        for g in seed["goals"]:
            authed_client.delete(f"/api/goals/{g['id']}")
        for et in seed["exercise_types"]:
            authed_client.delete(f"/api/exercise-types/{et['id']}")
        for mt in seed["metric_types"]:
            authed_client.delete(f"/api/metric-types/{mt['id']}")

        # Now import
        resp = authed_client.post("/api/import/json", json=exported)
        assert resp.status_code == 200
        result = resp.json()
        assert result["metric_types"] == 1
        assert result["metric_entries"] == 2
        assert result["exercise_types"] == 1
        assert result["result_entries"] == 1
        assert result["journal_entries"] == 2
        assert result["goals"] == 1

        # Verify data is back
        verify = authed_client.get("/api/export/json").json()
        assert len(verify["metric_types"]) == 1
        assert len(verify["metric_entries"]) == 2
        assert len(verify["journal_entries"]) == 2

    def test_json_import_skips_duplicates(self, authed_client: TestClient):
        _seed_data(authed_client)
        exported = authed_client.get("/api/export/json").json()

        # Import again — should skip existing records
        resp = authed_client.post("/api/import/json", json=exported)
        assert resp.status_code == 200
        result = resp.json()
        assert result["skipped"] > 0

    def test_json_import_invalid_version(self, authed_client: TestClient):
        resp = authed_client.post(
            "/api/import/json",
            json={"version": 999, "metric_types": []},
        )
        assert resp.status_code == 400

    def test_json_import_requires_auth(self, client: TestClient):
        resp = client.post(
            "/api/import/json",
            json={"version": 1},
            headers={"X-Requested-With": "HealthStudio"},
        )
        assert resp.status_code == 401


# ===========================================================================
# CSV Import
# ===========================================================================


class TestCsvImport:
    def test_csv_import_metric_entries(self, authed_client: TestClient):
        # Create a metric type first
        mt = authed_client.post("/api/metric-types", json={"name": "Body Fat", "unit": "%"}).json()

        csv_content = (
            f"metric_type_id,value,recorded_date,notes\n"
            f"{mt['id']},15.2,2025-01-01,Morning\n"
            f"{mt['id']},14.8,2025-01-02,\n"
        )

        resp = authed_client.post(
            "/api/import/csv/metric_entries",
            files={"file": ("metrics.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["imported"] == 2

    def test_csv_import_result_entries(self, authed_client: TestClient):
        et = authed_client.post(
            "/api/exercise-types",
            json={"name": "Deadlift", "category": "Strength", "result_unit": "lbs"},
        ).json()

        csv_content = (
            f"exercise_type_id,value,recorded_date,notes\n"
            f"{et['id']},315.0,2025-01-01,Heavy single\n"
        )

        resp = authed_client.post(
            "/api/import/csv/result_entries",
            files={"file": ("results.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["imported"] == 1

    def test_csv_import_invalid_entity(self, authed_client: TestClient):
        resp = authed_client.post(
            "/api/import/csv/invalid",
            files={"file": ("test.csv", "a,b\n1,2\n", "text/csv")},
        )
        assert resp.status_code == 400

    def test_csv_import_bad_csv(self, authed_client: TestClient):
        resp = authed_client.post(
            "/api/import/csv/metric_entries",
            files={"file": ("bad.csv", "not,valid,csv,headers\n", "text/csv")},
        )
        assert resp.status_code == 400

    def test_csv_import_requires_auth(self, client: TestClient):
        resp = client.post(
            "/api/import/csv/metric_entries",
            files={"file": ("test.csv", "a,b\n1,2\n", "text/csv")},
            headers={"X-Requested-With": "HealthStudio"},
        )
        assert resp.status_code == 401
