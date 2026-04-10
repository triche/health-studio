"""Tests for the unified timeline (Phase 4)."""

from __future__ import annotations

from datetime import date as _date
from typing import TYPE_CHECKING

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricEntry, MetricType
from app.models.result import ExerciseType, ResultEntry
from app.services.tags import sync_tags
from app.services.timeline import get_timeline

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_journal(
    db: Session,
    *,
    title: str = "Test Journal",
    content: str = "Some content",
    entry_date: str = "2026-04-01",
) -> JournalEntry:
    entry = JournalEntry(title=title, content=content, entry_date=_date.fromisoformat(entry_date))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _make_metric_type(db: Session, *, name: str = "Body Weight", unit: str = "lbs") -> MetricType:
    mt = MetricType(name=name, unit=unit)
    db.add(mt)
    db.commit()
    db.refresh(mt)
    return mt


def _make_metric_entry(
    db: Session,
    mt: MetricType,
    *,
    value: float = 205,
    recorded_date: str = "2026-03-31",
) -> MetricEntry:
    entry = MetricEntry(
        metric_type_id=mt.id, value=value, recorded_date=_date.fromisoformat(recorded_date)
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _make_exercise_type(
    db: Session,
    *,
    name: str = "Back Squat",
    category: str = "barbell",
    result_unit: str = "lbs",
) -> ExerciseType:
    et = ExerciseType(name=name, category=category, result_unit=result_unit)
    db.add(et)
    db.commit()
    db.refresh(et)
    return et


def _make_result_entry(
    db: Session,
    et: ExerciseType,
    *,
    value: float = 315,
    display_value: str | None = "315 lbs",
    recorded_date: str = "2026-04-01",
    is_pr: bool = False,
    is_rx: bool = True,
) -> ResultEntry:
    entry = ResultEntry(
        exercise_type_id=et.id,
        value=value,
        display_value=display_value,
        recorded_date=_date.fromisoformat(recorded_date),
        is_pr=is_pr,
        is_rx=is_rx,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _make_goal(
    db: Session,
    *,
    title: str = "Squat 405",
    status: str = "active",
    target_type: str = "result",
    target_id: str = "placeholder",
    target_value: float = 405,
    created_date: str = "2026-03-15",
) -> Goal:
    goal = Goal(
        title=title,
        target_type=target_type,
        target_id=target_id,
        target_value=target_value,
        status=status,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------


class TestTimelineMixedTypes:
    def test_returns_interleaved_entries(self, db: Session) -> None:
        """Timeline returns journal, metric, result, and goal entries sorted by date."""
        _make_journal(db, entry_date="2026-04-01")
        mt = _make_metric_type(db)
        _make_metric_entry(db, mt, recorded_date="2026-03-31")
        et = _make_exercise_type(db)
        _make_result_entry(db, et, recorded_date="2026-03-30")
        _make_goal(db)

        result = get_timeline(db)
        items = result["items"]

        assert len(items) == 4
        types = [i["type"] for i in items]
        assert "journal" in types
        assert "metric" in types
        assert "result" in types
        assert "goal" in types


class TestTimelineTypeFilter:
    def test_filters_by_single_type(self, db: Session) -> None:
        """type filter returns only matching entities."""
        _make_journal(db, entry_date="2026-04-01")
        mt = _make_metric_type(db)
        _make_metric_entry(db, mt, recorded_date="2026-03-31")

        result = get_timeline(db, types=["journal"])
        assert len(result["items"]) == 1
        assert result["items"][0]["type"] == "journal"

    def test_filters_by_multiple_types(self, db: Session) -> None:
        """type filter with multiple types works."""
        _make_journal(db, entry_date="2026-04-01")
        mt = _make_metric_type(db)
        _make_metric_entry(db, mt, recorded_date="2026-03-31")
        et = _make_exercise_type(db)
        _make_result_entry(db, et, recorded_date="2026-03-30")

        result = get_timeline(db, types=["journal", "result"])
        assert len(result["items"]) == 2
        item_types = {i["type"] for i in result["items"]}
        assert item_types == {"journal", "result"}


class TestTimelineTagFilter:
    def test_filters_by_tag(self, db: Session) -> None:
        """Only tagged entities appear when tag filter is set."""
        j1 = _make_journal(db, title="Tagged", entry_date="2026-04-01")
        sync_tags(db, "journal", j1.id, ["strength"])
        _make_journal(db, title="Untagged", entry_date="2026-03-31")

        result = get_timeline(db, tag="strength")
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Tagged"


class TestTimelineDateRange:
    def test_date_from(self, db: Session) -> None:
        """date_from excludes older entries."""
        _make_journal(db, title="Old", entry_date="2026-01-01")
        _make_journal(db, title="New", entry_date="2026-04-01")

        result = get_timeline(db, date_from=_date(2026, 3, 1))
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "New"

    def test_date_to(self, db: Session) -> None:
        """date_to excludes newer entries."""
        _make_journal(db, title="Old", entry_date="2026-01-01")
        _make_journal(db, title="New", entry_date="2026-04-01")

        result = get_timeline(db, date_to=_date(2026, 2, 1))
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Old"

    def test_date_range(self, db: Session) -> None:
        """Both boundaries work together."""
        _make_journal(db, title="Too Old", entry_date="2026-01-01")
        _make_journal(db, title="In Range", entry_date="2026-03-15")
        _make_journal(db, title="Too New", entry_date="2026-06-01")

        result = get_timeline(db, date_from=_date(2026, 3, 1), date_to=_date(2026, 4, 1))
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "In Range"


class TestTimelinePagination:
    def test_pagination(self, db: Session) -> None:
        """page and per_page work correctly."""
        for i in range(5):
            _make_journal(db, title=f"Entry {i}", entry_date=f"2026-04-{i + 1:02d}")

        result = get_timeline(db, page=1, per_page=2)
        assert len(result["items"]) == 2
        assert result["total"] >= 5
        assert result["page"] == 1
        assert result["per_page"] == 2

    def test_second_page(self, db: Session) -> None:
        """Second page returns different items."""
        for i in range(5):
            _make_journal(db, title=f"Entry {i}", entry_date=f"2026-04-{i + 1:02d}")

        page1 = get_timeline(db, page=1, per_page=2)
        page2 = get_timeline(db, page=2, per_page=2)
        ids1 = {i["id"] for i in page1["items"]}
        ids2 = {i["id"] for i in page2["items"]}
        assert ids1.isdisjoint(ids2)


class TestTimelineOrdering:
    def test_ordered_by_date_descending(self, db: Session) -> None:
        """Items are ordered by date descending."""
        _make_journal(db, title="Old", entry_date="2026-01-01")
        _make_journal(db, title="New", entry_date="2026-04-01")
        mt = _make_metric_type(db)
        _make_metric_entry(db, mt, recorded_date="2026-02-15")

        result = get_timeline(db)
        dates = [i["date"] for i in result["items"]]
        assert dates == sorted(dates, reverse=True)


class TestTimelineEmpty:
    def test_empty_returns_empty_list(self, db: Session) -> None:
        """No data returns empty items list."""
        result = get_timeline(db)
        assert result["items"] == []
        assert result["total"] == 0


class TestTimelineGoalEvents:
    def test_goals_appear_with_creation_date(self, db: Session) -> None:
        """Goals appear in the timeline with their creation date."""
        _make_goal(db, title="Squat 405")
        result = get_timeline(db, types=["goal"])
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Squat 405"
        assert result["items"][0]["type"] == "goal"
        assert result["items"][0]["metadata"]["status"] == "active"
        assert result["items"][0]["metadata"]["event"] == "created"


class TestTimelineItemShape:
    def test_journal_shape(self, db: Session) -> None:
        """Journal items have expected fields."""
        _make_journal(
            db, title="My Journal", content="Hello world body text", entry_date="2026-04-01"
        )
        result = get_timeline(db, types=["journal"])
        item = result["items"][0]
        assert item["type"] == "journal"
        assert item["title"] == "My Journal"
        assert "Hello world" in item["summary"]
        assert item["date"] == "2026-04-01"
        assert isinstance(item["tags"], list)
        assert isinstance(item["metadata"], dict)

    def test_metric_shape(self, db: Session) -> None:
        """Metric items have expected fields."""
        mt = _make_metric_type(db, name="Body Weight", unit="lbs")
        _make_metric_entry(db, mt, value=205, recorded_date="2026-03-31")
        result = get_timeline(db, types=["metric"])
        item = result["items"][0]
        assert item["type"] == "metric"
        assert item["title"] == "Body Weight"
        assert "205" in item["summary"]
        assert item["metadata"]["value"] == 205
        assert item["metadata"]["unit"] == "lbs"
        assert item["metadata"]["metric_type_id"] == mt.id

    def test_result_shape(self, db: Session) -> None:
        """Result items have expected fields."""
        et = _make_exercise_type(db, name="Back Squat")
        _make_result_entry(
            db, et, value=315, display_value="315 lbs", recorded_date="2026-04-01", is_pr=True
        )
        result = get_timeline(db, types=["result"])
        item = result["items"][0]
        assert item["type"] == "result"
        assert item["title"] == "Back Squat"
        assert "315" in item["summary"]
        assert item["metadata"]["value"] == 315
        assert item["metadata"]["is_pr"] is True
        assert item["metadata"]["exercise_type_id"] == et.id

    def test_goal_shape(self, db: Session) -> None:
        """Goal items have expected fields."""
        _make_goal(db, title="Squat 405", status="active")
        result = get_timeline(db, types=["goal"])
        item = result["items"][0]
        assert item["type"] == "goal"
        assert item["title"] == "Squat 405"
        assert item["metadata"]["status"] == "active"
        assert item["metadata"]["event"] == "created"


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestTimelineEndpoint:
    def test_returns_results(self, authed_client) -> None:
        """GET /api/timeline returns timeline items."""
        # Create some data via the API
        authed_client.post(
            "/api/journals",
            json={"title": "Timeline journal", "content": "Hello", "entry_date": "2026-04-01"},
        )
        resp = authed_client.get("/api/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["items"]) >= 1

    def test_type_filter(self, authed_client) -> None:
        """GET /api/timeline?types=journal filters results."""
        authed_client.post(
            "/api/journals",
            json={"title": "J1", "content": "Hello", "entry_date": "2026-04-01"},
        )
        authed_client.post(
            "/api/goals",
            json={
                "title": "G1",
                "target_type": "manual",
                "target_id": "",
                "target_value": 100,
            },
        )
        resp = authed_client.get("/api/timeline?types=journal")
        data = resp.json()
        types = {i["type"] for i in data["items"]}
        assert types == {"journal"}

    def test_pagination(self, authed_client) -> None:
        """Pagination parameters work."""
        for i in range(3):
            authed_client.post(
                "/api/journals",
                json={"title": f"J{i}", "content": "", "entry_date": f"2026-04-{i + 1:02d}"},
            )
        resp = authed_client.get("/api/timeline?page=1&per_page=2")
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2

    def test_empty_timeline(self, authed_client) -> None:
        """Empty database returns empty items."""
        resp = authed_client.get("/api/timeline")
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_requires_auth(self) -> None:
        """Timeline requires authentication."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        resp = client.get("/api/timeline")
        assert resp.status_code == 401
