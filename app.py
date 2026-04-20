"""Streamlit entry point for the AI Resume Analyzer & Job Matcher."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from resume_analyzer.demo import load_demo_job_description, load_demo_resume_text
from resume_analyzer.parsing import ResumeParsingError, extract_text_from_pdf, require_non_empty_text
from resume_analyzer.reporting import generate_pdf_report
from resume_analyzer.service import ResumeAnalyzerService
from resume_analyzer.utils import title_case_label

st.set_page_config(
    page_title="AI Resume Analyzer & Job Matcher",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    :root {
        --navy: #1f3a5f;
        --teal: #2f6f74;
        --amber: #c48332;
        --bg: #f6f4ef;
        --surface: #ffffff;
        --surface-soft: #eef2f4;
        --ink: #17212b;
        --muted: #566475;
        --line: #d7dfe6;
        --teal-soft: #e7f3f2;
        --amber-soft: #fbefe2;
        --navy-soft: #e9eff5;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(31, 58, 95, 0.06), transparent 28%),
            linear-gradient(180deg, var(--bg) 0%, #f3f5f7 100%);
        color: var(--ink);
        font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    }
    .block-container {
        max-width: 1380px;
        padding-top: 1.2rem;
        padding-bottom: 2.4rem;
    }
    .hero-card {
        background: linear-gradient(135deg, #1f3a5f 0%, #294c71 58%, #2f6f74 100%);
        border-radius: 22px;
        padding: 1.45rem 1.55rem;
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 18px 42px rgba(24, 37, 53, 0.12);
        margin-bottom: 1rem;
    }
    .hero-kicker {
        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-size: 0.76rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.76);
        margin-bottom: 0.5rem;
    }
    .hero-title {
        font-size: 2.15rem;
        line-height: 1.08;
        font-weight: 700;
        margin: 0 0 0.45rem 0;
    }
    .hero-copy {
        font-size: 1rem;
        line-height: 1.55;
        color: rgba(255, 255, 255, 0.9);
        max-width: 920px;
    }
    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.95rem;
    }
    .app-pill {
        display: inline-block;
        padding: 0.34rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        border: 1px solid transparent;
    }
    .pill-light {
        background: rgba(255, 255, 255, 0.14);
        border-color: rgba(255, 255, 255, 0.18);
        color: #ffffff;
    }
    .pill-navy {
        background: var(--navy-soft);
        border-color: #cddae7;
        color: var(--navy);
    }
    .pill-teal {
        background: var(--teal-soft);
        border-color: #c9dfdd;
        color: #24595d;
    }
    .pill-amber {
        background: var(--amber-soft);
        border-color: #efd5b7;
        color: #9b5f1e;
    }
    .section-kicker {
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.76rem;
        font-weight: 700;
        color: #617182;
        margin-bottom: 0.25rem;
    }
    .muted-line {
        color: var(--muted);
        font-size: 0.9rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: 0 10px 26px rgba(19, 32, 47, 0.04);
    }
    div[data-testid="stMetric"] {
        background: transparent;
        border: none;
        padding: 0;
    }
    div[data-testid="stMetricLabel"] {
        color: #617182;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: var(--ink);
        font-weight: 700;
    }
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px;
        border: 1px solid #27476a;
        background: #27476a;
        color: #ffffff;
        font-weight: 600;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #2f6f74;
        background: #2f6f74;
        color: #ffffff;
    }
    .stTextArea textarea, .stFileUploader {
        border-radius: 14px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 2.8rem;
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid var(--line);
        border-radius: 12px 12px 0 0;
        padding: 0 1rem;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        border-color: #adc4da;
        color: var(--navy);
    }
    .stAlert {
        border-radius: 14px;
    }
</style>
"""


@st.cache_resource
def get_service() -> ResumeAnalyzerService:
    """Create a cached service instance."""

    return ResumeAnalyzerService()


def initialize_session_state() -> None:
    """Prepare Streamlit session state defaults."""

    st.session_state.setdefault("job_description_input", "")
    st.session_state.setdefault("use_demo_resume", False)
    st.session_state.setdefault("analysis_result", None)
    st.session_state.setdefault("pdf_report_bytes", None)


