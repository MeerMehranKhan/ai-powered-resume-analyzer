"""Semantic similarity helpers with a robust local fallback."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from resume_analyzer.config import settings
from resume_analyzer.utils import clamp


class SemanticSimilarityEngine:
    """Compute semantic similarity with optional embeddings and a TF-IDF fallback."""

    def score(self, resume_text: str, job_description: str) -> tuple[float, str]:
        """Return a similarity score in the [0, 1] range and the backend label."""

        if settings.semantic_backend == "embeddings":
            embedded = self._embedding_score(resume_text, job_description)
            if embedded is not None:
                return embedded, "sentence-transformers"
            return self._tfidf_score(resume_text, job_description), "tf-idf fallback"

        return self._tfidf_score(resume_text, job_description), "tf-idf"

    def _embedding_score(
        self, resume_text: str, job_description: str
    ) -> float | None:  # pragma: no cover - optional dependency
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            return None

        try:
            model = self._load_model()
            embeddings = model.encode([resume_text, job_description], normalize_embeddings=True)
            score = float(np.dot(embeddings[0], embeddings[1]))
            return clamp(score, 0.0, 1.0)
        except Exception:
            return None

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model():  # pragma: no cover - optional dependency
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(settings.embedding_model_name)

    @staticmethod
    def _calibrate_tfidf(raw: float) -> float:
        """Calibrate raw TF-IDF cosine similarity into a more useful range.

        Raw TF-IDF cosine similarity between short documents (resumes and
        job descriptions) clusters between 0.10 and 0.30 even for strongly
        related pairs.  This sigmoid-inspired mapping stretches that useful
        band so that clearly related pairs score ~0.50-0.70 while unrelated
        pairs remain low.
        """

        stretched = raw * 2.8 + 0.12
        return clamp(stretched, 0.0, 1.0)

    @staticmethod
    def _tfidf_score(resume_text: str, job_description: str) -> float:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=4000)
        matrix = vectorizer.fit_transform([resume_text, job_description])
        raw_similarity = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        calibrated = SemanticSimilarityEngine._calibrate_tfidf(float(raw_similarity))
        return clamp(calibrated, 0.0, 1.0)

