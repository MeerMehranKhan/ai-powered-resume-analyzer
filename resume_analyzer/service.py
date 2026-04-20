"""Orchestration layer that ties parsing, scoring, and reporting together."""

from __future__ import annotations

from resume_analyzer.keywords import (
    compare_keywords,
    extract_resume_keywords,
    extract_weighted_job_keywords,
)
from resume_analyzer.models import AnalysisResult
from resume_analyzer.recommendations import (
    build_skill_gap_analysis,
    build_strengths_and_weaknesses,
    build_summary,
    suggest_bullet_improvements,
)
from resume_analyzer.reporting import generate_markdown_report
from resume_analyzer.scoring import (
    analyze_achievement_signals,
    build_ats_checks,
    build_score_components,
    infer_job_title,
)
from resume_analyzer.sections import build_parsed_resume, evaluate_sections
from resume_analyzer.similarity import SemanticSimilarityEngine


class ResumeAnalyzerService:
    """Facade for resume-to-job matching and feedback generation."""

    def __init__(self) -> None:
        self.similarity_engine = SemanticSimilarityEngine()

    def analyze(
        self,
        resume_text: str,
        job_description: str,
        source_label: str = "Uploaded resume",
    ) -> AnalysisResult:
        """Run the full analyzer on already-extracted resume text."""

        parsed_resume = build_parsed_resume(resume_text)
        weighted_job_keywords = extract_weighted_job_keywords(job_description)
        resume_keywords = extract_resume_keywords(resume_text)
        matched_keywords, missing_keywords, keyword_overlap_ratio = compare_keywords(
            weighted_job_keywords, resume_text
        )
        semantic_similarity, semantic_backend = self.similarity_engine.score(
            resume_text, job_description
        )
        section_feedback, section_quality_ratio = evaluate_sections(
            parsed_resume,
            resume_keywords=resume_keywords,
            prioritized_job_keywords=list(weighted_job_keywords.keys()),
        )
        ats_checks, ats_ratio = build_ats_checks(parsed_resume)
        achievement_signals, achievement_ratio = analyze_achievement_signals(parsed_resume)
        score_components = build_score_components(
            keyword_overlap_ratio=keyword_overlap_ratio,
            matched_keywords=matched_keywords,
            weighted_job_keywords=weighted_job_keywords,
            semantic_similarity=semantic_similarity,
            semantic_backend=semantic_backend,
            section_quality_ratio=section_quality_ratio,
            parsed_resume=parsed_resume,
            ats_ratio=ats_ratio,
            achievement_ratio=achievement_ratio,
            achievement_signals=achievement_signals,
        )
        overall_score = round(sum(component.score for component in score_components))
        skill_gaps = build_skill_gap_analysis(matched_keywords, missing_keywords)
        bullet_suggestions = suggest_bullet_improvements(parsed_resume, missing_keywords)
        strengths, weaknesses = build_strengths_and_weaknesses(
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            ats_checks=ats_checks,
            section_feedback=section_feedback,
            achievement_signals=achievement_signals,
        )
        summary = build_summary(
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            semantic_backend=semantic_backend,
        )

        result = AnalysisResult(
            source_label=source_label,
            job_title=infer_job_title(job_description),
            overall_score=overall_score,
            score_components=score_components,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            resume_keywords=resume_keywords,
            strengths=strengths,
            weaknesses=weaknesses,
            skill_gaps=skill_gaps,
            ats_checks=ats_checks,
            section_feedback=section_feedback,
            bullet_suggestions=bullet_suggestions,
            achievement_signals=achievement_signals,
            summary=summary,
            semantic_backend=semantic_backend,
            resume_text=resume_text,
            job_description=job_description,
        )
        result.markdown_report = generate_markdown_report(result)
        return result
