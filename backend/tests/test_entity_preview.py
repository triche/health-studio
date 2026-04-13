"""Tests for entity preview endpoint (Phase 5)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def _create_goal(client: TestClient, **overrides) -> dict:
    data = {
        "title": "Squat 405",
        "description": "Hit a 405 squat",
        "plan": "Progressive overload",
        "target_type": "result",
        "target_id": None,
        "target_value": 405,
        "start_value": 300,
        "lower_is_better": False,
        "status": "active",
        "deadline": "2026-12-31",
        **overrides,
    }
    resp = client.post("/api/goals", json=data)
    assert resp.status_code == 201
    return resp.json()


def _create_metric_type(client: TestClient, **overrides) -> dict:
    data = {"name": "Body Weight", "unit": "lbs", **overrides}
    resp = client.post("/api/metric-types", json=data)
    assert resp.status_code == 201
    return resp.json()


def _create_metric_entry(client: TestClient, metric_type_id: str, **overrides) -> dict:
    data = {
        "metric_type_id": metric_type_id,
        "value": 205,
        "recorded_date": "2026-04-01",
        **overrides,
    }
    resp = client.post("/api/metrics", json=data)
    assert resp.status_code == 201
    return resp.json()


def _create_exercise_type(client: TestClient, **overrides) -> dict:
    data = {"name": "Back Squat", "category": "Barbell", "result_unit": "lbs", **overrides}
    resp = client.post("/api/exercise-types", json=data)
    assert resp.status_code == 201
    return resp.json()


def _create_result_entry(client: TestClient, exercise_type_id: str, **overrides) -> dict:
    data = {
        "exercise_type_id": exercise_type_id,
        "value": 315,
        "recorded_date": "2026-03-20",
        "is_rx": True,
        **overrides,
    }
    resp = client.post("/api/results", json=data)
    assert resp.status_code == 201
    return resp.json()


class TestPreviewGoal:
    def test_preview_goal(self, authed_client: TestClient):
        """Preview returns goal with progress data."""
        et = _create_exercise_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="result",
            target_id=et["id"],
            target_value=405,
            start_value=300,
        )
        # Create a result to establish current value
        _create_result_entry(authed_client, et["id"], value=315)

        resp = authed_client.get(f"/api/entities/preview?type=goal&id={goal['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entity_type"] == "goal"
        assert data["entity_id"] == goal["id"]
        assert data["title"] == "Squat 405"
        assert data["status"] == "active"
        assert data["target_value"] == 405
        assert data["deadline"] == "2026-12-31"
        # Progress should be computed dynamically
        assert "progress" in data
        assert isinstance(data["progress"], (int, float))
        assert "current_value" in data


class TestPreviewMetricType:
    def test_preview_metric_type(self, authed_client: TestClient):
        """Preview returns metric type with latest value and trend."""
        mt = _create_metric_type(authed_client)
        # Create several entries for trend
        for _i, (d, v) in enumerate(
            [
                ("2026-03-25", 207),
                ("2026-03-26", 206),
                ("2026-03-27", 206),
                ("2026-03-28", 205.5),
                ("2026-03-29", 205),
                ("2026-03-30", 204.5),
                ("2026-04-01", 205),
            ]
        ):
            _create_metric_entry(authed_client, mt["id"], value=v, recorded_date=d)

        resp = authed_client.get(f"/api/entities/preview?type=metric_type&id={mt['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entity_type"] == "metric_type"
        assert data["entity_id"] == mt["id"]
        assert data["title"] == "Body Weight"
        assert data["unit"] == "lbs"
        assert data["latest_value"] == 205
        assert data["latest_date"] == "2026-04-01"
        assert len(data["trend"]) == 7
        # Trend should be ordered by date ascending
        dates = [p["date"] for p in data["trend"]]
        assert dates == sorted(dates)

    def test_preview_metric_type_no_entries(self, authed_client: TestClient):
        """Preview returns metric type with null latest value when no entries."""
        mt = _create_metric_type(authed_client)

        resp = authed_client.get(f"/api/entities/preview?type=metric_type&id={mt['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["latest_value"] is None
        assert data["latest_date"] is None
        assert data["trend"] == []


class TestPreviewExerciseType:
    def test_preview_exercise_type(self, authed_client: TestClient):
        """Preview returns exercise type with PR and recent results."""
        et = _create_exercise_type(authed_client)
        # Create several results
        _create_result_entry(authed_client, et["id"], value=275, recorded_date="2026-03-01")
        _create_result_entry(authed_client, et["id"], value=295, recorded_date="2026-03-10")
        _create_result_entry(authed_client, et["id"], value=315, recorded_date="2026-03-20")

        resp = authed_client.get(f"/api/entities/preview?type=exercise_type&id={et['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entity_type"] == "exercise_type"
        assert data["entity_id"] == et["id"]
        assert data["title"] == "Back Squat"
        assert data["category"] == "Barbell"
        assert data["result_unit"] == "lbs"
        assert data["pr_value"] == 315
        assert data["pr_date"] == "2026-03-20"
        assert len(data["recent_results"]) <= 5
        # Recent results ordered by date ascending
        dates = [r["date"] for r in data["recent_results"]]
        assert dates == sorted(dates)

    def test_preview_exercise_type_no_results(self, authed_client: TestClient):
        """Preview returns exercise type with null PR when no results."""
        et = _create_exercise_type(authed_client)

        resp = authed_client.get(f"/api/entities/preview?type=exercise_type&id={et['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pr_value"] is None
        assert data["pr_date"] is None
        assert data["recent_results"] == []


class TestPreviewNotFound:
    def test_preview_not_found(self, authed_client: TestClient):
        """404 for unknown entity."""
        resp = authed_client.get("/api/entities/preview?type=goal&id=nonexistent-id")
        assert resp.status_code == 404


class TestPreviewInvalidType:
    def test_preview_invalid_type(self, authed_client: TestClient):
        """400 for unsupported entity type."""
        resp = authed_client.get("/api/entities/preview?type=unknown&id=some-id")
        assert resp.status_code == 400


class TestPreviewRequiresAuth:
    def test_preview_requires_auth(self, client: TestClient):
        """Preview endpoint requires authentication."""
        resp = client.get("/api/entities/preview?type=goal&id=some-id")
        assert resp.status_code == 401
