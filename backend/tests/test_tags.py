"""Tests for entity tags (Phase 3 — Digital Thread)."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricType
from app.models.result import ExerciseType
from app.models.tag import EntityTag
from app.services import tags as tag_service


@pytest.fixture()
def sample_goal(db):
    g = Goal(
        title="Squat 405",
        target_type="result",
        target_id="et-1",
        target_value=405,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@pytest.fixture()
def sample_journal(db):
    j = JournalEntry(title="Leg Day", content="Great workout", entry_date=date(2026, 4, 1))
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


@pytest.fixture()
def sample_metric_type(db):
    mt = MetricType(name="Body Weight", unit="lbs")
    db.add(mt)
    db.commit()
    db.refresh(mt)
    return mt


@pytest.fixture()
def sample_exercise_type(db):
    et = ExerciseType(name="Back Squat", category="power_lift", result_unit="lbs")
    db.add(et)
    db.commit()
    db.refresh(et)
    return et


# ---------------------------------------------------------------------------
# Tag service unit tests
# ---------------------------------------------------------------------------


class TestAddTag:
    def test_add_tag(self, db, sample_goal):
        tag = tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        assert tag.tag == "strength"
        assert tag.entity_type == "goal"
        assert tag.entity_id == sample_goal.id

    def test_add_tag_normalized(self, db, sample_goal):
        tag = tag_service.add_tag(db, "goal", sample_goal.id, "  Strength  ")
        assert tag.tag == "strength"

    def test_add_tag_idempotent(self, db, sample_goal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tags = tag_service.get_tags(db, "goal", sample_goal.id)
        assert tags == ["strength"]


class TestRemoveTag:
    def test_remove_tag(self, db, sample_goal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tag_service.remove_tag(db, "goal", sample_goal.id, "strength")
        tags = tag_service.get_tags(db, "goal", sample_goal.id)
        assert tags == []

    def test_remove_nonexistent_tag(self, db, sample_goal):
        # Should not raise
        tag_service.remove_tag(db, "goal", sample_goal.id, "nonexistent")


class TestGetTags:
    def test_get_tags(self, db, sample_goal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tag_service.add_tag(db, "goal", sample_goal.id, "lower body")
        tags = tag_service.get_tags(db, "goal", sample_goal.id)
        assert sorted(tags) == ["lower body", "strength"]


class TestSyncTags:
    def test_sync_tags_adds_new(self, db, sample_goal):
        tag_service.sync_tags(db, "goal", sample_goal.id, ["strength", "lower body"])
        tags = tag_service.get_tags(db, "goal", sample_goal.id)
        assert sorted(tags) == ["lower body", "strength"]

    def test_sync_tags_removes_missing(self, db, sample_goal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tag_service.add_tag(db, "goal", sample_goal.id, "old-tag")
        tag_service.sync_tags(db, "goal", sample_goal.id, ["strength", "new-tag"])
        tags = tag_service.get_tags(db, "goal", sample_goal.id)
        assert sorted(tags) == ["new-tag", "strength"]

    def test_sync_tags_empty_clears_all(self, db, sample_goal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tag_service.sync_tags(db, "goal", sample_goal.id, [])
        tags = tag_service.get_tags(db, "goal", sample_goal.id)
        assert tags == []


class TestListAllTags:
    def test_list_all_tags(self, db, sample_goal, sample_journal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tag_service.add_tag(db, "journal", sample_journal.id, "strength")
        tag_service.add_tag(db, "goal", sample_goal.id, "recovery")
        result = tag_service.list_all_tags(db)
        assert len(result) == 2
        # Sorted by count desc
        assert result[0]["tag"] == "strength"
        assert result[0]["count"] == 2
        assert result[1]["tag"] == "recovery"
        assert result[1]["count"] == 1


class TestGetEntitiesByTag:
    def test_get_entities_by_tag(self, db, sample_goal, sample_journal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tag_service.add_tag(db, "journal", sample_journal.id, "strength")
        entities = tag_service.get_entities_by_tag(db, "strength")
        assert len(entities) == 2
        types = {e["entity_type"] for e in entities}
        assert types == {"goal", "journal"}

    def test_get_entities_by_tag_filtered(self, db, sample_goal, sample_journal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        tag_service.add_tag(db, "journal", sample_journal.id, "strength")
        entities = tag_service.get_entities_by_tag(db, "strength", entity_type="goal")
        assert len(entities) == 1
        assert entities[0]["entity_type"] == "goal"

    def test_get_entities_by_tag_includes_title(self, db, sample_goal):
        tag_service.add_tag(db, "goal", sample_goal.id, "strength")
        entities = tag_service.get_entities_by_tag(db, "strength")
        assert entities[0]["title"] == "Squat 405"


# ---------------------------------------------------------------------------
# API integration tests — tags on entity CRUD
# ---------------------------------------------------------------------------


class TestJournalTagsCRUD:
    def test_journal_create_with_tags(self, authed_client: TestClient):
        res = authed_client.post(
            "/api/journals",
            json={
                "title": "Leg Day",
                "content": "Tagged workout",
                "entry_date": "2026-04-01",
                "tags": ["strength", "lower body"],
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert sorted(data["tags"]) == ["lower body", "strength"]

    def test_journal_update_tags(self, authed_client: TestClient):
        res = authed_client.post(
            "/api/journals",
            json={
                "title": "Leg Day",
                "content": "workout",
                "entry_date": "2026-04-01",
                "tags": ["strength"],
            },
        )
        journal_id = res.json()["id"]
        res = authed_client.put(
            f"/api/journals/{journal_id}",
            json={"tags": ["recovery", "mobility"]},
        )
        assert res.status_code == 200
        assert sorted(res.json()["tags"]) == ["mobility", "recovery"]

    def test_journal_list_filter_by_tag(self, authed_client: TestClient):
        authed_client.post(
            "/api/journals",
            json={
                "title": "Tagged",
                "content": "a",
                "entry_date": "2026-04-01",
                "tags": ["strength"],
            },
        )
        authed_client.post(
            "/api/journals",
            json={
                "title": "Untagged",
                "content": "b",
                "entry_date": "2026-04-01",
            },
        )
        res = authed_client.get("/api/journals?tag=strength")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Tagged"


class TestGoalTagsCRUD:
    def _create_metric_type(self, client: TestClient) -> str:
        res = client.post("/api/metric-types", json={"name": "Weight", "unit": "lbs"})
        return res.json()["id"]

    def test_goal_create_with_tags(self, authed_client: TestClient):
        mt_id = self._create_metric_type(authed_client)
        res = authed_client.post(
            "/api/goals",
            json={
                "title": "Lose weight",
                "target_type": "metric",
                "target_id": mt_id,
                "target_value": 180,
                "tags": ["nutrition", "health"],
            },
        )
        assert res.status_code == 201
        assert sorted(res.json()["tags"]) == ["health", "nutrition"]

    def test_goal_list_filter_by_tag(self, authed_client: TestClient):
        mt_id = self._create_metric_type(authed_client)
        authed_client.post(
            "/api/goals",
            json={
                "title": "Tagged Goal",
                "target_type": "metric",
                "target_id": mt_id,
                "target_value": 180,
                "tags": ["nutrition"],
            },
        )
        authed_client.post(
            "/api/goals",
            json={
                "title": "Untagged Goal",
                "target_type": "metric",
                "target_id": mt_id,
                "target_value": 200,
            },
        )
        res = authed_client.get("/api/goals?tag=nutrition")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Tagged Goal"


class TestMetricTypeTagsCRUD:
    def test_metric_type_create_with_tags(self, authed_client: TestClient):
        res = authed_client.post(
            "/api/metric-types",
            json={"name": "Body Weight", "unit": "lbs", "tags": ["health"]},
        )
        assert res.status_code == 201
        assert res.json()["tags"] == ["health"]

    def test_metric_type_list_filter_by_tag(self, authed_client: TestClient):
        authed_client.post(
            "/api/metric-types",
            json={"name": "Body Weight", "unit": "lbs", "tags": ["health"]},
        )
        authed_client.post(
            "/api/metric-types",
            json={"name": "Sleep", "unit": "hours"},
        )
        res = authed_client.get("/api/metric-types?tag=health")
        assert res.status_code == 200
        items = res.json()
        assert len(items) == 1
        assert items[0]["name"] == "Body Weight"


class TestExerciseTypeTagsCRUD:
    def test_exercise_type_create_with_tags(self, authed_client: TestClient):
        res = authed_client.post(
            "/api/exercise-types",
            json={
                "name": "Back Squat",
                "category": "power_lift",
                "result_unit": "lbs",
                "tags": ["strength", "lower body"],
            },
        )
        assert res.status_code == 201
        assert sorted(res.json()["tags"]) == ["lower body", "strength"]

    def test_exercise_type_list_filter_by_tag(self, authed_client: TestClient):
        authed_client.post(
            "/api/exercise-types",
            json={
                "name": "Back Squat",
                "category": "power_lift",
                "result_unit": "lbs",
                "tags": ["strength"],
            },
        )
        authed_client.post(
            "/api/exercise-types",
            json={
                "name": "Fran",
                "category": "crossfit_benchmark",
                "result_unit": "seconds",
            },
        )
        res = authed_client.get("/api/exercise-types?tag=strength")
        assert res.status_code == 200
        items = res.json()
        assert len(items) == 1
        assert items[0]["name"] == "Back Squat"


# ---------------------------------------------------------------------------
# Tags endpoints
# ---------------------------------------------------------------------------


class TestTagsEndpoints:
    def test_list_all_tags(self, authed_client: TestClient):
        # Create entities with tags
        authed_client.post(
            "/api/journals",
            json={
                "title": "A",
                "content": "a",
                "entry_date": "2026-04-01",
                "tags": ["strength", "recovery"],
            },
        )
        mt_res = authed_client.post(
            "/api/metric-types",
            json={"name": "Weight", "unit": "lbs", "tags": ["strength"]},
        )
        assert mt_res.status_code == 201

        res = authed_client.get("/api/tags")
        assert res.status_code == 200
        data = res.json()
        tags = {t["tag"]: t["count"] for t in data}
        assert tags["strength"] == 2
        assert tags["recovery"] == 1

    def test_get_entities_by_tag(self, authed_client: TestClient):
        authed_client.post(
            "/api/journals",
            json={
                "title": "Tagged Journal",
                "content": "x",
                "entry_date": "2026-04-01",
                "tags": ["strength"],
            },
        )
        res = authed_client.get("/api/tags/strength")
        assert res.status_code == 200
        data = res.json()
        assert data["tag"] == "strength"
        assert len(data["entities"]) == 1
        assert data["entities"][0]["title"] == "Tagged Journal"

    def test_get_entities_by_tag_type_filter(self, authed_client: TestClient):
        authed_client.post(
            "/api/journals",
            json={
                "title": "J",
                "content": "x",
                "entry_date": "2026-04-01",
                "tags": ["strength"],
            },
        )
        authed_client.post(
            "/api/metric-types",
            json={"name": "Weight", "unit": "lbs", "tags": ["strength"]},
        )
        res = authed_client.get("/api/tags/strength?type=journal")
        assert res.status_code == 200
        data = res.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["entity_type"] == "journal"


# ---------------------------------------------------------------------------
# Search integration
# ---------------------------------------------------------------------------


class TestTagSearchIntegration:
    def test_tag_in_search_results(self, authed_client: TestClient):
        authed_client.post(
            "/api/journals",
            json={
                "title": "Mobility Work",
                "content": "Stretching session",
                "entry_date": "2026-04-01",
                "tags": ["recovery", "mobility"],
            },
        )
        res = authed_client.get("/api/search?q=mobility")
        assert res.status_code == 200
        results = res.json()["results"]
        assert len(results) >= 1


# ---------------------------------------------------------------------------
# Cascade delete
# ---------------------------------------------------------------------------


class TestTagCascadeDelete:
    def test_delete_journal_removes_tags(self, authed_client: TestClient, db):
        res = authed_client.post(
            "/api/journals",
            json={
                "title": "To Delete",
                "content": "bye",
                "entry_date": "2026-04-01",
                "tags": ["temp"],
            },
        )
        journal_id = res.json()["id"]
        authed_client.delete(f"/api/journals/{journal_id}")
        tags = (
            db.query(EntityTag)
            .filter(
                EntityTag.entity_type == "journal",
                EntityTag.entity_id == journal_id,
            )
            .all()
        )
        assert tags == []

    def test_delete_goal_removes_tags(self, authed_client: TestClient, db):
        mt_res = authed_client.post(
            "/api/metric-types",
            json={"name": "Weight", "unit": "lbs"},
        )
        mt_id = mt_res.json()["id"]
        res = authed_client.post(
            "/api/goals",
            json={
                "title": "Tagged Goal",
                "target_type": "metric",
                "target_id": mt_id,
                "target_value": 180,
                "tags": ["temp"],
            },
        )
        goal_id = res.json()["id"]
        authed_client.delete(f"/api/goals/{goal_id}")
        tags = (
            db.query(EntityTag)
            .filter(
                EntityTag.entity_type == "goal",
                EntityTag.entity_id == goal_id,
            )
            .all()
        )
        assert tags == []


# ---------------------------------------------------------------------------
# Export/Import
# ---------------------------------------------------------------------------


class TestTagExportImport:
    def test_export_includes_tags(self, authed_client: TestClient):
        authed_client.post(
            "/api/journals",
            json={
                "title": "Tagged",
                "content": "x",
                "entry_date": "2026-04-01",
                "tags": ["strength"],
            },
        )
        res = authed_client.get("/api/export/json")
        assert res.status_code == 200
        data = res.json()
        assert "entity_tags" in data
        assert len(data["entity_tags"]) == 1
        assert data["entity_tags"][0]["tag"] == "strength"

    def test_import_restores_tags(self, authed_client: TestClient, db):
        # Create and export
        authed_client.post(
            "/api/journals",
            json={
                "title": "Tagged",
                "content": "x",
                "entry_date": "2026-04-01",
                "tags": ["strength", "recovery"],
            },
        )
        export_res = authed_client.get("/api/export/json")
        export_data = export_res.json()

        # Clear all data
        from app.models import Goal, JournalEntry, MetricEntry, ResultEntry

        db.query(EntityTag).delete()
        db.query(Goal).delete()
        db.query(ResultEntry).delete()
        db.query(MetricEntry).delete()
        db.query(JournalEntry).delete()
        db.commit()

        # Import
        res = authed_client.post("/api/import/json", json=export_data)
        assert res.status_code == 200

        # Verify tags are restored
        tags = db.query(EntityTag).all()
        assert len(tags) == 2
        tag_names = sorted(t.tag for t in tags)
        assert tag_names == ["recovery", "strength"]
