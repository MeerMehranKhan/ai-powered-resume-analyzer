"""Application configuration sourced from environment variables when needed."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    """Runtime settings for the analyzer."""

    app_name: str = "AI Resume Analyzer & Job Matcher"
    semantic_backend: str = os.getenv("RESUME_ANALYZER_SEMANTIC_BACKEND", "tfidf")
    embedding_model_name: str = os.getenv(
        "RESUME_ANALYZER_EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    top_keyword_count: int = int(os.getenv("RESUME_ANALYZER_TOP_KEYWORDS", "24"))
    max_bullet_suggestions: int = int(
        os.getenv("RESUME_ANALYZER_MAX_BULLET_SUGGESTIONS", "5")
    )


settings = Settings()
