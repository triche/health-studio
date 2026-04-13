"""Tests for the graph visualization API (Phase 6)."""

from __future__ import annotations

from datetime import date as _date
from typing import TYPE_CHECKING

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.mention import EntityMention
from app.models.metric import MetricType
from app.models.result import ExerciseType
from app.services.graph import build_graph
from app.services.tags import sync_tags

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


def _make_goal(
    db: Session,
    *,
    title: str = "Squat 405",
    target_type: str = "result",
    target_id: str = "placeholder",
    target_value: float = 405,
    status: str = "active",
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


def _make_mention(
    db: Session, journal: JournalEntry, entity_type: str, entity_id: str, display_text: str = ""
) -> EntityMention:
    mention = EntityMention(
        journal_id=journal.id,
        entity_type=entity_type,
        entity_id=entity_id,
        display_text=display_text or f"{entity_type}:{entity_id}",
    )
    db.add(mention)
    db.commit()
    db.refresh(mention)
    return mention


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------


class TestGraphMentionEdges:
    def test_mention_links_appear_as_edges(self, db: Session) -> None:
        """Mention from journal to goal produces an edge."""
        journal = _make_journal(db)
        goal = _make_goal(db)
        _make_mention(db, journal, "goal", goal.id)

        graph = build_graph(db)
        edges = graph["edges"]

        mention_edges = [e for e in edges if e["type"] == "mentions"]
        assert len(mention_edges) == 1
        assert mention_edges[0]["source"] == f"journal:{journal.id}"
        assert mention_edges[0]["target"] == f"goal:{goal.id}"

    def test_mention_to_metric_type(self, db: Session) -> None:
        """Mention from journal to metric_type produces an edge."""
        journal = _make_journal(db)
        mt = _make_metric_type(db)
        _make_mention(db, journal, "metric_type", mt.id)

        graph = build_graph(db)
        mention_edges = [e for e in graph["edges"] if e["type"] == "mentions"]
        assert len(mention_edges) == 1
        assert mention_edges[0]["target"] == f"metric_type:{mt.id}"

    def test_mention_to_exercise_type(self, db: Session) -> None:
        """Mention from journal to exercise_type produces an edge."""
        journal = _make_journal(db)
        et = _make_exercise_type(db)
        _make_mention(db, journal, "exercise_type", et.id)

        graph = build_graph(db)
        mention_edges = [e for e in graph["edges"] if e["type"] == "mentions"]
        assert len(mention_edges) == 1
        assert mention_edges[0]["target"] == f"exercise_type:{et.id}"


class TestGraphGoalTargetEdges:
    def test_goal_target_metric_edge(self, db: Session) -> None:
        """Goal targeting a metric_type produces a tracks edge."""
        mt = _make_metric_type(db)
        goal = _make_goal(db, target_type="metric", target_id=mt.id)

        graph = build_graph(db)
        tracks_edges = [e for e in graph["edges"] if e["type"] == "tracks"]
        assert len(tracks_edges) == 1
        assert tracks_edges[0]["source"] == f"goal:{goal.id}"
        assert tracks_edges[0]["target"] == f"metric_type:{mt.id}"

    def test_goal_target_exercise_edge(self, db: Session) -> None:
        """Goal targeting an exercise_type produces a tracks edge."""
        et = _make_exercise_type(db)
        goal = _make_goal(db, target_type="result", target_id=et.id)

        graph = build_graph(db)
        tracks_edges = [e for e in graph["edges"] if e["type"] == "tracks"]
        assert len(tracks_edges) == 1
        assert tracks_edges[0]["source"] == f"goal:{goal.id}"
        assert tracks_edges[0]["target"] == f"exercise_type:{et.id}"


class TestGraphSharedTagEdges:
    def test_shared_tag_creates_edge(self, db: Session) -> None:
        """Two entities with the same tag are connected by a shared_tag edge."""
        journal = _make_journal(db)
        goal = _make_goal(db)
        sync_tags(db, "journal", journal.id, ["strength"])
        sync_tags(db, "goal", goal.id, ["strength"])

        graph = build_graph(db)
        tag_edges = [e for e in graph["edges"] if e["type"] == "shared_tag"]
        assert len(tag_edges) == 1
        assert tag_edges[0]["tag"] == "strength"

        # Verify the edge connects our two entities (order may vary)
        endpoints = {tag_edges[0]["source"], tag_edges[0]["target"]}
        assert f"journal:{journal.id}" in endpoints
        assert f"goal:{goal.id}" in endpoints

    def test_no_shared_tag_edge_for_different_tags(self, db: Session) -> None:
        """Entities with different tags have no shared_tag edge."""
        journal = _make_journal(db)
        goal = _make_goal(db)
        sync_tags(db, "journal", journal.id, ["cardio"])
        sync_tags(db, "goal", goal.id, ["strength"])

        graph = build_graph(db)
        tag_edges = [e for e in graph["edges"] if e["type"] == "shared_tag"]
        assert len(tag_edges) == 0


class TestGraphNodeTypes:
    def test_all_entity_types_represented(self, db: Session) -> None:
        """All entity types appear as nodes in the graph."""
        _make_journal(db)
        _make_metric_type(db)
        _make_exercise_type(db)
        _make_goal(db)

        graph = build_graph(db, include_orphans=True)
        node_types = {n["type"] for n in graph["nodes"]}
        assert node_types == {"journal", "metric_type", "exercise_type", "goal"}

    def test_node_has_required_fields(self, db: Session) -> None:
        """Each node has id, type, label, and tags."""
        journal = _make_journal(db, title="My Entry")
        sync_tags(db, "journal", journal.id, ["recovery"])

        graph = build_graph(db, include_orphans=True)
        node = next(n for n in graph["nodes"] if n["type"] == "journal")
        assert node["id"] == f"journal:{journal.id}"
        assert node["label"] == "My Entry"
        assert node["tags"] == ["recovery"]

    def test_goal_node_has_status_and_progress(self, db: Session) -> None:
        """Goal nodes include status and progress metadata."""
        _make_goal(db, status="active")

        graph = build_graph(db, include_orphans=True)
        node = next(n for n in graph["nodes"] if n["type"] == "goal")
        assert "status" in node
        assert "progress" in node


class TestGraphFilterOrphans:
    def test_orphan_nodes_excluded(self, db: Session) -> None:
        """Orphans (no edges) are excluded when include_orphans=False."""
        # Connected: journal mentions goal
        journal = _make_journal(db, title="Connected")
        goal = _make_goal(db)
        _make_mention(db, journal, "goal", goal.id)

        # Orphan: standalone metric_type with no edges
        _make_metric_type(db, name="Unlinked")

        graph = build_graph(db, include_orphans=False)
        node_ids = {n["id"] for n in graph["nodes"]}
        assert f"journal:{journal.id}" in node_ids
        assert f"goal:{goal.id}" in node_ids
        # Orphan metric_type should not be present
        orphan_types = [n for n in graph["nodes"] if n["label"] == "Unlinked"]
        assert len(orphan_types) == 0

    def test_orphan_nodes_included(self, db: Session) -> None:
        """Orphans are included when include_orphans=True."""
        _make_metric_type(db, name="Standalone")

        graph = build_graph(db, include_orphans=True)
        node_labels = {n["label"] for n in graph["nodes"]}
        assert "Standalone" in node_labels


class TestGraphMinConnections:
    def test_min_connections_filter(self, db: Session) -> None:
        """Nodes with fewer connections than min_connections are excluded."""
        journal = _make_journal(db, title="Hub Journal")
        goal1 = _make_goal(db, title="Goal 1")
        goal2 = _make_goal(db, title="Goal 2")
        mt = _make_metric_type(db, name="Lonely Metric")
        _make_mention(db, journal, "goal", goal1.id)
        _make_mention(db, journal, "goal", goal2.id)
        # journal has 2 edges, each goal has 1 edge, metric has 0

        graph = build_graph(db, min_connections=2, include_orphans=True)
        node_ids = {n["id"] for n in graph["nodes"]}
        assert f"journal:{journal.id}" in node_ids
        # Nodes with < 2 connections should be filtered out
        assert f"metric_type:{mt.id}" not in node_ids


class TestGraphEmpty:
    def test_empty_database_returns_empty_graph(self, db: Session) -> None:
        """Empty database returns empty graph."""
        graph = build_graph(db)
        assert graph["nodes"] == []
        assert graph["edges"] == []


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestGraphEndpoint:
    def test_get_graph(self, authed_client) -> None:
        """GET /api/graph returns graph data."""
        response = authed_client.get("/api/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    def test_get_graph_with_filters(self, authed_client) -> None:
        """GET /api/graph accepts query parameters."""
        response = authed_client.get(
            "/api/graph", params={"min_connections": 1, "include_orphans": "true"}
        )
        assert response.status_code == 200

    def test_graph_requires_auth(self, client) -> None:
        """GET /api/graph requires authentication."""
        response = client.get("/api/graph")
        assert response.status_code == 401
