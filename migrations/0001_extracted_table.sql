-- Extracted from app/database/models.py
-- Generated at 2026-07-07 09:44:01

 """
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    url TEXT,
    created_at TEXT NOT NULL DEFAULT (date
