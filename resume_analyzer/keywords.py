"""Keyword extraction and overlap analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
import re

from resume_analyzer.config import settings
from resume_analyzer.constants import (
    GENERIC_KEYWORD_PHRASES,
    SKILL_SYNONYMS,
    STOPWORDS,
)
from resume_analyzer.utils import (
    canonicalize_term,
    deduplicate_preserve_order,
    normalize_text,
    sentence_split,
    tokenize,
)

REQUIREMENT_CUE_PATTERN = re.compile(
    r"\b(required|must|need to|experience with|proficient in|preferred|bonus|nice to have)\b",
    re.IGNORECASE,
)


def _phrase_regex(phrase: str) -> re.Pattern[str]:
    canonical = canonicalize_term(phrase)
    return re.compile(rf"(?<!\w){re.escape(canonical)}(?!\w)", re.IGNORECASE)


def extract_known_skills(text: str) -> set[str]:
    """Extract canonical skills from a text block using a curated taxonomy."""

    normalized = normalize_text(text)
    matches: set[str] = set()
    for canonical_skill, variants in SKILL_SYNONYMS.items():
        for variant in variants:
            if _phrase_regex(variant).search(normalized):
                matches.add(canonical_skill)
                break
    return matches


def _generate_candidate_phrases(text: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for sentence in sentence_split(text):
        sentence_tokens = tokenize(sentence, minimum_length=2)
        cue_bonus = 0.6 if REQUIREMENT_CUE_PATTERN.search(sentence) else 0.0
        for ngram_size in (1, 2, 3):
            if len(sentence_tokens) < ngram_size:
                continue
            for index in range(len(sentence_tokens) - ngram_size + 1):
                ngram_tokens = sentence_tokens[index : index + ngram_size]
                if any(token in STOPWORDS for token in ngram_tokens):
                    continue
                if len(set(ngram_tokens)) == 1:
                    continue
                phrase = " ".join(ngram_tokens)
                if len(phrase) < 3 or phrase in GENERIC_KEYWORD_PHRASES:
                    continue
                score = 1.0 + (ngram_size - 1) * 0.25 + cue_bonus
                counter[phrase] += score
    return counter


def extract_weighted_job_keywords(text: str) -> dict[str, float]:
    """Extract weighted keywords from the job description."""

    weighted: dict[str, float] = {}
    prioritized_sentences = [
        normalize_text(sentence)
        for sentence in sentence_split(text)
        if REQUIREMENT_CUE_PATTERN.search(sentence)
    ]

    for skill in sorted(extract_known_skills(text)):
        is_prioritized = any(
            _phrase_regex(variant).search(sentence)
            for sentence in prioritized_sentences
            for variant in SKILL_SYNONYMS.get(skill, {skill})
        )
        weight = 2.4 if is_prioritized else 2.0
        weighted[skill] = weight

    phrase_counter = _generate_candidate_phrases(text)
    for phrase, score in phrase_counter.most_common(settings.top_keyword_count * 3):
        canonical_phrase = canonicalize_term(phrase)
        if canonical_phrase in weighted or canonical_phrase in STOPWORDS:
            continue
        if len(canonical_phrase.split()) == 1 and len(canonical_phrase) < 4:
            continue
        weighted[canonical_phrase] = round(min(2.2, score), 2)
        if len(weighted) >= settings.top_keyword_count:
            break

    return weighted


def extract_resume_keywords(text: str) -> list[str]:
    """Extract recruiter-visible keywords from a resume."""

    known_skills = sorted(extract_known_skills(text))
    phrase_candidates = [
        phrase
        for phrase, _ in _generate_candidate_phrases(text).most_common(20)
        if len(phrase.split()) > 1
    ]
    return deduplicate_preserve_order(known_skills + phrase_candidates)[: settings.top_keyword_count]


def keyword_present(keyword: str, text: str) -> bool:
    """Return True when a keyword is present in a text block."""

    normalized = normalize_text(text)
    canonical = canonicalize_term(keyword)
    if not canonical:
        return False

    if _phrase_regex(canonical).search(normalized):
        return True

    keyword_tokens = [token for token in tokenize(canonical) if token not in STOPWORDS]
    text_token_set = set(tokenize(normalized))
    if not keyword_tokens:
        return False

    overlap = len(text_token_set.intersection(keyword_tokens))
    return overlap >= max(1, len(keyword_tokens) - 1)


def compare_keywords(
    weighted_job_keywords: dict[str, float], resume_text: str
) -> tuple[list[str], list[str], float]:
    """Compute matched and missing keywords plus the weighted overlap ratio."""

    matched: list[str] = []
    missing: list[str] = []
    matched_weight = 0.0
    total_weight = sum(weighted_job_keywords.values()) or 1.0

    for keyword, weight in weighted_job_keywords.items():
        if keyword_present(keyword, resume_text):
            matched.append(keyword)
            matched_weight += weight
        else:
            missing.append(keyword)

    overlap_ratio = matched_weight / total_weight
    return matched, missing, overlap_ratio


def group_keywords_by_category(keywords: list[str]) -> dict[str, list[str]]:
    """Group extracted keywords into rough categories for gap analysis."""

    grouped: dict[str, list[str]] = defaultdict(list)
    for keyword in keywords:
        for canonical_skill, variants in SKILL_SYNONYMS.items():
            if keyword == canonical_skill or keyword in variants:
                from resume_analyzer.constants import SKILL_TO_CATEGORY

                grouped[SKILL_TO_CATEGORY.get(canonical_skill, "Domain Knowledge")].append(
                    canonical_skill
                )
                break
        else:
            grouped["Domain Knowledge"].append(keyword)

    return {group: deduplicate_preserve_order(items) for group, items in grouped.items()}
