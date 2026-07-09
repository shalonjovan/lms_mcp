"""Tests for AI solution generator."""

from unittest.mock import patch

import pytest

from app.ai.solver import solve_assignment, SOLVER_PROMPTS


class TestSolver:
    @patch("app.ai.solver.LLMClient")
    def test_solve_document(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "# Solution\n\nReport content here."
        result = solve_assignment("Write Report", "Write a report on X", assignment_type="document")
        assert result == "# Solution\n\nReport content here."

    @patch("app.ai.solver.LLMClient")
    def test_solve_programming(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "```python\nprint('hello')\n```"
        result = solve_assignment(
            "Python Task", "Write a hello world", assignment_type="programming"
        )
        assert "python" in result

    @patch("app.ai.solver.LLMClient")
    def test_auto_classify_when_no_type_given(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "# Solution"
        # Will call classifier first, then solver
        with patch("app.ai.solver.classify_assignment") as mock_classify:
            mock_classify.return_value = "document"
            result = solve_assignment("Write Essay", "Write about history", assignment_type=None)
            mock_classify.assert_called_once_with("Write Essay", "Write about history")
            assert result == "# Solution"

    @patch("app.ai.solver.LLMClient")
    def test_solve_with_attachment_texts(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "# Solution\nWith references."
        solve_assignment(
            "Research Paper",
            "Write about AI",
            assignment_type="document",
            attachment_texts=["Paper content here"],
        )
        call_kwargs = mock_client.generate.call_args[1]
        assert "Attachment 1" in call_kwargs["user_prompt"]
        assert "Paper content here" in call_kwargs["user_prompt"]

    @patch("app.ai.solver.LLMClient")
    def test_solve_falls_back_to_other_prompt(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "# Fallback solution"
        result = solve_assignment("Task", "Do something", assignment_type="unknown_type")
        assert result == "# Fallback solution"

    def test_solver_prompts_defined_for_all_types(self):
        expected_types = {
            "document", "programming", "handwritten",
            "presentation", "quiz", "image", "other",
        }
        assert set(SOLVER_PROMPTS.keys()) == expected_types

    @patch("app.ai.solver.LLMClient")
    def test_solve_max_tokens_is_8192(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "# Solution"
        solve_assignment("Task", "Content", assignment_type="document")
        call_kwargs = mock_client.generate.call_args[1]
        assert call_kwargs["max_tokens"] == 8192

    @patch("app.ai.solver.LLMClient")
    def test_solve_low_temperature(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "# Solution"
        solve_assignment("Task", "Content", assignment_type="document")
        call_kwargs = mock_client.generate.call_args[1]
        assert call_kwargs["temperature"] == 0.5
