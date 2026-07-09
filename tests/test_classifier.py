"""Tests for assignment type classifier."""

from unittest.mock import patch

import pytest

from app.ai.classifier import classify_assignment, CLASSIFICATION_SYSTEM_PROMPT


class TestClassifier:
    @patch("app.ai.classifier.LLMClient")
    def test_classify_document(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "document"
        result = classify_assignment("Write a report on DBMS", "Write a 2000-word report")
        assert result == "document"

    @patch("app.ai.classifier.LLMClient")
    def test_classify_programming(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "programming"
        result = classify_assignment("Implement a sorting algorithm", "Write code in Python")
        assert result == "programming"

    @patch("app.ai.classifier.LLMClient")
    def test_classify_unknown_falls_back_to_other(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "something_unexpected"
        result = classify_assignment("Some random task", "Do something")
        assert result == "other"

    @patch("app.ai.classifier.LLMClient")
    def test_result_is_lowercased_and_stripped(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "  DOCUMENT  "
        result = classify_assignment("Write an essay", "Details here")
        assert result == "document"

    @patch("app.ai.classifier.LLMClient")
    def test_classify_with_attachments(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "handwritten"
        result = classify_assignment(
            "Math Problem Set",
            "Solve the following problems",
            attachment_names=["scan_001.jpg", "scan_002.jpg"],
        )
        assert result == "handwritten"
        # Verify attachments were included in the prompt
        call_kwargs = mock_client.generate.call_args[1]
        assert "scan_001.jpg" in call_kwargs["user_prompt"]

    @patch("app.ai.classifier.LLMClient")
    def test_classify_description_truncated(self, MockLLMClient):
        mock_client = MockLLMClient.return_value
        mock_client.generate.return_value = "document"
        long_desc = "x" * 5000
        classify_assignment("Long Assignment", long_desc)
        call_kwargs = mock_client.generate.call_args[1]
        # Description should be truncated to 2000 chars
        assert len(call_kwargs["user_prompt"]) <= 2100  # allow for prefix

    def test_classification_prompt_contains_types(self):
        for t in ["document", "programming", "handwritten", "presentation", "quiz", "image", "other"]:
            assert t in CLASSIFICATION_SYSTEM_PROMPT
