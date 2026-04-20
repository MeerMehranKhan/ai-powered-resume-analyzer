# Architecture Guide

## Overview

This project is intentionally built as a local-first portfolio application:

- `app.py` handles the Streamlit interface and user interaction.
- `resume_analyzer/service.py` orchestrates the full analysis pipeline.
- Parsing, keyword extraction, section analysis, scoring, recommendations, and report generation live in separate modules for readability and extension.
- The app works without any external API keys.
- Semantic matching uses a robust fallback strategy:
  - `sentence-transformers` if the package and model are available.
  - TF-IDF cosine similarity otherwise.

## Data Flow

1. The user uploads a resume PDF or loads the bundled demo resume.
2. `resume_analyzer/parsing.py` extracts plain text from the PDF using PyMuPDF.
3. `resume_analyzer/sections.py` identifies core resume sections and extracts bullet-style content.
4. `resume_analyzer/keywords.py` extracts weighted keywords from the job description and recruiter-visible keywords from the resume.
5. `resume_analyzer/similarity.py` computes semantic similarity between the resume and the job description.
6. `resume_analyzer/scoring.py` calculates the explainable score breakdown:
   - Keyword Alignment
   - Semantic Relevance
   - Section Quality
   - ATS Readiness
   - Achievement Evidence
7. `resume_analyzer/recommendations.py` generates skill gaps, bullet rewrite suggestions, and summary narratives.
8. `resume_analyzer/reporting.py` produces a Markdown report and, when `fpdf2` is installed, a PDF report.

## Scoring System

The final score is out of 100 and is intentionally transparent.

| Component | Weight | What it measures |
| --- | ---: | --- |
| Keyword Alignment | 35 | Weighted overlap between the job description and the resume |
| Semantic Relevance | 25 | Overall topical similarity between the two documents |
| Section Quality | 15 | Presence and quality of core sections like Summary, Experience, Skills, and Education |
| ATS Readiness | 15 | Formatting and scanability heuristics such as clear headings and bullet usage |
| Achievement Evidence | 10 | Action verbs, measurable impact, and strength of accomplishment bullets |

## Extension Points

- Replace the curated skill taxonomy in `resume_analyzer/constants.py` with a domain-specific ontology.
- Add OCR in `resume_analyzer/parsing.py` for scanned resumes.
- Add optional LLM-generated rewrite suggestions behind an environment flag while keeping the current rule-based path as the default.
- Export structured JSON from `resume_analyzer/service.py` if you want an API layer later.
- Add more tests around edge cases such as multi-column resumes or highly specialized job descriptions.
