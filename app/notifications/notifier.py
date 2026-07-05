"""Notification system for new assignments and status updates."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def notify_new_assignment(assignment: dict[str, Any]):
    """Alert the user about a newly detected assignment."""
    title = assignment.get("title", "Unknown")
    course = assignment.get("course_name", "Unknown course")
    due = assignment.get("due_date", "No due date")

    msg = (
        f"\n{'='*60}\n"
        f"📋 NEW ASSIGNMENT DETECTED\n"
        f"  Title: {title}\n"
        f"  Course: {course}\n"
        f"  Due: {due}\n"
        f"{'='*60}\n"
    )
    logger.info(msg)
    print(msg)


def notify_submission_result(assignment_title: str, success: bool, details: str = ""):
    """Notify the user about submission result."""
    status = "✅ SUBMITTED" if success else "❌ SUBMISSION FAILED"
    msg = f"\n{status}: {assignment_title}"
    if details:
        msg += f"\n  Details: {details}"
    logger.info(msg)
    print(msg)


def notify_status(assignment_title: str, status: str):
    """Notify about a change in assignment status."""
    msg = f"\n📌 Status update [{assignment_title}]: {status}"
    logger.info(msg)
    print(msg)
