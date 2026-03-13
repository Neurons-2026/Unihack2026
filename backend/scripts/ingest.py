import asyncio

from services.ingestion import fetch_trending_cards
from services.preprocessing import preprocess_cards
from services.recommendation import rank_cards


async def main():
  raw = await fetch_trending_cards("local")
  cleaned = await preprocess_cards(raw)
  ranked = await rank_cards(cleaned)
  for card in ranked:
    print(card.json())


if __name__ == "__main__":
  asyncio.run(main())
