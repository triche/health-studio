"""Shared fixtures for CLI tests."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".health-studio"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def tmp_config_file(tmp_config_dir):
    """Create a temporary config file with valid content."""
    config_file = tmp_config_dir / "config.toml"
    config_file.write_text(
        '[server]\nbase_url = "http://localhost:8000"\n\n'
        '[auth]\napi_key = "hs_testkey1234567890abcdefghijklmno"\n'
    )
    config_file.chmod(0o600)
    return config_file


@pytest.fixture
def mock_env_api_key():
    """Set API key via environment variable."""
    with patch.dict(os.environ, {"HEALTH_STUDIO_API_KEY": "hs_envkey1234567890abcdefghijklmno"}):
        yield


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    client = MagicMock()
    return client


@pytest.fixture
def sample_journal_list():
    """Sample journal list API response."""
    return {
        "items": [
            {
                "id": "j1",
                "title": "Morning Thoughts",
                "content": "# Hello\nSome content",
                "entry_date": "2024-01-15",
                "created_at": "2024-01-15T10:00:00",
                "updated_at": "2024-01-15T10:00:00",
            },
            {
                "id": "j2",
                "title": "Evening Reflection",
                "content": "Felt good today",
                "entry_date": "2024-01-14",
                "created_at": "2024-01-14T20:00:00",
                "updated_at": "2024-01-14T20:00:00",
            },
        ],
        "total": 2,
        "page": 1,
        "per_page": 20,
    }


@pytest.fixture
def sample_metric_types():
    """Sample metric types API response."""
    return [
        {"id": "mt1", "name": "Weight", "unit": "lbs", "created_at": "2024-01-01T00:00:00"},
        {"id": "mt2", "name": "Steps", "unit": "count", "created_at": "2024-01-01T00:00:00"},
    ]


@pytest.fixture
def sample_exercise_types():
    """Sample exercise types API response."""
    return [
        {
            "id": "et1",
            "name": "Back Squat",
            "category": "power_lift",
            "result_unit": "lbs",
            "created_at": "2024-01-01T00:00:00",
        },
        {
            "id": "et2",
            "name": "Fran",
            "category": "crossfit_benchmark",
            "result_unit": "seconds",
            "created_at": "2024-01-01T00:00:00",
        },
    ]


@pytest.fixture
def sample_goals_list():
    """Sample goals list API response."""
    return {
        "items": [
            {
                "id": "g1",
                "title": "Squat 300lbs",
                "description": "Get stronger",
                "plan": "",
                "target_type": "result",
                "target_id": "et1",
                "target_value": 300.0,
                "start_value": 225.0,
                "current_value": 275.0,
                "lower_is_better": False,
                "status": "active",
                "deadline": "2024-06-01",
                "progress": 66.7,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-15T00:00:00",
            }
        ],
        "total": 1,
        "page": 1,
        "per_page": 20,
    }


@pytest.fixture
def sample_dashboard():
    """Sample dashboard summary API response."""
    return {
        "recent_journals": [
            {
                "id": "j1",
                "title": "Morning Thoughts",
                "entry_date": "2024-01-15",
            }
        ],
        "active_goals": [
            {
                "id": "g1",
                "title": "Squat 300lbs",
                "progress": 66.7,
                "status": "active",
            }
        ],
        "latest_metrics": [
            {
                "metric_name": "Weight",
                "unit": "lbs",
                "value": 185.0,
                "recorded_date": "2024-01-15",
            }
        ],
        "recent_prs": [
            {
                "exercise_name": "Back Squat",
                "value": 275.0,
                "result_unit": "lbs",
                "recorded_date": "2024-01-14",
            }
        ],
    }
