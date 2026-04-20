"""Resume parsing utilities."""

from __future__ import annotations

import re

import fitz

from resume_analyzer.utils import normalize_whitespace


class ResumeParsingError(ValueError):
    """Raised when a resume PDF cannot be parsed into useful text."""


def clean_resume_text(text: str) -> str:
    """Normalize extracted resume text for downstream analysis."""

    cleaned = normalize_whitespace(text)
    cleaned = cleaned.replace("\uf0b7", "-").replace("\u2022", "-")
    cleaned = re.sub(r"\n\s*-\s*", "\n- ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a text-based PDF using PyMuPDF."""

    if not file_bytes:
        raise ResumeParsingError("The uploaded PDF is empty.")

    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:  # pragma: no cover - library-specific failures vary
        raise ResumeParsingError(
            "The file could not be opened as a PDF. Please upload a valid resume PDF."
        ) from exc

    page_text: list[str] = []
    with document:
        if document.page_count == 0:
            raise ResumeParsingError("The uploaded PDF has no pages.")

        for page in document:
            page_text.append(page.get_text("text"))

    extracted_text = clean_resume_text("\n".join(page_text))
    if len(extracted_text.strip()) < 40:
        raise ResumeParsingError(
            "The PDF does not contain enough readable text. This local-first build expects a text-based PDF, not a scanned image."
        )

    return extracted_text


def require_non_empty_text(text: str, label: str) -> str:
    """Validate non-empty user input."""

    cleaned = text.strip()
    if not cleaned:
        raise ValueError(f"{label} is required.")
    return cleaned
