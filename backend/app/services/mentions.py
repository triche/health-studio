"""Entity mention parsing, resolution, and sync for the digital thread."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from sqlalchemy import func

from app.models.goal import Goal
from app.models.mention import EntityMention
from app.models.metric import MetricType
from app.models.result import ExerciseType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Match [[type:Name]] — case-insensitive, accepts aliases
_MENTION_PATTERN = re.compile(
    r"\[\[("
    r"goal|goals|"
    r"metric|metrics|metric_type|"
    r"exercise|exercises|exercise_type|result|results"
    r"):([^\]]+)\]\]",
    re.IGNORECASE,
)

# Map shorthand type names (lowered) to model entity_type values
_TYPE_MAP: dict[str, str] = {
    "goal": "goal",
    "goals": "goal",
    "metric": "metric_type",
    "metrics": "metric_type",
    "metric_type": "metric_type",
    "exercise": "exercise_type",
    "exercises": "exercise_type",
    "exercise_type": "exercise_type",
    "result": "exercise_type",
    "results": "exercise_type",
}

# Map entity_type to (Model, name_column)
_ENTITY_MODELS: dict[str, tuple[type, str]] = {
    "goal": (Goal, "title"),
    "metric_type": (MetricType, "name"),
    "exercise_type": (ExerciseType, "name"),
}


def parse_mentions(content: str) -> list[tuple[str, str]]:
    """Extract (entity_type, display_text) pairs from journal content.

    Returns deduplicated list. Unrecognised entity types are ignored.
    """
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []
    for match in _MENTION_PATTERN.finditer(content):
        raw_type, display_text = match.group(1), match.group(2).strip()
        entity_type = _TYPE_MAP.get(raw_type.lower())
        if entity_type is None:
            continue
        key = (entity_type, display_text)
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


def resolve_mentions(db: Session, mentions: list[tuple[str, str]]) -> list[dict[str, str]]:
    """Resolve display names to entity IDs via case-insensitive lookup.

    Returns list of {entity_type, entity_id, display_text} for found entities.
    Unresolved mentions are silently skipped.
    """
    resolved: list[dict[str, str]] = []
    for entity_type, display_text in mentions:
        model_info = _ENTITY_MODELS.get(entity_type)
        if model_info is None:
            continue
        model_cls, name_col = model_info
        col = getattr(model_cls, name_col)
        row = db.query(model_cls).filter(func.lower(col) == display_text.lower()).first()
        if row is not None:
            resolved.append(
                {
                    "entity_type": entity_type,
                    "entity_id": row.id,
                    "display_text": display_text,
                }
            )
    return resolved


def sync_mentions(db: Session, journal_id: str, content: str) -> None:
    """Parse content, resolve mentions, and upsert the entity_mentions table.

    Deletes stale mentions, inserts new ones, leaves existing unchanged.
    """
    parsed = parse_mentions(content)
    resolved = resolve_mentions(db, parsed)

    # Current mentions in DB for this journal
    existing = db.query(EntityMention).filter(EntityMention.journal_id == journal_id).all()
    existing_map: dict[tuple[str, str], EntityMention] = {
        (m.entity_type, m.entity_id): m for m in existing
    }

    # Resolved set
    resolved_keys: set[tuple[str, str]] = set()
    for item in resolved:
        key = (item["entity_type"], item["entity_id"])
        resolved_keys.add(key)
        if key not in existing_map:
            db.add(
                EntityMention(
                    journal_id=journal_id,
                    entity_type=item["entity_type"],
                    entity_id=item["entity_id"],
                    display_text=item["display_text"],
                )
            )

    # Delete stale mentions
    for key, mention in existing_map.items():
        if key not in resolved_keys:
            db.delete(mention)

    db.flush()


def get_journal_mentions(db: Session, journal_id: str) -> list[EntityMention]:
    """Return all entity mentions for a journal entry."""
    return db.query(EntityMention).filter(EntityMention.journal_id == journal_id).all()


def get_backlinks(db: Session, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
    """Return journal entries that reference the given entity."""
    from app.models.journal import JournalEntry

    mentions = (
        db.query(EntityMention)
        .filter(
            EntityMention.entity_type == entity_type,
            EntityMention.entity_id == entity_id,
        )
        .all()
    )

    if not mentions:
        return []

    journal_ids = [m.journal_id for m in mentions]
    journals = (
        db.query(JournalEntry)
        .filter(JournalEntry.id.in_(journal_ids))
        .order_by(JournalEntry.entry_date.desc())
        .all()
    )

    # Build mention display text lookup for snippets
    mention_map: dict[str, str] = {m.journal_id: m.display_text for m in mentions}

    result: list[dict[str, Any]] = []
    for journal in journals:
        snippet = _extract_snippet(journal.content, entity_type, mention_map.get(journal.id, ""))
        result.append(
            {
                "journal_id": journal.id,
                "title": journal.title,
                "entry_date": journal.entry_date,
                "snippet": snippet,
            }
        )
    return result


def _extract_snippet(
    content: str, entity_type: str, display_text: str, max_length: int = 200
) -> str:
    """Extract a ~max_length character snippet centered on the first mention."""
    # Find any [[alias:display_text]] in the content, where alias maps to entity_type
    aliases = [k for k, v in _TYPE_MAP.items() if v == entity_type]
    alias_group = "|".join(re.escape(a) for a in aliases)
    escaped_name = re.escape(display_text)
    pattern = re.compile(
        rf"\[\[({alias_group}):{escaped_name}\]\]",
        re.IGNORECASE,
    )
    match = pattern.search(content)

    if not match:
        # Fallback: return start of content
        return content[:max_length] + ("…" if len(content) > max_length else "")

    idx = match.start()
    mention_len = match.end() - match.start()

    # Center the snippet on the mention
    half = (max_length - mention_len) // 2
    start = max(0, idx - half)
    end = min(len(content), idx + mention_len + half)

    snippet = content[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(content):
        snippet = snippet + "…"
    return snippet


def get_entity_names(db: Session) -> dict[str, list[dict[str, str]]]:
    """Return all entity names grouped by type, for autocomplete."""
    goals = db.query(Goal).all()
    metric_types = db.query(MetricType).all()
    exercise_types = db.query(ExerciseType).all()

    return {
        "goals": [{"id": g.id, "name": g.title} for g in goals],
        "metric_types": [{"id": m.id, "name": m.name} for m in metric_types],
        "exercise_types": [{"id": e.id, "name": e.name} for e in exercise_types],
    }
