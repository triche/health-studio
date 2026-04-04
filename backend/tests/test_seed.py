"""Tests for the seed command."""
from __future__ import annotations

from app.models.metric import MetricType
from app.models.result import ExerciseType
from app.seed import DEFAULT_EXERCISE_TYPES, DEFAULT_METRIC_TYPES, seed


def test_seed_populates_metric_types(db):
    metrics_added, _ = seed(db)
    assert metrics_added == len(DEFAULT_METRIC_TYPES)
    assert db.query(MetricType).count() == len(DEFAULT_METRIC_TYPES)

    names = {mt.name for mt in db.query(MetricType).all()}
    for name, _ in DEFAULT_METRIC_TYPES:
        assert name in names


def test_seed_populates_exercise_types(db):
    _, exercises_added = seed(db)
    assert exercises_added == len(DEFAULT_EXERCISE_TYPES)
    assert db.query(ExerciseType).count() == len(DEFAULT_EXERCISE_TYPES)

    names = {et.name for et in db.query(ExerciseType).all()}
    for name, _, _ in DEFAULT_EXERCISE_TYPES:
        assert name in names


def test_seed_is_idempotent(db):
    seed(db)
    metrics_added, exercises_added = seed(db)
    assert metrics_added == 0
    assert exercises_added == 0
    assert db.query(MetricType).count() == len(DEFAULT_METRIC_TYPES)
    assert db.query(ExerciseType).count() == len(DEFAULT_EXERCISE_TYPES)
