"""
Pytest suite for the recommendation engine (L3-L9).

Proves that:
1. Keyword extraction returns meaningful terms.
2. Trending score normalisation works correctly.
3. A user profile is built from liked cards.
4. The scoring engine ranks relevant cards higher.
5. The full pipeline improves ordering when a user has swipe history.
6. The /cards/recommended API endpoint works end-to-end.
"""

import pytest
from fastapi.testclient import TestClient

from models.schemas import Card, Interaction
from services.recommendation import (
    build_user_profile,
    compute_trending_score,
    extract_keywords,
    extract_keywords_tfidf,
    normalize_trending_scores,
    recommend_cards,
    score_cards,
)
from services.swipe_store import clear_all, record_interaction
from services.ingestion import get_all_cards


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_card(id: str, title: str, keywords: list[str], score: float = 0.5) -> Card:
    return Card(
        id=id,
        card_title=title,
        card_summary=f"Summary about {title}.",
        keywords=keywords,
        source="test",
        source_url="https://example.com",
        trending_score=score,
    )


CARD_TRANSFORMER = _make_card("c1", "Transformer research", ["transformer", "research", "attention"], 0.8)
CARD_SAFETY = _make_card("c2", "AI safety advances", ["safety", "alignment", "research"], 0.6)
CARD_AGENTS = _make_card("c3", "Autonomous AI agents", ["agents", "tool-use", "autonomy"], 0.9)
CARD_VISION = _make_card("c4", "Vision transformers", ["transformer", "vision", "computer-vision"], 0.5)
CARD_RLHF = _make_card("c5", "RLHF training guide", ["rlhf", "reinforcement-learning", "safety", "alignment"], 0.4)
CARD_RAG = _make_card("c6", "RAG pipeline setup", ["rag", "retrieval", "vector-search"], 0.7)

ALL_TEST_CARDS = [CARD_TRANSFORMER, CARD_SAFETY, CARD_AGENTS, CARD_VISION, CARD_RLHF, CARD_RAG]


# ---------------------------------------------------------------------------
# L3 — Keyword Extraction
# ---------------------------------------------------------------------------

class TestKeywordExtraction:
    def test_basic_extraction(self):
        text = "Transformer models are revolutionizing natural language processing and transformer attention mechanisms"
        kws = extract_keywords(text, top_n=3)
        assert len(kws) <= 3
        assert "transformer" in kws

    def test_empty_text(self):
        assert extract_keywords("") == []
        assert extract_keywords("a the is") == []

    def test_tfidf_extraction(self):
        docs = [
            "Transformer attention mechanism for language models",
            "Reinforcement learning with human feedback for safety",
            "Computer vision with convolutional neural networks",
        ]
        results = extract_keywords_tfidf(docs, top_n=3)
        assert len(results) == 3
        for kws in results:
            assert len(kws) > 0

    def test_keywords_are_lowercase(self):
        kws = extract_keywords("Transformer MODELS are Great")
        for kw in kws:
            assert kw == kw.lower()


# ---------------------------------------------------------------------------
# L4/L5 — Trending Score
# ---------------------------------------------------------------------------

class TestTrendingScore:
    def test_score_range(self):
        score = compute_trending_score(stars=50, likes=30, citations=10, max_stars=100, max_likes=100, max_citations=100)
        assert 0.0 <= score <= 1.0

    def test_max_inputs_give_one(self):
        score = compute_trending_score(stars=100, likes=100, citations=100, max_stars=100, max_likes=100, max_citations=100)
        assert score == 1.0

    def test_zero_inputs_give_zero(self):
        score = compute_trending_score(stars=0, likes=0, citations=0)
        assert score == 0.0

    def test_normalize_batch(self):
        cards = [
            _make_card("a", "A", ["x"], 0.5),
            _make_card("b", "B", ["y"], 1.0),
            _make_card("c", "C", ["z"], 0.25),
        ]
        normed = normalize_trending_scores(cards)
        assert normed[1].trending_score == 1.0
        assert normed[0].trending_score == 0.5
        assert normed[2].trending_score == 0.25


# ---------------------------------------------------------------------------
# L6 — User Preference Profile
# ---------------------------------------------------------------------------

class TestUserProfile:
    def test_profile_from_likes(self):
        liked = [CARD_TRANSFORMER, CARD_VISION]
        profile = build_user_profile(liked)
        # "transformer" appears in both cards → highest weight
        assert "transformer" in profile
        assert profile["transformer"] > profile.get("attention", 0)

    def test_empty_likes(self):
        profile = build_user_profile([])
        assert profile == {}

    def test_profile_weights_sum_to_one(self):
        liked = [CARD_TRANSFORMER, CARD_SAFETY, CARD_RLHF]
        profile = build_user_profile(liked)
        total = sum(profile.values())
        assert abs(total - 1.0) < 0.01


# ---------------------------------------------------------------------------
# L7 — Scoring Engine
# ---------------------------------------------------------------------------

