"""
In-memory swipe/interaction store.

Tracks which cards each session has swiped and in which direction.
In production, replace with Supabase persistence.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from models.schemas import Card, Interaction
from services.ingestion import get_all_cards

# session_id -> list of Interaction records
_interactions: Dict[str, List[Interaction]] = defaultdict(list)


def record_interaction(interaction: Interaction) -> None:
    """Store a swipe / interaction event."""
    _interactions[interaction.session_id].append(interaction)


def get_interactions(session_id: str) -> List[Interaction]:
    """Return all interactions for a session."""
    return list(_interactions.get(session_id, []))


def get_swiped_ids(session_id: str) -> Set[str]:
    """Return card IDs the user has already swiped on (left or right)."""
    return {
        i.card_id
        for i in _interactions.get(session_id, [])
        if i.action in ("like", "skip", "swipe_right", "swipe_left")
    }


def get_liked_cards(session_id: str) -> List[Card]:
    """Return full Card objects for cards the user swiped right / liked."""
    liked_ids = {
        i.card_id
        for i in _interactions.get(session_id, [])
        if i.action in ("like", "swipe_right")
    }
    if not liked_ids:
        return []
    all_cards = get_all_cards()
    return [c for c in all_cards if c.id in liked_ids]


def clear_session(session_id: str) -> None:
    """Reset a session's history (useful for testing)."""
    _interactions.pop(session_id, None)


def clear_all() -> None:
    """Reset all sessions (useful for testing)."""
    _interactions.clear()
