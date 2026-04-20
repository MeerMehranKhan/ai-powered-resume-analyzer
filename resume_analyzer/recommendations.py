"""Narrative recommendations and bullet rewrite guidance."""

from __future__ import annotations

import re

from resume_analyzer.config import settings
from resume_analyzer.constants import SKILL_TO_CATEGORY, WEAK_VERB_REPLACEMENTS
from resume_analyzer.models import (
    ATSCheck,
    AchievementSignals,
    BulletSuggestion,
    ParsedResume,
    SectionFeedback,
    SkillGap,
)
from resume_analyzer.utils import (
    contains_metric,
    deduplicate_preserve_order,
    starts_with_action_verb,
    title_case_label,
)


def build_skill_gap_analysis(
    matched_keywords: list[str],
    missing_keywords: list[str],
) -> list[SkillGap]:
    """Create a recruiter-friendly skill gap summary grouped by category."""

    grouped: dict[str, dict[str, list[str]]] = {}

    for keyword in matched_keywords:
        category = SKILL_TO_CATEGORY.get(keyword, "Domain Knowledge")
        grouped.setdefault(category, {"matched": [], "missing": []})["matched"].append(keyword)

    for keyword in missing_keywords:
        category = SKILL_TO_CATEGORY.get(keyword, "Domain Knowledge")
        grouped.setdefault(category, {"matched": [], "missing": []})["missing"].append(keyword)

    gaps: list[SkillGap] = []
    for category, items in grouped.items():
        matched = deduplicate_preserve_order(items["matched"])
        missing = deduplicate_preserve_order(items["missing"])
        if not matched and not missing:
            continue
        recommendation = (
            "Keep reinforcing this category with stronger proof in bullets and projects."
            if not missing
            else "Add these only if they are truthful. If not, target them in a practice project or learning plan before applying."
        )
        gaps.append(
            SkillGap(
                category=category,
                matched=matched,
                missing=missing,
                recommendation=recommendation,
            )
        )

    return sorted(gaps, key=lambda gap: (len(gap.missing), -len(gap.matched)), reverse=True)


def _strengthen_opening(text: str) -> str:
    cleaned = text.strip().lstrip("-* ").strip()
    lowered = cleaned.lower()
    for weak_phrase, replacement in WEAK_VERB_REPLACEMENTS.items():
        if lowered.startswith(weak_phrase):
            remainder = cleaned[len(weak_phrase) :].strip(" :,-")
            if remainder:
                return f"{replacement} {remainder}"
            return replacement

    if not starts_with_action_verb(cleaned):
        return f"Delivered {cleaned[0].lower() + cleaned[1:]}" if cleaned else cleaned
    return cleaned[0].upper() + cleaned[1:]


def suggest_bullet_improvements(
    parsed_resume: ParsedResume,
    missing_keywords: list[str],
) -> list[BulletSuggestion]:
    """Generate grounded rewrite suggestions for the weakest bullets."""

    candidate_bullets: list[tuple[str, str]] = []
    for section in ("experience", "projects"):
        for bullet in parsed_resume.bullets_by_section.get(section, []):
            candidate_bullets.append((section, bullet))

    scored_candidates: list[tuple[int, str, str]] = []
    for section, bullet in candidate_bullets:
        weakness_score = 0
        if not starts_with_action_verb(bullet):
            weakness_score += 2
        if not contains_metric(bullet):
            weakness_score += 2
        if len(bullet.split()) < 8 or len(bullet.split()) > 28:
            weakness_score += 1
        if re.search(r"\b(helped|worked on|responsible for|participated in)\b", bullet, re.IGNORECASE):
            weakness_score += 2
        if weakness_score:
            scored_candidates.append((weakness_score, section, bullet))

    suggestions: list[BulletSuggestion] = []
    for _, section, bullet in sorted(scored_candidates, reverse=True)[: settings.max_bullet_suggestions]:
        suggestion = _strengthen_opening(bullet).rstrip(".")
        if not contains_metric(bullet):
            suggestion += "; add the real scope, metric, or business outcome if you have it"
        if missing_keywords:
            suggestion += f". If accurate, connect it to relevant keywords such as {', '.join(missing_keywords[:2])}"
        reason_parts = []
        if not starts_with_action_verb(bullet):
            reason_parts.append("it opens weakly")
        if not contains_metric(bullet):
            reason_parts.append("it lacks measurable impact")
        if not reason_parts:
            reason_parts.append("it can be sharper and more outcome-focused")
        suggestions.append(
            BulletSuggestion(
                section=title_case_label(section),
                original=bullet,
                suggestion=suggestion + ".",
                reason=" and ".join(reason_parts).capitalize() + ".",
            )
        )

    return suggestions


def build_strengths_and_weaknesses(
    matched_keywords: list[str],
    missing_keywords: list[str],
    ats_checks: list[ATSCheck],
    section_feedback: list[SectionFeedback],
    achievement_signals: AchievementSignals,
) -> tuple[list[str], list[str]]:
    """Create concise strengths and weaknesses lists for the dashboard and report."""

    strengths: list[str] = []
    weaknesses: list[str] = []

    if matched_keywords:
        strengths.append(f"Relevant keyword coverage includes {', '.join(matched_keywords[:4])}.")

    passed_checks = [check.label.lower() for check in ats_checks if check.passed]
    if passed_checks:
        strengths.append(f"ATS-friendly signals are present in {', '.join(passed_checks[:2])}.")

    if achievement_signals.quantified_bullets:
        strengths.append(
            f"{achievement_signals.quantified_bullets} bullet(s) already include measurable results."
        )

    strong_sections = [feedback.section for feedback in section_feedback if feedback.percentage >= 70]
    if strong_sections:
        strengths.append(
            f"Section quality is strongest in {', '.join(title_case_label(section) for section in strong_sections[:3])}."
        )

    if missing_keywords:
        weaknesses.append(f"Important missing keywords include {', '.join(missing_keywords[:4])}.")

    failed_checks = [check.recommendation for check in ats_checks if not check.passed]
    if failed_checks:
        weaknesses.append(failed_checks[0])

    weak_sections = [feedback for feedback in section_feedback if feedback.percentage < 60]
    if weak_sections:
        weaknesses.append(
            f"Section-level improvements are needed in {', '.join(title_case_label(item.section) for item in weak_sections[:3])}."
        )

    if achievement_signals.total_bullets and achievement_signals.quantified_bullets == 0:
        weaknesses.append("None of the experience or project bullets show quantified impact yet.")

    return strengths[:4], weaknesses[:4]


def build_summary(
    overall_score: int,
    strengths: list[str],
    weaknesses: list[str],
    semantic_backend: str,
) -> str:
    """Build a clean narrative summary from the analysis."""

    score_band = (
        "strong"
        if overall_score >= 80
        else "competitive"
        if overall_score >= 65
        else "developing"
    )
    summary = (
        f"This resume is a {score_band} match with a score of {overall_score}%. "
        f"The analysis uses a transparent local scoring pipeline with {semantic_backend} semantic matching."
    )
    if strengths:
        summary += f" Key strengths: {strengths[0]}"
    if weaknesses:
        summary += f" Biggest gap: {weaknesses[0]}"
    return summary
