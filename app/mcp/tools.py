"""MCP tool implementations — the bridge between AI and LMS."""

import logging
from pathlib import Path

from app.lms.auth import login as lms_login, logout as lms_logout, is_logged_in
from app.lms.assignments import (
    list_assignments as lms_list_assignments,
    get_assignment as lms_get_assignment,
    download_attachment as lms_download_attachment,
)
from app.lms.submission import (
    check_submission_open as lms_check_open,
    upload_submission as lms_upload,
    submit_assignment as lms_submit,
    get_submission_status as lms_status,
)
from app.ai.classifier import classify_assignment as ai_classify
from app.ai.solver import solve_assignment as ai_solve
from app.documents.generator import generate_docx, generate_pdf
from app.documents.templates import render_markdown_template
from app.database.repository import (
    save_assignment,
    get_assignment as db_get_assignment,
    get_all_assignments as db_all_assignments,
    save_submission,
    update_assignment_status,
    update_assignment_type,
    log_history,
)
from app.notifications.notifier import notify_status

logger = logging.getLogger(__name__)


async def login(username: str | None = None, password: str | None = None) -> str:
    """Log in to the LMS.

    Args:
        username: LMS username (email). Uses env var if omitted.
        password: LMS password. Uses env var if omitted.

    Returns:
        Status message.
    """
    success = await lms_login(username, password)
    if success:
        log_history("system", "login", "User logged in successfully")
        return "Successfully logged in to LMS"
    return "Login failed — check credentials"


async def logout() -> str:
    """Log out from the LMS."""
    await lms_logout()
    log_history("system", "logout", "User logged out")
    return "Logged out from LMS"


async def list_assignments() -> list[dict]:
    """List all visible assignments from the LMS dashboard.

    Returns:
        List of assignment summaries (id, title, course, due_date, status).
    """
    try:
        logged_in = await is_logged_in()
        if not logged_in:
            await lms_login()

        assignments = await lms_list_assignments()
        for a in assignments:
            save_assignment(a["id"], a)
        log_history("system", "list_assignments", f"Found {len(assignments)} assignments")
        return assignments
    except Exception as e:
        logger.error(f"Error listing assignments: {e}")
        return []


async def get_assignment(assignment_id: str) -> dict:
    """Get full details of a specific assignment.

    Args:
        assignment_id: The LMS assignment ID.

    Returns:
        Assignment details including title, description, due date, attachments.
    """
    try:
        logged_in = await is_logged_in()
        if not logged_in:
            await lms_login()

        details = await lms_get_assignment(assignment_id)
        save_assignment(assignment_id, details)
        log_history(assignment_id, "get_details", "Fetched assignment details")
        return details
    except Exception as e:
        logger.error(f"Error getting assignment {assignment_id}: {e}")
        # Fall back to DB
        db_result = db_get_assignment(assignment_id)
        if db_result:
            return db_result
        return {"error": str(e), "assignment_id": assignment_id}


async def download_attachment(assignment_id: str, attachment_url: str, filename: str | None = None) -> str:
    """Download an assignment attachment.

    Args:
        assignment_id: The assignment ID.
        attachment_url: URL of the file to download.
        filename: Optional custom filename for the saved file.

    Returns:
        Path to the downloaded file.
    """
    path = await lms_download_attachment(assignment_id, attachment_url, filename)
    log_history(assignment_id, "download_attachment", f"Downloaded to {path}")
    return str(path)


async def classify_assignment(assignment_id: str) -> str:
    """Classify an assignment type using AI.

    Args:
        assignment_id: The assignment ID.

    Returns:
        Classification type: document, programming, handwritten, presentation, quiz, image, or other.
    """
    assign = db_get_assignment(assignment_id)
    if not assign:
        # Try fetching from LMS
        assign = await get_assignment(assignment_id)
        if isinstance(assign, dict) and "error" in assign:
            return f"Error: {assign['error']}"

    if not assign or not assign.get("title"):
        return "Error: Assignment not found"

    a_type = ai_classify(
        assign.get("title", ""),
        assign.get("description", "") or assign.get("intro", ""),
    )
    update_assignment_type(assignment_id, a_type)
    log_history(assignment_id, "classify", f"Classified as {a_type}")
    return a_type


