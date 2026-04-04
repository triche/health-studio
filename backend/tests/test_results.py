from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def _create_exercise_type(
    authed_client: TestClient,
    *,
    name: str = "Back Squat",
    category: str = "power_lift",
    result_unit: str = "lbs",
) -> dict:
    resp = authed_client.post(
        "/api/exercise-types",
        json={"name": name, "category": category, "result_unit": result_unit},
    )
    assert resp.status_code == 201
    return resp.json()


def _create_result(
    authed_client: TestClient,
    exercise_type_id: str,
    *,
    value: float = 225.0,
    recorded_date: str = "2025-06-01",
    notes: str | None = None,
    display_value: str | None = None,
    is_rx: bool | None = None,
) -> dict:
    body: dict = {
        "exercise_type_id": exercise_type_id,
        "value": value,
        "recorded_date": recorded_date,
    }
    if notes is not None:
        body["notes"] = notes
    if display_value is not None:
        body["display_value"] = display_value
    if is_rx is not None:
        body["is_rx"] = is_rx
    resp = authed_client.post("/api/results", json=body)
    assert resp.status_code == 201
    return resp.json()


# ============================================================================
# Exercise Types
# ============================================================================


class TestExerciseTypeCRUD:
    def test_create_exercise_type(self, authed_client: TestClient):
        data = _create_exercise_type(authed_client)
        assert data["name"] == "Back Squat"
        assert data["category"] == "power_lift"
        assert data["result_unit"] == "lbs"
        assert "id" in data
        assert "created_at" in data

    def test_list_exercise_types(self, authed_client: TestClient):
        _create_exercise_type(authed_client, name="Back Squat")
        _create_exercise_type(authed_client, name="Deadlift")
        resp = authed_client.get("/api/exercise-types")
        assert resp.status_code == 200
        types = resp.json()
        assert len(types) == 2
        names = [t["name"] for t in types]
        assert "Back Squat" in names
        assert "Deadlift" in names

    def test_update_exercise_type(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client)
        resp = authed_client.put(
            f"/api/exercise-types/{et['id']}",
            json={"name": "Front Squat"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Front Squat"

    def test_delete_exercise_type(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client)
        resp = authed_client.delete(f"/api/exercise-types/{et['id']}")
        assert resp.status_code == 204
        resp = authed_client.get("/api/exercise-types")
        assert len(resp.json()) == 0

    def test_duplicate_exercise_type_returns_409(self, authed_client: TestClient):
        _create_exercise_type(authed_client, name="Snatch")
        resp = authed_client.post(
            "/api/exercise-types",
            json={"name": "Snatch", "category": "olympic_lift", "result_unit": "lbs"},
        )
        assert resp.status_code == 409

    def test_get_nonexistent_exercise_type_returns_404(self, authed_client: TestClient):
        resp = authed_client.put(
            "/api/exercise-types/nonexistent",
            json={"name": "X"},
        )
        assert resp.status_code == 404


# ============================================================================
# Result Entries
# ============================================================================


class TestResultEntryCRUD:
    def test_create_result_entry(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client)
        data = _create_result(authed_client, et["id"])
        assert data["exercise_type_id"] == et["id"]
        assert data["value"] == 225.0
        assert data["recorded_date"] == "2025-06-01"
        assert "id" in data
        assert "is_pr" in data
        assert data["is_rx"] is False

    def test_create_result_entry_with_rx(self, authed_client: TestClient):
        et = _create_exercise_type(
            authed_client, name="Fran", category="crossfit_benchmark", result_unit="seconds"
        )
        data = _create_result(authed_client, et["id"], value=300, is_rx=True)
        assert data["is_rx"] is True

    def test_get_result_entry(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client)
        created = _create_result(authed_client, et["id"])
        resp = authed_client.get(f"/api/results/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_list_result_entries(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client)
        _create_result(authed_client, et["id"], value=225, recorded_date="2025-06-01")
        _create_result(authed_client, et["id"], value=235, recorded_date="2025-06-08")
        resp = authed_client.get("/api/results")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_list_result_entries_filter_by_exercise_type(self, authed_client: TestClient):
        et1 = _create_exercise_type(authed_client, name="Back Squat")
        et2 = _create_exercise_type(authed_client, name="Deadlift")
        _create_result(authed_client, et1["id"], value=225)
        _create_result(authed_client, et2["id"], value=315)
        resp = authed_client.get(f"/api/results?exercise_type_id={et1['id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["exercise_type_id"] == et1["id"]

    def test_update_result_entry(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client)
        created = _create_result(authed_client, et["id"], value=225)
        resp = authed_client.put(
            f"/api/results/{created['id']}",
            json={"value": 230},
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == 230

    def test_delete_result_entry(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client)
        created = _create_result(authed_client, et["id"])
        resp = authed_client.delete(f"/api/results/{created['id']}")
        assert resp.status_code == 204
        resp = authed_client.get("/api/results")
        assert resp.json()["total"] == 0

    def test_get_nonexistent_result_returns_404(self, authed_client: TestClient):
        resp = authed_client.get("/api/results/nonexistent")
        assert resp.status_code == 404


# ============================================================================
# PR Detection
# ============================================================================


class TestPRDetection:
    def test_first_result_is_pr(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client, result_unit="lbs")
        data = _create_result(authed_client, et["id"], value=225)
        assert data["is_pr"] is True

    def test_higher_value_is_pr_for_lbs(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client, result_unit="lbs")
        _create_result(authed_client, et["id"], value=225, recorded_date="2025-06-01")
        data = _create_result(authed_client, et["id"], value=235, recorded_date="2025-06-08")
        assert data["is_pr"] is True

    def test_lower_value_is_not_pr_for_lbs(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client, result_unit="lbs")
        _create_result(authed_client, et["id"], value=225, recorded_date="2025-06-01")
        data = _create_result(authed_client, et["id"], value=215, recorded_date="2025-06-08")
        assert data["is_pr"] is False

    def test_lower_time_is_pr_for_seconds(self, authed_client: TestClient):
        """For time-based exercises, lower is better."""
        et = _create_exercise_type(
            authed_client, name="Fran", category="crossfit_benchmark", result_unit="seconds"
        )
        _create_result(authed_client, et["id"], value=300, recorded_date="2025-06-01")
        data = _create_result(authed_client, et["id"], value=280, recorded_date="2025-06-08")
        assert data["is_pr"] is True

    def test_higher_time_is_not_pr_for_seconds(self, authed_client: TestClient):
        et = _create_exercise_type(
            authed_client, name="Grace", category="crossfit_benchmark", result_unit="seconds"
        )
        _create_result(authed_client, et["id"], value=180, recorded_date="2025-06-01")
        data = _create_result(authed_client, et["id"], value=200, recorded_date="2025-06-08")
        assert data["is_pr"] is False


# ============================================================================
# PR Recalculation on Update
# ============================================================================


class TestPRRecalculationOnUpdate:
    def test_update_value_recalculates_pr(self, authed_client: TestClient):
        """Updating a result's value should recalculate its PR status."""
        et = _create_exercise_type(authed_client, result_unit="lbs")
        r1 = _create_result(authed_client, et["id"], value=225, recorded_date="2025-06-01")
        assert r1["is_pr"] is True
        # Second entry is not a PR (lower weight)
        r2 = _create_result(authed_client, et["id"], value=200, recorded_date="2025-06-05")
        assert r2["is_pr"] is False
        # Update r2 to a higher value — should now be a PR
        resp = authed_client.put(f"/api/results/{r2['id']}", json={"value": 250})
        assert resp.status_code == 200
        assert resp.json()["is_pr"] is True

    def test_update_rx_flag_recalculates_pr(self, authed_client: TestClient):
        """Toggling is_rx on a crossfit result should recalculate its PR status."""
        et = _create_exercise_type(
            authed_client, name="Fran", category="crossfit_benchmark", result_unit="seconds"
        )
        # Non-RX fast time
        _create_result(authed_client, et["id"], value=180, recorded_date="2025-06-01", is_rx=False)
        # RX slower time — is a PR because RX > non-RX
        r2 = _create_result(
            authed_client, et["id"], value=300, recorded_date="2025-06-08", is_rx=True
        )
        assert r2["is_pr"] is True
        # Uncheck RX — now it's slower non-RX, not a PR
        resp = authed_client.put(f"/api/results/{r2['id']}", json={"is_rx": False})
        assert resp.status_code == 200
        assert resp.json()["is_pr"] is False

    def test_update_unrelated_field_preserves_pr(self, authed_client: TestClient):
        """Updating notes should not change PR status."""
        et = _create_exercise_type(authed_client, result_unit="lbs")
        r1 = _create_result(authed_client, et["id"], value=225, recorded_date="2025-06-01")
        assert r1["is_pr"] is True
        resp = authed_client.put(f"/api/results/{r1['id']}", json={"notes": "felt good"})
        assert resp.status_code == 200
        assert resp.json()["is_pr"] is True


# ============================================================================
# RX PR Detection (CrossFit time-based)
# ============================================================================


class TestRXPRDetection:
    def test_rx_beats_non_rx_even_with_slower_time(self, authed_client: TestClient):
        """An RX result is always a PR over a non-RX result for time-based crossfit."""
        et = _create_exercise_type(
            authed_client, name="Fran", category="crossfit_benchmark", result_unit="seconds"
        )
        # Non-RX fast time
        _create_result(authed_client, et["id"], value=180, recorded_date="2025-06-01", is_rx=False)
        # RX slower time — should still be PR because RX > non-RX
        data = _create_result(
            authed_client, et["id"], value=300, recorded_date="2025-06-08", is_rx=True
        )
        assert data["is_pr"] is True

    def test_non_rx_does_not_beat_rx(self, authed_client: TestClient):
        """A non-RX result can never be a PR if an RX result exists."""
        et = _create_exercise_type(
            authed_client, name="Grace", category="crossfit_benchmark", result_unit="seconds"
        )
        _create_result(authed_client, et["id"], value=300, recorded_date="2025-06-01", is_rx=True)
        # Non-RX faster time — not a PR because RX exists
        data = _create_result(
            authed_client, et["id"], value=100, recorded_date="2025-06-08", is_rx=False
        )
        assert data["is_pr"] is False

    def test_faster_rx_beats_slower_rx(self, authed_client: TestClient):
        """Within RX results, lower time still wins."""
        et = _create_exercise_type(
            authed_client, name="Helen", category="crossfit_benchmark", result_unit="seconds"
        )
        _create_result(authed_client, et["id"], value=300, recorded_date="2025-06-01", is_rx=True)
        data = _create_result(
            authed_client, et["id"], value=280, recorded_date="2025-06-08", is_rx=True
        )
        assert data["is_pr"] is True

    def test_slower_rx_does_not_beat_faster_rx(self, authed_client: TestClient):
        et = _create_exercise_type(
            authed_client, name="Diane", category="crossfit_benchmark", result_unit="seconds"
        )
        _create_result(authed_client, et["id"], value=200, recorded_date="2025-06-01", is_rx=True)
        data = _create_result(
            authed_client, et["id"], value=250, recorded_date="2025-06-08", is_rx=True
        )
        assert data["is_pr"] is False

    def test_first_rx_result_is_pr(self, authed_client: TestClient):
        et = _create_exercise_type(
            authed_client, name="Karen", category="crossfit_benchmark", result_unit="seconds"
        )
        data = _create_result(
            authed_client, et["id"], value=400, recorded_date="2025-06-01", is_rx=True
        )
        assert data["is_pr"] is True

    def test_rx_does_not_affect_weight_based_pr(self, authed_client: TestClient):
        """RX flag has no effect on PR logic for weight-based exercises."""
        et = _create_exercise_type(
            authed_client, name="Back Squat", category="power_lift", result_unit="lbs"
        )
        _create_result(authed_client, et["id"], value=225, recorded_date="2025-06-01", is_rx=True)
        # Lower weight is not a PR regardless of RX
        data = _create_result(
            authed_client, et["id"], value=215, recorded_date="2025-06-08", is_rx=True
        )
        assert data["is_pr"] is False


# ============================================================================
# Reps-based PR Detection
# ============================================================================


class TestRepsPRDetection:
    def test_higher_reps_is_pr(self, authed_client: TestClient):
        et = _create_exercise_type(
            authed_client, name="Strict Pull-Up", category="custom", result_unit="reps"
        )
        _create_result(authed_client, et["id"], value=10, recorded_date="2025-06-01")
        data = _create_result(authed_client, et["id"], value=15, recorded_date="2025-06-08")
        assert data["is_pr"] is True

    def test_lower_reps_is_not_pr(self, authed_client: TestClient):
        et = _create_exercise_type(
            authed_client, name="Strict Pull-Up", category="custom", result_unit="reps"
        )
        _create_result(authed_client, et["id"], value=15, recorded_date="2025-06-01")
        data = _create_result(authed_client, et["id"], value=10, recorded_date="2025-06-08")
        assert data["is_pr"] is False

    def test_first_reps_entry_is_pr(self, authed_client: TestClient):
        et = _create_exercise_type(
            authed_client, name="Strict Pull-Up", category="custom", result_unit="reps"
        )
        data = _create_result(authed_client, et["id"], value=8, recorded_date="2025-06-01")
        assert data["is_pr"] is True


# ============================================================================
# PR History Endpoint
# ============================================================================


class TestPRHistory:
    def test_pr_history_returns_prs_only(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client, result_unit="lbs")
        _create_result(authed_client, et["id"], value=225, recorded_date="2025-06-01")
        _create_result(authed_client, et["id"], value=215, recorded_date="2025-06-05")
        _create_result(authed_client, et["id"], value=235, recorded_date="2025-06-10")
        resp = authed_client.get(f"/api/results/prs/{et['id']}")
        assert resp.status_code == 200
        prs = resp.json()
        assert len(prs) == 2
        assert prs[0]["value"] == 225
        assert prs[1]["value"] == 235

    def test_pr_history_nonexistent_exercise_returns_404(self, authed_client: TestClient):
        resp = authed_client.get("/api/results/prs/nonexistent")
        assert resp.status_code == 404


# ============================================================================
# Trend Endpoint
# ============================================================================


class TestResultTrend:
    def test_trend_returns_correct_data(self, authed_client: TestClient):
        et = _create_exercise_type(authed_client, result_unit="lbs")
        _create_result(authed_client, et["id"], value=225, recorded_date="2025-06-01")
        _create_result(authed_client, et["id"], value=235, recorded_date="2025-06-08")
        resp = authed_client.get(f"/api/results/trends/{et['id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["exercise_type_id"] == et["id"]
        assert body["exercise_name"] == "Back Squat"
        assert body["result_unit"] == "lbs"
        assert len(body["data"]) == 2
        assert body["data"][0]["value"] == 225
        assert body["data"][1]["value"] == 235

    def test_trend_nonexistent_exercise_returns_404(self, authed_client: TestClient):
        resp = authed_client.get("/api/results/trends/nonexistent")
        assert resp.status_code == 404
