"""Explainable scoring logic for the analyzer."""

from __future__ import annotations

import re

from resume_analyzer.constants import REQUIRED_SECTIONS, SCORING_WEIGHTS
from resume_analyzer.models import ATSCheck, AchievementSignals, ParsedResume, ScoreComponent
from resume_analyzer.utils import contains_metric, safe_ratio, starts_with_action_verb


def infer_job_title(job_description: str) -> str:
    """Infer a display-friendly job title from the job description."""

    for line in job_description.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" in stripped and stripped.lower().startswith("title"):
            return stripped.split(":", 1)[1].strip().title()
        if 3 <= len(stripped.split()) <= 10:
            return stripped.title()
        break
    return "Target Role"


def build_ats_checks(parsed_resume: ParsedResume) -> tuple[list[ATSCheck], float]:
    """Run lightweight ATS-friendly heuristics against the parsed resume."""

    text = parsed_resume.raw_text
    header_text = "\n".join(text.splitlines()[:12])
    experience_bullets = parsed_resume.bullets_by_section.get("experience", [])
    project_bullets = parsed_resume.bullets_by_section.get("projects", [])
    total_bullets = len(experience_bullets) + len(project_bullets)
    long_lines = [line for line in text.splitlines() if len(line.strip()) > 160]
    odd_symbol_count = len(re.findall(r"[|\t]", text))

    checks = [
        ATSCheck(
            label="Clear section headings",
            passed=len([section for section in REQUIRED_SECTIONS if section in parsed_resume.sections]) >= 3,
            impact="ATS parsers map content more reliably when headings are explicit.",
            recommendation="Use standard headings like Summary, Experience, Skills, and Education.",
        ),
        ATSCheck(
            label="Bullet-based experience",
            passed=total_bullets >= 4,
            impact="Bullets improve scanability and make impact statements easier to parse.",
            recommendation="Turn dense role descriptions into concise bullets with one accomplishment per line.",
        ),
        ATSCheck(
            label="Contact details present",
            passed=bool(re.search(r"@|\+?\d[\d\s().-]{7,}|linkedin\.com", header_text, re.IGNORECASE)),
            impact="Recruiters need an easy way to identify and contact the candidate.",
            recommendation="Keep email, phone, and optionally LinkedIn near the top of the resume.",
        ),
        ATSCheck(
            label="Readable line density",
            passed=safe_ratio(len(long_lines), max(1, len(text.splitlines()))) <= 0.12,
            impact="Very long lines often come from tables or multi-column layouts that ATS systems struggle with.",
            recommendation="Avoid wide tables and keep bullets tight enough to wrap naturally.",
        ),
        ATSCheck(
            label="Low layout noise",
            passed=odd_symbol_count <= 6,
            impact="Excessive symbols and separators can create parsing noise.",
            recommendation="Prefer plain text bullets over decorative icons or heavy separators.",
        ),
    ]

    passed_ratio = safe_ratio(sum(check.passed for check in checks), len(checks))
    return checks, passed_ratio


def analyze_achievement_signals(parsed_resume: ParsedResume) -> tuple[AchievementSignals, float]:
    """Measure bullet quality using action verbs and quantified impact."""

    bullets = parsed_resume.bullets_by_section.get("experience", []) + parsed_resume.bullets_by_section.get(
        "projects", []
    )
    if not bullets:
        return AchievementSignals(0, 0, 0, 0), 0.0

    action_bullets = sum(starts_with_action_verb(bullet) for bullet in bullets)
    quantified_bullets = sum(contains_metric(bullet) for bullet in bullets)
    weak_bullets = sum(
        not starts_with_action_verb(bullet) or not contains_metric(bullet) for bullet in bullets
    )

    action_ratio = safe_ratio(action_bullets, len(bullets))
    quantified_ratio = safe_ratio(quantified_bullets, len(bullets))
    score_ratio = min(1.0, (action_ratio * 0.55) + (quantified_ratio * 0.45))
    return (
        AchievementSignals(
            total_bullets=len(bullets),
            action_bullets=action_bullets,
            quantified_bullets=quantified_bullets,
            weak_bullets=weak_bullets,
        ),
        score_ratio,
    )


def build_score_components(
    keyword_overlap_ratio: float,
    matched_keywords: list[str],
    weighted_job_keywords: dict[str, float],
    semantic_similarity: float,
    semantic_backend: str,
    section_quality_ratio: float,
    parsed_resume: ParsedResume,
    ats_ratio: float,
    achievement_ratio: float,
    achievement_signals: AchievementSignals,
) -> list[ScoreComponent]:
    """Convert raw ratios into user-facing score components."""

    section_count = len(parsed_resume.sections)
    key_section_count = len([section for section in REQUIRED_SECTIONS if section in parsed_resume.sections])
    weighted_keyword_count = len(weighted_job_keywords)

    return [
        ScoreComponent(
            name="Keyword Alignment",
            score=SCORING_WEIGHTS["keyword_alignment"] * keyword_overlap_ratio,
            max_score=SCORING_WEIGHTS["keyword_alignment"],
            explanation=(
                f"Matched {len(matched_keywords)} of {weighted_keyword_count} prioritized job keywords."
            ),
        ),
        ScoreComponent(
            name="Semantic Relevance",
            score=SCORING_WEIGHTS["semantic_relevance"] * semantic_similarity,
            max_score=SCORING_WEIGHTS["semantic_relevance"],
            explanation=(
                f"Semantic similarity was computed with the {semantic_backend} backend."
            ),
        ),
        ScoreComponent(
            name="Section Quality",
            score=SCORING_WEIGHTS["section_quality"] * section_quality_ratio,
            max_score=SCORING_WEIGHTS["section_quality"],
            explanation=(
                f"Detected {section_count} sections, including {key_section_count} of {len(REQUIRED_SECTIONS)} core sections."
            ),
        ),
        ScoreComponent(
            name="ATS Readiness",
            score=SCORING_WEIGHTS["ats_readiness"] * ats_ratio,
            max_score=SCORING_WEIGHTS["ats_readiness"],
            explanation="Scored on scanability, headings, bullet structure, and low formatting noise.",
        ),
        ScoreComponent(
            name="Achievement Evidence",
            score=SCORING_WEIGHTS["achievement_evidence"] * achievement_ratio,
            max_score=SCORING_WEIGHTS["achievement_evidence"],
            explanation=(
                f"{achievement_signals.action_bullets} of {achievement_signals.total_bullets} bullets start with action verbs and "
                f"{achievement_signals.quantified_bullets} include measurable evidence."
            ),
        ),
    ]
