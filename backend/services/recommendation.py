import logging
from datetime import datetime, timezone
from typing import List, Optional

from models.schemas import Card

logger = logging.getLogger(__name__)

# Today's swipes are weighted 2x; older history is discounted to 0.5x.
_RECENCY_TODAY = 2.0
_RECENCY_PAST = 0.5


def _recency_multiplier(created_at: Optional[str]) -> float:
    """Return a weight based on whether the interaction happened today (UTC)."""
    if not created_at:
        return _RECENCY_PAST
    try:
        # Supabase returns ISO-8601 strings; strip timezone info for date comparison
        ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        today = datetime.now(timezone.utc).date()
        return _RECENCY_TODAY if ts.date() == today else _RECENCY_PAST
    except Exception:
        return _RECENCY_PAST


async def rank_cards(cards: List[Card], session_id: Optional[str] = None) -> List[Card]:
    """Rank cards using a blend of trending score and session keyword affinity.

    Cold start (no history): pure trending_score order.
    Warm start: 30% trending + 70% keyword affinity built from swipe history.
    Today's interactions are weighted 2x; older history is weighted 0.5x so
    that current interests dominate while long-term taste still informs results.
    Already-seen cards are pushed to the bottom so fresh content surfaces first.
    A light diversity pass prevents any one source from dominating the top.
    """
    keyword_scores: dict[str, float] = {}
    seen_card_ids: set[str] = set()

    if session_id:
        try:
            from models.database import get_supabase
            db = get_supabase()

            result = db.table("interactions").select(
                "card_id, action, dwell_time_ms, created_at"
            ).eq("session_id", session_id).execute()

            interactions = result.data or []
            if interactions:
                interacted_ids = list({row["card_id"] for row in interactions})
                kw_result = db.table("cards").select("id, keywords").in_("id", interacted_ids).execute()
                kw_map: dict[str, list[str]] = {
                    c["id"]: (c.get("keywords") or []) for c in (kw_result.data or [])
                }

                for row in interactions:
                    cid = row["card_id"]
                    action = row["action"]
                    dwell = row.get("dwell_time_ms") or 0
                    seen_card_ids.add(cid)

                    if action == "swipe_right":
                        delta = 2.0
                    elif action == "swipe_left":
                        # Long dwell on a skip means the user was still interested
                        delta = -0.5 if dwell < 8000 else 0.3
                    else:
                        continue  # undo or unknown — no signal

                    recency = _recency_multiplier(row.get("created_at"))
                    delta *= recency

                    for kw in kw_map.get(cid, []):
                        key = kw.lower()
                        keyword_scores[key] = keyword_scores.get(key, 0) + delta

        except Exception as exc:
            logger.warning("Could not load interaction history for ranking: %s", exc)

    max_trending = max((c.trending_score or 0 for c in cards), default=1) or 1
    has_history = bool(keyword_scores)

    def _score(card: Card) -> float:
        trending = (card.trending_score or 0) / max_trending
        kw = sum(keyword_scores.get(k.lower(), 0) for k in (card.keywords or []))
        if not has_history:
            return trending
        return 0.3 * trending + 0.7 * kw

    unseen = [c for c in cards if c.id not in seen_card_ids]
    already_seen = [c for c in cards if c.id in seen_card_ids]

    ranked_unseen = sorted(unseen, key=_score, reverse=True)
    ranked_seen = sorted(already_seen, key=_score, reverse=True)

    return _diversify(ranked_unseen) + ranked_seen


def _diversify(cards: List[Card], cap: int = 4) -> List[Card]:
    """Prevent any single source from occupying more than `cap` of the top slots."""
    result: List[Card] = []
    source_counts: dict[str, int] = {}
    deferred: List[Card] = []

    for card in cards:
        src = card.source or "unknown"
        if source_counts.get(src, 0) < cap:
            result.append(card)
            source_counts[src] = source_counts.get(src, 0) + 1
        else:
            deferred.append(card)

    result.extend(deferred)
    return result
