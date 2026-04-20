"""Markdown and PDF report generation."""

from __future__ import annotations

from io import BytesIO

from resume_analyzer.models import AnalysisResult
from resume_analyzer.utils import title_case_label, to_ascii


def generate_markdown_report(result: AnalysisResult) -> str:
    """Generate a portable Markdown report from the analysis result."""

    lines = [
        "# Resume Analysis Report",
        "",
        f"**Role Target:** {result.job_title}",
        f"**Source:** {result.source_label}",
        f"**Overall Match Score:** {result.overall_score}%",
        "",
        "## Score Breakdown",
        "",
    ]

    for component in result.score_components:
        lines.append(
            f"- **{component.name}:** {component.score:.1f}/{component.max_score:.0f} ({component.percentage}%) - {component.explanation}"
        )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            result.summary,
            "",
            "## Strengths",
            "",
        ]
    )
    lines.extend(
        f"- {strength}" for strength in (result.strengths or ["None detected"])
    )
    lines.extend(
        [
            "",
            "## Weaknesses",
            "",
        ]
    )
    lines.extend(
        f"- {weakness}" for weakness in (result.weaknesses or ["None detected"])
    )
    lines.extend(
        [
            "",
            "## Keywords",
            "",
            f"- **Matched:** {', '.join(result.matched_keywords) if result.matched_keywords else 'None'}",
            f"- **Missing:** {', '.join(result.missing_keywords) if result.missing_keywords else 'None'}",
            "",
            "## Skill Gap Analysis",
            "",
        ]
    )

    for gap in result.skill_gaps:
        lines.extend(
            [
                f"### {gap.category}",
                "",
                f"- **Matched:** {', '.join(gap.matched) if gap.matched else 'None'}",
                f"- **Missing:** {', '.join(gap.missing) if gap.missing else 'None'}",
                f"- **Recommendation:** {gap.recommendation}",
                "",
            ]
        )

    lines.extend(["## ATS Checks", ""])
    for check in result.ats_checks:
        status = "Pass" if check.passed else "Risk"
        lines.append(f"- **{check.label} ({status}):** {check.impact} {check.recommendation}")

    lines.extend(["", "## Section Feedback", ""])
    for feedback in result.section_feedback:
        lines.extend(
            [
                f"### {title_case_label(feedback.section)} ({feedback.percentage}%)",
                "",
                f"- **Strengths:** {', '.join(feedback.strengths) if feedback.strengths else 'None noted'}",
                f"- **Risks:** {', '.join(feedback.risks) if feedback.risks else 'None noted'}",
                f"- **Suggestions:** {', '.join(feedback.suggestions) if feedback.suggestions else 'None'}",
                "",
            ]
        )

    lines.extend(["## Bullet Improvement Suggestions", ""])
    if result.bullet_suggestions:
        for suggestion in result.bullet_suggestions:
            lines.extend(
                [
                    f"### {suggestion.section}",
                    "",
                    f"- **Original:** {suggestion.original}",
                    f"- **Suggested rewrite direction:** {suggestion.suggestion}",
                    f"- **Why:** {suggestion.reason}",
                    "",
                ]
            )
    else:
        lines.extend(["- No bullet rewrite suggestions were generated.", ""])

    return "\n".join(lines).strip() + "\n"


def generate_pdf_report(result: AnalysisResult) -> bytes | None:
    """Generate a simple PDF report when fpdf2 is available."""

    try:
        from fpdf import FPDF
    except Exception:  # pragma: no cover - optional dependency
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_title("Resume Analysis Report")

    def write_block(text: str, line_height: float, font_style: str, font_size: int) -> None:
        """Write a wrapped block starting from the left margin."""

        content = to_ascii(text).strip()
        pdf.set_font("Helvetica", font_style, font_size)
        pdf.set_x(pdf.l_margin)
        if not content:
            pdf.ln(line_height)
            return
        pdf.multi_cell(pdf.epw, line_height, content)
        pdf.set_x(pdf.l_margin)

    def heading(text: str, level: int = 1) -> None:
        size = 18 if level == 1 else 14 if level == 2 else 11
        pdf.ln(2)
        write_block(text, line_height=8, font_style="B", font_size=size)

    def body(text: str) -> None:
        write_block(text, line_height=6, font_style="", font_size=10)

    heading("Resume Analysis Report", level=1)
    body(f"Role Target: {result.job_title}")
    body(f"Source: {result.source_label}")
    body(f"Overall Match Score: {result.overall_score}%")

    heading("Score Breakdown", level=2)
    for component in result.score_components:
        body(
            f"- {component.name}: {component.score:.1f}/{component.max_score:.0f} ({component.percentage}%) - {component.explanation}"
        )

    heading("Summary", level=2)
    body(result.summary)

    heading("Keywords", level=2)
    body(f"Matched: {', '.join(result.matched_keywords) if result.matched_keywords else 'None'}")
    body(f"Missing: {', '.join(result.missing_keywords) if result.missing_keywords else 'None'}")

    heading("ATS Checks", level=2)
    for check in result.ats_checks:
        state = "Pass" if check.passed else "Risk"
        body(f"- {check.label} ({state}): {check.recommendation}")

    heading("Bullet Suggestions", level=2)
    if result.bullet_suggestions:
        for suggestion in result.bullet_suggestions:
            body(f"- {suggestion.original}")
            body(f"  Suggested direction: {suggestion.suggestion}")
    else:
        body("No bullet rewrites were needed.")

    raw_output = pdf.output()
    buffer = BytesIO()
    if isinstance(raw_output, (bytes, bytearray)):
        buffer.write(bytes(raw_output))
    else:
        buffer.write(raw_output.encode("latin-1", "ignore"))
    return buffer.getvalue()
