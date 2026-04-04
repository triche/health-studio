"""Seed the database with default metric types and exercise types."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.database import Base, SessionLocal, engine
from app.models.metric import MetricType
from app.models.result import ExerciseType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEFAULT_METRIC_TYPES: list[tuple[str, str]] = [
    ("Weight", "lbs"),
    ("Waist Circumference", "inches"),
    ("Steps", "count"),
    ("Sleep Duration", "minutes"),
    ("Water Intake", "oz"),
]

DEFAULT_EXERCISE_TYPES: list[tuple[str, str, str]] = [
    # Olympic Lifts
    ("Snatch", "olympic_lift", "lbs"),
    ("Clean & Jerk", "olympic_lift", "lbs"),
    ("Push Press", "olympic_lift", "lbs"),
    ("Push Jerk", "olympic_lift", "lbs"),
    ("Split Jerk", "olympic_lift", "lbs"),
    # Power Lifts
    ("Back Squat", "power_lift", "lbs"),
    ("Front Squat", "power_lift", "lbs"),
    ("Deadlift", "power_lift", "lbs"),
    ("Bench Press", "power_lift", "lbs"),
    ("Overhead Press", "power_lift", "lbs"),
    # CrossFit Benchmarks
    ("Fran", "crossfit_benchmark", "seconds"),
    ("Grace", "crossfit_benchmark", "seconds"),
    ("Murph", "crossfit_benchmark", "seconds"),
    ("Helen", "crossfit_benchmark", "seconds"),
    ("Diane", "crossfit_benchmark", "seconds"),
    ("Elizabeth", "crossfit_benchmark", "seconds"),
    ("Jackie", "crossfit_benchmark", "seconds"),
    ("Karen", "crossfit_benchmark", "seconds"),
    ("Cindy", "crossfit_benchmark", "seconds"),
    ("Annie", "crossfit_benchmark", "seconds"),
    ("Fight Gone Bad", "crossfit_benchmark", "seconds"),
    ("Filthy Fifty", "crossfit_benchmark", "seconds"),
    ("DT", "crossfit_benchmark", "seconds"),
    ("Isabel", "crossfit_benchmark", "seconds"),
    ("Amanda", "crossfit_benchmark", "seconds"),
    # Running
    ("400m", "running", "seconds"),
    ("800m", "running", "seconds"),
    ("1 Mile", "running", "seconds"),
    ("5K", "running", "seconds"),
    ("10K", "running", "seconds"),
    ("Half Marathon", "running", "seconds"),
    ("Marathon", "running", "seconds"),
]


def seed(db: Session) -> tuple[int, int]:
    """Insert default metric types and exercise types. Returns (metrics_added, exercises_added)."""
    metrics_added = 0
    for name, unit in DEFAULT_METRIC_TYPES:
        exists = db.query(MetricType).filter(MetricType.name == name).first()
        if not exists:
            db.add(MetricType(name=name, unit=unit))
            metrics_added += 1

    exercises_added = 0
    for name, category, result_unit in DEFAULT_EXERCISE_TYPES:
        exists = db.query(ExerciseType).filter(ExerciseType.name == name).first()
        if not exists:
            db.add(ExerciseType(name=name, category=category, result_unit=result_unit))
            exercises_added += 1

    db.commit()
    return metrics_added, exercises_added


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        metrics_added, exercises_added = seed(db)
        print(f"Seeded {metrics_added} metric types and {exercises_added} exercise types.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
