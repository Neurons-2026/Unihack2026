import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from services.scrapers.github_trending import scrape_github_trending

SOURCE_SLUG = "github_trending"


def to_card_view(items: list[dict]) -> list[dict]:
    cards: list[dict] = []
    for item in items:
        summary_source = item.get("raw_summary") or item.get("title") or "Trending repository"
        card_summary = summary_source if len(summary_source) <= 120 else summary_source[:117].rstrip() + "..."
        language = (item.get("metadata") or {}).get("language")
        fallback_keyword = (language or "github").lower()
        score = ((item.get("ranking") or {}).get("source_rank_score")) or 0.0
        cards.append(
            {
                "id": item["id"],
                "card_title": f"GitHub trending: {item.get('title', item['id'])}",
                "card_summary": card_summary,
                "keywords": [fallback_keyword],
                "source": item["source"],
                "source_url": item["source_url"],
                "thumbnail_keyword": fallback_keyword,
                "trending_score": score,
            }
        )
    return cards


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape GitHub Trending and persist output locally.")
    parser.add_argument("--limit", type=int, default=10, help="Number of trending repos to scrape.")
    parser.add_argument(
        "--no-readme",
        action="store_true",
        help="Disable per-repo README fetching.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/scraped",
        help="Output directory relative to backend/.",
    )
    args = parser.parse_args()

    items = scrape_github_trending(limit=args.limit, include_readme=not args.no_readme)
    cards = to_card_view(items)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    root_dir = Path(args.output_dir)
    run_dir = root_dir / SOURCE_SLUG / date_key
    latest_dir = root_dir / SOURCE_SLUG / "latest"
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    content_items_path = run_dir / f"content_items_{stamp}.json"
    cards_path = run_dir / f"cards_{stamp}.json"
    latest_content_items_path = latest_dir / "content_items_latest.json"
    latest_cards_path = latest_dir / "cards_latest.json"

    content_items_json = json.dumps(items, indent=2, ensure_ascii=True)
    cards_json = json.dumps(cards, indent=2, ensure_ascii=True)

    content_items_path.write_text(content_items_json, encoding="utf-8")
    cards_path.write_text(cards_json, encoding="utf-8")
    latest_content_items_path.write_text(content_items_json, encoding="utf-8")
    latest_cards_path.write_text(cards_json, encoding="utf-8")

    print(f"Scraped {len(items)} items")
    print(f"Content items: {content_items_path}")
    print(f"Cards: {cards_path}")
    print(f"Latest content items: {latest_content_items_path}")
    print(f"Latest cards: {latest_cards_path}")


if __name__ == "__main__":
    main()
