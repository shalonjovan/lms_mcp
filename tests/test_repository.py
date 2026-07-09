"""Tests for database repository CRUD operations."""

import json
from pathlib import Path

import pytest

from app.database.repository import (
    save_assignment,
    get_assignment,
    get_all_assignments,
    update_assignment_status,
    update_assignment_type,
    save_submission,
    get_latest_submission,
    log_history,
    get_history,
    save_course,
    get_all_courses,
)


def _override_db_path(temp_db_path: Path):
    """Monkey-patch DATABASE_PATH by re-patching _get_conn closure."""
    import app.database.repository as repo
    original = repo.DATABASE_PATH
    repo.DATABASE_PATH = temp_db_path
    return original


class TestAssignments:
    def test_save_and_get_assignment(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("12345", sample_assignment)
        result = get_assignment("12345")
        assert result is not None
        assert result["title"] == "Database Design Project"
        assert result["course_name"] == "Database Systems"

    def test_save_returns_true_for_new(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        is_new = save_assignment("12345", sample_assignment)
        assert is_new is True

    def test_save_returns_false_for_existing(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("12345", sample_assignment)
        is_new = save_assignment("12345", sample_assignment)
        assert is_new is False

    def test_get_all_assignments(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("1", {**sample_assignment, "id": "1"})
        save_assignment("2", {**sample_assignment, "id": "2", "title": "Second"})
        all_assignments = get_all_assignments()
        assert len(all_assignments) == 2

    def test_get_assignment_not_found(self, temp_db_path: Path):
        _override_db_path(temp_db_path)
        assert get_assignment("nonexistent") is None

    def test_update_status(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("12345", sample_assignment)
        update_assignment_status("12345", "submitted")
        result = get_assignment("12345")
        assert result["status"] == "submitted"

    def test_update_type(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("12345", sample_assignment)
        update_assignment_type("12345", "programming")
        result = get_assignment("12345")
        assert result["assignment_type"] == "programming"

    def test_assignment_default_status_is_new(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("12345", sample_assignment)
        result = get_assignment("12345")
        assert result["status"] == "new"


class TestSubmissions:
    def test_save_and_get_latest_submission(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("12345", sample_assignment)
        sub_id = save_submission("12345", solution_text="test solution")
        assert sub_id is not None
        latest = get_latest_submission("12345")
        assert latest is not None
        assert latest["solution_text"] == "test solution"
        assert latest["submission_status"] == "draft"

    def test_latest_submission_returns_newest(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        import time
        save_assignment("12345", sample_assignment)
        save_submission("12345", solution_text="first")
        time.sleep(0.1)
        save_submission("12345", solution_text="second")
        latest = get_latest_submission("12345")
        assert latest["solution_text"] == "second"

    def test_no_submission_returns_none(self, temp_db_path: Path):
        _override_db_path(temp_db_path)
        assert get_latest_submission("nonexistent") is None


class TestHistory:
    def test_log_and_get_history(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("12345", sample_assignment)
        log_history("12345", "test_action", "test details")
        entries = get_history("12345")
        assert len(entries) == 1
        assert entries[0]["action"] == "test_action"
        assert entries[0]["details"] == "test details"

    def test_get_all_history(self, temp_db_path: Path, sample_assignment: dict):
        _override_db_path(temp_db_path)
        save_assignment("1", {**sample_assignment, "id": "1"})
        save_assignment("2", {**sample_assignment, "id": "2"})
        log_history("1", "action1")
        log_history("2", "action2")
        all_entries = get_history()
        assert len(all_entries) == 2


class TestCourses:
    def test_save_and_get_courses(self, temp_db_path: Path):
        _override_db_path(temp_db_path)
        save_course("CS301", "Database Systems", "/course/view.php?id=301")
        courses = get_all_courses()
        assert len(courses) >= 1
        assert courses[0]["course_id"] == "CS301"
        assert courses[0]["name"] == "Database Systems"

    def test_save_course_updates_existing(self, temp_db_path: Path):
        _override_db_path(temp_db_path)
        save_course("CS301", "Old Name")
        save_course("CS301", "New Name")
        courses = get_all_courses()
        assert courses[0]["name"] == "New Name"
