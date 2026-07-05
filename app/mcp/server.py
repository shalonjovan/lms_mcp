"""MCP Server — registers all LMS tools for AI agent consumption."""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from app.mcp import tools

logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP(
    "LMS Assistant",
    instructions="AI-Powered LMS Assistant — monitor, solve, and submit assignments",
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


def run_server():
    """Run the MCP server using stdio transport (for AI agent integration)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
        stream=sys.stderr,
    )
    logger.info("Starting LMS Assistant MCP Server (stdio)...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
