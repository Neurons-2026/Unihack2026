import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from services.preprocessing import build_text_views, scraped_item_to_card
from services.scrapers.openai_news import scrape_openai_news


SOURCE = "openai_blog"
SOURCE_SLUG = "openai_news"


def _load_keywords_map(path: str) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _keywords_for_item(item: dict, keywords_map: dict) -> list[str]:
    url = item.get("url", "")
    slug = url.rstrip("/").split("/")[-1] if url else ""
    kws = keywords_map.get(url) or keywords_map.get(slug) or []
    return [str(k).strip() for k in kws if str(k).strip()]


def to_content_items(items: list[dict], keywords_map: dict) -> list[dict]:
    output: list[dict] = []
    for rank, item in enumerate(items, start=1):
        url = item.get("url", "")
        slug = url.rstrip("/").split("/")[-1] if url else f"item-{rank}"
        keywords = _keywords_for_item(item, keywords_map)
        output.append(
            {
                "schema_version": "1.0.0",
                "id": f"openai:{slug}",
                "source": SOURCE,
                "source_url": url,
                "title": item.get("title", ""),
                "raw_summary": "",
                "raw_content": item.get("raw_text", ""),
                "pipeline_state": "keywords_enriched" if keywords else "raw_scraped",
                "preprocessing": {},
                "ranking": {
                    "source_rank_score": max(0.0, (len(items) - rank + 1) / max(1, len(items))),
                    "trending_score": max(0.0, (len(items) - rank + 1) / max(1, len(items))),
                },
                "metadata": {
                    "published_date": item.get("date", ""),
                    "rank": rank,
                    "keywords": keywords,
                    "freshness_basis": "news_listing_order",
                },
                "provenance": {
                    "collector": "openai_news_scraper",
                    "collector_version": "0.2.0",
                    "dedupe_key": f"openai:{slug}",
                },
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        cleaned_text, preview_text = build_text_views(item.get("raw_text", ""))
        output[-1]["preprocessing"] = {
            "cleaned_text": cleaned_text,
            "preview_text": preview_text,
            "quality_notes": ["rss_scraped", "metadata_cleaned"],
            "enrichment_used": False,
        }
    return output


def to_card_view(items: list[dict], keywords_map: dict) -> list[dict]:
    cards: list[dict] = []
    for item in items:
        keywords = _keywords_for_item(item, keywords_map)
        cards.append(scraped_item_to_card(item, keywords=keywords, source=SOURCE))
    return cards


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape OpenAI News into standardized pipeline outputs.")
    parser.add_argument("--limit", type=int, default=5, help="Number of articles to scrape.")
    parser.add_argument("--output-dir", default="data/scraped", help="Output directory relative to backend/.")
    parser.add_argument(
        "--keywords-json",
        default="",
        help="Optional JSON path mapping {url_or_slug: [keywords]} from Harry's extractor.",
    )
    args = parser.parse_args()

    items = scrape_openai_news(n=args.limit)
    keywords_map = _load_keywords_map(args.keywords_json)
    content_items = to_content_items(items, keywords_map)
    cards = to_card_view(items, keywords_map)

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

    content_items_json = json.dumps(content_items, indent=2, ensure_ascii=True)
    cards_json = json.dumps(cards, indent=2, ensure_ascii=True)

    content_items_path.write_text(content_items_json, encoding="utf-8")
    cards_path.write_text(cards_json, encoding="utf-8")
    latest_content_items_path.write_text(content_items_json, encoding="utf-8")
    latest_cards_path.write_text(cards_json, encoding="utf-8")

    print(f"Scraped {len(items)} OpenAI articles")
    print(f"Content items: {content_items_path}")
    print(f"Cards: {cards_path}")


if __name__ == "__main__":
    main()
