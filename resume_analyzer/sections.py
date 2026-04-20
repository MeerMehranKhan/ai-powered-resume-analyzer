"""Resume section detection and section-level feedback."""

from __future__ import annotations

import re

from resume_analyzer.constants import CORE_SECTION_ORDER, REQUIRED_SECTIONS, SECTION_PATTERNS
from resume_analyzer.models import ParsedResume, SectionFeedback
from resume_analyzer.utils import contains_metric, starts_with_action_verb

BULLET_PATTERN = re.compile(r"^\s*(?:[-*\u2022\u25aa\u25e6\u25cf]|\d+[.)])\s+(.+)$")


def _normalize_heading(line: str) -> str:
    return re.sub(r"[^a-z ]", "", line.lower().strip(": ").strip())


def detect_section_heading(line: str) -> str | None:
    """Map a heading line to a canonical section label."""

    normalized = _normalize_heading(line)
    if not normalized or len(normalized.split()) > 5:
        return None

    for section, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.fullmatch(pattern, normalized):
                return section
    return None


def detect_resume_sections(text: str) -> dict[str, str]:
    """Split resume text into sections using common heading patterns."""

    lines = [line.strip() for line in text.splitlines()]
    sections: dict[str, list[str]] = {"header": []}
    current_section = "header"

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if sections[current_section] and sections[current_section][-1] != "":
                sections[current_section].append("")
            continue

        heading = detect_section_heading(line)
        if heading:
            current_section = heading
            sections.setdefault(current_section, [])
            continue

        sections.setdefault(current_section, []).append(line)

    normalized_sections = {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if "\n".join(lines).strip()
    }

    if len(normalized_sections) == 1 and "header" in normalized_sections:
        return {"experience": normalized_sections["header"]}

    return normalized_sections


def extract_bullets_by_section(sections: dict[str, str]) -> dict[str, list[str]]:
    """Extract bullet-like lines from each section."""

    bullets_by_section: dict[str, list[str]] = {}

    for section, content in sections.items():
        bullets: list[str] = []
        for line in content.splitlines():
            match = BULLET_PATTERN.match(line)
            if match:
                bullets.append(match.group(1).strip())

        if not bullets and section in {"experience", "projects"}:
            sentences = [
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])\s+|\n+", content)
                if len(sentence.strip()) > 30
            ]
            bullets = sentences[:6]

        bullets_by_section[section] = bullets

    return bullets_by_section


def build_parsed_resume(text: str) -> ParsedResume:
    """Create a structured resume object from extracted text."""

    sections = detect_resume_sections(text)
    bullets_by_section = extract_bullets_by_section(sections)
    return ParsedResume(raw_text=text, sections=sections, bullets_by_section=bullets_by_section)