def load_demo_inputs() -> None:
    """Populate the page with bundled demo inputs."""

    st.session_state["job_description_input"] = load_demo_job_description()
    st.session_state["use_demo_resume"] = True


def reset_demo_mode() -> None:
    """Switch the page back to upload mode."""

    st.session_state["use_demo_resume"] = False


def fit_label(score: int) -> tuple[str, str]:
    """Convert a numeric score into a fit label and tone."""

    if score >= 80:
        return "Strong fit", "teal"
    if score >= 65:
        return "Moderate fit", "navy"
    return "Needs work", "amber"


def render_pills(items: list[str], tone: str = "navy", light: bool = False) -> None:
    """Render a row of pill labels."""

    if not items:
        return

    class_name = "pill-light" if light else f"pill-{tone}"
    pill_markup = "".join(
        f"<span class='app-pill {class_name}'>{html.escape(item)}</span>" for item in items
    )
    st.markdown(f"<div class='pill-row'>{pill_markup}</div>", unsafe_allow_html=True)


def render_header() -> None:
    """Render the app header."""

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">Resume Analysis Workspace</div>
            <div class="hero-title">Resume Analyzer & Job Matcher</div>
            <div class="hero-copy">
                Analyze a resume against a target job with transparent scoring, grounded keyword matching,
                ATS diagnostics, section-level review, and report exports that are easy to share.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_pills(
        [
            "Trust-focused navy base",
            "Teal for positive signals",
            "Amber for gaps and risks",
        ],
        light=True,
    )


def render_panel(title: str, body: str, bullets: list[str] | None = None) -> None:
    """Render a bordered information panel."""

    with st.container(border=True):
        st.markdown(f"<div class='section-kicker'>Panel</div>", unsafe_allow_html=True)
        st.markdown(f"#### {title}")
        st.write(body)
        if bullets:
            for item in bullets:
                st.markdown(f"- {item}")


def render_list_card(title: str, items: list[str]) -> None:
    """Render a simple list card."""

    with st.container(border=True):
        st.markdown(f"<div class='section-kicker'>{title}</div>", unsafe_allow_html=True)
        if items:
            for item in items:
                st.markdown(f"- {item}")
        else:
            st.caption("No items to display.")


def render_metric_card(label: str, value: str, note: str, badge: tuple[str, str] | None = None) -> None:
    """Render a KPI card using native Streamlit components."""

    with st.container(border=True):
        st.metric(label, value)
        if badge:
            render_pills([badge[0]], tone=badge[1])
        st.caption(note)


def render_input_workspace() -> tuple[object, str, bool]:
    """Render the input area and supporting guidance."""

    input_col, guide_col = st.columns([1.7, 1], gap="large")

    with input_col:
        with st.container(border=True):
            st.markdown("<div class='section-kicker'>Inputs</div>", unsafe_allow_html=True)
            st.markdown("### Upload resume and target role")

            toggle_cols = st.columns(2)
            if toggle_cols[0].button("Load Demo Example", use_container_width=True):
                load_demo_inputs()
            if toggle_cols[1].button("Use My Own Resume", use_container_width=True):
                reset_demo_mode()

            current_mode = (
                "Bundled demo resume" if st.session_state["use_demo_resume"] else "Uploaded PDF"
            )
            st.markdown(
                f"<div class='muted-line'>Current source mode: <strong>{html.escape(current_mode)}</strong></div>",
                unsafe_allow_html=True,
            )

            with st.form("resume_analysis_form", clear_on_submit=False):
                st.markdown("**Resume PDF**")
                uploaded_file = st.file_uploader(
                    "Upload a text-based PDF resume",
                    type=["pdf"],
                    label_visibility="collapsed",
                    help="This build expects a text-based PDF. Scanned image PDFs are not supported yet.",
                )

                if st.session_state["use_demo_resume"]:
                    st.info("The demo resume is active. You can still replace the job description below.")
                else:
                    st.caption("Use a clean PDF with selectable text for the best extraction results.")

                st.markdown("**Target Job Description**")
                job_description = st.text_area(
                    "Paste the target role",
                    key="job_description_input",
                    height=310,
                    label_visibility="collapsed",
                    placeholder=(
                        "Paste the full job description here, including responsibilities, requirements, "
                        "and preferred qualifications."
                    ),
                )
                st.caption("Longer job descriptions usually produce better keyword and fit analysis.")

                analyze_clicked = st.form_submit_button("Run Analysis", use_container_width=True)

    with guide_col:
        render_panel(
            "What you get back",
            "The app is designed to return a recruiter-friendly evaluation rather than a vague one-line verdict.",
            bullets=[
                "Weighted overall match score",
                "Matched and missing keywords",
                "ATS checks and structure feedback",
                "Grounded bullet rewrite suggestions",
            ],
        )
        render_panel(
            "How the score works",
            "The score combines clear components so you can see where the fit is strong and where it breaks down.",
            bullets=[
                "Keyword alignment",
                "Semantic relevance",
                "Section quality",
                "ATS readiness",
                "Achievement strength in bullets",
            ],
        )
        render_panel(
            "Best input quality",
            "This tool performs best when the source material is complete, recent, and easy to parse.",
            bullets=[
                "Use the latest version of your resume",
                "Paste the full role description, not just the title",
                "Keep suggestions truthful and evidence-based",
            ],
        )

    return uploaded_file, st.session_state["job_description_input"], analyze_clicked