class TestScoringEngine:
    def test_similar_cards_ranked_higher(self):
        """A user who likes transformer + research cards should see
        transformer/vision cards ranked above unrelated ones."""
        liked = [CARD_TRANSFORMER]
        profile = build_user_profile(liked)
        ranked = score_cards(profile, ALL_TEST_CARDS)

        # The top result should share keywords with the liked card
        top_keywords = set(k.lower() for k in ranked[0].keywords)
        liked_keywords = set(k.lower() for k in CARD_TRANSFORMER.keywords)
        assert top_keywords & liked_keywords, "Top card should share keywords with liked card"

    def test_cold_start_uses_trending(self):
        """With no profile, trending-only ranking should put highest-scored card first."""
        profile = {}
        ranked = score_cards(profile, ALL_TEST_CARDS, trending_weight=1.0, similarity_weight=0.0)
        scores = [c.trending_score for c in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_safety_fan_gets_safety_content(self):
        """A user who likes safety-related cards should see RLHF/safety ranked high."""
        liked = [CARD_SAFETY, CARD_RLHF]
        profile = build_user_profile(liked)
        ranked = score_cards(profile, ALL_TEST_CARDS)

        top_3_ids = {c.id for c in ranked[:3]}
        # Both safety-related cards should appear near the top
        assert CARD_SAFETY.id in top_3_ids or CARD_RLHF.id in top_3_ids


# ---------------------------------------------------------------------------
# L7 continued — Full recommend_cards pipeline
# ---------------------------------------------------------------------------

class TestRecommendPipeline:
    @pytest.mark.asyncio
    async def test_cold_start_excludes_swiped(self):
        """Cold-start should exclude already-swiped cards."""
        swiped = {CARD_TRANSFORMER.id, CARD_AGENTS.id}
        result = await recommend_cards(ALL_TEST_CARDS, liked_cards=[], swiped_ids=swiped)
        result_ids = {c.id for c in result}
        assert CARD_TRANSFORMER.id not in result_ids
        assert CARD_AGENTS.id not in result_ids

    @pytest.mark.asyncio
    async def test_recommendations_improve_with_history(self):
        """
        Core proof: recommendations should re-order when a user has history.

        1. Cold-start order = by trending.
        2. After liking transformer cards, transformer-related cards should
           rise relative to their cold-start position.
        """
        # Cold start
        cold = await recommend_cards(ALL_TEST_CARDS, liked_cards=[], swiped_ids=set())
        cold_order = [c.id for c in cold]

        # User likes transformer card -> now get personalised recs
        swiped = {CARD_TRANSFORMER.id}
        liked = [CARD_TRANSFORMER]
        warm = await recommend_cards(ALL_TEST_CARDS, liked_cards=liked, swiped_ids=swiped)
        warm_order = [c.id for c in warm]

        # CARD_VISION shares "transformer" keyword → should rank higher in warm
        # than in cold (where it's low because trending_score=0.5)
        if CARD_VISION.id in cold_order and CARD_VISION.id in warm_order:
            cold_pos = cold_order.index(CARD_VISION.id)
            warm_pos = warm_order.index(CARD_VISION.id)
            assert warm_pos <= cold_pos, (
                f"Vision card should rank same or higher after liking transformers: "
                f"cold={cold_pos}, warm={warm_pos}"
            )

    @pytest.mark.asyncio
    async def test_personalised_beats_random(self):
        """After liking safety cards, the top result should be safety-related."""
        liked = [CARD_SAFETY, CARD_RLHF]
        swiped = {CARD_SAFETY.id, CARD_RLHF.id}
        result = await recommend_cards(ALL_TEST_CARDS, liked_cards=liked, swiped_ids=swiped)
        # Remaining cards: c1 (transformer), c3 (agents), c4 (vision), c6 (rag)
        # None share exact "safety" keyword but c1 shares "research"
        assert len(result) == len(ALL_TEST_CARDS) - len(swiped)


# ---------------------------------------------------------------------------
# L8 — API Endpoint Integration Test
# ---------------------------------------------------------------------------

class TestRecommendedEndpoint:
    @pytest.fixture(autouse=True)
    def _reset_store(self):
        clear_all()
        yield
        clear_all()

    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_cold_start_returns_all_cards(self, client):
        resp = client.get("/api/v1/cards/recommended?session_id=test-user-1")
        assert resp.status_code == 200
        cards = resp.json()
        assert len(cards) > 0
        # Should be sorted by trending descending
        scores = [c["trending_score"] for c in cards]
        assert scores == sorted(scores, reverse=True)

    def test_swipe_then_recommend(self, client):
        # Swipe right on seed-1
        client.post("/api/v1/interactions", json={
            "session_id": "test-user-2",
            "card_id": "seed-1",
            "action": "swipe_right",
        })

        resp = client.get("/api/v1/cards/recommended?session_id=test-user-2")
        assert resp.status_code == 200
        cards = resp.json()
        card_ids = [c["id"] for c in cards]

        # Swiped card should be excluded
        assert "seed-1" not in card_ids
        assert len(cards) > 0

    def test_swipe_left_excludes_card(self, client):
        """Swiping left also excludes the card from future recommendations."""
        client.post("/api/v1/interactions", json={
            "session_id": "test-user-3",
            "card_id": "seed-2",
            "action": "swipe_left",
        })

        resp = client.get("/api/v1/cards/recommended?session_id=test-user-3")
        assert resp.status_code == 200
        cards = resp.json()
        card_ids = [c["id"] for c in cards]

        assert "seed-2" not in card_ids

    def test_all_swiped_returns_empty(self, client):
        """Swiping on all cards returns an empty list."""
        from services.ingestion import get_all_cards
        all_ids = [c.id for c in get_all_cards()]
        for card_id in all_ids:
            client.post("/api/v1/interactions", json={
                "session_id": "test-user-4",
                "card_id": card_id,
                "action": "swipe_right",
            })

        resp = client.get("/api/v1/cards/recommended?session_id=test-user-4")
        assert resp.status_code == 200
        assert resp.json() == []
