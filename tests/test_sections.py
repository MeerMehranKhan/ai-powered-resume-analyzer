"""Tests for section parsing and fallback behavior."""

from __future__ import annotations

from resume_analyzer.sections import build_parsed_resume


def test_build_parsed_resume_detects_standard_sections() -> None:
    text = """
    SUMMARY
    Data analyst with strong Python and SQL experience.
    EXPERIENCE
    - Built reporting pipelines.
    SKILLS
    Python, SQL, dashboards
    EDUCATION
    B.S. in Information Systems
    """
    parsed = build_parsed_resume(text)
    assert "summary" in parsed.sections
    assert "experience" in parsed.sections
    assert parsed.bullets_by_section["experience"]


def test_build_parsed_resume_falls_back_when_no_headings_exist() -> None:
    parsed = build_parsed_resume(
        "Built automated dashboards for revenue operations and delivered recurring analysis."
    )
    assert "experience" in parsed.sections
