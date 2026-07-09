"""Tests for MCP server registration (tools, resources, prompts)."""

import pytest

from app.mcp.server import mcp


class TestServerTools:
    async def test_tool_list_not_empty(self):
        tools = await mcp.list_tools()
        assert len(tools) > 0

    async def test_required_tools_registered(self):
        tool_names = {t.name for t in await mcp.list_tools()}
        required = {
            "login", "logout", "list_assignments", "get_assignment",
            "download_attachment", "classify_assignment", "solve_assignment",
            "generate_document", "upload_submission", "submit_assignment",
            "get_submission_status", "check_submission_open",
        }
        missing = required - tool_names
        assert not missing, f"Missing tools: {missing}"

    async def test_all_tools_have_descriptions(self):
        for t in await mcp.list_tools():
            assert t.description, f"Tool '{t.name}' has no description"

    async def test_tool_input_schemas_defined(self):
        for t in await mcp.list_tools():
            assert t.inputSchema is not None, f"Tool '{t.name}' has no input schema"


class TestServerResources:
    async def test_resource_list_not_empty(self):
        resources = await mcp.list_resources()
        assert len(resources) > 0

    async def test_required_resources_registered(self):
        resource_uris = {str(r.uri) for r in await mcp.list_resources()}
        required = {
            "lms://assignments",
            "lms://history",
            "lms://status",
        }
        missing = required - resource_uris
        assert not missing, f"Missing resources: {missing}"

    async def test_resource_templates_registered(self):
        templates = await mcp.list_resource_templates()
        template_uris = {str(t.uriTemplate) for t in templates}
        required = {
            "lms://assignments/{assignment_id}",
            "lms://assignments/{assignment_id}/submission",
        }
        missing = required - template_uris
        assert not missing, f"Missing resource templates: {missing}"


class TestServerPrompts:
    async def test_prompts_registered(self):
        prompts = await mcp.list_prompts()
        prompt_names = {p.name for p in prompts}
        required = {
            "solve_assignment_prompt",
            "classify_assignment_prompt",
            "review_submission",
        }
        missing = required - prompt_names
        assert not missing, f"Missing prompts: {missing}"

    async def test_all_prompts_have_descriptions(self):
        for p in await mcp.list_prompts():
            assert p.description, f"Prompt '{p.name}' has no description"
