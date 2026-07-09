"""Shared fixtures for tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from app.database.models import init_db, SCHEMA


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Provide a temporary SQLite database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    init_db(str(db_path))
    yield db_path
    os.unlink(str(db_path))


@pytest.fixture
def sample_assignment() -> dict:
    return {
        "id": "12345",
        "title": "Database Design Project",
        "course_id": "CS301",
        "course": "Database Systems",
        "intro": "Design a normalized database schema for a library system.",
        "due_date": "2026-07-20",
        "attachments": [],
    }


@pytest.fixture
def sample_solution() -> str:
    return "# Solution\n\nThis is a test solution.\n\n## Section 1\n\nSome content here."
