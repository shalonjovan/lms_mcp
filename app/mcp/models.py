"""Pydantic models for MCP tool inputs and outputs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AssignmentInfo(BaseModel):
    """Represents an assignment from the LMS."""
    id: str
    title: str
    course: str | None = None
    course_name: str | None = None
    due_date: str | None = None
    description: str | None = None
    status: str | None = None
    assignment_type: str | None = None
    attachments: list[dict[str, Any]] | None = None


class SolveAssignmentInput(BaseModel):
    """Input for solving an assignment."""
    assignment_id: str = Field(description="The LMS assignment ID")
    provider: str | None = Field(
        default=None,
        description="AI provider override (google, anthropic, openai)",
    )


class GenerateDocumentInput(BaseModel):
    """Input for generating a document."""
    assignment_id: str = Field(description="The LMS assignment ID")
    fmt: str = Field(default="docx", description="Output format: docx or pdf")


class UploadSubmissionInput(BaseModel):
    """Input for uploading a submission file."""
    assignment_id: str = Field(description="The LMS assignment ID")
    file_path: str = Field(description="Path to the file to upload")


class SubmissionResult(BaseModel):
    """Result of a submission operation."""
    success: bool
    message: str
    status: str | None = None
    submitted_at: datetime | None = None
    assignment_id: str | None = None


class SubmissionStatus(BaseModel):
    """Status check result for an assignment submission."""
    assignment_id: str
    open: bool
    status: str = ""
    time_remaining: str = ""
    has_action_buttons: bool = False
    available_actions: list[str] = []
    details: str = ""


class HealthStatus(BaseModel):
    """Server health and connection status."""
    server: str = "running"
    lms_connected: bool = False
    scheduler_running: bool = False
    database: str = "ok"
