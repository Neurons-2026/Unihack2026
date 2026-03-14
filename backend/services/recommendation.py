"""
Recommendation engine for 10min AI Daily.

Contains:
- Keyword extraction (TF-IDF)
- Trending score normalization
- User preference profile building
- Cosine-similarity scoring engine
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Set

from models.schemas import Card


# ---------------------------------------------------------------------------
# L3 — Keyword Extraction
# ---------------------------------------------------------------------------

# Common English stop-words (kept minimal for speed)
_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "dare",
    "it", "its", "this", "that", "these", "those", "i", "we", "you", "he",
    "she", "they", "me", "us", "him", "her", "them", "my", "our", "your",
    "his", "their", "what", "which", "who", "whom", "where", "when", "how",
    "not", "no", "nor", "so", "if", "then", "than", "too", "very", "just",
    "about", "above", "after", "again", "all", "also", "am", "any", "as",
    "because", "before", "between", "both", "each", "few", "get", "got",
    "into", "more", "most", "new", "now", "only", "other", "over", "own",
    "same", "some", "such", "up", "out", "s", "t", "don", "re", "ve", "ll",
}

_TOKEN_RE = re.compile(r"[a-z][a-z0-9\-]{1,}")


def _tokenize(text: str) -> List[str]:
    """Lowercase tokenize, keep alphanumeric + hyphens, drop stop-words."""
    return [tok for tok in _TOKEN_RE.findall(text.lower()) if tok not in _STOP_WORDS]


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    Extract top-N keywords from *text* using term-frequency heuristic.

    For a single-document hackathon context, pure TF (with stop-word removal)
    gives good-enough results without needing a corpus for IDF.
    """
    tokens = _tokenize(text)
    if not tokens:
        return []
    freq = Counter(tokens)
    # Boost multi-word-ish tokens (contain hyphen) slightly
    for tok in freq:
        if "-" in tok:
            freq[tok] = int(freq[tok] * 1.3)
    return [tok for tok, _ in freq.most_common(top_n)]


def extract_keywords_tfidf(documents: List[str], top_n: int = 5) -> List[List[str]]:
    """
    Extract top-N keywords per document using scikit-learn TF-IDF.

    Use when you have a *corpus* of documents (e.g. all cards).
    Falls back to the simple heuristic if sklearn is unavailable.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        return [extract_keywords(doc, top_n) for doc in documents]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        token_pattern=r"[a-zA-Z][a-zA-Z0-9\-]{1,}",
        max_features=500,
    )
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()

    results: List[List[str]] = []
    for row_idx in range(tfidf_matrix.shape[0]):
        row = tfidf_matrix.getrow(row_idx).toarray().flatten()
        top_indices = row.argsort()[::-1][:top_n]
        results.append([feature_names[i] for i in top_indices if row[i] > 0])
    return results


# ---------------------------------------------------------------------------
# L4 / L5 — Trending Score Calculation
# ---------------------------------------------------------------------------

def compute_trending_score(
    stars: int = 0,
    likes: int = 0,
    citations: int = 0,
    max_stars: int = 1,
    max_likes: int = 1,
    max_citations: int = 1,
) -> float:
    """
    Return a 0-1 normalized trending score from raw metadata.

    Weights: stars 0.4, likes 0.35, citations 0.25
    Each metric is min-max normalized against the *batch* max before weighting.
    """
    s = stars / max(max_stars, 1)
    l = likes / max(max_likes, 1)
    c = citations / max(max_citations, 1)
    return round(0.40 * s + 0.35 * l + 0.25 * c, 4)


def normalize_trending_scores(cards: List[Card]) -> List[Card]:
    """
    Re-compute trending_score for a batch of cards so the top card = 1.0.

    If cards already have scores, normalizes them into [0, 1].
    """
    scores = [c.trending_score or 0.0 for c in cards]
    max_score = max(scores) if scores else 1.0
    if max_score == 0:
        max_score = 1.0
    for card, raw in zip(cards, scores):
        card.trending_score = round(raw / max_score, 4)
    return cards


# ---------------------------------------------------------------------------
# L6 — User Preference Profile
# ---------------------------------------------------------------------------

def build_user_profile(liked_cards: List[Card]) -> Dict[str, float]:
    """
    Build a keyword-frequency interest vector from cards the user swiped right on.

    Returns {keyword: weight} where weight = count / total_keywords.
    """
    keyword_counts: Counter = Counter()
    for card in liked_cards:
        for kw in card.keywords:
            keyword_counts[kw.lower()] += 1
    total = sum(keyword_counts.values()) or 1
    return {kw: round(count / total, 4) for kw, count in keyword_counts.items()}


# ---------------------------------------------------------------------------
# L7 — Scoring / Recommendation Engine
# ---------------------------------------------------------------------------

def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Cosine similarity between two sparse keyword vectors."""
    common_keys = set(vec_a) & set(vec_b)
    if not common_keys:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _card_keyword_vector(card: Card) -> Dict[str, float]:
    """Turn a card's keyword list into a unit-weight vector."""
    return {kw.lower(): 1.0 for kw in card.keywords}


def score_cards(
    user_profile: Dict[str, float],
    candidates: List[Card],
    trending_weight: float = 0.3,
    similarity_weight: float = 0.7,
) -> List[Card]:
    """
    Score and sort *candidates* by blended relevance:
        final = similarity_weight * cosine(user_profile, card_keywords)
              + trending_weight  * card.trending_score

    Returns cards sorted descending by final score.
    """
    scored: List[tuple[float, Card]] = []
    for card in candidates:
        sim = _cosine_similarity(user_profile, _card_keyword_vector(card))
        trend = card.trending_score or 0.0
        final = similarity_weight * sim + trending_weight * trend
        scored.append((final, card))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [card for _, card in scored]


# ---------------------------------------------------------------------------
# Public convenience used by the /cards/recommended endpoint
# ---------------------------------------------------------------------------

async def rank_cards(cards: List[Card]) -> List[Card]:
    """Backwards-compatible sort by trending_score (cold-start path)."""
    return sorted(cards, key=lambda c: c.trending_score or 0, reverse=True)


async def recommend_cards(
    all_cards: List[Card],
    liked_cards: List[Card],
    swiped_ids: Set[str],
) -> List[Card]:
    """
    Full recommendation pipeline:
    1. Filter out already-swiped cards.
    2. If no likes yet → cold-start (rank by trending).
    3. Otherwise → build profile, score by similarity + trending.
    """
    unswiped = [c for c in all_cards if c.id not in swiped_ids]
    unswiped = normalize_trending_scores(unswiped)

    if not liked_cards:
        # Cold start — trending only
        return sorted(unswiped, key=lambda c: c.trending_score or 0, reverse=True)

    profile = build_user_profile(liked_cards)
    return score_cards(profile, unswiped)
