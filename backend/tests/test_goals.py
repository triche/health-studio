"""Tests for Goals CRUD and progress computation."""

from __future__ import annotations


def _create_metric_type(authed_client, name="Weight", unit="lbs"):
    r = authed_client.post("/api/metric-types", json={"name": name, "unit": unit})
    assert r.status_code == 201
    return r.json()


def _create_exercise_type(
    authed_client, name="Back Squat", category="power_lift", result_unit="lbs"
):
    r = authed_client.post(
        "/api/exercise-types",
        json={"name": name, "category": category, "result_unit": result_unit},
    )
    assert r.status_code == 201
    return r.json()


def _create_goal(authed_client, **overrides):
    payload = {
        "title": "Lose Weight",
        "description": "Get to 180 lbs",
        "plan": "## Steps\n- Eat less\n- Move more",
        "target_type": "metric",
        "target_id": "some-id",
        "target_value": 180.0,
        "status": "active",
    }
    payload.update(overrides)
    r = authed_client.post("/api/goals", json=payload)
    return r


def _log_metric(authed_client, metric_type_id, value, recorded_date="2025-01-15"):
    return authed_client.post(
        "/api/metrics",
        json={
            "metric_type_id": metric_type_id,
            "value": value,
            "recorded_date": recorded_date,
        },
    )


def _log_result(authed_client, exercise_type_id, value, recorded_date="2025-01-15"):
    return authed_client.post(
        "/api/results",
        json={
            "exercise_type_id": exercise_type_id,
            "value": value,
            "recorded_date": recorded_date,
        },
    )