def evaluate_sections(
    parsed_resume: ParsedResume,
    resume_keywords: list[str],
    prioritized_job_keywords: list[str],
) -> tuple[list[SectionFeedback], float]:
    """Generate section-level feedback and an aggregate quality ratio."""

    section_feedback: list[SectionFeedback] = []
    resume_sections = parsed_resume.sections
    resume_keyword_set = set(resume_keywords)
    job_keyword_examples = prioritized_job_keywords[:3]

    summary_text = resume_sections.get("summary", "")
    summary_strengths: list[str] = []
    summary_risks: list[str] = []
    summary_suggestions: list[str] = []
    summary_score = 0.0
    if summary_text:
        summary_score += 2
        summary_word_count = len(summary_text.split())
        if 35 <= summary_word_count <= 110:
            summary_score += 1.5
            summary_strengths.append("The summary is an appropriate length for quick recruiter scanning.")
        else:
            summary_risks.append("The summary is either too short or too dense to work as a crisp opening pitch.")
            summary_suggestions.append("Aim for 2-4 lines that frame your role, domain, and strongest relevant skills.")

        overlap_count = len([keyword for keyword in job_keyword_examples if keyword in summary_text.lower()])
        if overlap_count:
            summary_score += 1.5
            summary_strengths.append("The summary already mirrors some of the target role language.")
        else:
            summary_risks.append("The summary does not yet echo the most important language from the job description.")
            if job_keyword_examples:
                summary_suggestions.append(
                    f"Reflect truthful keywords like {', '.join(job_keyword_examples)} in the summary when relevant."
                )
    else:
        summary_risks.append("No dedicated summary section was detected.")
        summary_suggestions.append(
            "Add a short professional summary to position your strengths before the recruiter reaches your experience."
        )
    section_feedback.append(
        SectionFeedback(
            section="summary",
            score=summary_score,
            max_score=5.0,
            strengths=summary_strengths,
            risks=summary_risks,
            suggestions=summary_suggestions,
        )
    )

    experience_text = resume_sections.get("experience", "")
    experience_bullets = parsed_resume.bullets_by_section.get("experience", [])
    experience_strengths: list[str] = []
    experience_risks: list[str] = []
    experience_suggestions: list[str] = []
    experience_score = 0.0
    if experience_text:
        experience_score += 2.0
        if len(experience_bullets) >= 3:
            experience_score += 1.0
            experience_strengths.append("The experience section uses bullets, which is ATS-friendly and easier to skim.")
        else:
            experience_risks.append("The experience section has too few bullet points for a strong impact narrative.")
            experience_suggestions.append("Break dense paragraphs into result-oriented bullets.")

        action_bullets = sum(starts_with_action_verb(bullet) for bullet in experience_bullets)
        quantified_bullets = sum(contains_metric(bullet) for bullet in experience_bullets)
        if action_bullets >= max(1, len(experience_bullets) // 2):
            experience_score += 1.0
            experience_strengths.append("Most bullets start with clear action verbs.")
        else:
            experience_risks.append("Several bullets use passive or vague openings.")
            experience_suggestions.append("Lead bullets with verbs such as Built, Led, Automated, or Improved.")

        if quantified_bullets >= max(1, len(experience_bullets) // 3):
            experience_score += 1.0
            experience_strengths.append("There is some measurable evidence of impact.")
        else:
            experience_risks.append("The section needs more proof of scale, speed, accuracy, or business outcome.")
            experience_suggestions.append("Add real metrics, scope, or frequency wherever you can support them.")
    else:
        experience_risks.append("No clear experience section was detected.")
        experience_suggestions.append("Use an Experience heading with scannable bullets for each role.")
    section_feedback.append(
        SectionFeedback(
            section="experience",
            score=experience_score,
            max_score=5.0,
            strengths=experience_strengths,
            risks=experience_risks,
            suggestions=experience_suggestions,
        )
    )

    skills_text = resume_sections.get("skills", "")
    skills_strengths: list[str] = []
    skills_risks: list[str] = []
    skills_suggestions: list[str] = []
    skills_score = 0.0
    if skills_text:
        skills_score += 2.0
        listed_skill_count = len(resume_keyword_set)
        if listed_skill_count >= 8:
            skills_score += 2.0
            skills_strengths.append("The skills section has enough depth to help ATS matching.")
        else:
            skills_risks.append("The skills section is present but still thin.")
            skills_suggestions.append("List the most relevant tools, methods, and platforms you can truthfully support.")

        if any(keyword in resume_keyword_set for keyword in job_keyword_examples):
            skills_score += 1.0
            skills_strengths.append("The skills section already overlaps with the target job language.")
        elif job_keyword_examples:
            skills_risks.append("The skills section does not yet highlight the most important job-specific tools.")
            skills_suggestions.append(
                f"Surface truthful matches such as {', '.join(job_keyword_examples)} if they belong on your resume."
            )
    else:
        skills_risks.append("No dedicated skills section was detected.")
        skills_suggestions.append("Add a Skills section so ATS systems can find tools and methods quickly.")
    section_feedback.append(
        SectionFeedback(
            section="skills",
            score=skills_score,
            max_score=5.0,
            strengths=skills_strengths,
            risks=skills_risks,
            suggestions=skills_suggestions,
        )
    )

    education_text = resume_sections.get("education", "")
    education_strengths: list[str] = []
    education_risks: list[str] = []
    education_suggestions: list[str] = []
    education_score = 0.0
    if education_text:
        education_score += 3.0
        education_strengths.append("Education is clearly separated, which helps resume completeness.")
    else:
        education_risks.append("No education section was detected.")
        education_suggestions.append("Add Education even if you keep it brief.")
    section_feedback.append(
        SectionFeedback(
            section="education",
            score=education_score,
            max_score=3.0,
            strengths=education_strengths,
            risks=education_risks,
            suggestions=education_suggestions,
        )
    )

    projects_text = resume_sections.get("projects", "")
    projects_strengths: list[str] = []
    projects_risks: list[str] = []
    projects_suggestions: list[str] = []
    projects_score = 0.0
    if projects_text:
        projects_score += 3.0
        projects_strengths.append("Projects help prove applied skill beyond the job title alone.")
    else:
        projects_risks.append("No project section was detected.")
        projects_suggestions.append(
            "If you have relevant side projects, capstones, or portfolio work, add them under a Projects section."
        )
    section_feedback.append(
        SectionFeedback(
            section="projects",
            score=projects_score,
            max_score=3.0,
            strengths=projects_strengths,
            risks=projects_risks,
            suggestions=projects_suggestions,
        )
    )

    total_score = sum(item.score for item in section_feedback)
    total_max = sum(item.max_score for item in section_feedback)
    required_missing_count = sum(
        1 for required in REQUIRED_SECTIONS if required not in parsed_resume.sections
    )
    base_ratio = total_score / total_max if total_max else 0.0
    penalty = min(0.25, required_missing_count * 0.05)
    return section_feedback, max(0.0, base_ratio - penalty)
