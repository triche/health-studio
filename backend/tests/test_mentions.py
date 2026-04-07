"""Tests for entity mentions & backlinks (Digital Thread Phase 1)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_journal(client: TestClient, title: str, content: str, entry_date: str = "2026-04-01"):
    resp = client.post(
        "/api/journals",
        json={"title": title, "content": content, "entry_date": entry_date},
    )
    assert resp.status_code == 201
    return resp.json()


def _create_goal(client: TestClient, title: str, target_type: str, target_id: str):
    resp = client.post(
        "/api/goals",
        json={
            "title": title,
            "target_type": target_type,
            "target_id": target_id,
            "target_value": 100.0,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _create_metric_type(client: TestClient, name: str, unit: str = "lbs"):
    resp = client.post("/api/metric-types", json={"name": name, "unit": unit})
    assert resp.status_code == 201
    return resp.json()


def _create_exercise_type(
    client: TestClient, name: str, category: str = "strength", result_unit: str = "lbs"
):
    resp = client.post(
        "/api/exercise-types",
        json={"name": name, "category": category, "result_unit": result_unit},
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Mention parsing unit tests
# ---------------------------------------------------------------------------


class TestParseMentions:
    def test_basic_mentions(self):
        from app.services.mentions import parse_mentions

        content = "Working on [[goal:Squat 405]] and tracking [[metric:Body Weight]]"
        mentions = parse_mentions(content)
        assert ("goal", "Squat 405") in mentions
        assert ("metric_type", "Body Weight") in mentions

    def test_exercise_mention(self):
        from app.services.mentions import parse_mentions

        content = "Did [[exercise:Back Squat]] today"
        mentions = parse_mentions(content)
        assert ("exercise_type", "Back Squat") in mentions

    def test_empty_content(self):
        from app.services.mentions import parse_mentions

        assert parse_mentions("") == []
        assert parse_mentions("No mentions here") == []

    def test_duplicates_deduplicated(self):
        from app.services.mentions import parse_mentions

        content = "[[goal:Squat 405]] and again [[goal:Squat 405]]"
        mentions = parse_mentions(content)
        assert len(mentions) == 1
        assert ("goal", "Squat 405") in mentions

    def test_multiple_types(self):
        from app.services.mentions import parse_mentions

        content = "[[goal:Run 5K]] [[metric:Heart Rate]] [[exercise:Deadlift]]"
        mentions = parse_mentions(content)
        assert len(mentions) == 3

    def test_invalid_type_ignored(self):
        from app.services.mentions import parse_mentions

        content = "[[unknown:Something]] and [[goal:Valid]]"
        mentions = parse_mentions(content)
        assert len(mentions) == 1
        assert ("goal", "Valid") in mentions

    def test_alias_results(self):
        from app.services.mentions import parse_mentions

        content = "Did [[results:Back Squat]] today"
        mentions = parse_mentions(content)
        assert ("exercise_type", "Back Squat") in mentions

    def test_alias_goals(self):
        from app.services.mentions import parse_mentions

        content = "Working on [[Goals:Squat 405]]"
        mentions = parse_mentions(content)
        assert ("goal", "Squat 405") in mentions

    def test_alias_metrics(self):
        from app.services.mentions import parse_mentions

        content = "Tracked [[Metrics:Body Weight]]"
        mentions = parse_mentions(content)
        assert ("metric_type", "Body Weight") in mentions

    def test_case_insensitive_type(self):
        from app.services.mentions import parse_mentions

        content = "[[GOAL:Squat 405]] and [[Exercise:Back Squat]] and [[Metric:BW]]"
        mentions = parse_mentions(content)
        assert ("goal", "Squat 405") in mentions
        assert ("exercise_type", "Back Squat") in mentions
        assert ("metric_type", "BW") in mentions


# ---------------------------------------------------------------------------
# Mention resolution tests
# ---------------------------------------------------------------------------


class TestResolveMentions:
    def test_resolve_goal(self, authed_client, db):
        goal = _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        from app.services.mentions import resolve_mentions

        resolved = resolve_mentions(db, [("goal", "Squat 405")])
        assert len(resolved) == 1
        assert resolved[0]["entity_type"] == "goal"
        assert resolved[0]["entity_id"] == goal["id"]
        assert resolved[0]["display_text"] == "Squat 405"

    def test_resolve_metric_type(self, authed_client, db):
        mt = _create_metric_type(authed_client, "Body Weight")
        from app.services.mentions import resolve_mentions

        resolved = resolve_mentions(db, [("metric_type", "Body Weight")])
        assert len(resolved) == 1
        assert resolved[0]["entity_id"] == mt["id"]

    def test_resolve_exercise_type(self, authed_client, db):
        et = _create_exercise_type(authed_client, "Back Squat")
        from app.services.mentions import resolve_mentions

        resolved = resolve_mentions(db, [("exercise_type", "Back Squat")])
        assert len(resolved) == 1
        assert resolved[0]["entity_id"] == et["id"]

    def test_not_found_skipped(self, db):
        from app.services.mentions import resolve_mentions

        resolved = resolve_mentions(db, [("goal", "Nonexistent")])
        assert resolved == []

    def test_case_insensitive(self, authed_client, db):
        _create_exercise_type(authed_client, "Back Squat")
        from app.services.mentions import resolve_mentions

        resolved = resolve_mentions(db, [("exercise_type", "back squat")])
        assert len(resolved) == 1


# ---------------------------------------------------------------------------
# Mention sync integration tests
# ---------------------------------------------------------------------------


class TestSyncMentions:
    def test_sync_on_create(self, authed_client, db):
        goal = _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        journal = _create_journal(authed_client, "Leg day", "Working toward [[goal:Squat 405]]")

        resp = authed_client.get(f"/api/journals/{journal['id']}/mentions")
        assert resp.status_code == 200
        mentions = resp.json()
        assert len(mentions) == 1
        assert mentions[0]["entity_type"] == "goal"
        assert mentions[0]["entity_id"] == goal["id"]

    def test_sync_on_update(self, authed_client, db):
        _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        et = _create_exercise_type(authed_client, "Back Squat")
        journal = _create_journal(authed_client, "Leg day", "Working toward [[goal:Squat 405]]")

        # Update to mention exercise instead of goal
        authed_client.put(
            f"/api/journals/{journal['id']}",
            json={"content": "Did some [[exercise:Back Squat]]"},
        )

        resp = authed_client.get(f"/api/journals/{journal['id']}/mentions")
        mentions = resp.json()
        assert len(mentions) == 1
        assert mentions[0]["entity_type"] == "exercise_type"
        assert mentions[0]["entity_id"] == et["id"]

    def test_sync_on_delete(self, authed_client, db):
        _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        journal = _create_journal(authed_client, "Leg day", "Working toward [[goal:Squat 405]]")

        # Delete journal — mentions should cascade
        resp = authed_client.delete(f"/api/journals/{journal['id']}")
        assert resp.status_code == 204

        # Verify journal is gone (and its mentions)
        resp = authed_client.get(f"/api/journals/{journal['id']}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Backlinks endpoint tests
# ---------------------------------------------------------------------------


class TestBacklinks:
    def test_goal_backlinks(self, authed_client):
        goal = _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        _create_journal(authed_client, "Day 1", "Working on [[goal:Squat 405]]")
        _create_journal(authed_client, "Day 2", "Still chasing [[goal:Squat 405]]")

        resp = authed_client.get(f"/api/goals/{goal['id']}/backlinks")
        assert resp.status_code == 200
        backlinks = resp.json()
        assert len(backlinks) == 2
        titles = {b["title"] for b in backlinks}
        assert titles == {"Day 1", "Day 2"}

    def test_metric_type_backlinks(self, authed_client):
        mt = _create_metric_type(authed_client, "Body Weight")
        _create_journal(authed_client, "Weigh-in", "Tracked [[metric:Body Weight]] today")

        resp = authed_client.get(f"/api/metric-types/{mt['id']}/backlinks")
        assert resp.status_code == 200
        backlinks = resp.json()
        assert len(backlinks) == 1
        assert backlinks[0]["title"] == "Weigh-in"

    def test_exercise_type_backlinks(self, authed_client):
        et = _create_exercise_type(authed_client, "Back Squat")
        _create_journal(authed_client, "Squat day", "Did [[exercise:Back Squat]] heavy sets")

        resp = authed_client.get(f"/api/exercise-types/{et['id']}/backlinks")
        assert resp.status_code == 200
        backlinks = resp.json()
        assert len(backlinks) == 1
        assert backlinks[0]["title"] == "Squat day"

    def test_backlinks_empty(self, authed_client):
        goal = _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        resp = authed_client.get(f"/api/goals/{goal['id']}/backlinks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_backlinks_snippet(self, authed_client):
        goal = _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        _create_journal(
            authed_client,
            "Thoughts",
            "Today I was thinking about my training and working toward"
            " [[goal:Squat 405]] and how it feels",
        )

        resp = authed_client.get(f"/api/goals/{goal['id']}/backlinks")
        backlinks = resp.json()
        assert len(backlinks) == 1
        # Snippet should contain the mention
        assert "[[goal:Squat 405]]" in backlinks[0]["snippet"]
        # Snippet should be reasonable length
        assert len(backlinks[0]["snippet"]) <= 220

    def test_backlinks_include_entry_date(self, authed_client):
        goal = _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        _create_journal(authed_client, "Day 1", "[[goal:Squat 405]]", entry_date="2026-04-01")

        resp = authed_client.get(f"/api/goals/{goal['id']}/backlinks")
        backlinks = resp.json()
        assert backlinks[0]["entry_date"] == "2026-04-01"
        assert "journal_id" in backlinks[0]


# ---------------------------------------------------------------------------
# Entity names endpoint tests
# ---------------------------------------------------------------------------


class TestEntityNames:
    def test_returns_all_types(self, authed_client):
        _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        _create_metric_type(authed_client, "Body Weight")
        _create_exercise_type(authed_client, "Back Squat")

        resp = authed_client.get("/api/entities/names")
        assert resp.status_code == 200
        data = resp.json()
        assert "goals" in data
        assert "metric_types" in data
        assert "exercise_types" in data
        assert any(g["name"] == "Squat 405" for g in data["goals"])
        assert any(m["name"] == "Body Weight" for m in data["metric_types"])
        assert any(e["name"] == "Back Squat" for e in data["exercise_types"])

    def test_empty_when_no_entities(self, authed_client):
        resp = authed_client.get("/api/entities/names")
        assert resp.status_code == 200
        data = resp.json()
        assert data["goals"] == []
        assert data["metric_types"] == []
        assert data["exercise_types"] == []


# ---------------------------------------------------------------------------
# Mentions endpoint tests
# ---------------------------------------------------------------------------


class TestMentionsEndpoint:
    def test_journal_mentions(self, authed_client):
        _create_goal(authed_client, "Squat 405", "metric_type", "fake-id")
        _create_metric_type(authed_client, "Body Weight")
        journal = _create_journal(
            authed_client,
            "Multi-mention",
            "Tracking [[goal:Squat 405]] and [[metric:Body Weight]]",
        )

        resp = authed_client.get(f"/api/journals/{journal['id']}/mentions")
        assert resp.status_code == 200
        mentions = resp.json()
        assert len(mentions) == 2
        types = {m["entity_type"] for m in mentions}
        assert types == {"goal", "metric_type"}

    def test_no_mentions(self, authed_client):
        journal = _create_journal(authed_client, "Plain entry", "No mentions here")

        resp = authed_client.get(f"/api/journals/{journal['id']}/mentions")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_mentions_404_for_missing_journal(self, authed_client):
        resp = authed_client.get("/api/journals/nonexistent/mentions")
        assert resp.status_code == 404

    def test_alias_results_sync(self, authed_client, db):
        """[[Results:Name]] should resolve to exercise_type."""
        et = _create_exercise_type(authed_client, "Strict Pull Up")
        journal = _create_journal(
            authed_client, "Pull up day", "Did [[Results:Strict Pull Up]] today"
        )

        resp = authed_client.get(f"/api/journals/{journal['id']}/mentions")
        mentions = resp.json()
        assert len(mentions) == 1
        assert mentions[0]["entity_type"] == "exercise_type"
        assert mentions[0]["entity_id"] == et["id"]

        # Backlink should also work
        resp = authed_client.get(f"/api/exercise-types/{et['id']}/backlinks")
        backlinks = resp.json()
        assert len(backlinks) == 1
        assert "[[Results:Strict Pull Up]]" in backlinks[0]["snippet"]