class TestGoalCRUD:
    def test_create_goal(self, authed_client):
        mt = _create_metric_type(authed_client)
        r = _create_goal(authed_client, target_id=mt["id"])
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Lose Weight"
        assert data["target_type"] == "metric"
        assert data["target_value"] == 180.0
        assert data["status"] == "active"
        assert data["current_value"] == 0.0
        assert "id" in data

    def test_create_goal_with_deadline(self, authed_client):
        mt = _create_metric_type(authed_client)
        r = _create_goal(authed_client, target_id=mt["id"], deadline="2025-12-31")
        assert r.status_code == 201
        assert r.json()["deadline"] == "2025-12-31"

    def test_create_goal_without_deadline(self, authed_client):
        mt = _create_metric_type(authed_client)
        r = _create_goal(authed_client, target_id=mt["id"])
        assert r.status_code == 201
        assert r.json()["deadline"] is None

    def test_get_goal(self, authed_client):
        mt = _create_metric_type(authed_client)
        goal = _create_goal(authed_client, target_id=mt["id"]).json()
        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == goal["id"]
        assert r.json()["title"] == "Lose Weight"

    def test_get_goal_not_found(self, authed_client):
        r = authed_client.get("/api/goals/nonexistent")
        assert r.status_code == 404

    def test_list_goals(self, authed_client):
        mt = _create_metric_type(authed_client)
        _create_goal(authed_client, target_id=mt["id"], title="Goal 1")
        _create_goal(authed_client, target_id=mt["id"], title="Goal 2")
        r = authed_client.get("/api/goals")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_list_goals_filter_by_status(self, authed_client):
        mt = _create_metric_type(authed_client)
        _create_goal(authed_client, target_id=mt["id"], title="Active Goal", status="active")
        g2 = _create_goal(authed_client, target_id=mt["id"], title="Completed Goal").json()
        authed_client.put(f"/api/goals/{g2['id']}", json={"status": "completed"})

        r = authed_client.get("/api/goals?status=active")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Active Goal"

    def test_update_goal(self, authed_client):
        mt = _create_metric_type(authed_client)
        goal = _create_goal(authed_client, target_id=mt["id"]).json()
        r = authed_client.put(
            f"/api/goals/{goal['id']}",
            json={"title": "Updated Title", "status": "completed"},
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Title"
        assert r.json()["status"] == "completed"

    def test_update_goal_partial(self, authed_client):
        mt = _create_metric_type(authed_client)
        goal = _create_goal(authed_client, target_id=mt["id"]).json()
        r = authed_client.put(f"/api/goals/{goal['id']}", json={"plan": "New plan"})
        assert r.status_code == 200
        assert r.json()["plan"] == "New plan"
        assert r.json()["title"] == "Lose Weight"  # unchanged

    def test_update_goal_not_found(self, authed_client):
        r = authed_client.put("/api/goals/nonexistent", json={"title": "X"})
        assert r.status_code == 404

    def test_delete_goal(self, authed_client):
        mt = _create_metric_type(authed_client)
        goal = _create_goal(authed_client, target_id=mt["id"]).json()
        r = authed_client.delete(f"/api/goals/{goal['id']}")
        assert r.status_code == 204
        r2 = authed_client.get(f"/api/goals/{goal['id']}")
        assert r2.status_code == 404

    def test_delete_goal_not_found(self, authed_client):
        r = authed_client.delete("/api/goals/nonexistent")
        assert r.status_code == 404


class TestGoalProgress:
    def test_metric_goal_current_value_from_latest_entry(self, authed_client):
        """current_value should reflect the latest metric entry for the target metric type."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client, target_type="metric", target_id=mt["id"], target_value=180.0
        ).json()
        _log_metric(authed_client, mt["id"], 200.0, "2025-01-01")
        _log_metric(authed_client, mt["id"], 190.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.status_code == 200
        assert r.json()["current_value"] == 190.0

    def test_result_goal_current_value_from_best_result(self, authed_client):
        """current_value should reflect the best (PR) result for the target exercise type."""
        et = _create_exercise_type(authed_client)
        goal = _create_goal(
            authed_client, target_type="result", target_id=et["id"], target_value=300.0
        ).json()
        _log_result(authed_client, et["id"], 225.0, "2025-01-01")
        _log_result(authed_client, et["id"], 250.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.status_code == 200
        assert r.json()["current_value"] == 250.0

    def test_progress_percentage_in_response(self, authed_client):
        """Goal response should include progress percentage."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client, target_type="metric", target_id=mt["id"], target_value=180.0
        ).json()
        _log_metric(authed_client, mt["id"], 190.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        data = r.json()
        # progress is included
        assert "progress" in data


class TestLowerIsBetter:
    """Tests for the lower_is_better flag on goals."""

    def test_create_goal_default_lower_is_better_false(self, authed_client):
        """Goals should default to lower_is_better=False."""
        mt = _create_metric_type(authed_client)
        r = _create_goal(authed_client, target_id=mt["id"])
        assert r.status_code == 201
        assert r.json()["lower_is_better"] is False

    def test_create_goal_with_lower_is_better_true(self, authed_client):
        """Goals can be created with lower_is_better=True."""
        mt = _create_metric_type(authed_client)
        r = _create_goal(authed_client, target_id=mt["id"], lower_is_better=True)
        assert r.status_code == 201
        assert r.json()["lower_is_better"] is True

    def test_update_goal_lower_is_better(self, authed_client):
        """lower_is_better can be toggled via update."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(authed_client, target_id=mt["id"]).json()
        assert goal["lower_is_better"] is False

        r = authed_client.put(f"/api/goals/{goal['id']}", json={"lower_is_better": True})
        assert r.status_code == 200
        assert r.json()["lower_is_better"] is True

    def test_lower_is_better_progress_above_target(self, authed_client):
        """When lower_is_better without start_value, current > target means incomplete.

        With target=240, current=253: progress = (240/253)*100 ≈ 94.9
        """
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="metric",
            target_id=mt["id"],
            target_value=240.0,
            lower_is_better=True,
        ).json()
        _log_metric(authed_client, mt["id"], 253.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        data = r.json()
        assert data["current_value"] == 253.0
        assert 94.0 < data["progress"] < 95.5  # ~94.9%

    def test_lower_is_better_progress_at_target(self, authed_client):
        """When lower_is_better and current == target, progress = 100%."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="metric",
            target_id=mt["id"],
            target_value=240.0,
            lower_is_better=True,
        ).json()
        _log_metric(authed_client, mt["id"], 240.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.json()["progress"] == 100.0

    def test_lower_is_better_progress_below_target(self, authed_client):
        """When lower_is_better and current < target, progress = 100%."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="metric",
            target_id=mt["id"],
            target_value=240.0,
            lower_is_better=True,
        ).json()
        _log_metric(authed_client, mt["id"], 235.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.json()["progress"] == 100.0

    def test_higher_is_better_still_works(self, authed_client):
        """Normal higher-is-better goals are unaffected (target=300, current=250 → 83.3%)."""
        et = _create_exercise_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="result",
            target_id=et["id"],
            target_value=300.0,
            lower_is_better=False,
        ).json()
        _log_result(authed_client, et["id"], 250.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        data = r.json()
        assert 83.0 < data["progress"] < 84.0  # ~83.3%


class TestStartValue:
    """Tests for the start_value field on goals."""

    def test_create_goal_default_start_value_none(self, authed_client):
        """Goals should default to start_value=None."""
        mt = _create_metric_type(authed_client)
        r = _create_goal(authed_client, target_id=mt["id"])
        assert r.status_code == 201
        assert r.json()["start_value"] is None

    def test_create_goal_with_start_value(self, authed_client):
        """Goals can be created with a start_value."""
        mt = _create_metric_type(authed_client)
        r = _create_goal(authed_client, target_id=mt["id"], start_value=253.0)
        assert r.status_code == 201
        assert r.json()["start_value"] == 253.0

    def test_update_goal_start_value(self, authed_client):
        """start_value can be set via update."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(authed_client, target_id=mt["id"]).json()
        r = authed_client.put(f"/api/goals/{goal['id']}", json={"start_value": 253.0})
        assert r.status_code == 200
        assert r.json()["start_value"] == 253.0

    def test_lower_is_better_with_start_value(self, authed_client):
        """Progress from start=253 to target=240 with current=247.

        progress = (253 - 247) / (253 - 240) * 100 = 6/13 * 100 ≈ 46.2%
        """
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="metric",
            target_id=mt["id"],
            target_value=240.0,
            start_value=253.0,
            lower_is_better=True,
        ).json()
        _log_metric(authed_client, mt["id"], 247.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        data = r.json()
        assert data["current_value"] == 247.0
        assert 45.0 < data["progress"] < 47.0  # ~46.2%

    def test_lower_is_better_with_start_value_at_goal(self, authed_client):
        """When current has reached target, progress = 100%."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="metric",
            target_id=mt["id"],
            target_value=240.0,
            start_value=253.0,
            lower_is_better=True,
        ).json()
        _log_metric(authed_client, mt["id"], 240.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.json()["progress"] == 100.0

    def test_lower_is_better_with_start_value_past_goal(self, authed_client):
        """When current is past (below) target, progress = 100%."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="metric",
            target_id=mt["id"],
            target_value=240.0,
            start_value=253.0,
            lower_is_better=True,
        ).json()
        _log_metric(authed_client, mt["id"], 235.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.json()["progress"] == 100.0

    def test_lower_is_better_with_start_value_worse_than_start(self, authed_client):
        """When current is worse (higher) than start, progress = 0%."""
        mt = _create_metric_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="metric",
            target_id=mt["id"],
            target_value=240.0,
            start_value=253.0,
            lower_is_better=True,
        ).json()
        _log_metric(authed_client, mt["id"], 260.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.json()["progress"] == 0.0

    def test_higher_is_better_with_start_value(self, authed_client):
        """Progress from start=200 to target=300 with current=250.

        progress = (250 - 200) / (300 - 200) * 100 = 50/100 = 50%
        """
        et = _create_exercise_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="result",
            target_id=et["id"],
            target_value=300.0,
            start_value=200.0,
            lower_is_better=False,
        ).json()
        _log_result(authed_client, et["id"], 250.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        data = r.json()
        assert data["progress"] == 50.0

    def test_higher_is_better_with_start_value_at_goal(self, authed_client):
        """When current has reached target, progress = 100%."""
        et = _create_exercise_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="result",
            target_id=et["id"],
            target_value=300.0,
            start_value=200.0,
            lower_is_better=False,
        ).json()
        _log_result(authed_client, et["id"], 300.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.json()["progress"] == 100.0

    def test_higher_is_better_with_start_value_below_start(self, authed_client):
        """When current is below start, progress = 0%."""
        et = _create_exercise_type(authed_client)
        goal = _create_goal(
            authed_client,
            target_type="result",
            target_id=et["id"],
            target_value=300.0,
            start_value=200.0,
            lower_is_better=False,
        ).json()
        _log_result(authed_client, et["id"], 190.0, "2025-01-15")

        r = authed_client.get(f"/api/goals/{goal['id']}")
        assert r.json()["progress"] == 0.0


class TestDashboardSummary:
    def test_dashboard_returns_structure(self, authed_client):
        r = authed_client.get("/api/dashboard/summary")
        assert r.status_code == 200
        data = r.json()
        assert "recent_journals" in data
        assert "active_goals" in data
        assert "latest_metrics" in data
        assert "recent_prs" in data

    def test_dashboard_recent_journals(self, authed_client):
        for i in range(7):
            authed_client.post(
                "/api/journals",
                json={
                    "title": f"Entry {i}",
                    "content": "text",
                    "entry_date": f"2025-01-{i + 1:02d}",
                },
            )
        r = authed_client.get("/api/dashboard/summary")
        data = r.json()
        assert len(data["recent_journals"]) <= 5

    def test_dashboard_active_goals(self, authed_client):
        mt = _create_metric_type(authed_client)
        _create_goal(authed_client, target_id=mt["id"], title="Active", status="active")
        g2 = _create_goal(authed_client, target_id=mt["id"], title="Done").json()
        authed_client.put(f"/api/goals/{g2['id']}", json={"status": "completed"})

        r = authed_client.get("/api/dashboard/summary")
        data = r.json()
        assert len(data["active_goals"]) == 1
        assert data["active_goals"][0]["title"] == "Active"

    def test_dashboard_latest_metrics(self, authed_client):
        mt1 = _create_metric_type(authed_client, name="Weight", unit="lbs")
        mt2 = _create_metric_type(authed_client, name="Steps", unit="count")
        _log_metric(authed_client, mt1["id"], 185.0, "2025-01-01")
        _log_metric(authed_client, mt2["id"], 10000, "2025-01-02")

        r = authed_client.get("/api/dashboard/summary")
        data = r.json()
        assert len(data["latest_metrics"]) == 2

    def test_dashboard_recent_prs(self, authed_client):
        et = _create_exercise_type(authed_client)
        _log_result(authed_client, et["id"], 225.0, "2025-01-01")
        _log_result(authed_client, et["id"], 250.0, "2025-01-15")

        r = authed_client.get("/api/dashboard/summary")
        data = r.json()
        assert len(data["recent_prs"]) >= 1

    def test_dashboard_goal_progress_matches_goals_page(self, authed_client):
        """Dashboard progress must use lower_is_better and start_value like Goals page."""
        mt = _create_metric_type(authed_client, name="Body Weight", unit="lbs")
        # Goal: lose weight from 200 → 180 (lower_is_better with start_value)
        goal = _create_goal(
            authed_client,
            target_id=mt["id"],
            target_value=180.0,
            start_value=200.0,
            lower_is_better=True,
            title="Lose Weight",
        ).json()
        _log_metric(authed_client, mt["id"], 190.0, "2025-01-15")

        # Get progress from goals page
        goal_resp = authed_client.get(f"/api/goals/{goal['id']}")
        goal_progress = goal_resp.json()["progress"]

        # Get progress from dashboard
        dash_resp = authed_client.get("/api/dashboard/summary")
        dash_goals = dash_resp.json()["active_goals"]
        dash_progress = next(g["progress"] for g in dash_goals if g["id"] == goal["id"])

        assert dash_progress == goal_progress
