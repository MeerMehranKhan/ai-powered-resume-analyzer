"""Typed models shared across the application."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ParsedResume:
    """Structured resume content derived from the extracted text."""

    raw_text: str
    sections: dict[str, str]
    bullets_by_section: dict[str, list[str]]

    @property
    def all_bullets(self) -> list[str]:
        """Return every bullet across all sections."""

        bullets: list[str] = []
        for section_bullets in self.bullets_by_section.values():
            bullets.extend(section_bullets)
        return bullets


@dataclass(slots=True)
class ScoreComponent:
    """A transparent scoring component."""

    name: str
    score: float
    max_score: float
    explanation: str

    @property
    def percentage(self) -> int:
        """Return the component score as a percentage."""

        if self.max_score == 0:
            return 0
        return round((self.score / self.max_score) * 100)


@dataclass(slots=True)
class ATSCheck:
    """A pass/fail ATS heuristic."""

    label: str
    passed: bool
    impact: str
    recommendation: str


@dataclass(slots=True)
class SectionFeedback:
    """Feedback for an individual resume section."""

    section: str
    score: float
    max_score: float
    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> int:
        """Return the section score as a percentage."""

        if self.max_score == 0:
            return 0
        return round((self.score / self.max_score) * 100)


@dataclass(slots=True)
class BulletSuggestion:
    """A rewrite direction for a weak bullet."""

    section: str
    original: str
    suggestion: str
    reason: str


@dataclass(slots=True)
class SkillGap:
    """A category-level view of matched and missing job requirements."""

    category: str
    matched: list[str]
    missing: list[str]
    recommendation: str


@dataclass(slots=True)
class AchievementSignals:
    """Signals used for bullet-quality scoring."""

    total_bullets: int
    action_bullets: int
    quantified_bullets: int
    weak_bullets: int


@dataclass(slots=True)
class AnalysisResult:
    """The full analyzer output rendered in the UI and report."""

    source_label: str
    job_title: str
    overall_score: int
    score_components: list[ScoreComponent]
    matched_keywords: list[str]
    missing_keywords: list[str]
    resume_keywords: list[str]
    strengths: list[str]
    weaknesses: list[str]
    skill_gaps: list[SkillGap]
    ats_checks: list[ATSCheck]
    section_feedback: list[SectionFeedback]
    bullet_suggestions: list[BulletSuggestion]
    achievement_signals: AchievementSignals
    summary: str
    semantic_backend: str
    resume_text: str
    job_description: str
    markdown_report: str = ""
