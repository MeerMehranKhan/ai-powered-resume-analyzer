"""Utility helpers shared across modules."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from resume_analyzer.constants import ACTION_VERBS

TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#./-]*")
METRIC_PATTERN = re.compile(
    r"(\d+[%x]?|\$\d+|\bpercent\b|\bminutes?\b|\bhours?\b|\bdays?\b|\bweeks?\b|\bmonths?\b|\byears?\b)",
    re.IGNORECASE,
)


def normalize_whitespace(text: str) -> str:
    """Collapse whitespace while preserving paragraph breaks."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_text(text: str) -> str:
    """Normalize free-form text for matching."""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.lower()
    normalized = (
        normalized.replace("\u2022", "-")
        .replace("\u25aa", "-")
        .replace("\u25cf", "-")
    )
    normalized = re.sub(r"[^\w\s+#./-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def canonicalize_term(term: str) -> str:
    """Create a consistent canonical form for a keyword or phrase."""

    term = normalize_text(term)
    return term.strip(" -:;,./")


def tokenize(text: str, minimum_length: int = 2) -> list[str]:
    """Tokenize free-form text into simple word-like units."""

    return [
        token.lower()
        for token in TOKEN_PATTERN.findall(text)
        if len(token) >= minimum_length
    ]


def sentence_split(text: str) -> list[str]:
    """Split text into rough sentence-like chunks."""

    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def deduplicate_preserve_order(items: Iterable[str]) -> list[str]:
    """Return a stable list without duplicates."""

    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def safe_ratio(numerator: float, denominator: float) -> float:
    """Return a safe ratio in the [0, 1] interval."""

    if denominator <= 0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value into a fixed interval."""

    return max(minimum, min(maximum, value))


def contains_metric(text: str) -> bool:
    """Return True when a line includes a quantitative signal."""

    return bool(METRIC_PATTERN.search(text))


def starts_with_action_verb(text: str) -> bool:
    """Return True when a bullet opens with a strong action verb."""

    tokens = tokenize(text, minimum_length=1)
    if not tokens:
        return False
    first_two = " ".join(tokens[:2])
    return tokens[0] in ACTION_VERBS or first_two in ACTION_VERBS


def title_case_label(value: str) -> str:
    """Render a snake-like section name as a user-facing title."""

    return value.replace("_", " ").title()


def to_ascii(text: str) -> str:
    """Convert text to ASCII-friendly output for PDF export."""

    text = (
        text.replace("\u2022", "- ")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return text.encode("ascii", "ignore").decode("ascii")