def render_score_breakdown(result) -> None:
    """Render the score breakdown table and progress bars."""

    with st.container(border=True):
        st.markdown("<div class='section-kicker'>Score Breakdown</div>", unsafe_allow_html=True)
        st.markdown("### Weighted component view")
        breakdown_df = pd.DataFrame(
            [
                {
                    "Component": component.name,
                    "Contribution": f"{component.score:.1f}",
                    "Weight": f"{component.max_score:.0f}",
                    "Percent": f"{component.percentage}%",
                    "Explanation": component.explanation,
                }
                for component in result.score_components
            ]
        )
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

        for component in result.score_components:
            st.markdown(f"**{component.name}**")
            st.caption(component.explanation)
            st.progress(component.percentage / 100)


def render_summary_cards(result) -> None:
    """Render top-level KPI cards."""

    fit_text, fit_tone = fit_label(result.overall_score)
    passed_checks = sum(check.passed for check in result.ats_checks)
    reviewed_sections = sum(
        1
        for feedback in result.section_feedback
        if feedback.section in {"summary", "experience", "skills", "education"} and feedback.score > 0
    )

    metric_cols = st.columns(5, gap="medium")
    with metric_cols[0]:
        render_metric_card(
            "Match Score",
            f"{result.overall_score}%",
            "Overall weighted resume-to-role fit.",
            badge=(fit_text, fit_tone),
        )
    with metric_cols[1]:
        render_metric_card(
            "Matched Keywords",
            str(len(result.matched_keywords)),
            "Prioritized role terms already reflected in the resume.",
        )
    with metric_cols[2]:
        render_metric_card(
            "Missing Keywords",
            str(len(result.missing_keywords)),
            "Relevant role terms not visible in the current resume.",
        )
    with metric_cols[3]:
        render_metric_card(
            "ATS Checks Passed",
            f"{passed_checks}/{len(result.ats_checks)}",
            "Formatting and scanability checks.",
        )
    with metric_cols[4]:
        render_metric_card(
            "Quantified Bullets",
            f"{result.achievement_signals.quantified_bullets}/{result.achievement_signals.total_bullets}",
            f"{reviewed_sections} core sections received detailed review.",
        )


def render_overview_tab(result) -> None:
    """Render the overview tab."""

    render_summary_cards(result)
    st.markdown("")

    left_col, right_col = st.columns([1.45, 1], gap="large")
    with left_col:
        render_score_breakdown(result)
    with right_col:
        render_panel("Assessment summary", result.summary)
        render_panel(
            "Run metadata",
            "This panel records the current target role and analysis backend.",
            bullets=[
                f"Target role: {result.job_title}",
                f"Resume source: {result.source_label}",
                f"Semantic backend: {result.semantic_backend}",
            ],
        )

    strengths_col, weaknesses_col = st.columns(2, gap="large")
    with strengths_col:
        render_list_card("Strengths", result.strengths)
    with weaknesses_col:
        render_list_card("Weaknesses", result.weaknesses)


