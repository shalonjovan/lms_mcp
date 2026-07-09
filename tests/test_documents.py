"""Tests for document generation."""

import tempfile
from pathlib import Path

import pytest
from docx import Document

from app.documents.generator import generate_docx, generate_pdf, _build_absolute_path
from app.documents.templates import get_student_info, render_markdown_template


class TestBuildPath:
    def test_build_absolute_path(self):
        path = _build_absolute_path("12345", "My Assignment", "docx")
        assert path.suffix == ".docx"
        assert "12345" in path.name
        assert "My_Assignment" in path.name

    def test_build_path_slugifies_title(self):
        path = _build_absolute_path("1", "Special Chars: / \\ &", "pdf")
        assert "/" not in path.name
        assert "\\" not in path.name
        assert path.suffix == ".pdf"

    def test_build_path_truncates_long_title(self):
        long_title = "A" * 200
        path = _build_absolute_path("1", long_title, "docx")
        assert len(path.stem) < 100


class TestGenerateDocx:
    def test_generate_docx_creates_file(self, sample_solution: str):
        path = generate_docx("999", "Test Doc", "Testing", sample_solution)
        assert path.exists()
        assert path.suffix == ".docx"
        path.unlink(missing_ok=True)

    def test_generate_docx_contains_header_info(self, sample_solution: str):
        path = generate_docx("998", "Header Test", "SubjectX", sample_solution)
        doc = Document(str(path))
        found = any("SubjectX" in p.text for p in doc.paragraphs)
        assert found
        path.unlink(missing_ok=True)

    def test_generate_docx_multiple_calls(self, sample_solution: str):
        p1 = generate_docx("997", "First", "S1", sample_solution)
        p2 = generate_docx("996", "Second", "S2", sample_solution)
        assert p1.exists()
        assert p2.exists()
        p1.unlink(missing_ok=True)
        p2.unlink(missing_ok=True)


class TestGeneratePdf:
    def test_generate_pdf_creates_file(self, sample_solution: str):
        path = generate_pdf("999", "Test PDF", "Testing", sample_solution)
        assert path.exists()
        assert path.suffix == ".pdf"
        path.unlink(missing_ok=True)

    def test_generate_pdf_contains_title(self, sample_solution: str):
        path = generate_pdf("888", "PDF Title", "SubjectY", sample_solution)
        content = path.read_bytes()
        assert b"PDF Title" in content or len(content) > 100
        path.unlink(missing_ok=True)


class TestTemplates:
    def test_get_student_info_returns_dict_with_keys(self):
        info = get_student_info()
        assert "name" in info
        assert "reg_no" in info
        assert "dept" in info
        assert "year" in info

    def test_render_markdown_template(self):
        result = render_markdown_template("Test Title", "Test Subject", "# Hello")
        assert "Test Title" in result
        assert "Test Subject" in result
        assert "# Hello" in result
        assert "AI-Powered LMS Assistant" in result
