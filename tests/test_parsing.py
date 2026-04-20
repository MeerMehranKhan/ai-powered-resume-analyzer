"""Tests for PDF parsing and input validation."""

from __future__ import annotations

import fitz
import pytest

from resume_analyzer.parsing import ResumeParsingError, extract_text_from_pdf, require_non_empty_text


def _build_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def test_extract_text_from_pdf_reads_text() -> None:
    pdf_bytes = _build_pdf_bytes(
        "SUMMARY\nData analyst with Python and SQL experience.\nEXPERIENCE\nBuilt dashboards."
    )
    extracted = extract_text_from_pdf(pdf_bytes)
    assert "python" in extracted.lower()
    assert "experience" in extracted.lower()


def test_extract_text_from_pdf_rejects_invalid_binary() -> None:
    with pytest.raises(ResumeParsingError):
        extract_text_from_pdf(b"not-a-real-pdf")


def test_require_non_empty_text_rejects_blank_input() -> None:
    with pytest.raises(ValueError):
        require_non_empty_text("   ", "Job description")
