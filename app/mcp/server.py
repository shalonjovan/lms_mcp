"""MCP Server — registers all LMS tools, resources, and prompts for AI agent consumption."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from app.mcp import tools

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage browser, scheduler, and DB lifecycle."""
    from app.database.models import init_db
    from config.settings import DATABASE_PATH
    init_db(str(DATABASE_PATH))
    logger.info("Database initialized")
    yield
    from app.lms.browser import close_browser
    from app.scheduler.monitor import stop_monitoring
    await close_browser()
    await stop_monitoring()
    logger.info("MCP server shutdown complete")


# Create the FastMCP server
mcp = FastMCP(
    "LMS Assistant",
    instructions="AI-Powered LMS Assistant — monitor, solve, and submit assignments",
    lifespan=_lifespan,
)


# ─── Resources ─────────────────────────────────────────────────────

@mcp.resource("lms://assignments")
async def list_assignments_resource() -> list[dict]:
    """List all known assignments from the database."""
    from app.database.repository import get_all_assignments
    return get_all_assignments()


@mcp.resource("lms://assignments/{assignment_id}")
async def get_assignment_resource(assignment_id: str) -> dict | str:
    """Get full details of a specific assignment (DB first, LMS fallback)."""
    from app.database.repository import get_assignment as db_get
    db_result = db_get(assignment_id)
    if db_result:
        return db_result
    result = await tools.get_assignment(assignment_id)
    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"
    return result


@mcp.resource("lms://assignments/{assignment_id}/submission")
async def submission_status_resource(assignment_id: str) -> dict | str:
    """Get the latest submission status for an assignment."""
    from app.database.repository import get_latest_submission
    sub = get_latest_submission(assignment_id)
    if sub:
        return sub
    return {"assignment_id": assignment_id, "status": "no submission found"}


@mcp.resource("lms://history")
async def history_resource() -> list[dict]:
    """Get recent activity history (last 50 entries)."""
    from app.database.repository import get_history
    return get_history()


@mcp.resource("lms://status")
async def status_resource() -> dict:
    """Get current server and LMS connection status."""
    from app.lms.auth import is_logged_in
    from app.scheduler.monitor import _scheduler
    try:
        logged_in = await is_logged_in()
    except Exception:
        logged_in = False
    return {
        "server": "running",
        "lms_connected": logged_in,
        "scheduler_running": _scheduler is not None and _scheduler.running if _scheduler else False,
        "database": "ok",
    }


# ─── Prompts ───────────────────────────────────────────────────────

@mcp.prompt()
def solve_assignment_prompt(assignment_id: str) -> str:
    """Template for solving an assignment end-to-end."""
    return (
        f"I need to solve assignment {assignment_id}.\n\n"
        f"1. Fetch details with `get_assignment` (id=\"{assignment_id}\")\n"
        f"2. Classify it with `classify_assignment` (id=\"{assignment_id}\")\n"
        f"3. Generate a solution with `solve_assignment` (id=\"{assignment_id}\")\n"
        f"4. Create a DOCX document with `generate_document` "
        f"(id=\"{assignment_id}\", fmt=\"docx\")\n"
        f"5. Review the document before submitting"
    )


@mcp.prompt()
def classify_assignment_prompt(assignment_id: str) -> str:
    """Template for classifying an assignment."""
    return (
        f"I need to classify assignment {assignment_id}.\n\n"
        f"1. Fetch details with `get_assignment` (id=\"{assignment_id}\")\n"
        f"2. Classify it with `classify_assignment` (id=\"{assignment_id}\")\n\n"
        f"Possible types: document, programming, handwritten, presentation, "
        f"quiz, image, or other."
    )


@mcp.prompt()
def review_submission(assignment_id: str) -> str:
    """Template for reviewing and submitting an assignment."""
    return (
        f"I need to review and submit assignment {assignment_id}.\n\n"
        f"1. Check the submission window with `check_submission_open` "
        f"(id=\"{assignment_id}\")\n"
        f"2. Check status with `get_submission_status` "
        f"(id=\"{assignment_id}\")\n"
        f"3. Verify the generated document exists\n"
        f"4. Upload with `upload_submission` "
        f"(id=\"{assignment_id}\", file_path=\"...\")\n"
        f"5. Submit with `submit_assignment` (id=\"{assignment_id}\")\n\n"
        f"IMPORTANT: Only submit if the submission window is open."
    )


# ─── Tool Registrations ───────────────────────────────────────────────

@mcp.tool()
async def login(username: str | None = None, password: str | None = None) -> str:
    """Log in to the LMS. Credentials from env vars if omitted."""
    return await tools.login(username, password)


@mcp.tool()
async def logout() -> str:
    """Log out from the LMS."""
    return await tools.logout()


@mcp.tool()
async def list_assignments() -> list[dict]:
    """List all visible assignments from the LMS dashboard."""
    return await tools.list_assignments()


@mcp.tool()
async def get_assignment(assignment_id: str) -> dict:
    """Get full details of a specific assignment by its ID."""
    return await tools.get_assignment(assignment_id)


@mcp.tool()
async def download_attachment(assignment_id: str, attachment_url: str, filename: str | None = None) -> str:
    """Download an attachment file for an assignment."""
    return await tools.download_attachment(assignment_id, attachment_url, filename)


@mcp.tool()
async def classify_assignment(assignment_id: str) -> str:
    """Classify an assignment type using AI (document, programming, handwritten, etc)."""
    return await tools.classify_assignment(assignment_id)


@mcp.tool()
async def solve_assignment(assignment_id: str) -> str:
    """Generate an AI solution for the assignment."""
    return await tools.solve_assignment(assignment_id)


@mcp.tool()
async def generate_document(assignment_id: str, fmt: str = "docx") -> str:
    """Generate a formatted DOCX or PDF submission document for the assignment."""
    return await tools.generate_document(assignment_id, fmt)


@mcp.tool()
async def upload_submission(assignment_id: str, file_path: str) -> str:
    """Upload a submission file to the LMS."""
    return await tools.upload_submission(assignment_id, file_path)


@mcp.tool()
async def submit_assignment(assignment_id: str) -> str:
    """Submit an uploaded assignment on the LMS."""
    return await tools.submit_assignment(assignment_id)


@mcp.tool()
async def get_submission_status(assignment_id: str) -> str:
    """Check the submission status of an assignment."""
    return await tools.get_submission_status(assignment_id)


@mcp.tool()
async def check_submission_open(assignment_id: str) -> dict:
    """Check if the submission window is currently open for an assignment.

    Returns open status, current submission status, time remaining,
    and whether action buttons are available on the page.
    """
    return await tools.check_submission_open(assignment_id)


# ─── Server Runners ─────────────────────────────────────────────────

def run_server():
    """Run the MCP server using stdio transport."""
    from config.settings import setup_logging
    setup_logging()
    logger.info("Starting LMS Assistant MCP Server (stdio)...")
    mcp.run(transport="stdio")


def run_sse_server():
    """Run the MCP server using SSE transport (for web/multi-server mode)."""
    from config.settings import setup_logging
    setup_logging()
    logger.info(
        "Starting LMS Assistant MCP Server (SSE) on %s:%s...",
        mcp.settings.host, mcp.settings.port,
    )
    mcp.run(transport="sse")


if __name__ == "__main__":
    run_server()
