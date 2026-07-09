"""Tests for MCP tool implementations (without browser)."""

from unittest.mock import patch, AsyncMock

import pytest

from app.mcp import tools


class TestLogin:
    @patch("app.mcp.tools.lms_login")
    @patch("app.mcp.tools.log_history")
    async def test_login_success(self, mock_log, mock_login):
        mock_login.return_value = True
        result = await tools.login("user", "pass")
        assert result == "Successfully logged in to LMS"
        mock_log.assert_called_once()

    @patch("app.mcp.tools.lms_login")
    @patch("app.mcp.tools.log_history")
    async def test_login_failure(self, mock_log, mock_login):
        mock_login.return_value = False
        result = await tools.login("user", "wrong_pass")
        assert result == "Login failed — check credentials"


class TestLogout:
    @patch("app.mcp.tools.lms_logout")
    @patch("app.mcp.tools.log_history")
    async def test_logout(self, mock_log, mock_logout):
        result = await tools.logout()
        assert result == "Logged out from LMS"


class TestListAssignments:
    @patch("app.mcp.tools.is_logged_in")
    @patch("app.mcp.tools.lms_login")
    @patch("app.mcp.tools.lms_list_assignments")
    @patch("app.mcp.tools.save_assignment")
    @patch("app.mcp.tools.log_history")
    async def test_list_success(
        self, mock_log, mock_save, mock_list, mock_login, mock_logged_in
    ):
        mock_logged_in.return_value = False  # will trigger login
        mock_list.return_value = [{"id": "1", "title": "A1"}]
        result = await tools.list_assignments()
        assert len(result) == 1
        mock_login.assert_awaited_once()

    @patch("app.mcp.tools.lms_list_assignments")
    @patch("app.mcp.tools.is_logged_in")
    @patch("app.mcp.tools.log_history")
    async def test_list_returns_empty_on_error(self, mock_log, mock_logged_in, mock_list):
        mock_logged_in.side_effect = Exception("Browser error")
        result = await tools.list_assignments()
        assert result == []


class TestGetAssignment:
    @patch("app.mcp.tools.is_logged_in")
    @patch("app.mcp.tools.lms_get_assignment")
    @patch("app.mcp.tools.save_assignment")
    @patch("app.mcp.tools.log_history")
    async def test_get_assignment_success(
        self, mock_log, mock_save, mock_get, mock_logged_in
    ):
        mock_logged_in.return_value = True
        mock_get.return_value = {"id": "1", "title": "Test"}
        result = await tools.get_assignment("1")
        assert result["title"] == "Test"

    @patch("app.mcp.tools.is_logged_in")
    @patch("app.mcp.tools.lms_get_assignment")
    @patch("app.mcp.tools.db_get_assignment")
    async def test_get_assignment_falls_back_to_db(
        self, mock_db, mock_lms, mock_logged_in
    ):
        mock_logged_in.side_effect = Exception("LMS error")
        mock_db.return_value = {"id": "1", "title": "Cached"}
        result = await tools.get_assignment("1")
        assert result["title"] == "Cached"


class TestCheckSubmissionOpen:
    @patch("app.mcp.tools.lms_check_open")
    @patch("app.mcp.tools.log_history")
    async def test_check_open(self, mock_log, mock_check):
        mock_check.return_value = {"open": True, "status": "open", "time_remaining": "2 days"}
        result = await tools.check_submission_open("1")
        assert result["open"] is True
        assert result["status"] == "open"


class TestUploadSubmission:
    @patch("app.mcp.tools.Path.exists")
    @patch("app.mcp.tools.lms_upload")
    @patch("app.mcp.tools.lms_check_open")
    @patch("app.mcp.tools.log_history")
    async def test_upload_blocked_when_closed(
        self, mock_log, mock_open, mock_upload, mock_exists
    ):
        mock_exists.return_value = True
        mock_open.return_value = {
            "open": False, "status": "closed",
            "time_remaining": "Overdue",
        }
        result = await tools.upload_submission("1", "/tmp/test.docx")
        assert "blocked" in result
        mock_upload.assert_not_awaited()

    @patch("app.mcp.tools.Path.exists")
    @patch("app.mcp.tools.lms_upload")
    @patch("app.mcp.tools.lms_check_open")
    @patch("app.mcp.tools.log_history")
    async def test_upload_file_not_found(
        self, mock_log, mock_open, mock_upload, mock_exists
    ):
        mock_exists.return_value = False
        result = await tools.upload_submission("1", "/nonexistent.docx")
        assert "not found" in result
        mock_open.assert_not_awaited()
