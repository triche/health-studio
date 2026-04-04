"""Tests for Alembic migrations."""
from __future__ import annotations

import os
import tempfile

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


def test_alembic_migration_applies_cleanly():
    """Alembic upgrade head on a fresh SQLite database creates all expected tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db_url = f"sqlite:///{db_path}"

        alembic_cfg = Config(
            os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
        )
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        command.upgrade(alembic_cfg, "head")

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        expected = {
            "users",
            "api_keys",
            "journal_entries",
            "metric_types",
            "metric_entries",
            "exercise_types",
            "result_entries",
            "goals",
            "alembic_version",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"
        engine.dispose()
