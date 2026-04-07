"""Tests for Phase 2 — Global Search (FTS5)."""

from __future__ import annotations

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricType
from app.models.result import ExerciseType
from app.services.search import index_entity, rebuild_index, remove_from_index, search

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_journal(db, *, title="Test Journal", content="Some content", entry_date="2026-04-01"):
    from datetime import date as _date

    entry = JournalEntry(
        title=title,
        content=content,
        entry_date=_date.fromisoformat(entry_date),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _make_goal(db, *, title="Squat 405", description="Get stronger", plan="Linear progression"):
    goal = Goal(
        title=title,
        description=description,
        plan=plan,
        target_type="manual",
        target_id="manual",
        target_value=405.0,
        status="active",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def _make_metric_type(db, *, name="Body Weight", unit="lbs"):
    mt = MetricType(name=name, unit=unit)
    db.add(mt)
    db.commit()
    db.refresh(mt)
    return mt


def _make_exercise_type(db, *, name="Back Squat", category="barbell", result_unit="lbs"):
    et = ExerciseType(name=name, category=category, result_unit=result_unit)
    db.add(et)
    db.commit()
    db.refresh(et)
    return et


# ---------------------------------------------------------------------------
# Unit tests — search service
# ---------------------------------------------------------------------------


class TestIndexEntity:
    def test_index_and_find(self, db):
        journal = _make_journal(db, title="Shoulder rehab session", content="Did mobility drills")
        index_entity(db, "journal", journal.id, "Shoulder rehab session", "Did mobility drills")
        results = search(db, "shoulder")
        assert len(results) == 1
        assert results[0]["entity_type"] == "journal"
        assert results[0]["entity_id"] == journal.id
        assert results[0]["title"] == "Shoulder rehab session"

    def test_index_replaces_on_update(self, db):
        journal = _make_journal(db, title="Old Title", content="old content")
        index_entity(db, "journal", journal.id, "Old Title", "old content")
        # Update
        index_entity(db, "journal", journal.id, "New Title", "new content")
        assert search(db, "Old Title") == []
        results = search(db, "New Title")
        assert len(results) == 1
        assert results[0]["title"] == "New Title"


class TestRemoveFromIndex:
    def test_remove_entity(self, db):
        journal = _make_journal(db, title="To Be Removed", content="temporary")
        index_entity(db, "journal", journal.id, "To Be Removed", "temporary")
        assert len(search(db, "Removed")) == 1
        remove_from_index(db, "journal", journal.id)
        assert search(db, "Removed") == []


class TestRebuildIndex:
    def test_rebuild_indexes_all_entities(self, db):
        _make_journal(db, title="Leg day notes", content="Squatted heavy")
        _make_goal(db, title="Squat 405", description="Big squat goal")
        _make_metric_type(db, name="Body Weight", unit="lbs")
        _make_exercise_type(db, name="Back Squat", category="barbell", result_unit="lbs")

        rebuild_index(db)

        results = search(db, "squat")
        # Should find the journal (body), goal (title), and exercise type (title)
        types = {r["entity_type"] for r in results}
        assert "journal" in types
        assert "goal" in types
        assert "exercise_type" in types

    def test_rebuild_clears_stale_entries(self, db):
        journal = _make_journal(db, title="Keep This", content="keep")
        index_entity(db, "journal", journal.id, "Keep This", "keep")
        # Also index a fake entity that doesn't exist in DB
        index_entity(db, "journal", "fake-id", "Ghost Entry", "should be cleared")
        assert len(search(db, "Ghost")) == 1
        rebuild_index(db)
        assert search(db, "Ghost") == []
        assert len(search(db, "Keep")) == 1


class TestSearch:
    def test_search_journal_by_title(self, db):
        journal = _make_journal(db, title="Shoulder rehab session", content="some content")
        index_entity(db, "journal", journal.id, "Shoulder rehab session", "some content")
        results = search(db, "shoulder")
        assert len(results) == 1
        assert results[0]["entity_type"] == "journal"

    def test_search_journal_by_content(self, db):
        journal = _make_journal(db, title="Morning Notes", content="worked on shoulder mobility")
        index_entity(db, "journal", journal.id, "Morning Notes", "worked on shoulder mobility")
        results = search(db, "mobility")
        assert len(results) == 1

    def test_search_goal_by_title(self, db):
        goal = _make_goal(db, title="Squat 405")
        index_entity(db, "goal", goal.id, "Squat 405", "Get stronger\nLinear progression", "active")
        results = search(db, "squat")
        assert len(results) == 1
        assert results[0]["entity_type"] == "goal"

    def test_search_exercise_type_by_name(self, db):
        et = _make_exercise_type(db, name="Shoulder Press")
        index_entity(db, "exercise_type", et.id, "Shoulder Press", "", "barbell lbs")
        results = search(db, "shoulder press")
        assert len(results) == 1
        assert results[0]["entity_type"] == "exercise_type"

    def test_search_metric_type_by_name(self, db):
        mt = _make_metric_type(db, name="Body Weight")
        index_entity(db, "metric_type", mt.id, "Body Weight", "", "lbs")
        results = search(db, "body weight")
        assert len(results) == 1
        assert results[0]["entity_type"] == "metric_type"

    def test_search_stemming(self, db):
        """'running' should match entry with 'run' via Porter stemming."""
        journal = _make_journal(db, title="Morning Run", content="Went for a run")
        index_entity(db, "journal", journal.id, "Morning Run", "Went for a run")
        results = search(db, "running")
        assert len(results) == 1

    def test_search_prefix(self, db):
        """'squat*' should match 'squatting'."""
        journal = _make_journal(db, title="Leg Day", content="Did some squatting drills")
        index_entity(db, "journal", journal.id, "Leg Day", "Did some squatting drills")
        results = search(db, "squat*")
        assert len(results) == 1

    def test_search_ranking_title_over_body(self, db):
        """Title match should rank higher than body match."""
        j1 = _make_journal(db, title="Shoulder Session", content="Warm up and lift")
        j2 = _make_journal(db, title="Random Notes", content="Need to work on shoulder mobility")
        index_entity(db, "journal", j1.id, "Shoulder Session", "Warm up and lift")
        index_entity(db, "journal", j2.id, "Random Notes", "Need to work on shoulder mobility")
        results = search(db, "shoulder")
        assert len(results) == 2
        # Title match should come first (lower/more negative rank = better in BM25)
        assert results[0]["title"] == "Shoulder Session"

    def test_search_type_filter(self, db):
        journal = _make_journal(db, title="Shoulder Day", content="Did overhead work")
        goal = _make_goal(db, title="Shoulder Strength")
        index_entity(db, "journal", journal.id, "Shoulder Day", "Did overhead work")
        index_entity(db, "goal", goal.id, "Shoulder Strength", "")
        # Filter to journals only
        results = search(db, "shoulder", entity_types=["journal"])
        assert len(results) == 1
        assert results[0]["entity_type"] == "journal"

    def test_search_pagination(self, db):
        for i in range(5):
            j = _make_journal(db, title=f"Shoulder Entry {i}", content=f"shoulder content {i}")
            index_entity(db, "journal", j.id, f"Shoulder Entry {i}", f"shoulder content {i}")

        page1 = search(db, "shoulder", limit=2, offset=0)
        page2 = search(db, "shoulder", limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        # No overlap
        ids1 = {r["entity_id"] for r in page1}
        ids2 = {r["entity_id"] for r in page2}
        assert ids1.isdisjoint(ids2)

    def test_search_empty_query(self, db):
        results = search(db, "")
        assert results == []

    def test_search_no_results(self, db):
        _make_journal(db, title="Leg Day", content="Squatted heavy")
        index_entity(db, "journal", "some-id", "Leg Day", "Squatted heavy")
        results = search(db, "swimming")
        assert results == []


# ---------------------------------------------------------------------------
# Integration tests — index sync via CRUD endpoints
# ---------------------------------------------------------------------------


class TestSearchIndexSyncOnCreate:
    def test_journal_appears_in_search_after_create(self, authed_client, db):
        resp = authed_client.post(
            "/api/journals",
            json={
                "title": "Shoulder Rehab",
                "content": "mobility work",
                "entry_date": "2026-04-01",
            },
        )
        assert resp.status_code == 201
        results = search(db, "shoulder")
        assert len(results) == 1
        assert results[0]["entity_type"] == "journal"

    def test_goal_appears_in_search_after_create(self, authed_client, db):
        resp = authed_client.post(
            "/api/goals",
            json={
                "title": "Squat 405",
                "description": "Hit a big squat",
                "target_type": "manual",
                "target_id": "manual",
                "target_value": 405,
            },
        )
        assert resp.status_code == 201
        results = search(db, "squat")
        assert len(results) == 1
        assert results[0]["entity_type"] == "goal"

    def test_metric_type_appears_in_search_after_create(self, authed_client, db):
        resp = authed_client.post(
            "/api/metric-types",
            json={"name": "Body Weight", "unit": "lbs"},
        )
        assert resp.status_code == 201
        results = search(db, "body weight")
        assert len(results) == 1
        assert results[0]["entity_type"] == "metric_type"

    def test_exercise_type_appears_in_search_after_create(self, authed_client, db):
        resp = authed_client.post(
            "/api/exercise-types",
            json={"name": "Shoulder Press", "category": "barbell", "result_unit": "lbs"},
        )
        assert resp.status_code == 201
        results = search(db, "shoulder press")
        assert len(results) == 1
        assert results[0]["entity_type"] == "exercise_type"


class TestSearchIndexSyncOnUpdate:
    def test_journal_updated_in_search(self, authed_client, db):
        resp = authed_client.post(
            "/api/journals",
            json={"title": "Old Title", "content": "old stuff", "entry_date": "2026-04-01"},
        )
        journal_id = resp.json()["id"]
        authed_client.put(
            f"/api/journals/{journal_id}",
            json={"title": "New Shoulder Title", "content": "new shoulder content"},
        )
        assert search(db, "old stuff") == []
        results = search(db, "new shoulder")
        assert len(results) == 1

    def test_goal_updated_in_search(self, authed_client, db):
        resp = authed_client.post(
            "/api/goals",
            json={
                "title": "Old Goal",
                "target_type": "manual",
                "target_id": "manual",
                "target_value": 100,
            },
        )
        goal_id = resp.json()["id"]
        authed_client.put(
            f"/api/goals/{goal_id}",
            json={"title": "Bench 315"},
        )
        assert search(db, "Old Goal") == []
        results = search(db, "Bench")
        assert len(results) == 1


class TestSearchIndexSyncOnDelete:
    def test_journal_removed_from_search(self, authed_client, db):
        resp = authed_client.post(
            "/api/journals",
            json={"title": "Temporary Entry", "content": "tmp", "entry_date": "2026-04-01"},
        )
        journal_id = resp.json()["id"]
        assert len(search(db, "Temporary")) == 1
        authed_client.delete(f"/api/journals/{journal_id}")
        assert search(db, "Temporary") == []

    def test_goal_removed_from_search(self, authed_client, db):
        resp = authed_client.post(
            "/api/goals",
            json={
                "title": "Doomed Goal",
                "target_type": "manual",
                "target_id": "manual",
                "target_value": 100,
            },
        )
        goal_id = resp.json()["id"]
        assert len(search(db, "Doomed")) == 1
        authed_client.delete(f"/api/goals/{goal_id}")
        assert search(db, "Doomed") == []


# ---------------------------------------------------------------------------
# Integration tests — search API endpoint
# ---------------------------------------------------------------------------


class TestSearchEndpoint:
    def test_search_returns_results(self, authed_client, db):
        authed_client.post(
            "/api/journals",
            json={
                "title": "Shoulder Rehab",
                "content": "mobility drills",
                "entry_date": "2026-04-01",
            },
        )
        resp = authed_client.get("/api/search", params={"q": "shoulder"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "shoulder"
        assert len(data["results"]) == 1
        assert data["total"] == 1
        assert data["results"][0]["entity_type"] == "journal"
        assert data["results"][0]["title"] == "Shoulder Rehab"

    def test_search_type_filter_via_api(self, authed_client, db):
        authed_client.post(
            "/api/journals",
            json={"title": "Shoulder Work", "content": "overhead", "entry_date": "2026-04-01"},
        )
        authed_client.post(
            "/api/goals",
            json={
                "title": "Shoulder Strength",
                "target_type": "manual",
                "target_id": "manual",
                "target_value": 200,
            },
        )
        resp = authed_client.get("/api/search", params={"q": "shoulder", "types": "goal"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["entity_type"] == "goal"

    def test_search_empty_query_returns_empty(self, authed_client, db):
        resp = authed_client.get("/api/search", params={"q": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []
        assert data["total"] == 0

    def test_search_pagination_via_api(self, authed_client, db):
        for i in range(5):
            authed_client.post(
                "/api/journals",
                json={
                    "title": f"Shoulder Entry {i}",
                    "content": f"shoulder content {i}",
                    "entry_date": "2026-04-01",
                },
            )
        resp = authed_client.get("/api/search", params={"q": "shoulder", "limit": 2, "offset": 0})
        data = resp.json()
        assert len(data["results"]) == 2

    def test_search_requires_auth(self, client, db):
        resp = client.get("/api/search", params={"q": "test"})
        assert resp.status_code == 401


class TestSearchRebuildOnImport:
    def test_import_rebuilds_search_index(self, authed_client, db):
        payload = {
            "version": 1,
            "metric_types": [{"id": "mt-1", "name": "Body Weight", "unit": "lbs"}],
            "exercise_types": [
                {"id": "et-1", "name": "Back Squat", "category": "barbell", "result_unit": "lbs"}
            ],
            "metric_entries": [],
            "result_entries": [],
            "journal_entries": [
                {
                    "id": "j-1",
                    "title": "Squat Day",
                    "content": "Heavy squats today",
                    "entry_date": "2026-04-01",
                }
            ],
            "goals": [
                {
                    "id": "g-1",
                    "title": "Squat 405",
                    "target_type": "manual",
                    "target_id": "manual",
                    "target_value": 405,
                    "status": "active",
                }
            ],
        }
        resp = authed_client.post("/api/import/json", json=payload)
        assert resp.status_code == 200

        # All imported entities should be searchable
        results = search(db, "squat")
        types = {r["entity_type"] for r in results}
        assert "journal" in types
        assert "goal" in types
        assert "exercise_type" in types
