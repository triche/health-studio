"""Tests for SQLAlchemy models — CRUD in an in-memory SQLite database."""

from __future__ import annotations

from datetime import date, datetime

from app.models.api_key import ApiKey
from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricEntry, MetricType
from app.models.result import ExerciseType, ResultEntry
from app.models.user import User


def test_create_user(db):
    user = User(id=1, display_name="Test User")
    db.add(user)
    db.commit()

    fetched = db.query(User).first()
    assert fetched is not None
    assert fetched.display_name == "Test User"
    assert fetched.id == 1
    assert isinstance(fetched.created_at, datetime)


def test_create_api_key(db):
    key = ApiKey(name="test-key", key_hash="hashed", prefix="hs_12345")
    db.add(key)
    db.commit()

    fetched = db.query(ApiKey).first()
    assert fetched is not None
    assert fetched.name == "test-key"
    assert fetched.revoked is False


def test_create_journal_entry(db):
    entry = JournalEntry(title="Day 1", content="# Hello", entry_date=date(2026, 1, 1))
    db.add(entry)
    db.commit()

    fetched = db.query(JournalEntry).first()
    assert fetched is not None
    assert fetched.title == "Day 1"
    assert fetched.entry_date == date(2026, 1, 1)


def test_create_metric_type_and_entry(db):
    mt = MetricType(name="Weight", unit="lbs")
    db.add(mt)
    db.commit()

    entry = MetricEntry(metric_type_id=mt.id, value=185.5, recorded_date=date(2026, 1, 1))
    db.add(entry)
    db.commit()

    fetched = db.query(MetricEntry).first()
    assert fetched is not None
    assert fetched.value == 185.5
    assert fetched.metric_type.name == "Weight"


def test_create_exercise_type_and_result(db):
    et = ExerciseType(name="Back Squat", category="power_lift", result_unit="lbs")
    db.add(et)
    db.commit()

    result = ResultEntry(
        exercise_type_id=et.id,
        value=315.0,
        recorded_date=date(2026, 1, 1),
        is_pr=True,
    )
    db.add(result)
    db.commit()

    fetched = db.query(ResultEntry).first()
    assert fetched is not None
    assert fetched.value == 315.0
    assert fetched.is_pr is True
    assert fetched.exercise_type.name == "Back Squat"


def test_create_goal(db):
    goal = Goal(
        title="Squat 405",
        target_type="result",
        target_id="some-uuid",
        target_value=405.0,
        current_value=315.0,
        status="active",
    )
    db.add(goal)
    db.commit()

    fetched = db.query(Goal).first()
    assert fetched is not None
    assert fetched.title == "Squat 405"
    assert fetched.target_value == 405.0
    assert fetched.status == "active"


def test_update_journal_entry(db):
    entry = JournalEntry(title="Draft", content="wip", entry_date=date(2026, 1, 1))
    db.add(entry)
    db.commit()

    entry.title = "Final"
    db.commit()

    fetched = db.query(JournalEntry).first()
    assert fetched.title == "Final"


def test_delete_metric_entry(db):
    mt = MetricType(name="Steps", unit="count")
    db.add(mt)
    db.commit()

    entry = MetricEntry(metric_type_id=mt.id, value=10000, recorded_date=date(2026, 1, 1))
    db.add(entry)
    db.commit()

    db.delete(entry)
    db.commit()
    assert db.query(MetricEntry).count() == 0
