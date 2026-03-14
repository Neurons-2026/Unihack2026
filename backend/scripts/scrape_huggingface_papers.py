import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from services.scrapers.huggingface_papers import scrape_huggingface_papers


def to_card_view(items: list[dict]) -> list[dict]:
    cards: list[dict] = []
    for item in items:
        summary_source = item.get("raw_summary") or item.get("title") or "Trending paper"
        card_summary = summary_source if len(summary_source) <= 120 else summary_source[:117].rstrip() + "..."
        score = ((item.get("ranking") or {}).get("source_rank_score")) or 0.0
        cards.append(
            {
                "id": item["id"],
                "card_title": f"HF paper: {item.get('title', item['id'])}",
                "card_summary": card_summary,
                "keywords": ["research"],
                "source": item["source"],
                "source_url": item["source_url"],
                "thumbnail_keyword": "paper",
                "trending_score": score,
            }
        )
    return cards


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape HuggingFace papers and persist output locally.")
    parser.add_argument("--limit", type=int, default=10, help="Number of papers to scrape from HF papers page.")
    parser.add_argument("--no-pdf", action="store_true", help="Disable PDF downloads.")
    parser.add_argument(
        "--pdf-limit",
        type=int,
        default=5,
        help="Maximum PDFs to download in this run.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/scraped",
        help="Output directory relative to backend/.",
    )
    parser.add_argument(
        "--pdf-dir",
        default="data/scraped/pdfs/huggingface",
        help="PDF directory relative to backend/.",
    )
    args = parser.parse_args()

    items = scrape_huggingface_papers(
        limit=args.limit,
        download_pdfs=not args.no_pdf,
        max_pdf_downloads=args.pdf_limit,
        pdf_dir=args.pdf_dir,
    )
    cards = to_card_view(items)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    content_items_path = out_dir / f"huggingface_papers_content_items_{stamp}.json"
    cards_path = out_dir / f"huggingface_papers_cards_{stamp}.json"
    latest_content_items_path = out_dir / "huggingface_papers_content_items_latest.json"
    latest_cards_path = out_dir / "huggingface_papers_cards_latest.json"

    content_items_json = json.dumps(items, indent=2, ensure_ascii=True)
    cards_json = json.dumps(cards, indent=2, ensure_ascii=True)

    content_items_path.write_text(content_items_json, encoding="utf-8")
    cards_path.write_text(cards_json, encoding="utf-8")
    latest_content_items_path.write_text(content_items_json, encoding="utf-8")
    latest_cards_path.write_text(cards_json, encoding="utf-8")

    downloaded_count = sum(1 for i in items if ((i.get("metadata") or {}).get("pdf_downloaded")))
    print(f"Scraped {len(items)} papers")
    print(f"Downloaded PDFs: {downloaded_count}")
    print(f"Content items: {content_items_path}")
    print(f"Cards: {cards_path}")
    print(f"Latest content items: {latest_content_items_path}")
    print(f"Latest cards: {latest_cards_path}")


if __name__ == "__main__":
    main()
