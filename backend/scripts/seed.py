import json
from pathlib import Path

from models.schemas import Card

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_cards.json"


def load_seed_cards() -> list[Card]:
    data = json.loads(SEED_PATH.read_text())
    return [Card(**item) for item in data]


if __name__ == "__main__":
    cards = load_seed_cards()
    for card in cards:
        print(card.json())