async def solve_assignment(assignment_id: str) -> str:
    """Generate an AI solution for an assignment.

    Args:
        assignment_id: The assignment ID.

    Returns:
        The generated solution text in Markdown.
    """
    assign = db_get_assignment(assignment_id)
    if not assign:
        return "Error: Assignment not found. Use get_assignment first."

    # Auto-classify if not done yet
    if not assign.get("assignment_type"):
        a_type = ai_classify(
            assign.get("title", ""),
            assign.get("description", "") or assign.get("intro", ""),
        )
        update_assignment_type(assignment_id, a_type)
    else:
        a_type = assign["assignment_type"]

    solution = ai_solve(
        assign.get("title", ""),
        assign.get("description", "") or assign.get("intro", ""),
        assignment_type=a_type,
    )

    # Save solution to DB
    save_submission(assignment_id, solution_text=solution, document_type="markdown")
    update_assignment_status(assignment_id, "solved")
    log_history(assignment_id, "solve", f"Generated solution ({len(solution)} chars)")
    notify_status(assign.get("title", ""), "Solution generated")
    return solution


async def generate_document(assignment_id: str, fmt: str = "docx") -> str:
    """Generate a formatted DOCX or PDF submission document.

    Args:
        assignment_id: The assignment ID.
        fmt: Output format — "docx" or "pdf".

    Returns:
        Path to the generated document.
    """
    assign = db_get_assignment(assignment_id)
    if not assign:
        return "Error: Assignment not found"

    solution_text = assign.get("description", "")
    # Try to get the latest AI-generated solution
    from app.database.repository import get_latest_submission
    sub = get_latest_submission(assignment_id)
    if sub and sub.get("solution_text"):
        solution_text = sub["solution_text"]

    markdown_body = render_markdown_template(
        assign.get("title", ""),
        assign.get("course_name", ""),
        solution_text,
    )

    if fmt == "pdf":
        path = generate_pdf(assignment_id, assign["title"], assign.get("course_name", ""), markdown_body)
    else:
        path = generate_docx(assignment_id, assign["title"], assign.get("course_name", ""), markdown_body)

    # Save document path
    save_submission(
        assignment_id,
        solution_text=solution_text,
        document_path=str(path),
        document_type=fmt,
        submission_status="draft",
    )
    update_assignment_status(assignment_id, "document_generated")
    log_history(assignment_id, "generate_document", f"Generated {fmt}: {path}")
    return str(path)


async def check_submission_open(assignment_id: str) -> dict:
    """Check if the submission window for an assignment is currently open.

    Inspects the assignment view page for action buttons, status, and
    time-remaining indicators before attempting any submission action.

    Args:
        assignment_id: The assignment ID.

    Returns:
        Dict with open (bool), status, time_remaining, has_action_buttons, details.
    """
    result = await lms_check_open(assignment_id)
    log_history(assignment_id, "check_open", f"Open: {result['open']} | Status: {result['status']}")
    return result


async def upload_submission(assignment_id: str, file_path: str) -> str:
    """Upload a file to the LMS assignment submission page.

    Checks if the submission window is open before attempting upload.

    Args:
        assignment_id: The assignment ID.
        file_path: Path to the file to upload.

    Returns:
        Status message.
    """
    if not Path(file_path).exists():
        return f"Error: File not found at {file_path}"

    open_check = await lms_check_open(assignment_id)
    if not open_check["open"]:
        msg = (
            f"Upload blocked: submission window is closed for "
            f"assignment {assignment_id}. Status: {open_check['status']}. "
            f"Time remaining: {open_check['time_remaining']}"
        )
        logger.warning(msg)
        log_history(assignment_id, "upload_blocked", msg)
        return msg

    success = await lms_upload(assignment_id, file_path)
    if success:
        log_history(assignment_id, "upload", f"Uploaded {file_path}")
        notify_status(assignment_id, "File uploaded")
        return f"Successfully uploaded {file_path}"
    return "Upload failed"


async def submit_assignment(assignment_id: str) -> str:
    """Submit an uploaded assignment.

    Checks if the submission window is open before attempting submission.

    Args:
        assignment_id: The assignment ID.

    Returns:
        Status message.
    """
    open_check = await lms_check_open(assignment_id)
    if not open_check["open"]:
        msg = (
            f"Submission blocked: submission window is closed for "
            f"assignment {assignment_id}. Status: {open_check['status']}. "
            f"Time remaining: {open_check['time_remaining']}"
        )
        logger.warning(msg)
        log_history(assignment_id, "submit_blocked", msg)
        return msg

    success = await lms_submit(assignment_id)
    if success:
        update_assignment_status(assignment_id, "submitted")
        log_history(assignment_id, "submit", "Assignment submitted")
        notify_status(assignment_id, "Submitted successfully")
        return "Assignment submitted successfully"
    return "Submission failed"


async def get_submission_status(assignment_id: str) -> str:
    """Check the submission status of an assignment.

    Args:
        assignment_id: The assignment ID.

    Returns:
        Status string from the LMS.
    """
    status = await lms_status(assignment_id)
    log_history(assignment_id, "check_status", f"Status: {status}")
    return status