def render_keywords_tab(result) -> None:
    """Render keyword and skill gap detail."""

    keyword_col, gap_col = st.columns([1.02, 1.38], gap="large")
    with keyword_col:
        with st.container(border=True):
            st.markdown("<div class='section-kicker'>Keyword Coverage</div>", unsafe_allow_html=True)
            st.markdown("### Matched keywords")
            render_pills(result.matched_keywords[:18], tone="teal")
            st.markdown("")
            st.markdown("### Missing keywords")
            render_pills(result.missing_keywords[:18], tone="amber")
            st.markdown("")
            st.markdown("### Resume keywords surfaced")
            render_pills(result.resume_keywords[:18], tone="navy")

    with gap_col:
        with st.container(border=True):
            st.markdown("<div class='section-kicker'>Gap Analysis</div>", unsafe_allow_html=True)
            st.markdown("### Skills and requirement gaps")
            gap_frame = pd.DataFrame(
                [
                    {
                        "Category": gap.category,
                        "Matched": ", ".join(gap.matched) if gap.matched else "-",
                        "Missing": ", ".join(gap.missing) if gap.missing else "-",
                        "Recommendation": gap.recommendation,
                    }
                    for gap in result.skill_gaps
                ]
            )
            if gap_frame.empty:
                st.info("No skill gap groups were generated.")
            else:
                st.dataframe(gap_frame, use_container_width=True, hide_index=True)


def render_ats_and_sections_tab(result) -> None:
    """Render ATS checks and section review."""

    ats_col, section_col = st.columns([1, 1.2], gap="large")

    with ats_col:
        with st.container(border=True):
            st.markdown("<div class='section-kicker'>ATS Checks</div>", unsafe_allow_html=True)
            st.markdown("### Formatting and parsing review")
            for check in result.ats_checks:
                tone = "teal" if check.passed else "amber"
                label = "Pass" if check.passed else "Risk"
                render_pills([label], tone=tone)
                st.markdown(f"**{check.label}**")
                st.caption(check.impact)
                st.write(check.recommendation)
                st.divider()

    with section_col:
        with st.container(border=True):
            st.markdown("<div class='section-kicker'>Section Review</div>", unsafe_allow_html=True)
            st.markdown("### Section-by-section feedback")
            section_df = pd.DataFrame(
                [
                    {
                        "Section": title_case_label(feedback.section),
                        "Score": f"{feedback.percentage}%",
                        "Strengths": len(feedback.strengths),
                        "Risks": len(feedback.risks),
                        "Suggestions": len(feedback.suggestions),
                    }
                    for feedback in result.section_feedback
                ]
            )
            st.dataframe(section_df, use_container_width=True, hide_index=True)

            for feedback in result.section_feedback:
                with st.expander(f"{title_case_label(feedback.section)} - {feedback.percentage}%"):
                    st.markdown("**Strengths**")
                    if feedback.strengths:
                        for item in feedback.strengths:
                            st.markdown(f"- {item}")
                    else:
                        st.caption("No specific strengths were flagged for this section.")

                    st.markdown("**Risks**")
                    if feedback.risks:
                        for item in feedback.risks:
                            st.markdown(f"- {item}")
                    else:
                        st.caption("No major risks were flagged for this section.")

                    st.markdown("**Suggestions**")
                    if feedback.suggestions:
                        for item in feedback.suggestions:
                            st.markdown(f"- {item}")
                    else:
                        st.caption("No immediate changes are required here.")


