import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from services.scrapers.openai_news import scrape_openai_news


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape OpenAI News.")
    parser.add_argument("--limit", type=int, default=3, help="Number of articles to scrape.")
    parser.add_argument("--output-dir", default="data/scraped", help="Output directory.")
    args = parser.parse_args()

    print(f"Scraping top {args.limit} articles from OpenAI News...")
    items = scrape_openai_news(n=args.limit)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"openai_news_{stamp}.json"
    latest_path = out_dir / "openai_news_latest.json"

    output = json.dumps(items, indent=2, ensure_ascii=False)
    out_path.write_text(output, encoding="utf-8")
    latest_path.write_text(output, encoding="utf-8")

    print(f"Scraped {len(items)} items")
    for item in items:
        print(f"  [{item['date'][:10] if item['date'] else 'no-date'}] {item['title']}")
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
