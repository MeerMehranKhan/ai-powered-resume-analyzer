# AI Resume Analyzer & Job Matcher

An AI-powered, local-first Streamlit app that analyzes a resume against a job description and returns an explainable match score, keyword gaps, ATS feedback, section-level coaching, bullet improvement suggestions, and downloadable reports.

## Why This Project Matters

Most resume tools either feel shallow or hide their logic behind a black box. This project aims for a more credible middle ground:

- local-first analysis with no required external API
- transparent scoring instead of vague "AI magic"
- recruiter-friendly output with practical edits a candidate can actually use
- production-minded structure that can grow into an API, SaaS tool, or internal career platform

## Features

- Upload a resume as a PDF
- Paste a target job description
- Extract and clean resume text with PyMuPDF
- Detect resume sections such as Summary, Experience, Skills, Projects, and Education
- Extract weighted keywords from the job description
- Compare matched and missing keywords
- Compute an explainable overall match score
- Use semantic similarity for document-level alignment
- Surface ATS-style formatting and structure risks
- Generate skills gap analysis
- Provide section-by-section feedback
- Suggest stronger bullet rewrites without inventing experience
- Export a Markdown report
- Export a PDF report when `fpdf2` is installed
- Run with bundled demo inputs for screenshots and quick demos

## Tech Stack

- Python 3.11+
- Streamlit
- PyMuPDF
- scikit-learn
- NumPy
- pandas
- fpdf2
- pytest

Optional:

- `sentence-transformers` for stronger semantic matching if you want embeddings instead of the built-in TF-IDF fallback

## Architecture Overview

The app is split into focused Python modules instead of pushing all logic into Streamlit:

- `app.py`: Streamlit UI, workflow, downloads, and presentation
- `resume_analyzer/parsing.py`: PDF extraction and input validation
- `resume_analyzer/sections.py`: section detection, bullet extraction, section feedback
- `resume_analyzer/keywords.py`: weighted keyword extraction and overlap analysis
- `resume_analyzer/similarity.py`: semantic similarity with embeddings-or-fallback behavior
- `resume_analyzer/scoring.py`: transparent score calculation and ATS heuristics
- `resume_analyzer/recommendations.py`: strengths, weaknesses, skill gaps, bullet improvements
- `resume_analyzer/reporting.py`: Markdown and PDF report generation
- `resume_analyzer/service.py`: orchestration layer that ties everything together

For a deeper walkthrough, see [docs/architecture.md](docs/architecture.md).

## Folder Structure

```text
ai-powered-resume-analyzer/
|-- app.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- .streamlit/
|   `-- config.toml
|-- assets/
|   |-- sample_job_description.txt
|   `-- sample_resume.txt
|-- docs/
|   |-- architecture.md
|   `-- screenshots/
|       `-- README.md
|-- resume_analyzer/
|   |-- __init__.py
|   |-- config.py
|   |-- constants.py
|   |-- demo.py
|   |-- keywords.py
|   |-- models.py
|   |-- parsing.py
|   |-- recommendations.py
|   |-- reporting.py
|   |-- scoring.py
|   |-- sections.py
|   |-- service.py
|   |-- similarity.py
|   `-- utils.py
`-- tests/
    |-- test_keywords.py
    |-- test_parsing.py
    |-- test_sections.py
    `-- test_service.py
```

## How Data Flows Through the App

1. A PDF resume is uploaded in the Streamlit UI.
2. The PDF is parsed into plain text with PyMuPDF.
3. The resume is segmented into sections and bullet-like content.
4. The job description is scanned for weighted keywords and requirements.
5. The resume and job description are compared for:
   - keyword overlap
   - semantic relevance
   - ATS formatting quality
   - section completeness
   - achievement strength in bullets
6. The app generates:
   - an overall score
   - strengths and weaknesses
   - missing and matched keywords
   - skill gaps
   - ATS suggestions
   - section-level feedback
   - bullet rewrite suggestions
7. The final analysis can be downloaded as Markdown or PDF.

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Optional semantic upgrade:

```bash
pip install sentence-transformers
```

### 3. Run the app

```bash
streamlit run app.py
```

## Example Usage

1. Start the Streamlit app.
2. Click `Load Demo Example` for a quick walkthrough, or upload your own resume PDF.
3. Paste a job description.
4. Click `Analyze Resume`.
5. Review the score dashboard, keyword gaps, ATS suggestions, and bullet rewrites.
6. Download the analysis report in Markdown or PDF format.

## Environment Variables

This app does not require secrets to run. The `.env.example` file only contains optional runtime settings.
If you want to use it, copy `.env.example` to `.env` and edit the values you care about.

| Variable | Default | Purpose |
| --- | --- | --- |
| `RESUME_ANALYZER_SEMANTIC_BACKEND` | `tfidf` | Use `tfidf` for the stable local default or `embeddings` only if you intentionally want sentence-transformers |
| `RESUME_ANALYZER_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Model name used if embeddings are enabled |
| `RESUME_ANALYZER_TOP_KEYWORDS` | `24` | Number of prioritized keywords to surface |
| `RESUME_ANALYZER_MAX_BULLET_SUGGESTIONS` | `5` | Maximum number of bullet rewrites to generate |

## Testing

Run the test suite with:

```bash
pytest
```

Current test coverage includes:

- PDF parsing
- keyword extraction
- section detection
- end-to-end service output
- edge cases for invalid input

## Screenshots

Add screenshots here after running the app locally:

- `docs/screenshots/app-overview.png`
- `docs/screenshots/score-breakdown.png`
- `docs/screenshots/report-downloads.png`

## Limitations

- OCR is intentionally not enabled, so scanned image PDFs may fail to parse.
- Section detection is heuristic-based, which keeps the project simple but means unusual resume formats can reduce accuracy.
- The default semantic layer works locally via TF-IDF; embeddings are optional rather than required.
- Bullet rewrite suggestions are rule-based and conservative on purpose so the app does not fabricate experience.

## Future Improvements

- OCR support for scanned resumes
- Job-description weighting for "must-have" vs "nice-to-have" requirements
- Support Word documents in addition to PDF
- FastAPI backend and database for saved analyses
- Optional LLM-generated explanations behind an environment flag
- Recruiter-side analytics across multiple resumes

## Resume Bullet You Can Reuse

Built a local-first AI resume analyzer in Python that parses PDF resumes, scores job fit with explainable NLP heuristics, surfaces ATS and keyword gaps, and generates downloadable Markdown/PDF reports through a polished Streamlit interface.
