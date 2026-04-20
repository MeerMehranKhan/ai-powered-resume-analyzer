"""End-to-end tests for the analysis service."""

from __future__ import annotations

from resume_analyzer.demo import load_demo_job_description, load_demo_resume_text
from resume_analyzer.reporting import generate_pdf_report
from resume_analyzer.service import ResumeAnalyzerService


def test_service_returns_complete_analysis() -> None:
    service = ResumeAnalyzerService()
    result = service.analyze(
        resume_text=load_demo_resume_text(),
        job_description=load_demo_job_description(),
        source_label="demo",
    )

    assert 0 <= result.overall_score <= 100
    assert result.score_components
    assert result.markdown_report.startswith("# Resume Analysis Report")
    assert "python" in result.matched_keywords
    assert any(keyword in result.missing_keywords for keyword in {"tableau", "a/b testing", "snowflake", "dbt"})
    assert result.skill_gaps


def test_pdf_report_generation_returns_bytes() -> None:
    service = ResumeAnalyzerService()
    result = service.analyze(
        resume_text=load_demo_resume_text(),
        job_description=load_demo_job_description(),
        source_label="demo",
    )

    pdf_bytes = generate_pdf_report(result)
    assert pdf_bytes is not None
    assert pdf_bytes.startswith(b"%PDF")
