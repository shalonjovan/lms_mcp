"""Database CRUD operations for assignments, submissions, and history."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import DATABASE_PATH


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# --- Courses ---

def save_course(course_id: str, name: str, url: str = ""):
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO courses (course_id, name, url, updated_at)
               VALUES (?, ?, ?, datetime('now'))
               ON CONFLICT(course_id) DO UPDATE SET
                   name=excluded.name,
                   url=excluded.url,
                   updated_at=datetime('now')""",
            (course_id, name, url),
        )


def get_all_courses() -> list[dict[str, Any]]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM courses ORDER BY name").fetchall()
        return [dict(r) for r in rows]


# --- Assignments ---

def save_assignment(assignment_id: str, data: dict[str, Any]) -> bool:
    """Insert or update an assignment. Returns True if new (first seen)."""
    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT status FROM assignments WHERE assignment_id = ?",
            (assignment_id,),
        ).fetchone()

        conn.execute(
            """INSERT INTO assignments
               (assignment_id, title, course_id, course_name, description,
                intro_html, attachment_urls, due_date, status, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', datetime('now'))
               ON CONFLICT(assignment_id) DO UPDATE SET
                   title=excluded.title,
                   course_name=excluded.course_name,
                   description=excluded.description,
                   intro_html=excluded.intro_html,
                   attachment_urls=excluded.attachment_urls,
                   due_date=excluded.due_date,
                   updated_at=datetime('now')""",
            (
                assignment_id,
                data.get("title", ""),
                data.get("course_id", ""),
                data.get("course", ""),
                data.get("intro", ""),
                data.get("intro_html", ""),
                json.dumps(data.get("attachments", [])),
                data.get("due_date", ""),
            ),
        )
        return existing is None


def update_assignment_status(assignment_id: str, status: str):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE assignments SET status = ?, updated_at = datetime('now') WHERE assignment_id = ?",
            (status, assignment_id),
        )


def update_assignment_type(assignment_id: str, assignment_type: str):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE assignments SET assignment_type = ? WHERE assignment_id = ?",
            (assignment_type, assignment_id),
        )


def get_assignment(assignment_id: str) -> dict[str, Any] | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM assignments WHERE assignment_id = ?", (assignment_id,)
        ).fetchone()
        return dict(row) if row else None


def get_new_assignments() -> list[dict[str, Any]]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM assignments WHERE status = 'new' ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_assignments() -> list[dict[str, Any]]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM assignments ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


# --- Submissions ---

def save_submission(
    assignment_id: str,
    solution_text: str = "",
    document_path: str = "",
    document_type: str = "",
    submission_status: str = "draft",
) -> int:
    with _get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO submissions
               (assignment_id, solution_text, document_path, document_type, submission_status)
               VALUES (?, ?, ?, ?, ?)""",
            (assignment_id, solution_text, document_path, document_type, submission_status),
        )
        return cur.lastrowid


def update_submission_status(submission_id: int, status: str):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE submissions SET submission_status = ?, submitted_at = datetime('now') WHERE id = ?",
            (status, submission_id),
        )


def get_latest_submission(assignment_id: str) -> dict[str, Any] | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM submissions WHERE assignment_id = ? ORDER BY created_at DESC LIMIT 1",
            (assignment_id,),
        ).fetchone()
        return dict(row) if row else None


# --- History ---

def log_history(assignment_id: str, action: str, details: str = ""):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO history (assignment_id, action, details) VALUES (?, ?, ?)",
            (assignment_id, action, details),
        )


def get_history(assignment_id: str | None = None) -> list[dict[str, Any]]:
    with _get_conn() as conn:
        if assignment_id:
            rows = conn.execute(
                "SELECT * FROM history WHERE assignment_id = ? ORDER BY created_at",
                (assignment_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
        return [dict(r) for r in rows]