def render_bullet_suggestions_tab(result) -> None:
    """Render bullet rewrite guidance."""

    metric_cols = st.columns(4)
    metric_cols[0].metric("Total bullets reviewed", result.achievement_signals.total_bullets)
    metric_cols[1].metric("Action-led bullets", result.achievement_signals.action_bullets)
    metric_cols[2].metric("Quantified bullets", result.achievement_signals.quantified_bullets)
    metric_cols[3].metric("Weak bullets flagged", result.achievement_signals.weak_bullets)

    with st.container(border=True):
        st.markdown("<div class='section-kicker'>Bullet Rewrites</div>", unsafe_allow_html=True)
        st.markdown("### Suggested improvements")
        st.caption(
            "These suggestions improve structure and specificity. They do not invent achievements, tools, or metrics."
        )

        if result.bullet_suggestions:
            for suggestion in result.bullet_suggestions:
                render_pills([suggestion.section], tone="navy")
                st.markdown(f"**Original**  \n{suggestion.original}")
                st.markdown(f"**Stronger direction**  \n{suggestion.suggestion}")
                st.markdown(f"**Why**  \n{suggestion.reason}")
                st.divider()
        else:
            st.info("No weak bullets were flagged strongly enough to rewrite.")


def render_downloads(result, pdf_report_bytes: bytes | None) -> None:
    """Render report downloads."""

    with st.container(border=True):
        st.markdown("<div class='section-kicker'>Reports</div>", unsafe_allow_html=True)
        st.markdown("### Export analysis output")
        st.caption(
            "Use the Markdown report for GitHub or versioned notes. Use the PDF report for quick review or sharing."
        )
        md_col, pdf_col = st.columns(2)
        with md_col:
            st.download_button(
                label="Download Markdown Report",
                data=result.markdown_report,
                file_name="resume_analysis_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with pdf_col:
            if pdf_report_bytes:
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_report_bytes,
                    file_name="resume_analysis_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.warning("PDF export is currently unavailable.")

        with st.expander("Preview Markdown Report"):
            st.code(result.markdown_report, language="markdown")


def render_results(result, pdf_report_bytes: bytes | None) -> None:
    """Render the results dashboard."""

    st.subheader("Analysis Results")
    tabs = st.tabs(
        ["Overview", "Keywords & Gaps", "ATS & Sections", "Bullet Rewrites", "Report"]
    )
    with tabs[0]:
        render_overview_tab(result)
    with tabs[1]:
        render_keywords_tab(result)
    with tabs[2]:
        render_ats_and_sections_tab(result)
    with tabs[3]:
        render_bullet_suggestions_tab(result)
    with tabs[4]:
        render_downloads(result, pdf_report_bytes)


def main() -> None:
    """Render the Streamlit app."""

    initialize_session_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    render_header()

    uploaded_file, job_description, analyze_clicked = render_input_workspace()

    if analyze_clicked:
        try:
            validated_job_description = require_non_empty_text(
                job_description, "Job description"
            )
            with st.status("Running analysis...", expanded=True) as status:
                if st.session_state["use_demo_resume"]:
                    st.write("Loaded bundled demo resume.")
                    resume_text = load_demo_resume_text()
                    source_label = "Bundled demo resume"
                else:
                    if uploaded_file is None:
                        raise ValueError("Upload a resume PDF or switch on the demo example first.")
                    st.write("Extracting text from the uploaded PDF.")
                    resume_text = extract_text_from_pdf(uploaded_file.getvalue())
                    source_label = uploaded_file.name

                st.write(
                    "Scoring keyword overlap, semantic relevance, ATS readiness, section quality, and bullet strength."
                )
                result = get_service().analyze(
                    resume_text=resume_text,
                    job_description=validated_job_description,
                    source_label=source_label,
                )
                st.write("Generating downloadable reports.")
                pdf_report_bytes = generate_pdf_report(result)
                status.update(label="Analysis complete", state="complete")

            st.session_state["analysis_result"] = result
            st.session_state["pdf_report_bytes"] = pdf_report_bytes
        except ResumeParsingError as exc:
            st.error(str(exc))
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:  # pragma: no cover - UI safety net
            st.exception(exc)

    if st.session_state["analysis_result"] is not None:
        st.divider()
        render_results(
            st.session_state["analysis_result"],
            st.session_state["pdf_report_bytes"],
        )


if __name__ == "__main__":
    main()
