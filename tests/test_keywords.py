"""Tests for keyword extraction and overlap scoring."""

from __future__ import annotations

from resume_analyzer.keywords import compare_keywords, extract_resume_keywords, extract_weighted_job_keywords


JOB_DESCRIPTION = """
Senior Product Data Analyst

Requirements
- Advanced SQL and Python skills
- Experience with Tableau and dashboard design
- Strong statistics background
- Experience running A/B testing and experimentation
"""


RESUME_TEXT = """
SUMMARY
Data analyst with Python, SQL, statistics, and dashboard reporting experience.
SKILLS
Python, SQL, dashboards, reporting, statistics
"""


def test_extract_weighted_job_keywords_captures_core_requirements() -> None:
    keywords = extract_weighted_job_keywords(JOB_DESCRIPTION)
    assert "python" in keywords
    assert "sql" in keywords
    assert "tableau" in keywords


def test_compare_keywords_finds_matches_and_gaps() -> None:
    weighted_keywords = extract_weighted_job_keywords(JOB_DESCRIPTION)
    matched, missing, overlap_ratio = compare_keywords(weighted_keywords, RESUME_TEXT)
    assert "python" in matched
    assert "sql" in matched
    assert "tableau" in missing
    assert 0 <= overlap_ratio <= 1


def test_extract_resume_keywords_surfaces_resume_terms() -> None:
    resume_keywords = extract_resume_keywords(RESUME_TEXT)
    assert "python" in resume_keywords
    assert "sql" in resume_keywords
