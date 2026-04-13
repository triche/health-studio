"""Graph visualization service — Phase 6 of the digital thread.

Builds a nodes-and-edges structure representing the connections between
all health data entities. Edge types:
  - mentions: journal → entity (from entity_mentions table)
  - tracks: goal → metric_type or exercise_type (from goal target)
  - shared_tag: entities sharing the same tag
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import TYPE_CHECKING

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.mention import EntityMention
from app.models.metric import MetricType
from app.models.result import ExerciseType
from app.models.tag import EntityTag
from app.services.tags import get_tags

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _goal_progress(goal: Goal) -> int:
    """Compute simple progress percentage for a goal node."""
    if not goal.target_value:
        return 0
    current = goal.current_value or 0
    if goal.start_value is not None:
        denom = abs(goal.target_value - goal.start_value)
        if denom == 0:
            return 100
        progress = abs(current - goal.start_value) / denom * 100
    else:
        progress = current / goal.target_value * 100
    return max(0, min(100, int(progress)))


def build_graph(
    db: Session,
    *,
    min_connections: int = 0,
    include_orphans: bool = False,
) -> dict:
    """Build the full graph of entity connections.

    1. Fetch all entities as nodes
    2. Fetch all mention edges from entity_mentions
    3. Fetch all goal-target edges from goals
    4. Compute shared-tag edges from entity_tags
    5. Optionally filter orphan nodes (no edges)
    6. Optionally filter by minimum connection count
    """
    nodes: list[dict] = []
    node_ids: set[str] = set()
    edges: list[dict] = []

    # -- 1. Collect all nodes --

    for j in db.query(JournalEntry).all():
        nid = f"journal:{j.id}"
        node_ids.add(nid)
        nodes.append(
            {
                "id": nid,
                "type": "journal",
                "label": j.title,
                "date": j.entry_date.isoformat(),
                "tags": get_tags(db, "journal", j.id),
            }
        )

    for mt in db.query(MetricType).all():
        nid = f"metric_type:{mt.id}"
        node_ids.add(nid)
        nodes.append(
            {
                "id": nid,
                "type": "metric_type",
                "label": mt.name,
                "tags": get_tags(db, "metric_type", mt.id),
            }
        )

    for et in db.query(ExerciseType).all():
        nid = f"exercise_type:{et.id}"
        node_ids.add(nid)
        nodes.append(
            {
                "id": nid,
                "type": "exercise_type",
                "label": et.name,
                "tags": get_tags(db, "exercise_type", et.id),
            }
        )

    for g in db.query(Goal).all():
        nid = f"goal:{g.id}"
        node_ids.add(nid)
        nodes.append(
            {
                "id": nid,
                "type": "goal",
                "label": g.title,
                "status": g.status,
                "progress": _goal_progress(g),
                "tags": get_tags(db, "goal", g.id),
            }
        )

    # -- 2. Mention edges --

    for m in db.query(EntityMention).all():
        source = f"journal:{m.journal_id}"
        target = f"{m.entity_type}:{m.entity_id}"
        if source in node_ids and target in node_ids:
            edges.append({"source": source, "target": target, "type": "mentions"})

    # -- 3. Goal-target edges --

    for g in db.query(Goal).all():
        source = f"goal:{g.id}"
        # target_type is "metric" or "result", map to node type
        if g.target_type == "metric":
            target = f"metric_type:{g.target_id}"
        else:
            target = f"exercise_type:{g.target_id}"
        if target in node_ids:
            edges.append({"source": source, "target": target, "type": "tracks"})

    # -- 4. Shared-tag edges --

    # Group entities by tag
    tag_groups: dict[str, list[str]] = defaultdict(list)
    for et in db.query(EntityTag).all():
        nid = f"{et.entity_type}:{et.entity_id}"
        if nid in node_ids:
            tag_groups[et.tag].append(nid)

    # Create edges between all pairs within each tag group
    for tag, members in tag_groups.items():
        for a, b in combinations(sorted(members), 2):
            edges.append({"source": a, "target": b, "type": "shared_tag", "tag": tag})

    # -- 5 & 6. Filter nodes --

    if not include_orphans or min_connections > 0:
        # Count connections per node
        connection_count: dict[str, int] = defaultdict(int)
        for edge in edges:
            connection_count[edge["source"]] += 1
            connection_count[edge["target"]] += 1

        keep = set()
        for nid in node_ids:
            count = connection_count.get(nid, 0)
            if not include_orphans and count == 0:
                continue
            if min_connections > 0 and count < min_connections:
                continue
            keep.add(nid)

        nodes = [n for n in nodes if n["id"] in keep]
        edges = [e for e in edges if e["source"] in keep and e["target"] in keep]

    return {"nodes": nodes, "edges": edges}
